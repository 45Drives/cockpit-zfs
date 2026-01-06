import libzfs
import json

def main():
    with libzfs.ZFS() as zfs:
        z_pools = {}

        for p in zfs.pools:
            pool = p.asdict()
            name = pool.get("name")

            scan = pool.get("scan") or {}
            # normalize to stable shape
            scan["name"] = name
            scan["start_time"] = str(scan.get("start_time", ""))
            scan["end_time"] = str(scan.get("end_time", ""))
            scan["pause"] = str(scan.get("pause", "None"))
            # if missing, force a value the UI understands
            if scan.get("state", None) is None:
                scan["state"] = None

            z_pools[name] = scan

    print(json.dumps(z_pools, indent=4))

if __name__ == "__main__":
    main()