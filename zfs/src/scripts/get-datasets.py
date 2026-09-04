import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*ABCs.*collections.*")
import json
import subprocess
import sys

DISPLAY_COLUMNS = [
    'name',
    'type',
    'guid',
    'mountpoint',
    'encryption',
    'keystatus',
    'atime',
    'casesensitivity',
    'compression',
    'dedup',
    'dnodesize',
    'xattr',
    'recordsize',
    'quota',
    'readonly',
    'available',
    'creation',
    'mounted',
    'usedbyrefreservation',
    'usedbydataset',
    'canmount',
    'aclinherit',
    'acltype',
    'checksum',
    'refreservation',
    'used',
    'usedbysnapshots',
    'volsize',
]

NUMERIC_PROPERTIES = {
    'available',
    'quota',
    'refreservation',
    'used',
    'usedbydataset',
    'usedbyrefreservation',
    'usedbysnapshots',
    'volsize',
}

def _property(value, parsed=None, rawvalue=None):
    if parsed is None:
        parsed = value
    prop = {
        'value': value,
        'parsed': parsed,
    }
    if rawvalue is not None:
        prop['rawvalue'] = rawvalue
    return prop

def _parse_int(value, default=0):
    try:
        if value in ('', '-', 'none', 'N/A'):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def _warn(message):
    print(f"Warning: {message}", file=sys.stderr)

def _dataset_type(value):
    if value == 'filesystem':
        return 'FILESYSTEM'
    if value == 'volume':
        return 'VOLUME'
    return value.upper()

def _zfs_list_rows(columns, parsable=False):
    command = ['zfs', 'list', '-H']
    if parsable:
        command.append('-p')
    command.extend(['-t', 'filesystem,volume', '-o', ','.join(columns)])
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'zfs list failed')

    rows = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        values = line.split('\t')
        row = dict(zip(columns, values))
        rows[row.get('name', '')] = row

    return rows

def _snapshot_counts():
    result = subprocess.run(
        ['zfs', 'list', '-H', '-t', 'snapshot', '-o', 'name'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    if result.returncode != 0:
        return {}

    counts = {}
    for line in result.stdout.splitlines():
        snapshot_name = line.strip()
        if not snapshot_name or '@' not in snapshot_name:
            continue
        dataset_name = snapshot_name.split('@', 1)[0]
        counts[dataset_name] = counts.get(dataset_name, 0) + 1

    return counts

def _property_from_rows(display_row, parsed_row, property_name, default=''):
    value = display_row.get(property_name, default)
    rawvalue = parsed_row.get(property_name, value)
    if property_name in NUMERIC_PROPERTIES:
        return _property(value, _parse_int(rawvalue), rawvalue)

    if property_name == 'creation':
        return _property(value, str(rawvalue), rawvalue)

    return _property(value, rawvalue, rawvalue)

def _populate_children(datasets):
    by_name = {dataset['name']: dataset for dataset in datasets}
    for dataset in datasets:
        dataset['children'] = []

    for dataset in datasets:
        if '/' not in dataset['name']:
            continue
        parent_name = dataset['name'].rsplit('/', 1)[0]
        parent = by_name.get(parent_name)
        if parent is not None:
            parent['children'].append(dataset)

    return datasets

def _datasets_from_zfs_list():
    display_rows = _zfs_list_rows(DISPLAY_COLUMNS)
    parsed_rows = _zfs_list_rows(DISPLAY_COLUMNS, parsable=True)
    snapshot_counts = _snapshot_counts()

    datasets = []
    for name in display_rows:
        row = display_rows[name]
        parsed_row = parsed_rows.get(name, row)
        pool = name.split('/', 1)[0]
        dataset_type = _dataset_type(row.get('type', ''))
        is_encrypted = row.get('encryption', 'off') != 'off'
        key_loaded = row.get('keystatus') == 'available'

        datasets.append({
            'name': name,
            'id': name,
            'pool': pool,
            'type': dataset_type,
            'encrypted': is_encrypted,
            'key_loaded': key_loaded,
            'properties': {
                'guid': _property_from_rows(row, parsed_row, 'guid'),
                'mountpoint': _property_from_rows(row, parsed_row, 'mountpoint'),
                'encryption': _property_from_rows(row, parsed_row, 'encryption', 'off'),
                'keystatus': _property_from_rows(row, parsed_row, 'keystatus', 'none'),
                'atime': _property_from_rows(row, parsed_row, 'atime', 'on'),
                'casesensitivity': _property_from_rows(row, parsed_row, 'casesensitivity', 'sensitive'),
                'compression': _property_from_rows(row, parsed_row, 'compression', 'off'),
                'dedup': _property_from_rows(row, parsed_row, 'dedup', 'off'),
                'dnodesize': _property_from_rows(row, parsed_row, 'dnodesize', 'legacy'),
                'xattr': _property_from_rows(row, parsed_row, 'xattr', 'sa'),
                'recordsize': _property_from_rows(row, parsed_row, 'recordsize', '128K'),
                'quota': _property_from_rows(row, parsed_row, 'quota', 'none'),
                'readonly': _property_from_rows(row, parsed_row, 'readonly', 'off'),
                'available': _property_from_rows(row, parsed_row, 'available', '0'),
                'creation': _property_from_rows(row, parsed_row, 'creation'),
                'snapshot_count': _property(str(snapshot_counts.get(name, 0)), snapshot_counts.get(name, 0)),
                'mounted': _property_from_rows(row, parsed_row, 'mounted', 'no'),
                'usedbyrefreservation': _property_from_rows(row, parsed_row, 'usedbyrefreservation', '0B'),
                'usedbydataset': _property_from_rows(row, parsed_row, 'usedbydataset', '0B'),
                'canmount': _property_from_rows(row, parsed_row, 'canmount', 'on'),
                'aclinherit': _property_from_rows(row, parsed_row, 'aclinherit', 'restricted'),
                'acltype': _property_from_rows(row, parsed_row, 'acltype', 'posixacl'),
                'checksum': _property_from_rows(row, parsed_row, 'checksum', 'on'),
                'refreservation': _property_from_rows(row, parsed_row, 'refreservation', 'none'),
                'used': _property_from_rows(row, parsed_row, 'used', '0B'),
                'usedbysnapshots': _property_from_rows(row, parsed_row, 'usedbysnapshots', '0B'),
                'volsize': _property_from_rows(row, parsed_row, 'volsize', '0B'),
            },
            'children': [],
        })

    return _populate_children(datasets)

def basic_typed_children(children):
    for i in range(0, len(children)):
        children[i]['properties']['creation']['parsed'] = str(children[i]['properties']['creation']['parsed'])

        if len(children[i]['children']) >= 1:
            children[i]['children'] = basic_typed_children(children[i]['children'])

    return children

def main():
    try:
        import libzfs
    except ImportError as e:
        _warn(f"libzfs import failed, using zfs list fallback: {e}")
        print(json.dumps(_datasets_from_zfs_list(), indent=4))
        return

    try:
        with libzfs.ZFS() as zfs:
            z_datasets = []

            for p in zfs.datasets:
                try:
                    dataset = p.asdict()

                    # Only include filesystems and volumes (zvols)
                    if dataset.get('type') not in ('FILESYSTEM', 'VOLUME'):
                        continue

                    dataset['properties']['creation']['parsed'] = str(dataset['properties']['creation']['parsed'])

                    dataset['children'] = basic_typed_children(dataset['children'])

                    z_datasets.append(dataset)
                except Exception as e:
                    print(f"Warning: skipping dataset: {e}", file=sys.stderr)
                    continue

        print(json.dumps(z_datasets, indent=4))
    except Exception as e:
        _warn(f"libzfs dataset enumeration failed, using zfs list fallback: {e}")
        print(json.dumps(_datasets_from_zfs_list(), indent=4))
if __name__ == '__main__':
    main()
