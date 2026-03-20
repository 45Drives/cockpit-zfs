import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*ABCs.*collections.*")
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
        z_datasets = []

        for p in zfs.datasets:
            dataset = p.asdict()

            dataset['properties']['creation']['parsed'] = str(dataset['properties']['creation']['parsed'])

            dataset['children'] = basic_typed_children(dataset['children'])

            z_datasets.append(dataset)

    print(json.dumps(z_datasets, indent=4))
if __name__ == '__main__':
    main()