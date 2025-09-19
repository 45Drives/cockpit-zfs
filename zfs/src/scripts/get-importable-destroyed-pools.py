#!/usr/bin/env python3
import json, logging
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


logger = get_logger("cockpit_zfs_getimportabledestroyedpools", "getimportabledestroyedpools.log")

def main():
    try:
        logger.info("=" * 80)
        logger.info("Starting a new run of get-importable-destroyed-pools script")

        try:
            import libzfs
        except Exception as e:
            logger.error(f"libzfs import failed: {e}")
            print("[]")
            return

        z_pools = []
        try:
            with libzfs.ZFS() as zfs:
                destroyed_importable = zfs.find_import(destroyed="True", search_paths=["/dev", "/dev/disk/by-id", "/dev/disk/by-path", "/dev/disk/by-vdev"])
                for p in destroyed_importable:
                    try:
                        pool = p.asdict()
                        logger.debug(f"Found pool: {{'name': '{pool['name']}', 'status': '{pool['status']}'}}")
                        if "scan" in pool:
                            pool["scan"]["start_time"] = str(pool["scan"]["start_time"])
                            pool["scan"]["end_time"] = str(pool["scan"]["end_time"])
                        z_pools.append(pool)
                    except Exception as pool_error:
                        logger.error(f"Error processing pool: {pool_error}")
        except PermissionError as e:
            logger.error(f"Permission error in find_import(destroyed=True): {e}")
            print("[]")
            return

        print(json.dumps(z_pools, indent=4))
    except Exception as e:
        logger.error(f"Exception in getting importable destroyed pools: {e}")
        print("[]")

if __name__ == "__main__":
    main()