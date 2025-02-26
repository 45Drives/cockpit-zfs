import libzfs
import json

def get_disks(group):
    disks = []
    for vdev in group:

        if vdev['type'] == 'disk':
            disks.append({
                'name': vdev['name'],
                'stats':vdev['stats'],
                'guid': vdev['guid'],
                'status': vdev['status'],
            })
        else:
            newDisks = get_disks(vdev['children'])
            disks = disks + newDisks

    return disks

def main():
    with libzfs.ZFS() as zfs:
        z_pools = {}

        for p in zfs.pools:
            pool = p.asdict()
            disks = []
            for group in pool['groups']:
                disks = disks + get_disks(pool['groups'][group])
            z_pools[pool['name']] = disks

    print(json.dumps(z_pools, indent=4))
if __name__ == '__main__':
    main()
