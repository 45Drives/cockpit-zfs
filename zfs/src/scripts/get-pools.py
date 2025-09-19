#!/usr/bin/env python3
import os, json, subprocess, logging
# --- minimal inline logger (works without external module) ---
import sys, os, logging
from logging.handlers import RotatingFileHandler, SysLogHandler
from pathlib import Path

def get_logger(name: str, file_basename: str, app_name: str = "cockpit-zfs") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # avoid duplicate handlers if re-imported
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # 1) Syslog if available
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

    # 2) User-writable rotating file
    def _candidates():
        xs = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
        xc = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        xr = os.environ.get("XDG_RUNTIME_DIR")
        for base in [xs, xc, xr]:
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

    # 3) Fallback stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.warning("No syslog/file target available; logging to stdout.")
    return logger
# --- end inline logger ---


logger = get_logger("cockpit_zfs_getpools", "getpools.log")

def _pools_from_zpool_list_min():
    """Permission-friendly fallback when libzfs /dev/zfs is blocked."""
    try:
        # -H (scripted) -p (parsable numbers) -o selected fields
        res = subprocess.run(
            ["zpool", "list", "-Hpo", "name,size,allocated,capacity,free,health,guid"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        if res.returncode != 0:
            logger.error(f"zpool list failed: {res.stderr.strip()}")
            return []

        pools = []
        for line in res.stdout.strip().splitlines():
            if not line:
                continue
            name, size, alloc, cap, free, health, guid = line.split()
            pools.append({
                "name": name,
                "status": health,
                "guid": guid,
                "properties": {
                    "size": {"parsed": int(size)},
                    "allocated": {"parsed": int(alloc)},
                    "capacity": {"rawvalue": int(cap.rstrip("%"))},
                    "free": {"parsed": int(free)},
                    "health": {"parsed": health},
                    "autoexpand": {"parsed": False},
                    "autoreplace": {"parsed": False},
                    "autotrim": {"parsed": "off"},
                    "delegation": {"parsed": True},
                    "listsnapshots": {"parsed": False},
                    "readonly": {"parsed": False},
                    "failmode": {"parsed": "wait"},
                    "altroot": {"value": "-"},
                },
                "root_dataset": None,
                "scan": {
                    "function": None, "start_time": None, "end_time": None, "pause": None,
                    "state": None, "errors": 0, "percentage": 0,
                    "total_secs_left": 0, "bytes_issued": 0,
                    "bytes_processed": 0, "bytes_to_process": 0,
                },
                "groups": {"data": [], "cache": [], "dedup": [], "log": [], "spare": [], "special": []},
                "status_code": "OK",
                "status_detail": "",
                "error_count": 0,
            })
        logger.info(f"Pools (fallback) discovered: {len(pools)}")
        return pools
    except Exception as e:
        logger.error(f"Fallback zpool parse failed: {e}")
        return []

def basic_typed_children(children):
    try:
        for i in range(0, len(children)):
            children[i]["properties"]["creation"]["parsed"] = str(children[i]["properties"]["creation"]["parsed"])
            if len(children[i].get("children", [])) >= 1:
                children[i]["children"] = basic_typed_children(children[i]["children"])
        return children
    except Exception as e:
        logger.error(f"Exception in basic_typed_children: {e}")
        return []

def main():
    try:
        logger.info("=" * 80)
        logger.info("Starting a new run of get-pools script")

        try:
            import libzfs
        except Exception as e:
            logger.error(f"libzfs import failed: {e}")
            print(json.dumps(_pools_from_zpool_list_min(), indent=4))
            return

        try:
            with libzfs.ZFS() as zfs:
                z_pools = []
                for p in zfs.pools:
                    pool = p.asdict()
                    root_dataset = pool.get("root_dataset")
                    if root_dataset is not None:
                        pool["root_dataset"]["properties"]["creation"]["parsed"] = str(
                            pool["root_dataset"]["properties"]["creation"]["parsed"]
                        )
                        if "scan" in pool:
                            pool["scan"]["start_time"] = str(pool["scan"]["start_time"])
                            pool["scan"]["end_time"] = str(pool["scan"]["end_time"])
                            pool["scan"]["pause"] = str(pool["scan"]["pause"])
                        pool["root_dataset"]["children"] = basic_typed_children(pool["root_dataset"]["children"])
                    else:
                        pool["root_dataset"] = None

                    logger.debug(f"Parsed pool data: {{'name': '{pool['name']}', 'status': '{pool['status']}'}}")
                    z_pools.append(pool)

                logger.info(f"Pools discovered: {len(z_pools)}")
                print(json.dumps(z_pools, indent=4, default=str))
        except PermissionError as e:
            logger.error(f"Permission opening libzfs: {e}")
            print(json.dumps(_pools_from_zpool_list_min(), indent=4))
        except Exception as e:
            logger.error(f"Unhandled exception with libzfs: {e}")
            print(json.dumps(_pools_from_zpool_list_min(), indent=4))
    except Exception as e:
        logger.error(f"Exception in main: {e}")
        print("[]")

if __name__ == "__main__":
    main()