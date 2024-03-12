import subprocess
import argparse

def check_if_recv_dataset_has_snapshots(recvName, recvHost, recvPort, recvHostUser):
    # Construct the SSH command
    if recvPort == '22':
        ssh_cmd = ['ssh', f'{recvHostUser}@{recvHost}', f'zfs list -H -o name -t snapshot {recvName}']
    else:
        ssh_cmd = ['ssh', '-p', f'{recvPort}', f'{recvHostUser}@{recvHost}', f'zfs list -H -o name -t snapshot {recvName}']

    # Run the SSH command
    process_check_snapshots = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,  # Ensures text mode for stdout and stderr
    )

    # Wait for the command to complete and capture the output
    stdout, stderr = process_check_snapshots.communicate()

    # Check the return code
    if process_check_snapshots.returncode != 0:
        # raise Exception(f"Error:{stderr}")
        return False
    else:
        # Check if the output contains snapshots
        return bool(stdout.strip())
