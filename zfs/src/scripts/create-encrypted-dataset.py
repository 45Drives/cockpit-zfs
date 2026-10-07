# Python script for creating an encrypted ZFS dataset
import subprocess
import argparse
import tempfile
import os

CERTIFIED_PROFILE = "PROFILE_ID=45D-FIPS-RL9.6-v1"

def certified_profile_installed():
    try:
        with open('/etc/45drives/fips-profile', 'r') as profile_file:
            return any(line.strip() == CERTIFIED_PROFILE for line in profile_file)
    except OSError:
        return False

def create_encrypted_dataset(atime, case, compress, dedup, dnode, xattr, record, readonly, quota, encryption, keyformat, keylocation, path, passphrase_file):
    if certified_profile_installed():
        raise RuntimeError(
            'Native ZFS encryption is disabled in 45D-FIPS-RL9.6-v1; '
            'use LUKS/dm-crypt beneath the ZFS pool.'
        )

    try:
        # Create a secure temporary file to store the passphrase
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_passphrase_file:
            temp_passphrase_file.write(passphrase_file)
            temp_passphrase_file_path = temp_passphrase_file.name

        try:
            # Construct the ZFS create command with provided arguments
            process = subprocess.Popen(
                ['zfs', 'create',
                '-o', atime,
                '-o', case,
                '-o', compress,
                '-o', dedup,
                '-o', dnode,
                '-o', xattr,
                '-o', record,
                '-o', quota,
                '-o', readonly,
                '-o', encryption,
                '-o', keyformat,
                '-o', keylocation,
                path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Provide the passphrase file as input to the process
            with open(temp_passphrase_file_path, 'rb') as f:
                stdout, stderr = process.communicate(input=f.read())

            if process.returncode != 0:
                raise Exception(f"Error: {stderr.decode('utf-8')}")
            else:
                print(stdout)

        finally:
            # Delete the temporary passphrase file after using it
            os.remove(temp_passphrase_file_path)

    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Create and encrypt a ZFS Dataset')
    parser.add_argument('cmdString', type=str, help='zfs create')
    parser.add_argument('atime',type=str, help='access time')
    parser.add_argument('case',type=str, help='case sensitivity')
    parser.add_argument('compress',type=str, help='compression')
    parser.add_argument('dedup',type=str, help='deduplication')
    parser.add_argument('dnode',type=str, help='dnode size')
    parser.add_argument('xattr',type=str, help='extended attributes')
    parser.add_argument('record',type=str, help='record size')
    parser.add_argument('quota',type=str, help='quota')
    parser.add_argument('readonly',type=str, help='read only')
    parser.add_argument('encryption',type=str, help='encryption')
    parser.add_argument('keyformat',type=str, help='keyformat')
    parser.add_argument('keylocation',type=str, help='keylocation')
    parser.add_argument('path',type=str, help='path')
    parser.add_argument('passphrase',type=str, help='passphrase')

    args = parser.parse_args()

    # Extract values from command-line arguments
    cmdString = args.cmdString
    atime = args.atime
    case = args.case
    compress = args.compress
    dedup = args.dedup
    dnode = args.dnode
    xattr = args.xattr
    record = args.record
    quota = args.quota
    readonly = args.readonly
    encryption = args.encryption
    keyformat = args.keyformat
    keylocation = args.keylocation
    path = args.path
    passphrase = args.passphrase

    print(f"Executing command: {cmdString} create {atime} {case} {compress} {dedup} {dnode} {xattr} {record} {quota} {readonly} {encryption} {keyformat} {keylocation} {path}")

    # Call the function to create the encrypted dataset
    create_encrypted_dataset(atime, case, compress, dedup, dnode, xattr, record, quota, readonly, encryption, keyformat, keylocation, path, passphrase)

if __name__ == '__main__':
    main()

