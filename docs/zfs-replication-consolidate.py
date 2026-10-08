#!/usr/bin/env python3
"""Consolidate per-dataset ZFS replicas into one recursive replica without resending existing data.

Existing replicas with a shared snapshot are sent incrementally, in place. Datasets with no
usable replica are sent in full. If the backup root never received the source root (the usual
case for a backup pool root), only that root dataset's own data is overwritten by a full send of
the source root; child datasets are not touched or moved. --new-root relocates instead.
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
import time
import uuid
from pathlib import Path


DATASET_PATTERN = r"[A-Za-z][A-Za-z0-9_.:-]*(?:/[A-Za-z0-9_.:-]+)*"
SNAPSHOT = "migration-to-recursive"
VERSION = 5
# An incremental without -L fails if earlier replication used -L, so always send large blocks.
SEND_FLAGS = ["-L", "-e", "-c"]


class MigrationError(Exception):
    pass


def within(name, root):
    return name == root or name.startswith(root + "/")


def size(count):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if count < 1024:
            return f"{count:.0f} {unit}" if unit == "B" else f"{count:.2f} {unit}"
        count /= 1024
    return f"{count:.2f} TiB"


def relocating(config):
    return config["legacy_root"] != config["destination_root"]


def park_root(config):
    return f"{config['legacy_root'].split('/')[0]}/migration-parked-{config['hold_tag'][-12:]}"


def parked_name(config, park, name):
    if any(within(name, top) for top in park):
        return park_root(config) + name[len(config["legacy_root"]):]
    return None


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


def prompt_config(port=22, identity=None):
    config: dict = {
        "source_root": input("Source dataset root: ").strip(),
        "legacy_root": input("Backup root that holds the EXISTING replicas: ").strip(),
    }
    # Final value is chosen by choose_destination() once the backup can be inspected.
    config["destination_root"] = config["legacy_root"]
    config.update(
        ssh=input("Backup SSH destination (user@host or SSH alias): ").strip(),
        port=port,
        identity=identity,
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

    def rename(self, old, new, parents=False):
        self.query(["zfs", "rename", *(["-p"] if parents else []), old, new], True)

    def resume_target(self, token):
        if not re.fullmatch(r"[0-9A-Za-z-]+", token):
            raise MigrationError("Unexpected receive resume token format.")
        result = self.capture(["zfs", "send", "-nv", "-t", token])
        match = re.search(r"^\s*toname = (\S+)\s*$", result.stdout + "\n" + result.stderr, re.M)
        if not match:
            raise MigrationError("Cannot read the resume token's target snapshot.")
        return match.group(1)

    def used_by_dataset(self, name):
        value = self.query(["zfs", "get", "-H", "-p", "-o", "value", "usedbydataset", name], True)
        return int(value) if value.isdigit() else 0

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

    def transfer(self, send_args, destination, overwrite=False, progress=None):
        """Send and receive one dataset; return the number of stream bytes sent."""
        receive = ["zfs", "receive", "-s", *(["-F"] if overwrite else ["-u"]), destination]
        sender = subprocess.Popen(["zfs", "send", *send_args], stdout=subprocess.PIPE)
        receiver = subprocess.Popen(self.command(receive, True), stdin=subprocess.PIPE)
        assert sender.stdout is not None and receiver.stdin is not None
        sent = 0
        try:
            try:
                while chunk := sender.stdout.read(1 << 20):
                    receiver.stdin.write(chunk)
                    sent += len(chunk)
                    if progress:
                        progress(sent)
            except BrokenPipeError:
                pass
            finally:
                try:
                    receiver.stdin.close()
                except BrokenPipeError:
                    pass
            receive_status = receiver.wait()
            if receive_status and sender.poll() is None:
                sender.terminate()
            send_status = sender.wait()
            if send_status or receive_status:
                raise MigrationError(
                    f"Transfer failed (send={send_status}, receive={receive_status}). "
                    "Give Service the log; after approval, run copy again to resume."
                )
            return sent
        finally:
            sender.stdout.close()
            for process in (receiver, sender):
                if process.poll() is None:
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
    parked = transport.inventory(park_root(config), True, missing_ok=True)
    if not relocating(config):
        return source, destination, destination, parked
    legacy = {
        name: dataset for name, dataset in transport.inventory(config["legacy_root"], True).items()
        if not within(name, config["destination_root"]) and not within(name, park_root(config))
    }
    return source, destination, legacy, parked


def backup_layout(config, rows, legacy):
    """Return (park, left): backup datasets to move aside out of the new tree, and those left untouched."""
    by_legacy = {row["legacy"]: row for row in rows}
    renamed = [row["legacy"] for row in rows if row["rename"]]
    park, left = [], []
    for name in sorted(legacy):
        if name == config["destination_root"] or any(within(name, top) for top in park):
            continue
        row = by_legacy.get(name)
        if relocating(config):
            lands_in_new_tree = any(within(name, root) for root in renamed)
            if lands_in_new_tree and (row is None or row["action"] != "incremental"):
                park.append(name)
            elif not lands_in_new_tree:
                left.append(name)
        elif row is None:
            # Kept in place; a non-forced recursive receive ignores datasets the source does not have.
            left.append(name)
        elif row["action"] == "full" and not row["overwrite"]:
            park.append(name)
    return park, left


def existing_replica(config, park, row, lookup):
    """Return (name, dataset, pending_park) for a replica that is not yet at its destination."""
    moved = parked_name(config, park, row["legacy"])
    if moved:
        dataset = lookup(moved)
        if dataset is not None:
            return moved, dataset, False
    if relocating(config):
        return row["legacy"], lookup(row["legacy"]), False
    return row["legacy"], None, moved is not None


def new_row(config, name):
    suffix = name[len(config["source_root"]):]
    return {
        "source": name, "destination": config["destination_root"] + suffix,
        "legacy": config["legacy_root"] + suffix, "action": None, "rename": False, "overwrite": False,
        "status": "BLOCKED", "reason": "", "note": "",
        "base_source": None, "base_destination": None, "base_guid": None, "migration_guid": None,
    }


def classify(transport):
    config = transport.config
    relocate = relocating(config)
    source, destination, legacy, _ = load_inventories(transport)
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
        elif not relocate and not candidate["snapshots"] and not unusable(dataset, candidate):
            # No snapshots means it never received a replica; usually an empty container dataset.
            row.update(
                action="full", overwrite=True, status="READY",
                note=f"{row['legacy']} has no snapshots. Its own data "
                     f"({size(transport.used_by_dataset(row['legacy']))}) is replaced; child datasets are not touched.",
            )
        elif relocate or parent is not None:
            row.update(action="full", status="READY", note=why or "")
        else:
            row["reason"] = (why or "") + (
                " The backup root has snapshots or is encrypted, so it cannot be overwritten in place."
                " Service review required (see --new-root)."
            )
    park, left = backup_layout(config, rows, legacy)
    for row in rows:
        moved = parked_name(config, park, row["legacy"])
        if row["action"] == "incremental" and moved and not relocate:
            parent = by_source.get(row["source"].rsplit("/", 1)[0])
            row["rename"] = parent is None or parent["action"] != "incremental"
        if row["action"] == "full" and row["note"] and not row["overwrite"]:
            row["note"] = f"Existing copy {row['legacy']} is not usable ({row['note']}) and " + (
                f"will be moved aside to {moved}." if moved else "is left in place."
            )
    if park and transport.dataset(park_root(config), True) is not None:
        blockers.append(f"{park_root(config)} already exists; Service review required.")
    if relocate and destination:
        blockers.append(f"New backup root {config['destination_root']} already exists; choose a name that does not exist.")
    if not destination:
        parent = config["destination_root"].rsplit("/", 1)[0] if "/" in config["destination_root"] else None
        if parent is None or transport.dataset(parent, True) is None:
            blockers.append(f"Parent of backup root {config['destination_root']} does not exist on the backup.")
    if any(
        snapshot["name"].endswith("@" + SNAPSHOT)
        for dataset in list(source.values()) + list(destination.values()) + list(legacy.values())
        for snapshot in dataset["snapshots"]
    ):
        blockers.append("Migration snapshot already exists. Do not start a new migration over it.")
    blockers = [f"{row['source']}: {row['reason']}" for row in rows if row["status"] == "BLOCKED"] + blockers
    return {"datasets": rows, "blockers": blockers, "left_in_place": left, "park": park}


def observe_row(transport, row, source, destination, existing):
    """Return (status, location, reason); status is READY, PARTIAL, COMPLETE, or BLOCKED."""
    legacy_name, legacy, pending_park = existing
    if source is None:
        return "BLOCKED", None, "Source dataset missing."
    migration = migration_snapshot(row["source"], source)
    if row["migration_guid"] and (not migration or migration["guid"] != row["migration_guid"]):
        return "BLOCKED", None, "Source migration snapshot identity changed."
    if destination is not None and pending_park and row["action"] == "full":
        # The unusable copy at this path is moved aside at the start of copy.
        return "READY", None, ""
    if destination is not None:
        location, backup = row["destination"], destination
    elif row["action"] == "incremental" and legacy is not None:
        location, backup = legacy_name, legacy
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
    if row["overwrite"] and latest is None:
        return "READY", location, ""
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
    park = plan["park"]
    source, destination, legacy, parked = load_inventories(transport)
    if set(source) != {row["source"] for row in rows}:
        raise MigrationError("Source dataset hierarchy changed; Service review required.")
    allowed = set(plan.get("left_in_place", []))
    extras = sorted(
        name for name in set(destination) - {row["destination"] for row in rows}
        if name not in allowed and not within(name, park_root(config))
        and not any(within(name, top) for top in park)
    )
    if extras:
        raise MigrationError("Unexpected datasets under the backup root: " + ", ".join(extras))
    found, _ = backup_layout(config, rows, legacy)
    legacy_names = {row["legacy"] for row in rows}
    unexpected = [
        name for name in found
        if name not in legacy_names and not any(within(name, top) for top in park)
    ]
    if unexpected:
        raise MigrationError("Backup layout changed; not in the approved plan: " + ", ".join(unexpected))
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
    def lookup(name):
        return parked.get(name) if within(name, park_root(config)) else legacy.get(name)

    return {
        row["source"]: observe_row(
            transport, row, source.get(row["source"]), destination.get(row["destination"]),
            existing_replica(config, park, row, lookup),
        )
        for row in rows
    }


def observe_one(transport, plan, row):
    existing = existing_replica(transport.config, plan["park"], row, lambda name: transport.dataset(name, True))
    return observe_row(
        transport, row, transport.dataset(row["source"]), transport.dataset(row["destination"], True), existing,
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


def event(path, status, message, quiet=False):
    record = {
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": status, "message": message,
    }
    with path.with_suffix(".log.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    if not quiet:
        print(f"  {status:<9} {message}", flush=True)


def label(row):
    if row["overwrite"]:
        return "FULL, OVERWRITE"
    if row["rename"]:
        return "MOVE + INCREMENTAL"
    return {"incremental": "INCREMENTAL", "full": "FULL"}.get(row["action"], "-")


def report(path, config, plan, stage):
    """Write the full report to a file and print a short summary."""
    mode = "relocate" if relocating(config) else "root to root, in place"
    header = [
        f"ZFS migration report: {stage}",
        f"Source root: {config['source_root']}",
        f"Existing replicas: {config['ssh']}:{config['legacy_root']}",
        f"New recursive backup root: {config['ssh']}:{config['destination_root']}",
        f"Mode: {mode}",
        f"Hold tag: {config['hold_tag']}",
        "",
    ]
    detail, summary = [], []
    for row in plan["datasets"]:
        line = f"{row['status']} [{label(row)}]: {row['source']} -> {row['destination']} {row['reason']}".rstrip()
        detail.append(line)
        brief = f"  {label(row):<20} {row['source']} -> {row['destination']}"
        if "estimate" in row:
            brief += f"  ({size(row['estimate']['bytes'])})"
        if row["base_source"]:
            brief += f"  from @{row['base_source'].split('@', 1)[1]}"
        summary.append(brief if row["status"] == "READY" else line)
        if row["rename"]:
            detail.append(f"  Rename on backup: {row['legacy']} -> {row['destination']}")
        if row["note"]:
            detail.append("  " + row["note"])
            summary.append("      " + row["note"])
        if row["base_source"]:
            detail.append(f"  Base: {row['base_source']} -> {row['base_destination']} (GUID {row['base_guid']})")
        if row["migration_guid"]:
            detail.append(f"  Migration GUID: {row['migration_guid']}")
        if "estimate" in row:
            detail.append(f"  Estimated stream bytes: {row['estimate']['bytes']}")
            detail.append(row["estimate"]["output"])
    for top in plan.get("park", []):
        line = f"MOVE ASIDE on backup (kept, not deleted): {top} -> {parked_name(config, plan['park'], top)}"
        detail.append(line)
        summary.append("  " + line)
    rows = plan["datasets"]
    totals = (f"{len(rows)} datasets: {sum(row['action'] == 'incremental' for row in rows)} incremental, "
              f"{sum(row['action'] == 'full' for row in rows)} full, {sum(row['rename'] for row in rows)} renamed, "
              f"{len(plan.get('park', []))} moved aside")
    if any("estimate" in row for row in rows):
        totals += f". Estimated to send: {size(sum(row.get('estimate', {}).get('bytes', 0) for row in rows))}"
    tail = ["", totals]
    if plan.get("left_in_place"):
        tail.append("Not part of the new task, left untouched: " + ", ".join(plan["left_in_place"]))
    tail.extend("BLOCKER: " + blocker for blocker in plan.get("blockers", []))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = path.with_suffix(f".{stage}-{stamp}.txt")
    with filename.open("x", encoding="utf-8") as output:
        output.write("\n".join(header + detail + tail) + "\n")
    print(f"{config['source_root']} -> {config['ssh']}:{config['destination_root']} ({mode})")
    print("\n".join(summary + tail), flush=True)
    print(f"Full report: {filename}", flush=True)


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
    print("Creates one recursive snapshot set and holds the starting snapshots. Pause applications first if needed.")
    confirm("PREPARE")
    state["phase"] = "preparing"
    save_state(path, state)
    for row in plan["datasets"]:
        if row["action"] != "incremental":
            continue
        transport.hold(row["base_source"])
        event(path, "HELD_SOURCE_BASE", row["base_source"], quiet=True)
        held = backup_base(row, observations[row["source"]][1])
        transport.hold(held, True)
        event(path, "HELD_BACKUP_BASE", held, quiet=True)
    expect(observe_all(transport, plan, require_absent=True), {"READY"})
    target = f"{transport.config['source_root']}@{SNAPSHOT}"
    transport.query(["zfs", "snapshot", "-r", target])
    event(path, "SNAPSHOT", target)
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
    print("PREPARE PASSED. Applications may resume. Approve the report and backup capacity, then run copy.")


class Progress:
    """One updating status line on a terminal; periodic plain lines when output goes to a file."""

    def __init__(self, label, total, done_before, grand_total):
        self.label, self.total = label, total
        self.done_before, self.grand_total = done_before, grand_total
        self.interactive = sys.stdout.isatty()
        self.start = self.last = time.monotonic()
        self.width = 0
        if not self.interactive:
            print(f"  {label}: started" + (f", about {size(total)} to send" if total else ""), flush=True)

    def __call__(self, sent):
        now = time.monotonic()
        if now - self.last < (1 if self.interactive else 10):
            return
        self.last = now
        rate = sent / max(now - self.start, 0.001)
        text = f"  {self.label}: {size(sent)}"
        if self.total:
            # The ZFS estimate can be slightly low; never show more than 100%.
            total = max(self.total, sent)
            fraction = sent / total
            filled = int(fraction * 20)
            text += f" / {size(total)} [{'#' * filled}{'-' * (20 - filled)}] {fraction:.0%}"
            if rate > 0 and sent < total:
                text += f"  ETA {datetime.timedelta(seconds=int((total - sent) / rate))}"
        text += f"  {size(rate)}/s"
        if self.grand_total:
            text += f"  | all: {min((self.done_before + sent) / self.grand_total, 1.0):.0%}"
        if self.interactive:
            print("\r" + text.ljust(self.width), end="", flush=True)
            self.width = len(text)
        else:
            print(text, flush=True)

    def clear(self):
        if self.interactive and self.width:
            print("\r" + " " * self.width + "\r", end="", flush=True)


def detach(path):
    """Offer to run copy in its own session so closing the terminal does not stop it."""
    if os.environ.get("TMUX") or os.environ.get("STY"):
        return False
    print("WARNING: this terminal is not inside tmux or screen. If it closes or the SSH session drops, "
          "the copy stops (it can be resumed by running copy again).")
    if input("Run copy in the background so it keeps going if this terminal closes? [Y/n]: ").strip().lower() \
            not in ("", "y", "yes"):
        return False
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = path.with_suffix(f".copy-{stamp}.out")
    with output.open("x", encoding="utf-8") as handle:
        child = subprocess.Popen(
            [sys.executable, "-u", os.path.abspath(__file__), "copy", "--state", str(path), "--approved"],
            stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True,
        )
    event(path, "BACKGROUND", f"copy running as PID {child.pid}, output in {output}")
    print(f"Watch progress:  tail -f {output}")
    print("You can close this terminal. When the output ends with COPY PASSED, run verify.")
    return True


def copy(transport, state, path, approved=False):
    if state["phase"] not in ("prepared", "completed"):
        raise MigrationError("Copy requires a successful prepare. Ask Service about incomplete preparation.")
    if approved and not state.get("copy_approved"):
        raise MigrationError("Copy was not approved; run copy without --approved.")
    plan = state["plan"]
    observations = observe_all(transport, plan, require_snapshot=True)
    expect(observations, {"READY", "PARTIAL", "COMPLETE"})
    require_holds(transport, plan, observations)
    if not approved:
        for row in plan["datasets"]:
            if row["overwrite"] and observations[row["source"]][0] == "READY":
                print(f"NOTE: {row['destination']} itself is overwritten (it has no snapshots); its child datasets "
                      "are not touched but are briefly unmounted and remounted.")
        confirm("COPY")
        state["copy_approved"] = True
        save_state(path, state)
        if detach(path):
            return
    grand_total = sum(row.get("estimate", {}).get("bytes", 0) for row in plan["datasets"])
    done_before = 0
    # Move aside before any rename so original paths are still valid.
    for top in plan["park"]:
        moved = parked_name(transport.config, plan["park"], top)
        if transport.dataset(moved, True) is None:
            transport.rename(top, moved, parents=True)
            event(path, "PARKED", f"{top} -> {moved}")
    for index, row in enumerate(plan["datasets"], 1):
        name = f"{row['source']} -> {row['destination']}"
        target = f"{row['source']}@{SNAPSHOT}"
        status, location, reason = observe_one(transport, plan, row)
        result, sent = "DONE", None
        tag = f"[{index}/{len(plan['datasets'])}] {row['source']}"
        if status == "PARTIAL":
            token = transport.dataset(row["destination"], True)["token"]
            if transport.resume_target(token) != target:
                raise MigrationError(f"Resume token on {row['destination']} does not target {target}.")
            event(path, "RESUMING", name, quiet=True)
            try:
                remaining = transport.estimate(["-t", token])["bytes"]
            except MigrationError:
                remaining = None
            progress = Progress(tag + " (resuming)", remaining, done_before, grand_total)
            try:
                sent = transport.transfer(["-t", token], row["destination"], row["overwrite"], progress)
            finally:
                progress.clear()
            status, location, reason = observe_one(transport, plan, row)
        elif status == "READY":
            if row["action"] == "incremental" and location != row["destination"]:
                if not row["rename"]:
                    raise MigrationError(f"{location} did not move with its parent; Service review required.")
                transport.rename(location, row["destination"])
                event(path, "RENAMED", f"{location} -> {row['destination']}")
                status, location, reason = observe_one(transport, plan, row)
                if status != "READY" or location != row["destination"]:
                    raise MigrationError(f"Post-rename check failed: {row['destination']}: {status} {reason}")
            event(path, "STARTED", name, quiet=True)
            progress = Progress(tag, row.get("estimate", {}).get("bytes"), done_before, grand_total)
            try:
                sent = transport.transfer(send_args(row), row["destination"], row["overwrite"], progress)
            finally:
                progress.clear()
            status, location, reason = observe_one(transport, plan, row)
        elif status == "COMPLETE":
            result = "SKIPPED"
        if status != "COMPLETE":
            raise MigrationError(f"Verification failed: {name}: {status} {reason}")
        transport.hold(f"{row['destination']}@{SNAPSHOT}", True)
        done_before += row.get("estimate", {}).get("bytes", 0)
        detail = "already done" if sent is None else f"{row['action']}, sent {size(sent)}"
        event(path, result, f"{name} ({detail})")
    verify(transport, state)
    state["phase"] = "completed"
    save_state(path, state)
    print("COPY PASSED. Next: create and test the recursive task (Step 7).")


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
    print(f"VERIFY PASSED: all {len(plan['datasets'])} datasets under {transport.config['destination_root']} "
          f"share @{SNAPSHOT} with the source.")
    if plan.get("left_in_place"):
        print("Not part of the new task, left untouched: " + ", ".join(plan["left_in_place"]))


def choose_destination(transport, override):
    config = transport.config
    config["destination_root"] = override or config["legacy_root"]
    validate_config(config)
    if transport.dataset(config["source_root"]) is None:
        raise MigrationError(f"Source root not found: {config['source_root']}")


def run_mode(mode, path, new_root=None, approved=False, port=22, identity=None):
    if mode == "check":
        if path.exists():
            raise MigrationError("State file already exists. Keep it; do not restart check over an existing migration.")
        config = prompt_config(port, identity)
        transport = Transport(config)
        choose_destination(transport, new_root)
        plan = classify(transport)
        report(path, config, plan, "readiness")
        if plan["blockers"]:
            raise MigrationError("Readiness has blockers. Give the report to Service; do not prepare.")
        save_state(path, {"version": VERSION, "phase": "checked", "config": config, "plan": plan}, new=True)
        print("CHECK PASSED. Nothing was changed. Approve the report, then run prepare.")
        return
    with path.open(encoding="utf-8") as source:
        state = json.load(source)
    if state.get("version") != VERSION:
        raise MigrationError("Unsupported state file; use this script's own state, not an old plan.")
    transport = Transport(state["config"])
    if mode == "prepare":
        prepare(transport, state, path)
    elif mode == "copy":
        copy(transport, state, path, approved)
    else:
        verify(transport, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "prepare", "copy", "verify"))
    parser.add_argument("--state", type=Path, default=Path("migration-state.json"))
    parser.add_argument("--new-root", help="check only: replicate to this NEW backup dataset and move existing "
                                           "replicas under it, instead of root to root in place")
    parser.add_argument("--port", type=int, default=22, help="check only: backup SSH port (default 22)")
    parser.add_argument("--identity", help="check only: SSH private key file (default: SSH's own defaults)")
    parser.add_argument("--approved", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    path = args.state.resolve()
    try:
        descriptor = os.open(path.with_suffix(".lock"), os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(descriptor, "w") as lock:
            try:
                # The background copy waits for the command that started it to release the lock.
                fcntl.flock(lock, fcntl.LOCK_EX | (0 if args.approved else fcntl.LOCK_NB))
            except BlockingIOError:
                raise MigrationError("Another command is using this state file; do not run concurrent migrations.") from None
            run_mode(args.mode, path, args.new_root, args.approved and args.mode == "copy", args.port, args.identity)
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