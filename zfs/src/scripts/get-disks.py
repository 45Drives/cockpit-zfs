#!/usr/bin/env python3
import sys, os, logging, subprocess, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging.handlers import RotatingFileHandler, SysLogHandler
from pathlib import Path
from typing import Set

# ------------------------- logging -------------------------
def get_logger(name: str, file_basename: str, app_name: str = "cockpit-zfs") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for addr in ("/dev/log", "/run/systemd/journal/syslog"):
        try:
            if os.path.exists(addr):
                h = SysLogHandler(address=addr, facility=SysLogHandler.LOG_USER)
                h.setFormatter(logging.Formatter(f"{name}: %(levelname)s: %(message)s"))
                logger.addHandler(h)
                logger.debug(f"Syslog handler attached via {addr}")
                return logger
        except Exception:
            pass

    def _candidates():
        xs = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        xc = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        xr = os.environ.get("XDG_RUNTIME_DIR")
        for base in (xs, xc, xr):
            if base:
                yield os.path.join(base, app_name, "logs", file_basename)
        yield os.path.join(os.path.expanduser("~/.local/state"), app_name, "logs", file_basename)
        yield os.path.join("/tmp", app_name, file_basename)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    for path in _candidates():
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            fh = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3, delay=True)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
            logger.debug(f"File logger attached at {path}")
            return logger
        except Exception:
            pass

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.warning("No syslog/file target available; logging to stderr.")
    return logger


logger = get_logger("cockpit_zfs_getdisks", "getdisks.log")

# ------------------------- helpers -------------------------
_partitions_text_cache = None
def _partitions_text():
    """Cache /proc/partitions for cheap has_partitions checks (non-root-safe)."""
    global _partitions_text_cache
    if _partitions_text_cache is None:
        try:
            with open("/proc/partitions", "r") as f:
                _partitions_text_cache = f.read()
        except Exception:
            _partitions_text_cache = ""
    return _partitions_text_cache

def _has_partitions_for(base_name: str) -> bool:
    # matches sda1 / nvme0n1p2 lines in /proc/partitions
    return re.search(rf"\b{re.escape(base_name)}(p?\d+)\b", _partitions_text()) is not None

def _dev_base(p: str) -> str:
    """
    Normalize to base block dev:
      /dev/sda2         -> /dev/sda
      /dev/nvme0n1p3    -> /dev/nvme0n1
      /dev/mmcblk0p1    -> /dev/mmcblk0
      /dev/disk/by-vdev/1-2-part2 -> /dev/disk/by-vdev/1-2
      /dev/disk/by-path/...-part1 -> /dev/disk/by-path/...
      /dev/disk/by-id/...-part1   -> /dev/disk/by-id/...
    Never strip the trailing '1' from nvme0n1!
    """
    s = str(p)
    # NVMe partitions: keep nvmeXnY, drop pZ
    s = re.sub(r'^(.*?/nvme\d+n\d+)p\d+$', r'\1', s)
    # MMC partitions
    s = re.sub(r'^(.*?/mmcblk\d+)p\d+$', r'\1', s)
    # SCSI/SATA (sdX<partition#>)
    s = re.sub(r'^(.*?/sd[a-z]+)\d+$', r'\1', s)
    # Symlink paths with -partN suffix (by-vdev, by-path, by-id, etc.)
    s = re.sub(r'-part\d+$', '', s)
    return s


def _bootlike_bases_from_lsblk() -> Set[str]:
    """
    Identify disks that look like OS/boot disks even if not mounted,
    by scanning partition metadata (ESP/boot flags/part types).
    """
    out: Set[str] = set()
    try:
        r = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,PATH,TYPE,PARTTYPE,PARTTYPENAME,PARTFLAGS"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if r.returncode != 0:
            return out
        data = json.loads(r.stdout or "{}")

        EFI_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
        BIOS_GRUB_GUID = "21686148-6449-6e6f-744e-656564454649"

        def walk(node, cur_disk_base=None):
            ntype = (node.get("type") or "").lower()
            path = node.get("path")
            if ntype == "disk" and path:
                cur_disk_base = _dev_base(path)
            elif ntype == "part" and cur_disk_base:
                ptn = (node.get("parttypename") or "").lower()
                ptg = (node.get("parttype") or "").lower()
                pfl = (node.get("partflags") or "").lower()
                looks_boot = (
                    "boot" in pfl or "esp" in pfl or
                    "efi" in ptn or "bios boot" in ptn or
                    ptg == EFI_GUID or ptg == BIOS_GRUB_GUID
                )
                if looks_boot:
                    out.add(cur_disk_base)
            for ch in node.get("children", []) or []:
                walk(ch, cur_disk_base)

        for top in data.get("blockdevices", []) or []:
            walk(top)
    except Exception:
        pass
    return out


def _resolve_to_base_disks(src: str) -> Set[str]:
    """Return base /dev/sdX, /dev/nvmeXnY, etc. that back 'src' (md/dm/lvm/crypt safe)."""
    out: Set[str] = set()

    # If findmnt gave UUID=/LABEL=, resolve to a device first
    dev = src
    try:
        if src.startswith("UUID="):
            rr = subprocess.run(
                ["blkid", "-U", src.split("=", 1)[1]],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            if rr.returncode == 0 and rr.stdout.strip():
                dev = rr.stdout.strip()
        elif src.startswith("LABEL="):
            rr = subprocess.run(
                ["blkid", "-L", src.split("=", 1)[1]],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            if rr.returncode == 0 and rr.stdout.strip():
                dev = rr.stdout.strip()
    except Exception:
        pass

    # Inverse dependencies first so we see slaves (e.g., md0 -> sda2/sdb2 -> sda/sdb)
    for args in (
        ["lsblk", "-nrspo", "NAME,TYPE", dev],  # -s: holders -> slaves
        ["lsblk", "-nrpo",  "NAME,TYPE", dev],  # fallback: normal listing
    ):
        try:
            r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if r.returncode != 0:
                continue
            for line in r.stdout.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                name, typ = parts[0], parts[1]
                if typ in ("disk", "part"):
                    out.add(_dev_base(name))
            if out:
                break
        except Exception:
            pass

    return out


def _zpool_leaf_bases(pool: str) -> Set[str]:
    """Return base devices that back a ZFS pool, via `zpool status -P` (best-effort for non-root).
    Resolves symlinks (by-vdev, by-path, by-id) to real /dev/sdX paths."""
    out = set()
    try:
        zr = subprocess.run(["zpool", "status", "-P", pool],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if zr.returncode != 0:
            return out
        for ln in zr.stdout.splitlines():
            ln = ln.strip()
            # leaf device lines usually start with a path or short dev name as first token
            if not ln or ln.startswith(("pool:", "state:", "errors:", "config:", "action:", "see:")):
                continue
            tok = ln.split()[0]
            dev = None
            # Accept absolute /dev paths, or bare sdX/sdXn/nvmeXnYpZ
            if tok.startswith("/dev/"):
                dev = tok
            elif re.match(r"^(sd[a-z]+(\d+)?|nvme\d+n\d+(p\d+)?)$", tok):
                dev = "/dev/" + tok
            if dev:
                # Resolve symlinks (by-vdev/by-path/by-id) to real /dev/sdX
                try:
                    resolved = os.path.realpath(dev)
                    out.add(_dev_base(resolved))
                    # Also keep the unresolved base in case the symlink is broken
                    # (realpath returns the link path itself when target is missing)
                    if resolved != dev:
                        out.add(_dev_base(dev))
                    elif not resolved.startswith("/dev/sd") and not resolved.startswith("/dev/nvme"):
                        # Broken symlink: resolved == dev but it's not a real block device.
                        # Still add it so it can match the disk inventory entry.
                        out.add(_dev_base(dev))
                except Exception:
                    out.add(_dev_base(dev))
    except Exception:
        pass
    return out


def _get_boot_bases() -> Set[str]:
    """
    Return base block devices (e.g. {'/dev/sda','/dev/sdb','/dev/nvme0n1'})
    that back '/', '/boot', '/boot/efi'. Handles md/LVM/DM and ZFS root.
    Also unions in disks that look bootable (ESP/boot flags) even if not mounted.
    """
    out: Set[str] = set()

    # Pass 1: try lsblk topology (works when mountpoints appear under disks)
    try:
        r = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,PATH,TYPE,MOUNTPOINT,MOUNTPOINTS"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if r.returncode == 0:
            data = json.loads(r.stdout or "{}")
            boot_mounts = {"/", "/boot", "/boot/efi", "/efi"}

            def _first_mount(n):
                mp = n.get("mountpoint")
                if mp:
                    return mp
                mps = n.get("mountpoints")
                if isinstance(mps, list):
                    for x in mps:
                        if x:
                            return x
                return None

            def walk(node):
                has_boot = _first_mount(node) in boot_mounts
                disks = set()
                for ch in node.get("children", []) or []:
                    dset, ch_has = walk(ch)
                    disks |= dset
                    has_boot = has_boot or ch_has
                if has_boot and node.get("type") == "disk":
                    path = node.get("path") or ("/dev/" + node.get("name", ""))
                    disks.add(_dev_base(path))
                return disks, has_boot

            for top in data.get("blockdevices", []) or []:
                dset, _ = walk(top)
                out |= dset
    except Exception as e:
        logger.warning(f"lsblk topology walk failed: {e}")

    # Pass 2: authoritative via findmnt → devices (covers md/LVM/crypt/UUID/LABEL)
    try:
        fstype_src = {}
        for mp in ("/", "/boot", "/boot/efi", "/efi"):
            fr = subprocess.run(
                ["findmnt", "-nro", "FSTYPE,SOURCE", mp],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            if fr.returncode == 0 and fr.stdout.strip():
                fs, src = (fr.stdout.strip().split(None, 1) + [""])[:2]
                fstype_src[mp] = (fs.strip(), src.strip())

        # ZFS root: extract pool from dataset and add its leaves
        root_fs, root_src = fstype_src.get("/", ("", ""))
        if (root_fs or "").lower() == "zfs" and root_src:
            pool = root_src.split("/", 1)[0]
            out |= _zpool_leaf_bases(pool)

        # Non-ZFS or other mounts → resolve to base devices
        for mp, (fs, src) in fstype_src.items():
            if (fs or "").lower() != "zfs" and src:
                out |= _resolve_to_base_disks(src)
    except Exception as e:
        logger.warning(f"findmnt/resolve pass failed: {e}")

    # Pass 3: include disks that look bootable even if not currently mounted
    out |= _bootlike_bases_from_lsblk()

    logger.info(f"Boot ancestor/bootlike base devices: {sorted(out)}")
    return out



def _enrich_with_lsblk_and_udev(disks):
    """
    Non-root enrichment: add model/serial/usable/rota and better phy_path if missing,
    using one lsblk JSON call and per-device udevadm property calls.
    """
    if not disks:
        return disks

    # Build quick lookup by sd_path base
    by_sd = { _dev_base(d["sd_path"]): d for d in disks if d.get("sd_path") }

    # Single lsblk JSON call for base block devices
    try:
        r = subprocess.run(
            ["lsblk", "-dnpJ", "-o", "NAME,ROTA,SERIAL,MODEL,RO,SIZE,TYPE"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if r.returncode == 0:
            data = json.loads(r.stdout or "{}")
            for bd in data.get("blockdevices", []):
                name = bd.get("name")
                if not name:
                    continue
                base = _dev_base(name)
                target = by_sd.get(base)
                if not target:
                    continue

                # model / serial
                model = (bd.get("model") or "").strip()
                serial = (bd.get("serial") or "").strip()
                if target.get("model", "Unknown") == "Unknown" and model:
                    target["model"] = model
                if target.get("serial", "Unknown") == "Unknown" and serial:
                    target["serial"] = serial

                # usable from RO bit, if present
                ro = bd.get("ro")
                try:
                    if ro is not None:
                        target["usable"] = (int(ro) == 0)
                except Exception:
                    pass

                # rotation heuristic (true rota -> assume 7200, else 0)
                rota = bd.get("rota")
                try:
                    rota_bool = bool(int(rota))
                    if target.get("type","").upper() != "NVME":
                        target["rotation_rate"] = 7200 if rota_bool else 0
                except Exception:
                    pass
        else:
            logger.warning(f"lsblk enrichment failed: {r.stderr.strip()}")
    except Exception as e:
        logger.warning(f"lsblk enrichment exception: {e}")

    # Per-device udevadm for ID_PATH fallback and possible model/serial if lsblk lacked them
    for base, d in by_sd.items():
        try:
            ur = subprocess.run(
                ["udevadm", "info", "--query=property", f"--name={base}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            if ur.returncode != 0:
                continue
            props = {}
            for line in ur.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()
            # by-path: if lsdev text didn't have a good one
            if (not d.get("phy_path")) or d["phy_path"] in ("unknown", "N/A"):
                id_path = props.get("ID_PATH")
                if id_path:
                    d["phy_path"] = f"/dev/disk/by-path/{id_path}"

            # model / serial (only fill if still Unknown)
            if d.get("model", "Unknown") == "Unknown":
                m = props.get("ID_MODEL")
                if m:
                    d["model"] = m
            if d.get("serial", "Unknown") == "Unknown":
                s = props.get("ID_SERIAL_SHORT") or props.get("ID_SERIAL")
                if s:
                    d["serial"] = s
        except Exception:
            pass

    return disks


def _udev_alias_paths(base: str) -> dict:
    """Extract alias device symlinks (by-id, by-label, etc.) from udevadm DEVLINKS for a base device."""
    out = {}
    try:
        r = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name={base}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if r.returncode != 0:
            return out
        devlinks_str = ""
        for line in r.stdout.splitlines():
            if line.startswith("DEVLINKS="):
                devlinks_str = line.split("=", 1)[1].strip()
                break
        for p in devlinks_str.split():
            if p.startswith("/dev/disk/by-id/") and "id_path" not in out:
                out["id_path"] = p
            elif p.startswith("/dev/disk/by-label/") and "label_path" not in out:
                out["label_path"] = p
            elif p.startswith("/dev/disk/by-partlabel/") and "part_label_path" not in out:
                out["part_label_path"] = p
            elif p.startswith("/dev/disk/by-partuuid/") and "part_uuid" not in out:
                out["part_uuid"] = p
            elif p.startswith("/dev/disk/by-uuid/") and "uuid" not in out:
                out["uuid"] = p
    except Exception:
        pass
    return out


def _enrich_alias_paths(disks):
    """Add id_path, label_path, part_label_path, part_uuid, uuid to each disk record via udevadm."""
    for d in disks:
        base = _dev_base(d.get("sd_path", ""))
        if not base:
            continue
        aliases = _udev_alias_paths(base)
        for k, v in aliases.items():
            if k not in d or not d[k]:
                d[k] = v
    return disks


# ------------------------- lsdev paths -------------------------
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def _parse_lsdev_text_table(text: str):
    """
    Parse `lsdev -n -dtcp` rows like:
      | ** 1-1  (/dev/sda,/dev/disk/by-path/...,HDD,10.91 TiB) |
    """
    disks = []
    nonmatch_sample = 0

    for raw in text.splitlines():
        # 0) Strip ANSI
        raw = ANSI_RE.sub('', raw)

        # 1) Normalize borders: remove leading/trailing '|' and whitespace
        line = raw.strip()
        if line.startswith('|'):
            line = line[1:].rstrip()
        if line.endswith('|'):
            line = line[:-1].rstrip()
        line = line.strip()

        # 2) Skip ASCII borders / headers / legends
        if (not line or
            line.startswith("Storage Disk Info") or
            line.startswith("Disk Controller") or
            "Row " in line or
            "Legend:" in line or
            set(line) <= set("+-")  # lines like +-----+
        ):
            continue

        # 3) Remove non-color occupancy markers: "* " or "** "
        line = re.sub(r'^\*{1,2}\s*', '', line)

        # 4) We only care about rows that contain a tuple with a /dev/ path
        if "(" not in line or "/dev/" not in line:
            if nonmatch_sample < 5:
                logger.debug(f"lsdev row ignored (no tuple/dev): {repr(line)}")
                nonmatch_sample += 1
            continue

        # 5) Parse: 1-1 (/dev/sdx, /dev/disk/by-path/..., TYPE, CAPACITY)
        m = re.match(
            r'^\s*([0-9]+-[0-9]+)\s*'
            r'\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([A-Za-z]+)\s*,\s*([^)]+)\s*\)\s*$',
            line
        )
        if not m:
            if nonmatch_sample < 5:
                logger.debug(f"lsdev row did not match regex: {repr(line)}")
                nonmatch_sample += 1
            continue

        bay_id, dev, by_path, dtype, capacity = m.groups()
        base_name = os.path.basename(dev)

        disk_data = {
            "vdev_path": f"/dev/disk/by-vdev/{bay_id}",
            "phy_path": by_path or "unknown",
            "sd_path": dev,
            "name": bay_id,
            "model": "Unknown",
            "serial": "Unknown",
            "capacity": capacity.strip(),
            "type": dtype.strip(),
            "usable": True,
            "temp": "Unknown",
            "health": "Unknown",
            "rotation_rate": 0 if dtype.strip().upper() in ("SSD", "NVME") else 0,
            "power_on_count": None,
            "power_on_time": None,
            "has_partitions": _has_partitions_for(base_name),
        }
        logger.debug(f"Discovered disk (lsdev-text): {disk_data['name']} {dev} {by_path}")
        disks.append(disk_data)

    logger.info(f"Disks discovered via lsdev (text): {len(disks)}")
    return disks


def get_lsdev_disks():
    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            r = subprocess.run(["lsdev", "-jdHmtTsfcp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if r.returncode != 0:
                logger.error(f"lsdev JSON failed: {r.stderr}")
                return None

            data = json.loads(r.stdout or "{}")
            disks = []
            for row in data.get("rows", []) or []:
                for d in row:
                    if not d.get("occupied"):
                        continue
                    dev = d.get("dev")
                    if not dev:
                        continue
                    bay_id = d.get("bay-id", "")
                    base_name = os.path.basename(dev)
                    dtype = (d.get("disk_type") or "HDD").strip()
                    temp_raw = d.get("temp-c")
                    # Treat 0°C as unreported — HDDs can't physically operate at 0°C,
                    # so the SES enclosure likely doesn't support temperature sensing.
                    # "Unknown" lets merge_overlay preserve smartctl-based temperature.
                    temp_str = str(temp_raw) if (temp_raw is not None and temp_raw != 0) else "Unknown"

                    disk_data = {
                        "vdev_path": f"/dev/disk/by-vdev/{bay_id}" if bay_id else "N/A",
                        "phy_path": d.get("dev-by-path") or "unknown",
                        "sd_path": dev,
                        "name": bay_id or base_name,
                        "model": d.get("model-name") or "Unknown",
                        "serial": d.get("serial") or "Unknown",
                        "capacity": d.get("capacity", "0"),
                        "type": dtype,
                        "usable": True,
                        "temp": temp_str,
                        "health": d.get("health") or "Unknown",
                        "rotation_rate": d.get("rotation-rate") or (0 if dtype.upper() in ("SSD", "NVME") else 7200),
                        "power_on_count": d.get("power-cycle-count"),
                        "power_on_time": d.get("power-on-time"),
                        "has_partitions": bool(d.get("partitions", 0)),
                    }
                    logger.debug(f"Discovered disk (lsdev-JSON): {disk_data['name']} {dev}")
                    disks.append(disk_data)
            logger.info(f"Disks discovered via lsdev (JSON): {len(disks)}")
            return disks

        # Non-root path
        r = subprocess.run(["lsdev", "-ndtcp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if r.returncode != 0:
            logger.warning(f"lsdev text failed ({r.returncode}): {r.stderr.strip()}")
            return None

        disks = _parse_lsdev_text_table(r.stdout)

        # Enrich non-root details
        disks = _enrich_with_lsblk_and_udev(disks)
        return disks

    except Exception as e:
        logger.error(f"Exception in get_lsdev_disks: {e}")
        return None

# ------------------------- lsblk (NVMe & fallback) -------------------------
def _parse_smartctl_output(lines):
    """Extract SMART fields from smartctl output lines."""
    info = {"temp": None, "power_on_hours": None, "power_cycle_count": None, "health": None}
    for line in lines:
        if ("Temperature" in line and "Celsius" in line) or "Temperature_Celsius" in line:
            nums = [int(t) for t in re.findall(r"(\d+)", line)]
            if nums: info["temp"] = nums[-1]
        elif "Power_On_Hours" in line or "Power On Hours" in line:
            nums = re.findall(r"(\d+)", line); info["power_on_hours"] = int(nums[-1]) if nums else None
        elif "Power_Cycle_Count" in line or "Power Cycle Count" in line:
            nums = re.findall(r"(\d+)", line); info["power_cycle_count"] = int(nums[-1]) if nums else None
        elif "SMART overall-health" in line or "SMART overall-health self-assessment" in line:
            if ":" in line: info["health"] = line.split(":", 1)[1].strip()
    return info

def get_smartctl_data(device):
    """Best-effort SMART with device-type fallbacks for SATA-behind-SAS etc."""
    best = {"temp": None, "power_on_hours": None, "power_cycle_count": None, "health": None}
    # NVMe drives always work with default mode — no point trying sat/scsi
    modes = (None,) if "nvme" in device else (None, "sat", "scsi")
    for dtype in modes:
        try:
            cmd = ["smartctl", "-a"]
            if dtype:
                cmd += ["-d", dtype]
            cmd.append(f"/dev/{device}")
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=15)
            # smartctl return code is a bitmask:
            #   bit 0 = command line parse error
            #   bit 1 = device open failed
            # Bits 2-7 indicate disk issues but output is still valid.
            if r.returncode & 0x03:
                label = f"-d {dtype}" if dtype else "default"
                logger.info(f"smartctl ({label}) failed for {device}: rc={r.returncode}")
                continue
            info = _parse_smartctl_output(r.stdout.splitlines())
            if info["temp"] is not None:
                label = f"-d {dtype}" if dtype else "default"
                logger.debug(f"smartctl ({label}) got temp for {device}: {info['temp']}")
                return info
            # Got valid output but no temp — keep as fallback and try next type
            for k, v in info.items():
                if v is not None and best[k] is None:
                    best[k] = v
        except Exception as e:
            logger.error(f"smartctl exception ({dtype or 'default'}): {e}")
            continue
    # Return whatever we collected (may still have power/health even without temp)
    return best

def _map_by_vdev():
    base_dir = "/dev/disk/by-vdev"
    m = {}
    if not os.path.isdir(base_dir):
        return m
    for link in os.listdir(base_dir):
        full = os.path.join(base_dir, link)
        try:
            target = os.path.realpath(full)
            base = _dev_base(target)
            base_name = link.split("-part")[0]
            m[base] = os.path.join(base_dir, base_name)
        except Exception:
            pass
    return m

def _get_udev_phy_path(name):
    """Best-effort phy_path via udevadm."""
    try:
        ur = subprocess.run(["udevadm", "info", "--query=property", f"--name={name}"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True, timeout=10)
        if ur.returncode == 0:
            props = dict(line.split("=",1) for line in ur.stdout.splitlines() if "=" in line)
            if props.get("ID_PATH"):
                return f"/dev/disk/by-path/{props['ID_PATH']}"
    except Exception:
        pass
    return "unknown"

def get_lsblk_disks(nvme_only=False):
    try:
        byv_map = _map_by_vdev()

        r = subprocess.run(
            ["lsblk", "-dnpJ", "-o", "NAME,TYPE,SIZE,ROTA,SERIAL,MODEL,MOUNTPOINT,RO"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if r.returncode != 0:
            logger.error(f"lsblk command failed: {r.stderr}")
            return []

        data = json.loads(r.stdout or "{}")

        # Filter to relevant devices first
        candidates = []
        for device in (data.get("blockdevices") or []):
            name = device.get("name")
            if not name:
                continue
            if nvme_only and "nvme" not in name:
                continue
            if device.get("type","").lower() == "loop":
                continue
            candidates.append(device)

        # Fan out smartctl + udevadm for all disks in parallel
        smart_results = {}
        udev_results = {}
        with ThreadPoolExecutor(max_workers=min(len(candidates), 8) if candidates else 1) as pool:
            smart_futures = {
                pool.submit(get_smartctl_data, os.path.basename(dev["name"])): dev["name"]
                for dev in candidates
            }
            udev_futures = {
                pool.submit(_get_udev_phy_path, dev["name"]): dev["name"]
                for dev in candidates
            }
            for fut in as_completed(smart_futures):
                smart_results[smart_futures[fut]] = fut.result()
            for fut in as_completed(udev_futures):
                udev_results[udev_futures[fut]] = fut.result()

        disks = []
        for device in candidates:
            name = device["name"]
            base = _dev_base(name)

            vdev_path = byv_map.get(base)  # None if no alias
            slot_name = os.path.basename(vdev_path) if vdev_path else None
            pretty_name = slot_name or os.path.basename(base)  # prefer by-vdev, else sdX/nvmeXnY

            smart = smart_results.get(name, {"temp": None, "power_on_hours": None, "power_cycle_count": None, "health": None})
            rota = bool(int(device.get("rota", 0) or 0))
            try: usable = (int(device.get("ro", 0) or 0) == 0)
            except Exception: usable = True

            phy_path = udev_results.get(name, "unknown")

            health_raw = smart.get("health")
            health = "Unknown" if not health_raw else ("OK" if str(health_raw).upper() == "PASSED" else "POOR")
            is_nvme = "nvme" in name
            rota = bool(int(device.get("rota", 0) or 0))  # 1 = rotating
            dev_type = "NVMe" if is_nvme else ("HDD" if rota else "SSD")

            disks.append({
                "vdev_path": vdev_path or "N/A",
                "phy_path": phy_path,
                "sd_path": name,
                "name": pretty_name,                     # <- slot id when available
                "model": device.get("model") or "Unknown",
                "serial": device.get("serial") or "Unknown",
                "capacity": device.get("size", "0"),
                "usable": usable,
                "temp": f"{smart['temp']}℃" if smart["temp"] is not None else "Unknown",
                "health": health,
                "type": dev_type,
                "rotation_rate": 0 if is_nvme else (7200 if rota else 0),
                "power_on_count": smart["power_cycle_count"],
                "power_on_time": smart["power_on_hours"],
                "has_partitions": _has_partitions_for(os.path.basename(base)),
            })

        logger.info(f"Disks discovered via lsblk: {len(disks)}")
        return disks
    except Exception as e:
        logger.error(f"Exception in get_lsblk_disks: {e}")
        return []

UNKNOWN = {None, "", "Unknown", "N/A"}

PREFER_LSDEV = {
    "vdev_path", "name", "phy_path", "type", "capacity", "rotation_rate",
}

def merge_overlay(base: dict, overlay: dict) -> dict:
    out = dict(base)
    # 1) Add keys lsblk doesn’t have
    for k, v in overlay.items():
        if k not in out and v not in UNKNOWN:
            out[k] = v
    # 2) Resolve conflicts
    for k, v in overlay.items():
        if v in UNKNOWN:
            continue
        if k in PREFER_LSDEV:
            out[k] = v
        else:
            # keep existing unless it's unknown
            if out.get(k) in UNKNOWN:
                out[k] = v
    return out

def _all_pool_leaf_bases() -> Set[str]:
    """Return base devices for all currently imported ZFS pools (so we never exclude them as boot disks)."""
    out: Set[str] = set()
    try:
        r = subprocess.run(["zpool", "list", "-H", "-o", "name"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if r.returncode != 0:
            return out
        for pool_name in r.stdout.strip().splitlines():
            pool_name = pool_name.strip()
            if pool_name:
                out |= _zpool_leaf_bases(pool_name)
    except Exception:
        pass
    return out


def _slot_key(d):
    """Sort key: bay-id slots (X-Y) first in numeric order, then non-slot names alphabetically."""
    m = re.match(r"^(\d+)-(\d+)$", d.get("name", ""))
    if m:
        return (0, int(m.group(1)), int(m.group(2)))
    return (1, d.get("name", ""))


# ------------------------- main -------------------------
def main():
    try:
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            logger.info("Running unprivileged: SMART/serial may be limited.")

        logger.info("=" * 80)
        logger.info("Starting a new run of get-disks script")

        # Always collect everything from lsblk first (covers NVMe + sda/sdb/...)
        blk_all = get_lsblk_disks(nvme_only=False)
        disks_by_base = { _dev_base(d["sd_path"]): d for d in blk_all }

        lsdev_disks = get_lsdev_disks() or []
        for d in lsdev_disks:
            base = _dev_base(d.get("sd_path",""))
            if not base:
                continue
            disks_by_base[base] = merge_overlay(disks_by_base.get(base, {}), d)

        all_disks = list(disks_by_base.values())

        # Enrich all disks with alias paths (by-id, by-label, etc.)
        all_disks = _enrich_alias_paths(all_disks)

        # Fallback phy_path enrichment: scan /dev/disk/by-path/ symlinks to fill
        # missing phy_path values. This handles cases where udevadm didn't return
        # ID_PATH, ensuring we can match ZFS by-path vdev identifiers to disks.
        try:
            bypath_dir = "/dev/disk/by-path"
            if os.path.isdir(bypath_dir):
                bypath_map = {}  # base sd_path -> by-path link (base, no partition)
                for link in os.listdir(bypath_dir):
                    full = os.path.join(bypath_dir, link)
                    try:
                        target = os.path.realpath(full)
                        base = _dev_base(target)
                        link_base = re.sub(r'-part\d+$', '', link)
                        bypath_map[base] = f"{bypath_dir}/{link_base}"
                    except Exception:
                        pass
                for d in all_disks:
                    cur = d.get("phy_path", "")
                    if cur and cur not in ("unknown", "N/A"):
                        continue
                    sd_base = _dev_base(d.get("sd_path", ""))
                    if sd_base and sd_base in bypath_map:
                        d["phy_path"] = bypath_map[sd_base]
                        logger.debug(f"Enriched phy_path for {d.get('name')}: {d['phy_path']}")
        except Exception as e:
            logger.warning(f"by-path enrichment failed: {e}")

        # Gather active ZFS pool leaf bases so we never exclude them as boot disks
        pool_leaf_bases = _all_pool_leaf_bases()
        logger.info(f"Active ZFS pool leaf bases: {sorted(pool_leaf_bases)}")

        # FINAL SAFETY FILTER: remove boot-ancestor devices, but NEVER remove active pool members
        boot_bases_final = _get_boot_bases()
        before = len(all_disks)
        all_disks = [d for d in all_disks
                     if _dev_base(d.get("sd_path", "")) not in boot_bases_final
                     or _dev_base(d.get("sd_path", "")) in pool_leaf_bases]

        if len(all_disks) != before:
            logger.info(f"Final filter removed {before - len(all_disks)} boot-ancestor disk(s)")

        # Sort by bay slot ID for consistent UI ordering
        all_disks.sort(key=_slot_key)

        logger.info(f"Total disks discovered: {len(all_disks)}")
        print(json.dumps(all_disks, indent=4))
            
    except Exception as e:
        logger.error(f"Exception in main: {e}")
        print("[]")

if __name__ == "__main__":
    main()
