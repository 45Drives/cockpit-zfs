import json
import subprocess
import re

def _scan_from_zpool_status():
    """Fallback: parse scan info from 'zpool status' when libzfs is unavailable."""
    try:
        res = subprocess.run(
            ["zpool", "status"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if res.returncode != 0:
            return {}

        z_pools = {}
        current_pool = None
        scan_lines = []
        in_scan = False

        for line in res.stdout.splitlines():
            stripped = line.strip()
            m = re.match(r"pool:\s+(\S+)", stripped)
            if m:
                if current_pool and scan_lines:
                    z_pools[current_pool] = _parse_scan_block(current_pool, scan_lines)
                current_pool = m.group(1)
                scan_lines = []
                in_scan = False
                continue
            if stripped.startswith("scan:"):
                in_scan = True
                scan_lines.append(stripped[len("scan:"):].strip())
                continue
            if in_scan:
                if stripped.startswith("config:") or stripped.startswith("errors:"):
                    in_scan = False
                else:
                    scan_lines.append(stripped)

        if current_pool:
            if scan_lines:
                z_pools[current_pool] = _parse_scan_block(current_pool, scan_lines)
            else:
                z_pools[current_pool] = _empty_scan(current_pool)

        return z_pools
    except Exception:
        return {}

def _empty_scan(name):
    return {
        "name": name,
        "function": None,
        "start_time": "",
        "end_time": "",
        "pause": "None",
        "state": None,
        "errors": 0,
        "percentage": 0,
        "total_secs_left": 0,
        "bytes_issued": 0,
        "bytes_processed": 0,
        "bytes_to_process": 0,
    }

def _parse_scan_block(name, lines):
    scan = _empty_scan(name)
    text = " ".join(lines)

    if "scrub repaired" in text or "scrub in progress" in text:
        scan["function"] = "SCRUB"
    elif "resilver" in text:
        scan["function"] = "RESILVER"
    else:
        return scan

    if "in progress" in text:
        scan["state"] = "SCANNING"
    elif "paused" in text:
        scan["state"] = "SCANNING"
        scan["pause"] = "True"
    elif "repaired" in text or "completed" in text:
        scan["state"] = "FINISHED"

    pct_m = re.search(r"(\d+(?:\.\d+)?)%\s+done", text)
    if pct_m:
        scan["percentage"] = float(pct_m.group(1)) / 100.0

    time_m = re.search(r"(\d+:\d+:\d+)\s+to go", text)
    if time_m:
        parts = time_m.group(1).split(":")
        scan["total_secs_left"] = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    issued_m = re.search(r"(\d+(?:\.\d+)?[KMGTP]?)\s+scanned", text)
    processed_m = re.search(r"(\d+(?:\.\d+)?[KMGTP]?)\s+(?:issued|repaired)", text)
    if issued_m:
        scan["bytes_issued"] = issued_m.group(1)
    if processed_m:
        scan["bytes_processed"] = processed_m.group(1)

    return scan


def main():
    try:
        import libzfs
    except ImportError:
        print(json.dumps(_scan_from_zpool_status(), indent=4))
        return

    try:
        with libzfs.ZFS() as zfs:
            z_pools = {}

            for p in zfs.pools:
                pool = p.asdict()
                name = pool.get("name")

                scan = pool.get("scan") or {}
                scan["name"] = name
                scan["start_time"] = str(scan.get("start_time", ""))
                scan["end_time"] = str(scan.get("end_time", ""))
                scan["pause"] = str(scan.get("pause", "None"))
                if scan.get("state", None) is None:
                    scan["state"] = None

                z_pools[name] = scan

        print(json.dumps(z_pools, indent=4))
    except Exception:
        print(json.dumps(_scan_from_zpool_status(), indent=4))

if __name__ == "__main__":
    main()