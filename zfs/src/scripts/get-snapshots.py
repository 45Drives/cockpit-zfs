#!/usr/bin/env python3
import libzfs
import json
import sys
from typing import Optional

def basic_typed_children(children):
    for i in range(len(children)):
        children[i]['properties']['creation']['parsed'] = str(children[i]['properties']['creation']['parsed'])
        if len(children[i]['children']) >= 1:
            children[i]['children'] = basic_typed_children(children[i]['children'])
    return children

def _prop(snap, name) -> Optional[dict]:
    """
    Safely extract a ZFS property from a snapshot into an asdict()-like shape (avoiding asdict() due to crashing with large amounts of datasets):
    { "value": ..., "rawvalue": ..., "parsed": ... }
    Returns None if unavailable.
    """
    try:
        p = snap.properties.get(name)
        if p is None:
            return None
        out = {}
        if hasattr(p, "value"):
            out["value"] = str(p.value)
        if hasattr(p, "raw"):
            out["rawvalue"] = str(p.raw)
        if hasattr(p, "parsed"):
            out["parsed"] = str(p.parsed)
        return out
    except Exception:
        return None

def _safe_snapshot_dict(snap):
    """
    Build a safe dict for a snapshot WITHOUT calling asdict() (which would
    trigger holds lookups). Shaped to match the fields your UI expects.
    """
    name = snap.name  # "pool/dataset@snap"
    dataset = name.split("@", 1)[0] if "@" in name else name
    snap_name = name.split("@", 1)[1] if "@" in name else ""
    pool = dataset.split("/", 1)[0] if dataset else ""

    guid = _prop(snap, "guid") or {"value": ""}  # UI uses properties.guid.value
    creation = _prop(snap, "creation") or {"rawvalue": "0", "parsed": "", "value": ""}
    referenced = _prop(snap, "referenced") or {}
    used = _prop(snap, "used") or {}

    return {
        "name": name,
        "id": guid.get("value", "") or name,          # fallback to name if guid missing
        "snapshot_name": snap_name,                   # UI uses snapshot.snapshot_name
        "dataset": dataset,
        "pool": pool,
        "mountpoint": "",                             # snapshots typically not mounted
        "type": "snapshot",
        "properties": {
            "guid": guid,
            "creation": creation,
            "referenced": referenced,
            "used": used,
            # UI reads snapshot.properties.clones.parsed; keep a safe default
            "clones": {"parsed": []},
        },
        "holds": {},
    }

def get_all_snapshots():
    with libzfs.ZFS() as zfs:
        z_datasets = {}
        for d in zfs.datasets:
            snaps = []
            for snap in d.snapshots:
                try:
                    snaps.append(_safe_snapshot_dict(snap))
                except libzfs.ZFSException:
                    # Snapshot vanished or is otherwise inaccessible; skip it
                    continue
                except Exception:
                    # Be defensive against any unexpected property access errors
                    continue
            z_datasets[d.name] = snaps
    return json.dumps(z_datasets, indent=4)

def get_snapshots_by_dataset(dataset_name):
    with libzfs.ZFS() as zfs:
        z_datasets = {}
        try:
            d = zfs.get_dataset(dataset_name)
        except libzfs.ZFSException:
            return json.dumps({}, indent=4)

        snaps = []
        for snap in d.snapshots:
            try:
                snaps.append(_safe_snapshot_dict(snap))
            except libzfs.ZFSException:
                continue
            except Exception:
                continue
        z_datasets[d.name] = snaps
    return json.dumps(z_datasets, indent=4)

def get_snapshots_by_pool(pool_name):
    with libzfs.ZFS() as zfs:
        z_datasets = {}
        for d in zfs.datasets:
            # Be defensive: d.pool may be missing in some edge cases
            if getattr(d.pool, "name", None) == pool_name:
                snaps = []
                for snap in d.snapshots:
                    try:
                        snaps.append(_safe_snapshot_dict(snap))
                    except libzfs.ZFSException:
                        continue
                    except Exception:
                        continue
                z_datasets[d.name] = snaps
    return json.dumps(z_datasets, indent=4)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get-snapshots.py [all | dataset:<name> | pool:<name>]")
        return

    command = sys.argv[1]
    snapshots = None

    if command == 'all':
        snapshots = get_all_snapshots()
    elif command.startswith('dataset:'):
        dataset_name = command.split(':', 1)[1]
        snapshots = get_snapshots_by_dataset(dataset_name)
    elif command.startswith('pool:'):
        pool_name = command.split(':', 1)[1]
        snapshots = get_snapshots_by_pool(pool_name)
    else:
        print("Invalid command. Use 'all', 'dataset:<name>', or 'pool:<name>'.")
        return

    if snapshots:
        print(snapshots)

if __name__ == '__main__':
    main()
