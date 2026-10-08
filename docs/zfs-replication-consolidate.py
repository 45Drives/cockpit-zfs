#!/usr/bin/env python3
"""Consolidate per-dataset ZFS replicas into one recursive replica without forced rollback.

Existing replicas with a shared snapshot are sent incrementally. Datasets with no
usable replica are sent in full. If the backup root cannot share a snapshot with the
source root (e.g. a backup pool root that only received children), a NEW backup root
is seeded and existing replicas are renamed under it (same pool, snapshots preserved).
"""

import argparse
import atexit
import datetime
import fcntl
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


DATASET_PATTERN = r"[A-Za-z][A-Za-z0-9_.:-]*(?:/[A-Za-z0-9_.:-]+)*"
SNAPSHOT = "migration-to-recursive"
VERSION = 3
# An incremental without -L fails if earlier replication used -L, so always send large blocks.
SEND_FLAGS = ["-L", "-e", "-c"]


class MigrationError(Exception):
    pass


def within(name, root):
    return name == root or name.startswith(root + "/")


def relocating(config):
    return config["legacy_root"] != config["destination_root"]


def validate_config(config):
    for key in ("source_root", "legacy_root", "destination_root"):
        if not isinstance(config.get(key), str) or not re.fullmatch(DATASET_PATTERN, config[key]):
            raise MigrationError(f"Invalid {key}; use an actual ZFS dataset path.")
    if not isinstance(config.get("ssh"), str) or not re.fullmatch(
        r"(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9][A-Za-z0-9.:-]*", config["ssh"]
    ):
        raise MigrationError("Invalid SSH destination; use an SSH alias or user@host.")
    if type(config.get("port")) is not int or not 1 <= config["port"] <= 65535:
        raise MigrationError("SSH port must be between 1 and 65535.")
    if config.get("identity") is not None and not isinstance(config["identity"], str):
        raise MigrationError("Invalid SSH identity path.")
    if not isinstance(config.get("hold_tag"), str) or not re.fullmatch(
        r"service-repl-[a-f0-9]{12}", config["hold_tag"]
    ):
        raise MigrationError("Invalid migration hold tag.")
    if relocating(config) and config["legacy_root"].split("/")[0] != config["destination_root"].split("/")[0]:
        raise MigrationError("The new backup root must be in the same backup pool as the existing replicas.")


def prompt_config():
    config: dict = {
        "source_root": input("Source dataset root: ").strip(),
        "legacy_root": input("Backup root that holds the EXISTING replicas: ").strip(),
    }
    suggested = f"{config['legacy_root']}/{config['source_root'].rsplit('/', 1)[-1]}"
    config["destination_root"] = input(
        f"Backup root for the NEW recursive task [{suggested}] "
        f"(type {config['legacy_root']} to reuse the existing root in place): "
    ).strip() or suggested
    config.update(
        ssh=input("Backup SSH destination (user@host or SSH alias): ").strip(),
        port=int(input("SSH port [22]: ").strip() or "22"),
        identity=input("SSH identity file [blank for SSH defaults]: ").strip() or None,
        hold_tag="service-repl-" + uuid.uuid4().hex[:12],
    )
    if config["identity"]:
        config["identity"] = str(Path(config["identity"]).expanduser().resolve())
    validate_config(config)
    return config


def confirm(action):
    if input(f"Service approval is required. Type {action} to continue: ").strip() != action:
        raise MigrationError("Not approved; no new operation started.")


class Transport:
    def __init__(self, config):
        validate_config(config)
        self.config = config
        self.control_dir = tempfile.mkdtemp(prefix="zfs-consolidate-")
        atexit.register(self.close)

    def close(self):
        try:
            subprocess.run(
                self.command(["true"], True)[:-2] + ["-O", "exit", self.config["ssh"]],
                capture_output=True, timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            pass
        shutil.rmtree(self.control_dir, ignore_errors=True)

    def command(self, args, remote=False):
        if not remote:
            return args
        command = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=15", "-p", str(self.config["port"]),
            "-o", "ControlMaster=auto", "-o", "ControlPersist=60",
            "-o", f"ControlPath={self.control_dir}/%C",
        ]
        if self.config.get("identity"):
            command += ["-i", str(Path(self.config["identity"]).expanduser())]
        return command + [self.config["ssh"], " ".join(shlex.quote(arg) for arg in args)]

    def capture(self, args, remote=False):
        result = subprocess.run(
            self.command(args, remote), capture_output=True, text=True, timeout=120,
        )
        if result.returncode:
            raise MigrationError(result.stderr.strip() or f"Command failed: {args}")
        return result

    def query(self, args, remote=False):
        return self.capture(args, remote).stdout.strip()

    def inventory(self, root, remote=False, recursive=True, missing_ok=False):
        datasets = {}
        result = subprocess.run(self.command([
            "zfs", "list", "-H", "-p", *(["-r"] if recursive else []), "-t", "filesystem,volume",
            "-o", "name,type,origin,encryption,receive_resume_token", root,
        ], remote), capture_output=True, text=True, timeout=120)
        if result.returncode:
            if missing_ok and "does not exist" in result.stderr:
                return {}
            raise MigrationError(result.stderr.strip() or f"Cannot list {root}")
        for line in result.stdout.strip().splitlines():
            name, kind, origin, encryption, token = line.split("\t")
            if name != root and not name.startswith(root + "/"):
                raise MigrationError(f"Unexpected dataset outside selected root: {name}")
            datasets[name] = {
                "type": kind, "origin": origin, "encryption": encryption,
                "token": token, "snapshots": [],
            }
        if root not in datasets:
            raise MigrationError(f"Root dataset not found: {root}")
        output = self.query([
            "zfs", "list", "-H", "-p", *(["-r"] if recursive else ["-d", "1"]), "-t", "snapshot",
            "-o", "name,guid,createtxg", root,
        ], remote)
        for line in output.splitlines():
            name, guid, txg = line.split("\t")
            dataset = name.split("@", 1)[0]
            if dataset not in datasets:
                raise MigrationError(f"Snapshot dataset absent from inventory: {name}")
            datasets[dataset]["snapshots"].append({"name": name, "guid": guid, "txg": int(txg)})
        for dataset in datasets.values():
            dataset["snapshots"].sort(key=lambda snapshot: snapshot["txg"])
        return datasets

    def dataset(self, name, remote=False):
        return self.inventory(name, remote, recursive=False, missing_ok=True).get(name)

    def rename(self, old, new):
        self.query(["zfs", "rename", old, new], True)

    def resume_target(self, token):
        if not re.fullmatch(r"[0-9A-Za-z-]+", token):
            raise MigrationError("Unexpected receive resume token format.")
        result = self.capture(["zfs", "send", "-nv", "-t", token])
        match = re.search(r"^\s*toname = (\S+)\s*$", result.stdout + "\n" + result.stderr, re.M)
        if not match:
            raise MigrationError("Cannot read the resume token's target snapshot.")
        return match.group(1)

    def written(self, dataset, snapshot):
        suffix = snapshot.split("@", 1)[1]
        value = self.query([
            "zfs", "get", "-H", "-p", "-o", "value", f"written@{suffix}", dataset,
        ], True)
        if not value.isdigit():
            raise MigrationError(f"Cannot check backup writes: {dataset}")
        return int(value)

    def has_hold(self, snapshot, remote=False):
        output = self.query(["zfs", "holds", "-H", snapshot], remote)
        return any(
            fields[0] == snapshot and fields[1] == self.config["hold_tag"]
            for line in output.splitlines()
            if len(fields := line.split("\t")) >= 2
        )

    def hold(self, snapshot, remote=False):
        if not self.has_hold(snapshot, remote):
            self.query(["zfs", "hold", self.config["hold_tag"], snapshot], remote)
        if not self.has_hold(snapshot, remote):
            raise MigrationError(f"Hold verification failed: {snapshot}")

    def estimate(self, send_args):
        target = send_args[-1]
        result = self.capture(["zfs", "send", "-nPv", *send_args])
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        sizes = []
        for line in output.splitlines():
            fields = line.split("\t")
            if len(fields) == 2 and fields[0] == "size" and fields[1].isdigit():
                sizes.append(int(fields[1]))
        if len(sizes) != 1:
            raise MigrationError(f"Cannot parse send estimate for {target}; review installed ZFS output.")
        return {"bytes": sizes[0], "output": output}

    def transfer(self, send_args, destination):
        sender = subprocess.Popen(["zfs", "send", *send_args], stdout=subprocess.PIPE)
        pipe = sender.stdout
        assert pipe is not None
        receiver = None
        try:
            receiver = subprocess.Popen(
                self.command(["zfs", "receive", "-s", "-u", destination], True),
                stdin=pipe,
            )
            pipe.close()
            receive_status = receiver.wait()
            if receive_status and sender.poll() is None:
                sender.terminate()
            send_status = sender.wait()
            if send_status or receive_status:
                raise MigrationError(
                    f"Transfer failed (send={send_status}, receive={receive_status}). "
                    "Give Service the log; after approval, run copy again to resume."
                )
        finally:
            pipe.close()
            for process in (receiver, sender):
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait()


def latest_snapshot(dataset):
    return dataset["snapshots"][-1] if dataset and dataset["snapshots"] else None


def migration_snapshot(name, dataset):
    return next((snapshot for snapshot in dataset["snapshots"] if snapshot["name"] == f"{name}@{SNAPSHOT}"), None)


def unusable(source, backup):
    if backup["encryption"] != "off" or backup["origin"] != "-" or backup["token"] != "-":
        return "Backup copy has encryption, a clone origin, or a pending receive."
    if source["type"] != backup["type"]:
        return "Source and backup dataset types differ."
    return None


def find_base(transport, source, backup_name, backup):
    reason = unusable(source, backup)
    if reason:
        return None, reason
    latest = latest_snapshot(backup)
    if not latest:
        return None, "Backup copy has no snapshots."
    base = next((snapshot for snapshot in source["snapshots"] if snapshot["guid"] == latest["guid"]), None)
    if not base:
        return None, "Latest backup snapshot is not shared with the source."
    if transport.written(backup_name, latest["name"]):
        return None, "Backup has data written after its latest snapshot."
    return {"base_source": base["name"], "base_destination": latest["name"], "base_guid": base["guid"]}, None


def load_inventories(transport):
    config = transport.config
    source = transport.inventory(config["source_root"])
    destination = transport.inventory(config["destination_root"], True, missing_ok=True)
    if not relocating(config):
        return source, destination, destination
    legacy = {
        name: dataset for name, dataset in transport.inventory(config["legacy_root"], True).items()
        if not within(name, config["destination_root"])
    }
    return source, destination, legacy


def legacy_review(config, rows, legacy):
    """Return (blockers, left_in_place) for existing backup datasets."""
    by_legacy = {row["legacy"]: row for row in rows}
    renamed = [row["legacy"] for row in rows if row["rename"]]
    blockers, left = [], []
    for name in sorted(legacy):
        row = by_legacy.get(name)
        moves = any(within(name, root) for root in renamed)
        if not relocating(config):
            if row is None:
                blockers.append(f"Backup-only dataset requires review: {name}")
        elif moves and (row is None or row["action"] != "incremental"):
            blockers.append(f"{name} would be moved along with its renamed parent; Service review required.")
        elif not moves:
            left.append(name)
    return blockers, left


def new_row(config, name):
    suffix = name[len(config["source_root"]):]
    return {
        "source": name, "destination": config["destination_root"] + suffix,
        "legacy": config["legacy_root"] + suffix, "action": None, "rename": False,
        "status": "BLOCKED", "reason": "", "note": "",
        "base_source": None, "base_destination": None, "base_guid": None, "migration_guid": None,
    }


def classify(transport):
    config = transport.config
    relocate = relocating(config)
    source, destination, legacy = load_inventories(transport)
    rows, by_source, blockers = [], {}, []
    for name in sorted(source):
        row = new_row(config, name)
        rows.append(row)
        by_source[name] = row
        dataset = source[name]
        parent = by_source.get(name.rsplit("/", 1)[0]) if name != config["source_root"] else None
        if dataset["encryption"] != "off" or dataset["origin"] != "-" or dataset["token"] != "-":
            row["reason"] = "Source has encryption, a clone origin, or a pending receive."
            continue
        if relocate and within(row["legacy"], config["destination_root"]):
            row["reason"] = "Existing replica path overlaps the new backup root."
            continue
        # In relocation mode the new root is always seeded fresh; the existing root is never reused.
        candidate = None if relocate and parent is None else legacy.get(row["legacy"])
        if candidate is None:
            row.update(action="full", status="READY")
            continue
        base, why = find_base(transport, dataset, row["legacy"], candidate)
        if base:
            row.update(base, action="incremental", status="READY")
            row["rename"] = relocate and (parent is None or parent["action"] != "incremental")
            if row["rename"] and within(config["destination_root"], row["legacy"]):
                row.update(status="BLOCKED", reason="The new backup root is inside this existing replica.")
        elif relocate:
            row.update(action="full", status="READY", note=f"Existing copy {row['legacy']} is not usable ({why}) and is left in place.")
        else:
            row["reason"] = why or ""
            if parent is None:
                row["reason"] += (
                    f" In-place mode cannot work for this root. Re-run check and press Enter at the"
                    f" NEW backup root prompt to use {config['legacy_root']}/{name.rsplit('/', 1)[-1]}."
                )
    if relocate and destination:
        blockers.append(f"New backup root {config['destination_root']} already exists; choose a name that does not exist.")
    if not destination:
        parent = config["destination_root"].rsplit("/", 1)[0] if "/" in config["destination_root"] else None
        if parent is None or transport.dataset(parent, True) is None:
            blockers.append(f"Parent of backup root {config['destination_root']} does not exist on the backup.")
    legacy_blockers, left = legacy_review(config, rows, legacy)
    blockers += legacy_blockers
    if any(
        snapshot["name"].endswith("@" + SNAPSHOT)
        for dataset in list(source.values()) + list(destination.values()) + list(legacy.values())
        for snapshot in dataset["snapshots"]
    ):
        blockers.append("Migration snapshot already exists. Do not start a new migration over it.")
    blockers = [f"{row['source']}: {row['reason']}" for row in rows if row["status"] == "BLOCKED"] + blockers
    return {"datasets": rows, "blockers": blockers, "left_in_place": left}


def observe_row(transport, row, source, destination, legacy):
    """Return (status, location, reason); status is READY, PARTIAL, COMPLETE, or BLOCKED."""
    if source is None:
        return "BLOCKED", None, "Source dataset missing."
    migration = migration_snapshot(row["source"], source)
    if row["migration_guid"] and (not migration or migration["guid"] != row["migration_guid"]):
        return "BLOCKED", None, "Source migration snapshot identity changed."
    if destination is not None:
        location, backup = row["destination"], destination
    elif row["action"] == "incremental" and legacy is not None:
        location, backup = row["legacy"], legacy
    elif row["action"] == "full":
        return "READY", None, ""
    else:
        return "BLOCKED", None, "Existing backup replica not found."
    if backup["token"] != "-":
        if location == row["destination"] and row["migration_guid"]:
            return "PARTIAL", location, "Interrupted receive; copy will resume it."
        return "BLOCKED", location, "Backup has a pending receive."
    reason = unusable(source, backup)
    if reason:
        return "BLOCKED", location, reason
    latest = latest_snapshot(backup)
    if latest and latest["name"] == f"{location}@{SNAPSHOT}":
        if (location == row["destination"] and migration and latest["guid"] == migration["guid"]
                and not transport.written(location, latest["name"])):
            return "COMPLETE", location, ""
        return "BLOCKED", location, "Backup migration snapshot mismatched or modified after receive."
    if row["action"] == "full":
        return "BLOCKED", location, f"{location} already exists; a full transfer would overwrite it."
    if not latest or latest["guid"] != row["base_guid"]:
        return "BLOCKED", location, "Latest backup snapshot no longer matches the approved starting snapshot."
    base = next((snapshot for snapshot in source["snapshots"] if snapshot["guid"] == row["base_guid"]), None)
    if not base:
        return "BLOCKED", location, "Approved source starting snapshot is missing."
    if migration and base["txg"] >= migration["txg"]:
        return "BLOCKED", location, "Starting snapshot is not older than the migration snapshot."
    if transport.written(location, latest["name"]):
        return "BLOCKED", location, "Backup has data written after the starting snapshot."
    return "READY", location, ""


def observe_all(transport, plan, require_absent=False, require_snapshot=False):
    config = transport.config
    rows = plan["datasets"]
    source, destination, legacy = load_inventories(transport)
    if set(source) != {row["source"] for row in rows}:
        raise MigrationError("Source dataset hierarchy changed; Service review required.")
    extras = sorted(set(destination) - {row["destination"] for row in rows})
    if extras:
        raise MigrationError("Unexpected datasets under the backup root: " + ", ".join(extras))
    blockers, _ = legacy_review(config, rows, legacy)
    if blockers:
        raise MigrationError("Backup layout changed:\n" + "\n".join(blockers))
    if require_absent and any(
        snapshot["name"].endswith("@" + SNAPSHOT)
        for dataset in list(source.values()) + list(destination.values()) + list(legacy.values())
        for snapshot in dataset["snapshots"]
    ):
        raise MigrationError("Migration snapshot already exists. Do not start a new migration over it.")
    if require_snapshot:
        found = [migration_snapshot(name, dataset) for name, dataset in source.items()]
        if not all(found) or len({snapshot["txg"] for snapshot in found if snapshot}) != 1:
            raise MigrationError("Migration snapshots are not one complete recursive snapshot set.")
        if any(not row["migration_guid"] for row in rows):
            raise MigrationError("Plan does not pin migration snapshots; prepare did not finish.")
    return {
        row["source"]: observe_row(
            transport, row, source.get(row["source"]), destination.get(row["destination"]),
            legacy.get(row["legacy"]) if relocating(config) else None,
        )
        for row in rows
    }


def observe_one(transport, row):
    legacy = transport.dataset(row["legacy"], True) if row["legacy"] != row["destination"] else None
    return observe_row(
        transport, row, transport.dataset(row["source"]), transport.dataset(row["destination"], True), legacy,
    )


def expect(observations, allowed):
    problems = [
        f"{name}: {status} {reason}".strip()
        for name, (status, _, reason) in observations.items() if status not in allowed
    ]
    if problems:
        raise MigrationError("Preflight blocked; Service review required:\n" + "\n".join(problems))


def save_state(path, state, new=False):
    if new:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(state, output, indent=2)
            output.write("\n")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(state, output, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def event(path, status, message):
    record = {
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": status, "message": message,
    }
    with path.with_suffix(".log.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    print(f"{status}: {message}", flush=True)


def report(path, config, plan, stage):
    lines = [
        f"ZFS migration report: {stage}",
        f"Source root: {config['source_root']}",
        f"Existing replicas: {config['ssh']}:{config['legacy_root']}",
        f"New recursive backup root: {config['ssh']}:{config['destination_root']}",
        "Mode: " + ("RELOCATE (new root seeded, usable replicas renamed under it)"
                    if relocating(config) else "IN PLACE"),
        f"Hold tag: {config['hold_tag']}",
        "",
    ]
    labels = {"incremental": "INCREMENTAL", "full": "FULL"}
    for row in plan["datasets"]:
        label = "MOVE + INCREMENTAL" if row["rename"] else labels.get(row["action"], "-")
        lines.append(f"{row['status']} [{label}]: {row['source']} -> {row['destination']} {row['reason']}".rstrip())
        if row["rename"]:
            lines.append(f"  Rename on backup: {row['legacy']} -> {row['destination']}")
        if row["note"]:
            lines.append("  " + row["note"])
        if row["base_source"]:
            lines.append(f"  Base: {row['base_source']} -> {row['base_destination']} (GUID {row['base_guid']})")
        if row["migration_guid"]:
            lines.append(f"  Migration GUID: {row['migration_guid']}")
        if "estimate" in row:
            lines.append(f"  Estimated stream bytes: {row['estimate']['bytes']}")
            lines.append(row["estimate"]["output"])
    counts = {label: sum(row["action"] == key for row in plan["datasets"]) for key, label in labels.items()}
    lines.append("")
    lines.append(f"Datasets: {len(plan['datasets'])} ({counts['INCREMENTAL']} incremental, {counts['FULL']} full, "
                 f"{sum(row['rename'] for row in plan['datasets'])} renames)")
    if any("estimate" in row for row in plan["datasets"]):
        total = sum(row.get("estimate", {}).get("bytes", 0) for row in plan["datasets"])
        lines.append(f"Total estimated stream bytes: {total} ({total / 1024 ** 3:.2f} GiB)")
        lines.append("Service must check backup capacity separately; stream size is not disk usage.")
    if plan.get("left_in_place"):
        lines.append("Left in place on the backup (not part of the new task): " + ", ".join(plan["left_in_place"]))
    lines.extend("BLOCKER: " + blocker for blocker in plan.get("blockers", []))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = path.with_suffix(f".{stage}-{stamp}.txt")
    with filename.open("x", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    print(f"Report: {filename}", flush=True)


def backup_base(row, location):
    return f"{location}@{row['base_destination'].split('@', 1)[1]}"


def require_holds(transport, plan, observations):
    for row in plan["datasets"]:
        if not transport.has_hold(f"{row['source']}@{SNAPSHOT}"):
            raise MigrationError(f"Source migration hold missing: {row['source']}")
        if row["action"] != "incremental":
            continue
        if not transport.has_hold(row["base_source"]):
            raise MigrationError(f"Source starting hold missing: {row['base_source']}")
        held = backup_base(row, observations[row["source"]][1])
        if not transport.has_hold(held, True):
            raise MigrationError(f"Backup starting hold missing: {held}")


def send_args(row):
    target = f"{row['source']}@{SNAPSHOT}"
    base = ["-i", row["base_source"]] if row["action"] == "incremental" else []
    return SEND_FLAGS + base + [target]


def prepare(transport, state, path):
    if state["phase"] != "checked":
        raise MigrationError("Prepare is only allowed after check. Do not repeat snapshot creation; ask Service.")
    plan = state["plan"]
    observations = observe_all(transport, plan, require_absent=True)
    expect(observations, {"READY"})
    print("This protects starting snapshots and creates ONE recursive migration snapshot set.")
    print("Pause applications first if application-consistent snapshots are required.")
    confirm("PREPARE")
    state["phase"] = "preparing"
    save_state(path, state)
    for row in plan["datasets"]:
        if row["action"] != "incremental":
            continue
        transport.hold(row["base_source"])
        event(path, "HELD_SOURCE_BASE", row["base_source"])
        held = backup_base(row, observations[row["source"]][1])
        transport.hold(held, True)
        event(path, "HELD_BACKUP_BASE", held)
    expect(observe_all(transport, plan, require_absent=True), {"READY"})
    target = f"{transport.config['source_root']}@{SNAPSHOT}"
    transport.query(["zfs", "snapshot", "-r", target])
    event(path, "SNAPSHOT_CREATED", target)
    transport.query(["zfs", "hold", "-r", transport.config["hold_tag"], target])
    source = transport.inventory(transport.config["source_root"])
    for row in plan["datasets"]:
        snapshot = migration_snapshot(row["source"], source.get(row["source"], {"snapshots": []}))
        if not snapshot:
            raise MigrationError(f"Source migration snapshot missing: {row['source']}")
        row["migration_guid"] = snapshot["guid"]
    observations = observe_all(transport, plan, require_snapshot=True)
    expect(observations, {"READY"})
    require_holds(transport, plan, observations)
    for row in plan["datasets"]:
        row["estimate"] = transport.estimate(send_args(row))
    report(path, transport.config, plan, "transfer")
    state.update(phase="prepared", plan=plan)
    save_state(path, state)
    print("PREPARE PASSED. Applications paused only for snapshot creation may resume.")
    print("Service must approve the transfer report and backup capacity before copy.")


def copy(transport, state, path):
    if state["phase"] not in ("prepared", "completed"):
        raise MigrationError("Copy requires a successful prepare. Ask Service about incomplete preparation.")
    plan = state["plan"]
    observations = observe_all(transport, plan, require_snapshot=True)
    expect(observations, {"READY", "PARTIAL", "COMPLETE"})
    require_holds(transport, plan, observations)
    print("Review the transfer report with Service before approving these renames and transfers.")
    confirm("COPY")
    for row in plan["datasets"]:
        label = f"{row['source']} -> {row['destination']}"
        target = f"{row['source']}@{SNAPSHOT}"
        status, location, reason = observe_one(transport, row)
        result = "VERIFIED"
        if status == "PARTIAL":
            token = transport.dataset(row["destination"], True)["token"]
            if transport.resume_target(token) != target:
                raise MigrationError(f"Resume token on {row['destination']} does not target {target}.")
            event(path, "RESUMING", label)
            transport.transfer(["-t", token], row["destination"])
            status, location, reason = observe_one(transport, row)
        elif status == "READY":
            if row["action"] == "incremental" and location != row["destination"]:
                if not row["rename"]:
                    raise MigrationError(f"{row['legacy']} did not move with its parent; Service review required.")
                transport.rename(row["legacy"], row["destination"])
                event(path, "RENAMED", f"{row['legacy']} -> {row['destination']}")
                status, location, reason = observe_one(transport, row)
                if status != "READY" or location != row["destination"]:
                    raise MigrationError(f"Post-rename check failed: {row['destination']}: {status} {reason}")
            event(path, "STARTED", label)
            transport.transfer(send_args(row), row["destination"])
            status, location, reason = observe_one(transport, row)
        elif status == "COMPLETE":
            result = "SKIPPED"
        if status != "COMPLETE":
            raise MigrationError(f"Verification failed: {label}: {status} {reason}")
        transport.hold(f"{row['destination']}@{SNAPSHOT}", True)
        event(path, result, label)
    verify(transport, state)
    state["phase"] = "completed"
    save_state(path, state)
    print("COPY PASSED. Run verify before testing the new task.")


def verify(transport, state):
    if state["phase"] not in ("prepared", "completed"):
        raise MigrationError("Verify requires a successful prepare.")
    plan = state["plan"]
    observations = observe_all(transport, plan, require_snapshot=True)
    expect(observations, {"COMPLETE"})
    require_holds(transport, plan, observations)
    for row in plan["datasets"]:
        if not transport.has_hold(f"{row['destination']}@{SNAPSHOT}", True):
            raise MigrationError(f"Backup migration hold missing: {row['destination']}")
    print(f"VERIFY PASSED: all {len(plan['datasets'])} datasets match under {transport.config['destination_root']}.")
    print("Snapshot, written-data, receive-token, and hold checks passed. This is not a complete backup-change audit.")
    if plan.get("left_in_place"):
        print("Left in place on the backup (Service to review): " + ", ".join(plan["left_in_place"]))


def run_mode(mode, path):
    if mode == "check":
        if path.exists():
            raise MigrationError("State file already exists. Keep it; do not restart check over an existing migration.")
        config = prompt_config()
        transport = Transport(config)
        plan = classify(transport)
        report(path, config, plan, "readiness")
        if plan["blockers"]:
            raise MigrationError("Readiness has blockers. Give the report to Service; do not prepare.")
        save_state(path, {"version": VERSION, "phase": "checked", "config": config, "plan": plan}, new=True)
        print("CHECK PASSED. No ZFS snapshots, holds, or transfers were created.")
        print("Have Service review the readiness report before prepare.")
        return
    with path.open(encoding="utf-8") as source:
        state = json.load(source)
    if state.get("version") != VERSION:
        raise MigrationError("Unsupported state file; use this script's own state, not an old plan.")
    transport = Transport(state["config"])
    if mode == "prepare":
        prepare(transport, state, path)
    elif mode == "copy":
        copy(transport, state, path)
    else:
        verify(transport, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "prepare", "copy", "verify"))
    parser.add_argument("--state", type=Path, default=Path("migration-state.json"))
    args = parser.parse_args()
    path = args.state.resolve()
    try:
        descriptor = os.open(path.with_suffix(".lock"), os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(descriptor, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise MigrationError("Another command is using this state file; do not run concurrent migrations.") from None
            run_mode(args.mode, path)
        return 0
    except (MigrationError, OSError, ValueError, KeyError, TypeError, EOFError, subprocess.SubprocessError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        try:
            event(path, "FAILED", f"{args.mode}: {error}")
        except OSError:
            pass
        return 2
    except KeyboardInterrupt:
        print("STOPPED: Interrupted. Give Service the log; after approval, run the same command again.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())