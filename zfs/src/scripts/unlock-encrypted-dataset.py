# Python script for unlocking encrypted datasets
import subprocess
import argparse
import tempfile
import os
import sys

def unlock_locked_dataset(name, passphrase_file):
    try :
        # Create a secure temporary file to store the passphrase
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_passphrase_file:
            temp_passphrase_file.write(passphrase_file)
            temp_passphrase_file_path = temp_passphrase_file.name

        try:
            # Construct the ZFS create command with provided arguments
            process = subprocess.Popen(
                ['zfs', 'load-key',
                name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Provide the passphrase file as input to the process
            with open(temp_passphrase_file_path, 'rb') as f:
                stdout, stderr = process.communicate(input=f.read())

            if process.returncode != 0:
                raise RuntimeError(stderr.decode('utf-8', errors='replace'))
            else:
                print(stdout)

        finally:
            # Delete the temporary passphrase file after using it
            os.remove(temp_passphrase_file_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Unlock encrypted ZFS Dataset')
    parser.add_argument('name', type=str, help='dataset name')

    args = parser.parse_args()

    # Extract values from arguments
    name = args.name
    passphrase = sys.stdin.read()

    print(f"Executing unlock command on {name}")

    # Call function to unlock dataset
    unlock_locked_dataset(name, passphrase)

if __name__ == '__main__':
    main()