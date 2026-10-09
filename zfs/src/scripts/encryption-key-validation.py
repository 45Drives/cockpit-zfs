# Python script for checking encryption passphrase is valid
import subprocess
import argparse
import tempfile
import os
import sys

def check_key(fileSystemName, passphrase):
    try:
        # Create a secure temporary file to store the passphrase
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_passphrase_file:
            temp_passphrase_file.write(passphrase)
            temp_passphrase_file_path = temp_passphrase_file.name

        try:
            # Construct the ZFS change-key command with the provided file system name
            process = subprocess.Popen(
                ['zfs', 'load-key', '-n', fileSystemName],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Provide the passphrase file as input to the process
            with open(temp_passphrase_file_path, 'rb') as f:
                process.communicate(input=f.read())
                # stdout, stderr = process.communicate(input=f.read())

            return process.returncode == 0
            # if process.returncode != 0:
            #     raise Exception(f"Error: {stderr.decode('utf-8')}")
            # else:
                # print(stdout)
                # return process.returncode

        finally:
            # Delete the temporary passphrase file after using it
            os.remove(temp_passphrase_file_path)

    except Exception as e:
        return False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Check encryption key validity for ZFS Dataset')
    parser.add_argument('fileSystemName', type=str, help='fileSystemName')

    args = parser.parse_args()

    # Extract values from command-line arguments
    fileSystemName = args.fileSystemName
    passphrase = sys.stdin.read()

    # Call function to check key
    is_valid = check_key(fileSystemName, passphrase)
    print(str(is_valid).lower())  # Print 'true' or 'false'

if __name__ == '__main__':
    main()
