import libzfs
import json

def get_disks(group):
    disks = []
    for vdev in group:
        if vdev.get('type') == 'disk':
            disks.append({
                'name': vdev.get('name'),
                'stats': vdev.get('stats', {}),
                'guid': vdev.get('guid'),
                'status': vdev.get('status'),
            })
        else:
            children = vdev.get('children') or []
            disks.extend(get_disks(children))
    return disks

def main():
    with libzfs.ZFS() as zfs:
        z_pools = {}

        for p in zfs.pools:
            pool = p.asdict()
            name = pool.get('name')
            disks = []

            groups = pool.get('groups') or {}
            for group_name, group in groups.items():
                disks.extend(get_disks(group or []))

            z_pools[name] = disks

    print(json.dumps(z_pools, indent=4))

if __name__ == '__main__':
    main()
