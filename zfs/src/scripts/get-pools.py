import libzfs
import json

def basic_typed_children(children):
    for i in range(0, len(children)):
        children[i]['properties']['creation']['parsed'] = str(children[i]['properties']['creation']['parsed'])

        if len(children[i]['children']) >= 1:
            children[i]['children'] = basic_typed_children(children[i]['children'])

    return children

def main():
    with libzfs.ZFS() as zfs:
        z_pools = []

        for p in zfs.pools:
            pool = p.asdict()

            pool['root_dataset']['properties']['creation']['parsed'] = str(pool['root_dataset']['properties']['creation']['parsed'])

            if 'scan' in pool:
                pool['scan']['start_time'] = str(pool['scan']['start_time'])
                pool['scan']['end_time'] = str(pool['scan']['end_time'])
                pool['scan']['pause'] = str(pool['scan']['pause'])
                
            pool['root_dataset']['children'] = basic_typed_children(pool['root_dataset']['children'])

            z_pools.append(pool)

    print(json.dumps(z_pools, indent=4))
if __name__ == '__main__':
    main()
