# Python script for changing encrypted dataset keys
import subprocess
import argparse
import tempfile
import os
import sys

def change_key(fileSystemName, passphrase):
    try:
        # Create a secure temporary file to store the passphrase
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_passphrase_file:
            temp_passphrase_file.write(passphrase)
            temp_passphrase_file_path = temp_passphrase_file.name

        try:
            # Construct the ZFS change-key command with the provided file system name
            process = subprocess.Popen(
                ['zfs', 'change-key', fileSystemName],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Provide the passphrase file as input to the process
            with open(temp_passphrase_file_path, 'rb') as f:
                stdout, stderr = process.communicate(input=f.read())
            if process.returncode != 0:
                raise RuntimeError(stderr.decode('utf-8', errors='replace'))
            return True

        finally:
            # Delete the temporary passphrase file after using it
            os.remove(temp_passphrase_file_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Change encryption key for ZFS Dataset')
    parser.add_argument('fileSystemName', type=str, help='fileSystemName')

    args = parser.parse_args()

    # Extract values from command-line arguments
    fileSystemName = args.fileSystemName
    newPassphrase = sys.stdin.read()

    # print(f"Executing command: zfs change-key {fileSystemName}")

    # Call function to change key
    change_key(fileSystemName, newPassphrase)

if __name__ == '__main__':
    main()