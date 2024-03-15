# Python script for sending snapshots
import subprocess
import argparse
import re
import json
import os

def destroy_for_overwrite_local(recvName):
    destroy_cmd = ['zfs', 'destroy', f'{recvName}', '-R']

    process_destroy = subprocess.Popen(
        destroy_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print(f"Executing command: zfs destroy -R {recvName}")
    
    stdout, stderr = process_destroy.communicate()

    if process_destroy.returncode != 0:
        raise Exception(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout)

def destroy_for_overwrite_remote(recvName, recvHostUser, recvHost, recvPort=22):
    ssh_cmd = ['ssh']

    if recvPort != '22':
        ssh_cmd.extend(['-p', recvPort])

    ssh_cmd.append(recvHostUser + '@' + recvHost)

    ssh_cmd.extend(['zfs', 'destroy', f'{recvName}', '-R'])

    process_destroy = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print(f"Executing command: zfs destroy -R {recvName}")
    
    stdout, stderr = process_destroy.communicate()

    if process_destroy.returncode != 0:
        raise Exception(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout)

def remove_remote_file(hostname, username, port=22):
    ssh_cmd = ['ssh', '-p', str(port), f'{username}@{hostname}', f'if [ -e full_output.json ]; then rm full_output.json; fi']
    
    process_remove = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process_remove.communicate()

    if process_remove.returncode != 0:
        raise Exception(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout)

def send_dataset(sendName, recvName, sendName2="", forceOverwrite=False, compressed=False, raw=False, recvHost="", recvPort=22, recvHostUser="", mBufferSize=1, mBufferUnit="G"):
    try:
        # Initialize variables 
        snapshot_name = sendName
        total_size = None
        update_size = None
        status = None
        output_data = []
        final_data = None

        # Delete progress file if exists from previous send
        file_path = "full_output.json"
        if os.path.exists(file_path):
            os.remove(file_path)

        # If remote send, delete progress file if exists 
        if recvHost != "":
            remove_remote_file(recvHost, recvHostUser, recvPort)
            # If force overwrite required  
            # if forceOverwrite == True:
            #     destroy_for_overwrite_remote(recvName, recvHostUser, recvHost, recvPort)

        # Initial local send command
        send_cmd = ['zfs', 'send', '-v']

        if compressed:
            send_cmd.append('-Lce')

        if raw:
            send_cmd.append('-w')

        if sendName2 != "":
            send_cmd.extend(['-i', sendName2])

        send_cmd.append(sendName)

        print(f"SEND_CMD: {send_cmd}")

        process_send = subprocess.Popen(
            send_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # If sending locally
        if recvHost == "":
            recv_cmd = ['zfs', 'recv', '-v']

            if forceOverwrite:
                recv_cmd.append('-F')
                # If force overwrite required  
                destroy_for_overwrite_local(recvName)

            recv_cmd.append(recvName)

            print(f"RECV_CMD: {recv_cmd}")

            process_recv = subprocess.Popen(
                recv_cmd,
                stdin=process_send.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            while process_send.poll() is None:
                output = process_send.stderr.readline()
                
                if output:
                    # Extract total size
                    pattern_total = r'estimated size is (\d+(\.\d+)?[KMG])'
                    match_total = re.search(pattern_total, str(output))
                    if match_total:
                        total_size = match_total.group(1)

                    # Extract progress data
                    pattern_progress = r'(\d+:\d+\d+)\s+(\d+(\.\d+)?[KMG])\s+([\w\/@]+)'
                    match_progress = re.search(pattern_progress, str(output))
                    if match_progress:
                        update_size = match_progress.group(2)
                        snapshot_name = match_progress.group(4)
                        status = "ongoing"

                        # Create a data dictionary
                        data = {
                            "snapshot": snapshot_name,
                            "status": status,
                            "sent": update_size,
                            "totalSize": total_size,
                        }

                        output_data.append(data)
                        print(data)

                        with open(file_path, 'w') as json_file:
                            # Loop to append each line one at a time
                            json_file.write(json.dumps(data) + '\n')
                            json_file.flush()

                        # current_directory = os.getcwd()
                        # print("Current Working Directory:", current_directory)
                        
                    if match_progress is False:
                        break
                
            while process_recv.poll() is None:
                recv_output = process_recv.stdout.readline()

                # Check for the "received" line structure
                if "received" in str(recv_output):
                    # Extract the final progress information
                    pattern_final_progress = r'received\s+([\d.]+[KMG]?)\s+stream\s+in\s+(\d+)\s+seconds\s+\(([\d.]+[KMG]?)\/sec\)'

                    match_final_progress = re.search(pattern_final_progress, str(recv_output))
                    if match_final_progress:
                        received_size = match_final_progress.group(1)
                        status = "finished"
                        
                        # Create the final data object
                        final_data = {
                            "snapshot": snapshot_name,
                            "status": status,
                            "sent": received_size,
                            "totalSize": total_size,
                        }

                        # Print the data for verification
                        print(final_data)
                        output_data.append(final_data)

                        with open(file_path, 'w') as json_file:
                            json_file.write(json.dumps(final_data) + '\n')
                            json_file.flush()

            stdout, stderr = process_recv.communicate()

            if process_recv.returncode != 0:
                raise Exception(f"Error:{stderr}")
            else:
                print(stdout)

            # Print out entire JSON
            print(json.dumps(output_data, indent=2))

        # If sending remotely via SSH
        if recvHost != "":
            if forceOverwrite:
                destroy_for_overwrite_remote(recvName, recvHostUser, recvHost, recvPort)

            m_buff_cmd = ['mbuffer', '-s', '256k']
            m_buff_cmd.extend(['-m', mBufferSize + mBufferUnit])

            process_m_buff = subprocess.Popen(
                m_buff_cmd,
                stdin=process_send.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            ssh_cmd = ['ssh']

            if recvPort != '22':
                ssh_cmd.extend(['-p', recvPort])

            ssh_cmd.append(recvHostUser + '@' + recvHost)

            ssh_cmd.extend(['zfs', 'recv'])

            if forceOverwrite:
                ssh_cmd.append('-F')

            ssh_cmd.append('-v')

            ssh_cmd.append(recvName)

            print(f"SSH_CMD: {ssh_cmd}")

            process_ssh_recv = subprocess.Popen(
                ssh_cmd,
                stdin=process_m_buff.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            while process_send.poll() is None:
                output = process_send.stderr.readline()
                
                if output:
                    # Extract total size
                    pattern_total = r'estimated size is (\d+(\.\d+)?[KMG])'
                    match_total = re.search(pattern_total, str(output))
                    if match_total:
                        total_size = match_total.group(1)

                    # Extract progress data
                    pattern_progress = r'(\d+:\d+\d+)\s+(\d+(\.\d+)?[KMG])\s+([\w\/@]+)'
                    match_progress = re.search(pattern_progress, str(output))
                    if match_progress:
                        update_size = match_progress.group(2)
                        snapshot_name = match_progress.group(4)
                        status = "ongoing"

                        # Create a data dictionary
                        data = {
                            "snapshot": snapshot_name,
                            "status": status,
                            "sent": update_size,
                            "totalSize": total_size,
                        }

                        output_data.append(data)
                        print(data)

                        with open(file_path, 'w') as json_file:
                            # Loop to append each line one at a time
                            json_file.write(json.dumps(data) + '\n')
                            json_file.flush()

                        # current_directory = os.getcwd()
                        # print("Current Working Directory:", current_directory)
                        
                    if match_progress is False:
                        break
                
            while process_ssh_recv.poll() is None:
                ssh_output = process_ssh_recv.stdout.readline()

                if "received" in str(ssh_output):
                    # Extract the final progress information
                    pattern_final_progress = r'received\s+([\d.]+[KMG]?)\s+stream\s+in\s+(\d+)\s+seconds\s+\(([\d.]+[KMG]?)\/sec\)'

                    match_final_progress = re.search(pattern_final_progress, str(ssh_output))
                    if match_final_progress:
                        received_size = match_final_progress.group(1)
                        status = "finished"
                        
                        # Create the final data object
                        final_data = {
                            "snapshot": snapshot_name,
                            "status": status,
                            "sent": received_size,
                            "totalSize": total_size,
                        }

                        # Print the data for verification
                        print(final_data)
                        output_data.append(final_data)

                        # current_directory = os.getcwd()
                        # print("Current Working Directory:", current_directory)

                        with open(file_path, 'w') as json_file:
                            json_file.write(json.dumps(final_data) + '\n')
                            json_file.flush()

            stdout, stderr = process_ssh_recv.communicate()

            if process_ssh_recv.returncode != 0:
                raise Exception(f"Error: {stderr}")
            else:
                print(stdout)

             # Print out entire JSON
            print(json.dumps(output_data, indent=2))
        

    except Exception as e:
        print(f"An error occurred: {e}")

def main() : 
    parser = argparse.ArgumentParser(description='Send ZFS Dataset')
    parser.add_argument('sendName', type=str, help='sending dataset name')
    parser.add_argument('recvName', type=str, help='receiving dataset name')
    parser.add_argument('sendName2', type=str, help='first snap for incremental send')
    parser.add_argument('forceOverwrite', type=str, default='False', help='forcefully overwrite existing dataset')
    parser.add_argument('compressed', type=str, default='False', help='sending dataset compression')
    parser.add_argument('raw', type=str, default='False', help='sending dataset raw')
    parser.add_argument('recvHost', type=str, help='receiving dataset host')
    parser.add_argument('recvPort', type=str, default='22', help='receiving dataset port')
    parser.add_argument('recvHostUser', type=str, help='receiving dataset host user')
    parser.add_argument('mBufferSize', type=str, default='1', help='mbuffer size')
    parser.add_argument('mBufferUnit', type=str, default="G", help='mbuffer unit')

    args = parser.parse_args()

    sendName = args.sendName
    recvName = args.recvName
    sendName2 = args.sendName2
    forceOverwrite = args.forceOverwrite.lower() == 'true'
    compressed = args.compressed.lower() == 'true'
    raw = args.raw.lower() == 'true'
    recvHost = args.recvHost
    recvPort = args.recvPort
    recvHostUser = args.recvHostUser
    mBufferSize = args.mBufferSize
    mBufferUnit = args.mBufferUnit

    # if sendName2 != "":
    #     print(f"Sending incrementally to {recvName} from {sendName2} to {sendName}")
    # else:
    #     print(f"Executing command: zfs send {sendName} | {recvName}")

    send_dataset(sendName, recvName, sendName2, forceOverwrite, compressed, raw, recvHost, recvPort, recvHostUser, mBufferSize, mBufferUnit)

if __name__ == '__main__':
    main()