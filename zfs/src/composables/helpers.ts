import { Command, legacy, server, unwrap, ZPoolBase, ZpoolCreateOptions } from '@45drives/houston-common-lib';
import { ref, Ref } from 'vue';
// @ts-ignore
import test_ssh_script from"../scripts/test-ssh.py?raw";
import {VDevDisk, ZPool} from "@45drives/houston-common-lib";
import { Activity } from '../types';

const { errorString, useSpawn } = legacy;

//change true to 'on' and false to 'off'
export function isBoolOnOff(bool : boolean) {
	if (bool) {return 'on'} else {return 'off'}
}

export function isBoolCompression(bool : boolean) {
	if (bool) {return 'lz4'} else {return 'off'}
}

//change 'on' to true and 'off' to false
export function onOffToBool(state : string) {
    if (state == 'on') { return true } else if (state == 'off') { return false }
}

//change 'yes' to true and 'no' to false
export function yesNoToBool(state: string) {
	if (state == 'yes') { return true } else if (state == 'no') { return false }
}

//change the first letter of a word to upper case
export const upperCaseWord = (word => {
	let lowerCaseWord = word.toLowerCase();
	let firstLetter  = lowerCaseWord.charAt(0);
	let remainingLetters = lowerCaseWord.substring(1);
	let firstLetterCap = firstLetter.toUpperCase();
	return firstLetterCap + remainingLetters;
});

// Convert raw bytes to readable binary data size
export const convertBytesToSize = (bytes: number, precision: number = 2): string => {
	if (bytes === 0) {
		return `0 B`;
	}

	const binarySizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
	const base = 1024;

	const i = Math.min(Math.floor(Math.log(bytes) / Math.log(base)), binarySizes.length - 1);
	const convertedSize = (bytes / Math.pow(base, i)).toFixed(precision);

	return `${convertedSize} ${binarySizes[i]}`;
};


// Convert readable binary data size to raw bytes
export const convertSizeToBytes = (size: string): number => {
	const binarySizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
	const base = 1024;
	const decimalBase = 1000; // Base for decimal sizes
	// console.log('size:', size);

	const match = size.trim().match(/(\d+\.?\d*)\s*([a-zA-Z]+)/i);
	if (!match) {
		throw new Error(`Invalid size format: "${size}"`);
	}

	const [value, unit] = match.slice(1);
	const normalizedUnit = unit.toLowerCase();
	// console.log('normalizedUnit:', normalizedUnit);

	const decimalSizes = ['b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb'];

	// Check for binary unit
	const index = binarySizes.findIndex((sizeUnit) => sizeUnit.toLowerCase() === normalizedUnit);
	if (index !== -1) {
		// console.log('binary bytes:', (parseFloat(value) * Math.pow(base, index)));
		return parseFloat(value) * Math.pow(base, index);
	}

	// Check for decimal unit
	const decimalIndex = decimalSizes.findIndex((sizeUnit) => sizeUnit.toLowerCase() === normalizedUnit);
	if (decimalIndex !== -1) {
		// Convert decimal value to binary equivalent
		const decimalBytes = parseFloat(value) * Math.pow(decimalBase, decimalIndex);
		// Adjust to binary base
		const binaryBytes = decimalBytes * Math.pow(decimalBase / base, decimalIndex);
		// console.log('decimal converted binary bytes:', binaryBytes);
		return binaryBytes;
	}

	// If neither binary nor decimal unit is found
	throw new Error(`Unrecognized unit: "${unit}"`);
};



//get size number from data size string
export const getSizeNumberFromString = (sizeString) => {
	const [value, unit] = sizeString.split(' ');
	const numericValue = parseFloat(value);
	return numericValue;
}

//get size unit from data size string
export const getSizeUnitFromString = (sizeString) => {
	const [value, unit] = sizeString.split(' ');

	return unit;
}

export const getQuotaRefreservUnit = (bytes) => {
    const sizes = ['kib', 'mib', 'gib', 'tib'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    if (i === 0) {
        return `${bytes} Bytes`;
    }
    
    const convertedSize = (bytes / Math.pow(1024, i)).toFixed(2);
  
    return `${convertedSize} ${sizes[i-1]}`;
};

//get a string output of the current timestamp
export function getTimestampString() {
	const currentDateTime = new Date();
	const timestampString = currentDateTime.toLocaleString('en-US', {
		hour: 'numeric',
		minute: 'numeric',
		second: 'numeric',
		day: '2-digit',
		month: '2-digit',
		year: 'numeric'
	});

	//console.log("timestampString:", timestampString);
	
	return timestampString;
}

export function getSnapshotTimestamp() {
	const currentDateTime = new Date();
  
	const year = currentDateTime.getFullYear();
	const month = String(currentDateTime.getMonth() + 1).padStart(2, '0'); // Adding 1 because months are zero-based
	const day = String(currentDateTime.getDate()).padStart(2, '0');
	const hour = String(currentDateTime.getHours()).padStart(2, '0');
	const minute = String(currentDateTime.getMinutes()).padStart(2, '0');
	const second = String(currentDateTime.getSeconds()).padStart(2, '0');
  
	const timestamp = `${year}.${month}.${day}-${hour}.${minute}.${second}`;
  
	return timestamp;
}

export function getRawTimestampFromString(timestampString) {
	// Check if timestampString is undefined or null
	if (timestampString === undefined || timestampString === null) {
	  // Return an appropriate value, for example, you can return null or throw an error
	  return null; // or throw new Error('Timestamp string is undefined or null');
	}
  
	const rawTimestamp = new Date(timestampString).getTime() / 1000;
	return rawTimestamp;
}

export function convertRawTimestampToString(rawTimestamp) {
	const date = new Date(rawTimestamp * 1000);
    const timestamp = date.toISOString().replace(/T|Z/g, ' ').trim();
    return timestamp.substring(0, 19);
}

export function convertTimestampToLocal(timestamp) {
    // Check if the timestamp already has a space between date and time
    const hasSpace = timestamp.includes(' ');

    // If it has a space, use it directly; otherwise, convert to the desired format
    const utcTimestamp = hasSpace ? timestamp.replace(' ', 'T') + 'Z' : timestamp;

    const localTimestamp = new Date(utcTimestamp).toLocaleString('en-US', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });

    const rearrangedTimestamp = localTimestamp.replace(/\//g, '-').replace(',', '');

    const [date, time] = rearrangedTimestamp.split(' ');

    const [month, day, year] = date.split('-');
    const rearrangedDate = `${year}-${month}-${day}`;

    const finalTimestamp = `${rearrangedDate} ${time}`;

    return finalTimestamp;
}

export function convertTimestampFormat(timestamp) {
    const parsedTimestamp = new Date(timestamp);
    const year = parsedTimestamp.getFullYear();
    const month = (parsedTimestamp.getMonth() + 1).toString().padStart(2, '0');
    const day = parsedTimestamp.getDate().toString().padStart(2, '0');
    const hours = parsedTimestamp.getHours().toString().padStart(2, '0');
    const minutes = parsedTimestamp.getMinutes().toString().padStart(2, '0');
    const seconds = parsedTimestamp.getSeconds().toString().padStart(2, '0');

    const customFormat = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    return customFormat;
}

export const getPoolDiskType = (pool) => {
	let hasSSD = false;
	let hasHDD = false;
  
	pool.vdevs.forEach((vdev) => {
	  vdev.disks.forEach((disk) => {
		if (disk.type === "SSD") {
		  hasSSD = true;
		} else if (disk.type === "HDD") {
		  hasHDD = true;
		}
	  });
	});
  
	// Determine the disk configuration based on the flags.
	if (hasSSD && hasHDD) {
	  return "Hybrid";
	} else if (hasSSD) {
	  return "SSD";
	} else if (hasHDD) {
	  return "HDD";
	} else {
	  return "Unknown"; // No disks found
	}
};
  
export function getParentPath(datasetName) {
	const segments = datasetName.split('/');
	segments.pop();
	return segments.join('/');
}

export function convertSecondsToString(seconds) {
    let result = '';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        result += `${hours} hour${hours > 1 ? 's' : ''} `;
    }
    
    if (minutes > 0) {
        result += `${minutes} minute${minutes > 1 ? 's' : ''} `;
    }

    if (hours === 0 && minutes === 0) {
        result += `${seconds} second${seconds > 1 ? 's' : ''} `;
    }
    
    return result.trim();
}

export function addActivity(id: string, activities: Ref<Map<string, Ref<Activity>>>) {
	const activity = ref<Activity>({
		isActive: false,
		isPaused: false,
		isCanceled: false,
		isFinished: false,
	});
	activities.value.set(id, activity);
}

export function removeActivity(id: string, activities: Ref<Map<string, Ref<Activity>>>) {
	activities.value.delete(id);
}

export async function loadScanActivities(pools, scanActivities) {
	pools.value.forEach(pool => {
		addActivity(pool.name, scanActivities);
	});
	// console.log('scanActivities', scanActivities);
}

export async function loadTrimActivities(pools, trimActivities) {
	pools.value.forEach(pool => {
		addActivity(pool.name, trimActivities);
	});

	pools.value.forEach(pool => {
		pool.vdevs.forEach(vDev => {
			vDev.disks.forEach(disk => {
				addActivity(disk.name, trimActivities);
			});
		});		
	});
	
	// console.log('trimActivities', trimActivities);
}

export function getValue(type : string, value : string) {
	if (type == 'sector') {
		switch (value) {
			case "auto":
				return 'Auto Detect';
			case "9":
				return '512 B';
			case "12":
				return '4 KiB';
			case "13":
				return '8 KiB';
			case "14":
				return '16 KiB';
			case "15":
				return '32 KiB';
			case "16":
				return '64 KiB';
			default:
				return 'None';
		}
	} else if (type == 'record') {
		switch (value) {
			case "512b":
				return '512 B';
			case "4kib":
				return '4 KiB';
			case "8kib":
				return '8 KiB';
			case "16kib":
				return '16 KiB';
			case "32kib":
				return '32 KiB';
			case "64kib":
				return '64 KiB';
			case "128kib":
				return '128 KiB';
			case "256kib":
				return '256 KiB';
			case "512kib":
				return '512 KiB';
			case "1mib":
				return '1 MiB';
			default:
				return 'None';
		}
	} else if (type == 'dnode') {
		switch (value) {
			case "1k":
				return '1 KiB';
			case "2k":
				return '2 KiB';
			case "4k":
				return '4 KiB';
			case "8k":
				return '8 KiB';
			case "16k":
				return '16 KiB';
			case "auto":
				return 'Auto';
			case "legacy":
				return 'Legacy';
			default:
				return 'None';
		}
	} else if (type == 'compression') {
		switch (value) {
			case "on":
				return 'On';
			case "off":
				return 'Off';
			case "gzip":
				return 'GZIP';
			case "lz4":
				return 'LZ4';
			case "lzjb":
				return 'LZJB';
			case "zle":
				return 'ZLE';
			default:
				return 'None';
		}
	} else if (type == 'dedup') {
		switch (value) {
			case "on":
				return 'On';
			case "off":
				return 'Off';
			case "edonr,verify":
				return 'Edon-R + Verify';
			case "sha256":
				return 'SHA-256';
			case "sha256,verify":
				return 'SHA-256 + Verify';
			case "sha512":
				return 'SHA-512';
			case "sha512,verify":
				return 'SHA-512 + Verify';
			case "skein":
				return 'Skein';
			case "skein,verify":
				return 'Skein + Verify';
			case "verify":
				return 'Verify';
			default:
				return 'None';
		}
	}
}

export function checkInheritance(type: string, value : string, poolConfigOptions : ZpoolCreateOptions) {
	if (type == 'compression') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (${poolConfigOptions.compression!.toUpperCase()})`
		} else {
			return getValue('compression', value);
		}
	} else if (type == 'dedup') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (${upperCaseWord(poolConfigOptions.dedup!)})`
		} else {
			return getValue('dedup', value);
		}
	} else if (type == 'record') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (${getValue('record', poolConfigOptions.recordsize!.toString())})`
		} else {
			return getValue('record', value);
		}
	} else if (type == 'atime') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (On)`
		} else {
			return upperCaseWord(value);
		}
	} else if (type == 'case') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (Sensitive)`
		} else {
			return upperCaseWord(value);
		}
	} else if (type == 'dnode') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (Legacy)`
		} else {
			return getValue('dnode', value);
		}
	} else if (type == 'xattr') {
		if (value == 'inherited') {
			return `${upperCaseWord(value)} (System Attribute)`
		} else {
			return upperCaseWord(value);
		}
	}
}

export async function testSSH(sshTarget) {
    try {
        // console.log(`target: ${sshTarget}`);
        const state = useSpawn(['/usr/bin/env', 'python3', '-c', test_ssh_script, sshTarget], { superuser: 'try' });

        const output = await state.promise();
        // console.log('testSSH output:', output);

        if (output.stdout!.includes('True')) {
			return true;
		} else {
			return false;
		}
    } catch (error) {
        console.error(errorString(error));
        return false;
    }
}

//////////////// Formatting Status //////////////////
/////////////////////////////////////////////////////
export function formatStatus(status) {
	switch(status) {
		case 'ONLINE':
			return 'text-green-600';
		case 'DEGRADED':
			return 'text-orange-600';
		case 'FAULTED':
			return 'text-red-600';
		case 'SUSPENDED':
			return 'text-red-600';
		case 'OFFLINE':
			return 'text-red-600';
		case 'REMOVED':
			return 'text-red-600';
		case 'UNAVAIL':
			return 'text-red-600';
		case 'REPLACING':
			return 'text-orange-600';
		default:
			break;
	}
}

export function getCapacityColor(type: 'text' | 'bg', capacity: number, refreservationPercent?: number): string {
	// Calculate the available space as 100% minus the refreservation percent
	const availableSpace = refreservationPercent !== undefined ? 100 - refreservationPercent : 100;
	const capacityPercentOfAvailable = (capacity / availableSpace) * 100; // Calculate capacity as a percentage of available space

	// console.log('Available Space:', availableSpace, 'Capacity Percentage of Available:', capacityPercentOfAvailable);

	let colorString;
	if (capacityPercentOfAvailable <= 70) {
		colorString = `${type}-green-600`;
	} else if (capacityPercentOfAvailable > 70 && capacityPercentOfAvailable <= 85) {
		colorString = `${type}-orange-600`;
	} else if (capacityPercentOfAvailable > 85 && capacityPercentOfAvailable <= 100) {
		colorString = `${type}-red-600`;
	} else {
		colorString = `${type}-blue-600`; // Fallback color, if needed
	}

	return colorString;
}

export function getFullDiskInfo(disks: VDevDisk[], diskName: string): VDevDisk | undefined {
	if (!diskName) {
		console.warn("getFullDiskInfo called with an empty diskName.");
		return undefined;
	}

	const pathPrefixes: Record<string, string> = {
		phy_path: '/dev/disk/by-path/',
		sd_path: '/dev/',
		id_path: '/dev/disk/by-id/',
		label_path: '/dev/disk/by-label/',
		part_label_path: '/dev/disk/by-partlabel/',
		part_uuid: '/dev/disk/by-partuuid/',
		uuid: '/dev/disk/by-uuid/',
	};

	// console.log("Searching for disk with name:", diskName);

	// Find the disk by matching its name against possible paths
	const foundDisk = disks.find(disk => {
		if (disk.name?.trim() === diskName.trim() || disk.vdev_path?.trim() === diskName.trim()) {
			disk.path = disk.vdev_path?.trim() ?? disk.name?.trim() ?? ''; // Ensure it's always a string
			return true;
		}

		for (const [key, prefix] of Object.entries(pathPrefixes)) {
			const diskPath = (disk as any)[key]?.trim();
			if (diskPath && diskPath.replace(prefix, '') === diskName.trim()) {
				disk.path = diskPath; // Assign the actual matched path
				return true;
			}
		}

		return false;
	});

	if (foundDisk) {
		// console.log("Found disk:", foundDisk);
	}

	return foundDisk;
}



export function getDiskIDName(disks: VDevDisk[], diskIdentifier: string, selectedDiskName: string) {
	const phyPathPrefix = '/dev/disk/by-path/';
	const sdPathPrefix = '/dev/';
	const idPathPrefix = '/dev/disk/by-id/';
	const labelPathPrefix = '/dev/disk/by-label/';
	const partLabelPathPrefix = '/dev/disk/by-partlabel/';
	const partUUIDPrefix = '/dev/disk/by-partuuid/';
	const uuidPrefix = '/dev/disk/by-uuid/';

	const newDisk = ref();
	const diskName = ref('');
	const diskPath = ref('');

	// console.log('diskIdentifier:', diskIdentifier);
	// console.log('selectedDiskName:', selectedDiskName);

	// Find the selected disk
	// newDisk.value = disks.find(disk => disk.name!.trim() == selectedDiskName.trim());
	newDisk.value = disks.find(disk => {
		// console.log("Checking disk:", disk.name?.trim(), "against", selectedDiskName.trim());
		return disk.name?.trim() === selectedDiskName.trim();
	});

	switch (diskIdentifier) {
		case 'vdev_path':
			diskPath.value = newDisk.value!.vdev_path;
			diskName.value = selectedDiskName;
			break;
		case 'phy_path':
			diskPath.value = newDisk.value!.phy_path;
			diskName.value = diskPath.value.replace(phyPathPrefix, '');
			break;
		case 'sd_path':
			diskPath.value = newDisk.value!.sd_path;
			diskName.value = diskPath.value.replace(sdPathPrefix, '');
			break;
		case 'id_path':
			diskPath.value = newDisk.value!.id_path;
			diskName.value = diskPath.value.replace(idPathPrefix, '');
			break;
		case 'label_path':
			diskPath.value = newDisk.value!.label_path;
			diskName.value = diskPath.value.replace(labelPathPrefix, '');
			break;
		case 'part_label_path':
			diskPath.value = newDisk.value!.part_label_path;
			diskName.value = diskPath.value.replace(partLabelPathPrefix, '');
			break;
		case 'part_uuid':
			diskPath.value = newDisk.value!.part_uuid;
			diskName.value = diskPath.value.replace(partUUIDPrefix, '');
			break;
		case 'uuid':
			diskPath.value = newDisk.value!.uuid;
			diskName.value = diskPath.value.replace(uuidPrefix, '');
			break;
		default:
			console.log('Error with selectedDiskNames/diskIdentifier');
			break;
	}

	return diskName.value;
}


// export function findDiskByPathAndClean(disks, path) {
// 	// Regex to match partition suffixes like '-part1'
// 	const partitionSuffixRegex = /-part[0-9]+$/;

// 	// Only strip the partition if it's a partition (and not something like 'nvme0n1')
// 	const basePath = path.match(partitionSuffixRegex) ? path.replace(partitionSuffixRegex, '') : path;

// 	// console.log('Checking path:', path, 'Base path:', basePath);

// 	return disks.find((disk) => {
// 		// Clean paths for each disk property
// 		const sdPath = disk.sd_path ? cleanDiskPath(disk.sd_path) : null;
// 		const phyPath = disk.phy_path ? cleanDiskPath(disk.phy_path) : null;
// 		const vdevPath = disk.vdev_path ? cleanDiskPath(disk.vdev_path) : null;

// 		// Log paths being compared
// 		// console.log(`Comparing with disk paths: sd_path: ${sdPath}, phy_path: ${phyPath}, vdev_path: ${vdevPath}`);

// 		// Check if any cleaned path matches
// 		return [sdPath, phyPath, vdevPath]
// 			.some((diskPath) => diskPath === path || diskPath === basePath);
// 	});
// }

// Helper function to clean disk paths by removing partition numbers but leaving the rest intact
// function cleanDiskPath(path) {
// 	return path.replace(/-part[0-9]+$/, ''); // Only remove partition suffix like '-part1'
// }

// One canonical matcher. Works with reactive arrays (pass disks.value) or plain arrays.
export function matchDiskByVdevOrPath(disks: Array<any>, vdevPathOrAnyPath: string) {
	if (!vdevPathOrAnyPath) return undefined;

	// 1) Fast path: by-vdev → match by bay-id to disk.name
	const byVdev = vdevPathOrAnyPath.match(/\/dev\/disk\/by-vdev\/([0-9A-Za-z\-]+)(?:-part\d+)?$/);
	if (byVdev) {
		const bay = byVdev[1]; // e.g., "1-10"
		const hit = disks.find(d => d?.name === bay);
		if (hit) return hit;
	}

	// 2) Normalize both sides
	const clean = (p?: string) => {
		if (!p) return "";
		// Strip ANSI partitions styles:
		//  /dev/nvme0n1p2 → /dev/nvme0n1
		p = p.replace(/(\/nvme\d+n\d+)p\d+$/, "$1");
		//  /dev/mmcblk0p1 → /dev/mmcblk0
		p = p.replace(/(\/mmcblk\d+)p\d+$/, "$1");
		//  /dev/sda2 → /dev/sda
		p = p.replace(/(\/sd[a-z]+)\d+$/, "$1");
		//  by-vdev ...-partN → base
		p = p.replace(/-part\d+$/, "");
		return p;
	};

	const sameOrStartsWith = (a: string, b: string) =>
		a === b || (a && b && (b.startsWith(a) || a.startsWith(b)));

	const want = vdevPathOrAnyPath;
	const wantBase = clean(want);

	// 3) Try strict then relaxed matches across known fields
	const candidates = ["sd_path", "phy_path", "vdev_path", "id_path", "label_path", "part_label_path", "part_uuid", "uuid"];

	// strict match: exact or exact-after-clean
	let d = disks.find(dd => candidates.some(k => {
		const v = dd?.[k];
		return v === want || clean(v) === wantBase;
	}));
	if (d) return d;

	// relaxed: allow startsWith for cases like /dev/sda1 vs /dev/sda
	d = disks.find(dd => candidates.some(k => {
		const v = dd?.[k];
		return sameOrStartsWith(v ?? "", want) || sameOrStartsWith(clean(v ?? ""), wantBase);
	}));
	return d;
}



export function truncateName(name : string, threshold : number) {
    return (name.length > threshold ? name.slice(0, threshold) + '...' : name)
}


export async function isPoolUpgradable(poolName: string) {
	try {
		const state = useSpawn(['zpool', 'status', poolName], { superuser: 'try' });

		const output = await state.promise();
		// console.log('zpool status output:', output.stdout);

		// Split the output into lines
		const lines = output.stdout!.split('\n');

		// Define the patterns to match
		const statusPattern = /The pool is formatted using a legacy on-disk format/;
		const actionPattern = /Upgrade the pool using 'zpool upgrade'/;

		// Variables to track if patterns are found
		let statusFound = false;
		let actionFound = false;

		// Iterate through each line and check for patterns
		for (const line of lines) {
			if (statusPattern.test(line)) {
				statusFound = true;
			}
			if (actionPattern.test(line)) {
				actionFound = true;
			}

			// If both patterns are found, return true early
			if (statusFound && actionFound) {
				return true;
			}
		}

		// If the patterns aren't matched, the pool is not upgradable
		return false;	
	} catch (error) {
		console.error(errorString(error));
		return false;
	}
}

export function isCapacityPatternInvalid(capacityStr) {
	// Check if the capacity string matches a valid pattern like "32G", "9.01T", "500M", etc.
	return /^(\d+(\.\d+)?)(\s*[KMGTP]{1})$/i.test(capacityStr); // Ensure only single-letter units
}

export function formatCapacityString(capacityStr) {
	// Log the input capacity string
	// console.log("Formatting capacity: " + capacityStr);

	// Define a case-insensitive regex to match the pattern (e.g., "32G", "9.01T", "500M", etc.)
	const match = capacityStr.match(/^(\d+(\.\d+)?)(\s*[KMGTP])?$/i);
	if (!match) {
		throw new Error("Invalid capacity string format. Expected format like '32G', '500M', '9.01T', '1P'.");
	}

	// Extract the numeric value and unit
	const value = parseFloat(match[1]); // Numeric part
	const unit = match[3] ? match[3].trim().toUpperCase() : "G"; // Default to G if no unit is specified

	// // Standardize the unit to binary (KiB, MiB, GiB, TiB, PiB)
	// const binaryUnit = `${unit}iB`; // Append "iB" to the unit for binary consistency

	// Standardize the unit to decimal (KB, MB, GB, TB, PB)
	const decimalUnit = `${unit}B`;
	// console.log(`formatted capacity: ${value} ${decimalUnit}`)
	// Return the formatted string
	return `${value} ${decimalUnit}`;
}


export function changeUnitToBinary(capacity: any) {
	if (capacity == null) return capacity;

	// Only operate on strings
	if (typeof capacity !== 'string') return capacity;

	const s = capacity.trim();

	// Leave percents or plain numbers alone (e.g., "73%", "0", "12.5")
	if (/^\d+(\.\d+)?\s*%$/.test(s) || /^\d+(\.\d+)?$/.test(s)) return capacity;

	// Already binary (KiB/MiB/GiB/TiB/PiB) → return as-is (normalize single space)
	if (/^\d+(\.\d+)?\s*[KMGTPE]iB$/i.test(s)) return s.replace(/\s+/, ' ');

	// Decimal KB/MB/GB/TB/PB → add "i"
	const m = s.match(/^(\d+(?:\.\d+)?)\s*([KMGTPE])B$/i);
	if (m) return `${m[1]} ${m[2]}iB`;

	// Non-matching strings like "Unknown", "-", "bytes", etc. → leave unchanged
	return capacity;
}

export type ExecOut = { stdout: string; stderr: string };

export async function exec(cmd: string[]): Promise<ExecOut> {
	const res = await unwrap(server.execute(new Command(cmd, {superuser: 'try'})));
	return {
		stdout: res.getStdout().trim(),
		stderr: res.getStderr().trim(),
	};
}