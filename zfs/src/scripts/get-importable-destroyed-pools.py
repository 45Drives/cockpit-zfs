import libzfs
import json


def main():
    with libzfs.ZFS() as zfs:
        z_pools = []

        for p in zfs.find_import(destroyed='True', search_paths=['/dev', '/dev/disk/by-id', '/dev/disk/by-path', '/dev/disk/by-vdev']):
            pool = p.asdict()
            if 'scan' in pool:
                pool['scan']['start_time'] = str(pool['scan']['start_time'])
                pool['scan']['end_time'] = str(pool['scan']['end_time'])
            
            z_pools.append(pool)

    print(json.dumps(z_pools, indent=4))
if __name__ == '__main__':
    main()
