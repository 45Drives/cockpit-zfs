import subprocess
import json
import os, glob, re
import logging
from logging.handlers import RotatingFileHandler

# Configure rotating log handler
log_file = '/var/log/cockpit_zfs_getdisks.log'
handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)  # 5MB max size, 3 backups
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger('cockpit_zfs_getdisks')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

def get_wwn_path(dev_path):
    """Return the /dev/disk/by-id/wwn-* symlink for this device, if any."""
    base = re.sub(r'(p?\d+)$', '', dev_path)  # strip partition suffix
    for link in glob.glob('/dev/disk/by-id/wwn-*'):
        try:
            if os.path.realpath(link) == base:
                return link
        except Exception:
            continue
    return None

# Example usage of the logger in the script
def get_lsdev_disks():
    try:
        result = subprocess.run(['lsdev', '-jdHmtTsfcp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"lsdev command failed: {result.stderr.decode()}")
            return None  # Return None if lsdev command fails

        logger.debug("lsdev command succeeded.")
        json_data = json.loads(result.stdout)

        disks = []
        for row in json_data['rows']:
            for disk in row:
                if not disk['occupied']:
                    continue

                device_path = disk['dev']
                partitions = int(disk['partitions'])

                disk_data = {
                    'vdev_path': f'/dev/disk/by-vdev/{disk["bay-id"]}',
                    'phy_path': disk['dev-by-path'],
                    'sd_path': device_path,
                    'name': disk['bay-id'],
                    'model': disk['model-name'],
                    'serial': disk['serial'],
                    'capacity': disk['capacity'],
                    'type': disk['disk_type'],
                    'usable': True,
                    'temp': disk['temp-c'],
                    'health': disk['health'],
                    'rotation_rate': disk['rotation-rate'],
                    'power_on_count': disk['power-cycle-count'],
                    'power_on_time': disk['power-on-time'],
                    'has_partitions': False if partitions == 0 else True
                }
                
                wwn_link = get_wwn_path(device_path)
                disk_data['wwn_path'] = wwn_link if wwn_link else 'Unknown'
                disk_data['wwn'] = os.path.basename(wwn_link) if wwn_link else 'Unknown'
                
                disk_log_data = {
                    'name': disk['bay-id'],
                    'type': disk['disk_type'],
                    'health': disk['health'],
                    'temp': disk['temp-c'],
                }
                
                logger.debug(f"Discovered disk: {disk_log_data}")
                disks.append(disk_data)
                
        logger.info(f"Disks discovered: {len(disks)}")
        return disks
    except Exception as e:
        logger.error(f"Exception in get_lsdev_disks: {str(e)}")
        return None

def get_boot_disk():
    """Finds the physical disk that contains the boot partition or root filesystem using lsblk."""
    try:
        # Get block devices and mountpoints
        result = subprocess.run(['lsblk', '-no', 'NAME,MOUNTPOINT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"lsblk command failed: {result.stderr.decode()}")
            return None

        mount_data = result.stdout.decode().strip().split("\n")

        boot_device = None
        for line in mount_data:
            parts = line.strip().split(None, 1)  # Split into two parts (device, mountpoint)

            if len(parts) == 1:
                continue  # Skip devices with no mountpoints
            
            device, mountpoint = parts
            device = f"/dev/{device.strip()}"  # Convert to full path

            # **🔹 FIX: Remove tree characters (├─, └─, etc.) from device names**
            device = re.sub(r'[^\w/-]', '', device)

            if mountpoint == "/boot":  # Prefer boot partition first
                boot_device = device
                break
            elif mountpoint == "/":  # Use root partition as fallback
                boot_device = device

        if not boot_device:
            # print("No boot or root partition found.")
            return None

        # Convert partition (e.g., /dev/sda2) to the parent disk (/dev/sda)
        # parent_disk = re.sub(r'\d+$', '', boot_device)
        parent_disk = re.sub(r'(p?\d+)$', '', boot_device)

        # print(f"Detected boot disk: {parent_disk}")
        return parent_disk

    except Exception as e:
        print(f"Error determining boot disk: {e}")
        return None
    
def get_lsblk_disks(nvme_only=False):
    """Get all disks (or only NVMe disks if nvme_only=True) using lsblk JSON output and udevadm."""
    try:
        # Get the boot drive
        boot_drive = get_boot_disk()
        logger.info(f"Boot drive detected: {boot_drive}")
        
        # Run lsblk with JSON output, including mountpoints
        lsblk_result = subprocess.run(['lsblk', '-dnpJ', '-o', 'NAME,TYPE,SIZE,ROTA,SERIAL,MODEL,MOUNTPOINT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if lsblk_result.returncode != 0:
            logger.error(f"lsblk command failed: {lsblk_result.stderr.decode()}")
            return []

        logger.debug("lsblk command succeeded.")
        lsblk_data = json.loads(lsblk_result.stdout.decode())
        # print('lsblk_data:', lsblk_data)
        disks = []

        for device in lsblk_data['blockdevices']:
            device_name = device['name']
            
            # Skip if nvme_only is True and device is not NVMe
            if nvme_only and 'nvme' not in device['name']:
                continue
            if device['type'] == 'loop':  # Ignore loop devices
                continue  
            
             # Skip the boot disk
            if device_name == boot_drive or boot_drive in device_name:
                logger.info(f"Skipping boot drive: {device_name}")
                continue

            # Check if this device is a boot drive (mounted at / or /boot)
            if 'children' in device:
                for partition in device['children']:
                    # TODO: FILTER OUT BOOT DRIVES
                    if partition.get('mountpoint') in ['/', '/boot']:
                        logger.info(f"Skipping boot drive: {device['name']}")
                        continue

            # Collect additional information using smartctl if available
            smartctl_data = get_smartctl_data(device['name'].split('/')[-1])  # Get only the device name, e.g., 'sda'
            # print('smartctl_data', smartctl_data)
            
            # Get additional details using udevadm
            udevadm_result = subprocess.run(['udevadm', 'info', '--query=all', f'--name={device["name"]}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if udevadm_result.returncode != 0:
                logger.error(f"udevadm failed for {device['name']}: {udevadm_result.stderr.decode()}")
                continue

            udevadm_output = udevadm_result.stdout.decode().split('\n')
            # print('udevadm_output', udevadm_output)
            udev_info = {}
            for line in udevadm_output:
                if '=' in line:
                    key, value = line.split('=', 1)
                    udev_info[key.strip()] = value.strip()

            # Append the disk data to the list
            disk_data = {
                'vdev_path': 'N/A',
                'phy_path': f'/dev/disk/by-path/{udev_info.get("E: ID_PATH", "unknown")}',
                'sd_path': device['name'],
                'name': device['name'].split('/')[-1],
                'model': device.get('model', udev_info.get('E: ID_MODEL', 'Unknown')),
                'serial': device.get('serial', udev_info.get('E: ID_SERIAL_SHORT', 'Unknown')),
                'capacity': device['size'],
                'type': 'NVMe' if 'nvme' in device['name'] else device['type'].capitalize(),
                'usable': device.get('ro', '0') == '0',
                'temp': f'{smartctl_data["temp"]}℃' if smartctl_data["temp"] is not None else 'Unknown',
                'health': "OK" if smartctl_data['health'] == 'PASSED' else "POOR",
                'rotation_rate': 0 if 'nvme' in device['name'] else (device['rota'] == '1'),
                'power_on_count': smartctl_data['power_cycle_count'],
                'power_on_time': smartctl_data['power_on_hours'],
                'has_partitions': 'E: ID_PART_TABLE_TYPE' in udev_info
            }
            
            wwn_link = get_wwn_path(device['name'])  # e.g. /dev/nvme0n1 or /dev/sda
            disk_data['wwn_path'] = wwn_link if wwn_link else 'Unknown'
            disk_data['wwn'] = os.path.basename(wwn_link) if wwn_link else 'Unknown'

            # print('disk_data', disk_data)

            disk_log_data = {
                'name': device['name'].split('/')[-1],
                'type': 'NVMe' if 'nvme' in device['name'] else device['type'].capitalize(),
                'temp': f'{smartctl_data["temp"]}℃' if smartctl_data["temp"] is not None else 'Unknown',
                'health': "OK" if smartctl_data['health'] == 'PASSED' else "POOR",
                'mountpoint': device.get('mountpoint', 'none')
            }
            # print('disklog_data', disk_log_data)

            logger.debug(f"Discovered disk: {disk_log_data}")
            disks.append(disk_data)

        logger.info(f"Disks discovered: {len(disks)}")
        return disks

    except Exception as e:
        logger.error(f"Exception in get_lsblk_disks: {str(e)}")
        return []

def get_smartctl_data(device):
    """Runs smartctl to get additional information like temperature, power-on time, and health status."""
    try:
        smartctl_result = subprocess.run(['smartctl', '-a', f'/dev/{device}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if smartctl_result.returncode != 0:
            logger.error(f"smartctl failed for {device}: {smartctl_result.stderr.decode()}")
            return {'temp': None, 'power_on_hours': None, 'power_cycle_count': None, 'health': None}

        output = smartctl_result.stdout.decode().split('\n')
        logger.debug(f"smartctl command succeeded.")
        smart_info = {'temp': None, 'power_on_hours': None, 'power_cycle_count': None, 'health': None}

        for line in output:
            if 'Temperature' in line and 'Celsius' in line:
                smart_info['temp'] = int(line.split()[-2])  # Extract temperature
            elif 'Power On Hours' in line:
                smart_info['power_on_hours'] = int(line.split()[-1])  # Extract power-on hours
            elif 'Power Cycle Count' in line:
                smart_info['power_cycle_count'] = int(line.split()[-1])  # Extract power cycle count
            elif 'SMART overall-health' in line:
                smart_info['health'] = line.split(':')[-1].strip()

        return smart_info
    except Exception as e:
        logger.error(f"Exception in get_smartctl_data: {str(e)}")
        return {'temp': None, 'power_on_hours': None, 'power_cycle_count': None, 'health': None}

def main():
    try:
        logger.info("=" * 80)  # Separator line
        logger.info("Starting a new run of get-disks script")
        
        lsdev_disks = get_lsdev_disks()
        if lsdev_disks is not None:
            nvme_disks = get_lsblk_disks(nvme_only=True)
            all_disks = lsdev_disks + nvme_disks
        else:
            all_disks = get_lsblk_disks(nvme_only=False)

        logger.info(f"Total disks discovered: {len(all_disks)}")
        print(json.dumps(all_disks, indent=4))
    except Exception as e:
        logger.error(f"Exception in main: {str(e)}")

if __name__ == '__main__':
    main()