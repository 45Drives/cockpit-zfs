import { ref, Ref } from 'vue';
import { getPools, getImportablePools } from "./pools";
import { getDisks } from "./disks";
import { getDatasets } from "./datasets";
import { matchDiskByVdevOrPath, convertBytesToSize, isBoolOnOff, onOffToBool, getQuotaRefreservUnit, getSizeUnitFromString, getParentPath, convertTimestampToLocal, formatCapacityString, isCapacityPatternInvalid, changeUnitToBinary } from "./helpers";
import { getSnapshots, getSnapshotsOfDataset, getSnapshotsOfPool } from './snapshots';
import { getDiskStats, getScanGroup } from './scan';
import { VDevDisk, ZFSFileSystemInfo, VDev } from "@45drives/houston-common-lib"
import { PoolDiskStats, PoolScanObjectGroup, Snapshot } from '../types';
import { safeParse, unpackArray } from '../utils/json';

const vDevs = ref<VDev[]>([]);
const errors: string[] = [];

export async function loadDiskStats(poolDiskStats: Ref<PoolDiskStats>) {
	try {
		const rawJSON = await getDiskStats();
		const parsedJSON = safeParse(rawJSON, {});
		// console.log('***Disk Stats JSON:', parsedJSON);

		poolDiskStats.value = parsedJSON;
		// console.log("***\nPoolDiskStatsObject:", poolDiskStats.value);
	} catch (error) {
		console.error("An error occurred getting disk stats:", error);
	}
}

export async function loadScanObjectGroup(scanObject: Ref<PoolScanObjectGroup>) {
	try {
		const rawJSON = await getScanGroup();
		const parsedJSON = safeParse(rawJSON, {});
		// console.log('---Scan Object JSON:', parsedJSON);

		scanObject.value = parsedJSON;
		// console.log('---\nScanObject:', scanObject.value);
	} catch (error) {
		console.error("An error occurred getting scan object group:", error);
	}
}

export async function loadDisksThenPools(disks, pools) {
	//executes a python script to retrieve all disk data and outputs a JSON
	try {
		const rawJSON = await getDisks();
		// console.log('Raw JSON:', rawJSON);
		const { data: parsedJSON, error: disksErr } = unpackArray<any>(rawJSON, [])
		if (disksErr) console.warn('getDisks error:', disksErr);
		console.log('Disks JSON:', parsedJSON);
		
		//loops through and adds disk data from JSON to disk data object, pushes objects to disks array
		for (let i = 0; i < parsedJSON.length; i++) {
			const rawCap = isCapacityPatternInvalid(parsedJSON[i].capacity)
				? formatCapacityString(parsedJSON[i].capacity)
				: parsedJSON[i].capacity;
			
			const disk = {
				name: parsedJSON[i].name,
				capacity: changeUnitToBinary(rawCap),
				model: parsedJSON[i].model,
				type: parsedJSON[i].type === 'Disk' ? 'Disk' : parsedJSON[i].type,
				phy_path: parsedJSON[i].phy_path || 'N/A',
				sd_path: parsedJSON[i].sd_path || 'N/A',
				vdev_path: parsedJSON[i].type === 'NVMe' ? parsedJSON[i].sd_path : parsedJSON[i].vdev_path, // Fix for NVMe drives
				serial: parsedJSON[i].serial || 'N/A',
				usable: parsedJSON[i].usable || false,
				path: parsedJSON[i].type === 'NVMe' ? parsedJSON[i].sd_path : parsedJSON[i].vdev_path, // Ensure a valid path
				guid: '',
				status: parsedJSON[i].health || 'Unknown',
				powerOnHours: parsedJSON[i].power_on_time || 0,
				powerOnCount: parsedJSON[i].power_on_count || 0,
				temp: parsedJSON[i].temp || 'N/A',
				rotationRate: parsedJSON[i].rotation_rate || 0,
				stats: {},
				errors: errors,
				hasPartitions: parsedJSON[i].has_partitions || false,
			};


			disks.value.push(disk);
			// console.log("Disk:");
			// console.log(disk);
		}
		// console.log("pre-loaded Disks:", disks);

		//executes a python script to retrieve all pool data and outputs a JSON
		try {
			const rawJSON = await getPools();
			const { data: parsedJSON, error: poolsErr } = unpackArray<any>(rawJSON, []);
			if (poolsErr) console.warn('getPools error:', poolsErr);
			//loops through pool JSON
			for (let i = 0; i < parsedJSON.length; i++) {
				//calls parse function for each type of VDev that could be in the Pool, then pushes the VDev data to VDev array
				parsedJSON[i].groups.data.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'data'));
				parsedJSON[i].groups.cache.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'cache'));
				parsedJSON[i].groups.dedup.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'dedup'));
				parsedJSON[i].groups.log.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'log'));
				parsedJSON[i].groups.spare.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'spare'));
				parsedJSON[i].groups.special.forEach(vDev => parseVDevData(vDev, parsedJSON[i].name, disks, 'special'));

				//adds pool data from JSON into pool data object, pushes into array 
				if (parsedJSON[i].root_dataset != null) {
					const rawCap = isCapacityPatternInvalid(parsedJSON[i].properties.capacity.rawvalue)
						? formatCapacityString(parsedJSON[i].properties.capacity.rawvalue)
						: parsedJSON[i].properties.capacity.rawvalue;
					const poolData = {
						name: parsedJSON[i].name,
						status: parsedJSON[i].status_code == 'OK' ? parsedJSON[i].status : parsedJSON[i].properties.health.parsed,
						guid: parsedJSON[i].guid,
						properties: {
							rawsize: parsedJSON[i].properties.size.parsed,
							size: changeUnitToBinary(convertBytesToSize(parsedJSON[i].properties.size.parsed)),
							allocated: convertBytesToSize(parsedJSON[i].properties.allocated.parsed),
							capacity: parsedJSON[i].properties.capacity.rawvalue,
							free: changeUnitToBinary(convertBytesToSize(parsedJSON[i].properties.free.parsed)),
							readOnly: parsedJSON[i].properties.readonly.parsed,
							sector: parsedJSON[i].properties.ashift.rawvalue,
							record: parsedJSON[i].root_dataset.properties.recordsize.value,
							compression: parsedJSON[i].root_dataset.properties.compression.parsed,
							deduplication: onOffToBool(parsedJSON[i].root_dataset.properties.dedup.parsed),
							refreservationRawSize: parsedJSON[i].root_dataset.properties.refreservation.parsed,
							// refreservationPercent: parsedJSON[i].root_dataset ? Number(((parsedJSON[i].root_dataset.properties.refreservation.parsed / parsedJSON[i].root_dataset.properties.used.parsed) * 100).toFixed(2)) : 0,
							refreservationPercent: parsedJSON[i].root_dataset ? Number(((parsedJSON[i].root_dataset.properties.refreservation.parsed / parsedJSON[i].properties.size.parsed) * 100).toFixed(2)) : 0,
							autoExpand: parsedJSON[i].properties.autoexpand.parsed,
							autoReplace: parsedJSON[i].properties.autoreplace.parsed,
							autoTrim: onOffToBool(parsedJSON[i].properties.autotrim.parsed),
							delegation: parsedJSON[i].properties.delegation.parsed,
							listSnapshots: parsedJSON[i].properties.listsnapshots.parsed,
							// multiHost: isBoolOnOff(parsedJSON[i].properties.multihost),
							health: parsedJSON[i].properties.health.parsed,
							altroot: parsedJSON[i].properties.altroot.value,
							available: changeUnitToBinary(convertBytesToSize(parsedJSON[i]?.root_dataset?.properties?.available.parsed)),

						},
						failMode: parsedJSON[i].properties.failmode.parsed,
						comment: parsedJSON[i].properties.comment.value !== '-' ? parsedJSON[i].properties.comment.value : '',
						scan: {
							name: parsedJSON[i].name,
							function: parsedJSON[i].scan.function,
							start_time: parsedJSON[i].scan.start_time,
							end_time: parsedJSON[i].scan.end_time,
							pause: parsedJSON[i].scan.pause,
							state: parsedJSON[i].scan.state,
							errors: parsedJSON[i].scan.errors,
							percentage: parsedJSON[i].scan.percentage,
							total_secs_left: parsedJSON[i].scan.total_secs_left,
							bytes_issued: parsedJSON[i].scan.bytes_issued,
							bytes_processed: parsedJSON[i].scan.bytes_processed,
							bytes_to_process: parsedJSON[i].scan.bytes_to_process,
						},
						errors: errors,
						statusCode: parsedJSON[i].status_code,
						statusDetail: parsedJSON[i].status_detail,
						errorCount: parsedJSON[i].error_count,

						//adds VDev array to Pool data object
						vdevs: vDevs.value,

						// fileSystems: parsedJSON[i].root_dataset.value,
					}
					pools.value.push(poolData);

					console.log("poolData after JSON load (with root):", poolData);
					vDevs.value = [];
				} else {
					const rawCap = isCapacityPatternInvalid(Number(parsedJSON[i].properties.capacity.rawvalue))
						? formatCapacityString(Number(parsedJSON[i].properties.capacity.rawvalue))
						: Number(parsedJSON[i].properties.capacity.rawvalue);
					const poolData = {
						name: parsedJSON[i].name,
						status: parsedJSON[i].status_code == 'OK' ? parsedJSON[i].status : parsedJSON[i].properties.health.parsed,
						guid: parsedJSON[i].guid,
						properties: {
							rawsize: parsedJSON[i].properties.size.parsed,
							size: convertBytesToSize(parsedJSON[i].properties.size.parsed),
							allocated: convertBytesToSize(parsedJSON[i].properties.allocated.parsed),
							capacity: Number(parsedJSON[i].properties.capacity.rawvalue),
							free: convertBytesToSize(parsedJSON[i].properties.free.parsed),
							readOnly: parsedJSON[i].properties.readonly.parsed,
							sector: parsedJSON[i].properties.ashift.rawvalue,
							record: '',
							compression: false,
							deduplication: false,
							refreservationRawSize: 0,
							refreservationPercent: parsedJSON[i].root_dataset ? Number(((parsedJSON[i].root_dataset.properties.refreservation.parsed / parsedJSON[i].properties.size.parsed) * 100).toFixed(2)) : 0,
							autoExpand: parsedJSON[i].properties.autoexpand.parsed,
							autoReplace: parsedJSON[i].properties.autoreplace.parsed,
							autoTrim: onOffToBool(parsedJSON[i].properties.autotrim.parsed),
							delegation: parsedJSON[i].properties.delegation.parsed,
							listSnapshots: parsedJSON[i].properties.listsnapshots.parsed,
							health: parsedJSON[i].properties.health.parsed,
							altroot: parsedJSON[i].properties.altroot.value,
							available: convertBytesToSize(parsedJSON[i]?.root_dataset?.properties?.available.parsed),
						},
						failMode: parsedJSON[i].properties.failmode.parsed,
						comment: parsedJSON[i].properties.comment.value !== '-' ? parsedJSON[i].properties.comment.value : '',
						scan: {
							name: parsedJSON[i].name,
							function: parsedJSON[i].scan.function,
							start_time: parsedJSON[i].scan.start_time,
							end_time: parsedJSON[i].scan.end_time,
							pause: parsedJSON[i].scan.pause,
							state: parsedJSON[i].scan.state,
							errors: parsedJSON[i].scan.errors,
							percentage: parsedJSON[i].scan.percentage,
							total_secs_left: parsedJSON[i].scan.total_secs_left,
							bytes_issued: parsedJSON[i].scan.bytes_issued,
							bytes_processed: parsedJSON[i].scan.bytes_processed,
							bytes_to_process: parsedJSON[i].scan.bytes_to_process,
						},
						errors: errors,
						statusCode: parsedJSON[i].status_code,
						statusDetail: parsedJSON[i].status_detail,
						errorCount: parsedJSON[i].error_count,

						//adds VDev array to Pool data object
						vdevs: vDevs.value,

						// fileSystems: parsedJSON[i].root_dataset.value,
					}
					pools.value.push(poolData);

					console.log("poolData after JSON load (no root):", poolData);
					vDevs.value = [];
				}
			}

			const poolDiskTypes = pools.value.map(pool => {
				// console.log('mapping pool disk types for pool:', pool.name);
				const vDevDiskTypes = pool.vdevs.map(vDev => {
					// console.log('mapping pool disk types for vdev:', vDev.name);
					// Map over the disks within each VDev and extract their types
					const diskTypes = vDev.disks.map(disk => disk.type);

					// Check if all disk types within this VDev are the same
					// does not currently account for 'replacing' type
					const allSameDiskType = diskTypes.every(type => type === diskTypes[0]);

					// Return the disk type for this VDev
					return allSameDiskType ? diskTypes[0] : 'Hybrid';
				});

				// Check if all VDev disk types within the pool are the same
				const allSameDiskType = vDevDiskTypes.every(type => type === vDevDiskTypes[0]);

				// Determine the pool's diskType based on VDev diskTypes
				return allSameDiskType ? vDevDiskTypes[0] : 'Hybrid';
			});

			pools.value.forEach((pool, index) => {
				pool.diskType = poolDiskTypes[index];
				// console.log(`pool: ${pool.name} type: ${poolDiskTypes[index]}`);
			});

			console.log("loaded Pools:", pools);

			await loadDisksExtraData(disks.value, pools.value);

			console.log("loaded Disks:", disks);


		} catch (error) {
			// Handle any errors that may occur during the asynchronous operation
			console.error("An error occurred getting pools:", error);
		}
	} catch (error) {
		// Handle any errors that may occur during the asynchronous operation
		console.error("An error occurred getting disks/pools:", error);
	}
}

export async function loadDatasets(datasets) {
	//executes a python script to retrieve all dataset data and outputs a JSON
	try {
		const rawJSON = await getDatasets();
		const { data: parsedJSON, error } = unpackArray<any>(rawJSON, []);
		if (error) console.warn('getDatasets error:', error);
		// console.log('Datasets JSON:', parsedJSON);

		//loops through JSON data and adds data to a Dataset object
		for (let i = 0; i < parsedJSON.length; i++) {
			const dataset: ZFSFileSystemInfo = {
				name: parsedJSON[i].name,
				id: parsedJSON[i].id,
				mountpoint: parsedJSON[i].properties.mountpoint.value,
				pool: parsedJSON[i].pool,
				encrypted: parsedJSON[i].encrypted,
				key_loaded: parsedJSON[i].key_loaded,
				type: parsedJSON[i].type,
				inherit: false,
				properties: {
					guid: parsedJSON[i].properties.guid.parsed,
					encryption: parsedJSON[i].properties.encryption.parsed,
					accessTime: parsedJSON[i].properties.atime.value,
					caseSensitivity: parsedJSON[i].properties.casesensitivity.value,
					compression: parsedJSON[i].properties.compression.value,
					deduplication: parsedJSON[i].properties.dedup.value,
					dNodeSize: parsedJSON[i].properties.dnodesize.value,
					extendedAttributes: parsedJSON[i].properties.xattr.value,
					recordSize: parsedJSON[i].properties.recordsize.value,
					quota: {
						value: parsedJSON[i].properties.quota.value,
						raw: parsedJSON[i].properties.quota.parsed,
						unit: getSizeUnitFromString(getQuotaRefreservUnit(parsedJSON[i].properties.quota.parsed)),
					},
					readOnly: parsedJSON[i].properties.readonly.value,
					isReadOnly: onOffToBool(parsedJSON[i].properties.readonly.value),
					available: parsedJSON[i].properties.available.parsed,
					creation: parsedJSON[i].properties.creation.value,
					snapshotCount: parsedJSON[i].properties.snapshot_count.value,
					mounted: parsedJSON[i].properties.mounted.value,
					usedbyRefreservation: convertBytesToSize(parsedJSON[i].properties.usedbyrefreservation.parsed),
					usedByDataset: convertBytesToSize(parsedJSON[i].properties.usedbydataset.parsed),
					canMount: parsedJSON[i].properties.canmount.value,
					aclInheritance: parsedJSON[i].properties.aclinherit.value,
					aclType: parsedJSON[i].properties.acltype.value,
					checksum: parsedJSON[i].properties.checksum.value,
					refreservation: {
						raw: parsedJSON[i].properties.refreservation.parsed,
						value: parsedJSON[i].properties.refreservation.value,
						unit: getSizeUnitFromString(getQuotaRefreservUnit(parsedJSON[i].properties.refreservation.parsed)),
					},
					used: parsedJSON[i].properties.used.parsed,
					usedBySnapshots: convertBytesToSize(parsedJSON[i].properties.usedbysnapshots.parsed)
				},
				children: parsedJSON[i].children,
				parentFS: getParentPath(parsedJSON[i].name),
			}

			datasets.value.push(dataset);
		}

		console.log("loaded Datasets:", datasets);


	} catch (error) {
		// Handle any errors that may occur during the asynchronous operation
		console.error("An error occurred getting datasets:", error);
	}
}

export async function loadDisks(disks) {
	try {
		const rawJSON = await getDisks();
		const { data: parsedJSON, error } = unpackArray<any>(rawJSON, []);
		if (error) console.warn('getDisks error:', error);
		// console.log('Disks JSON:', parsedJSON);

		//loops through and adds disk data from JSON to disk data object, pushes objects to disks array
		for (let i = 0; i < parsedJSON.length; i++) {
			const rawCap = isCapacityPatternInvalid(parsedJSON[i].capacity)
				? formatCapacityString(parsedJSON[i].capacity)
				: parsedJSON[i].capacity;
			const disk = {
				name: parsedJSON[i].name,
				capacity: changeUnitToBinary(rawCap),
				model: parsedJSON[i].model,
				type: parsedJSON[i].type === 'Disk' ? 'Disk' : parsedJSON[i].type,
				phy_path: parsedJSON[i].phy_path || 'N/A',
				sd_path: parsedJSON[i].sd_path || 'N/A',
				vdev_path: parsedJSON[i].type === 'NVMe' ? parsedJSON[i].sd_path : parsedJSON[i].vdev_path, // Fix for NVMe drives
				serial: parsedJSON[i].serial || 'N/A',
				usable: parsedJSON[i].usable || false,
				path: parsedJSON[i].type === 'NVMe' ? parsedJSON[i].sd_path : parsedJSON[i].vdev_path, // Ensure a valid path
				guid: '',
				status: parsedJSON[i].health || 'Unknown',
				powerOnHours: parsedJSON[i].power_on_time || 0,
				powerOnCount: parsedJSON[i].power_on_count || 0,
				temp: parsedJSON[i].temp || 'N/A',
				rotationRate: parsedJSON[i].rotation_rate || 0,
				stats: {},
				errors: errors,
				hasPartitions: parsedJSON[i].has_partitions || false,
			};

			disks.value.push(disk);
			// console.log("Disk:", disk);
		}
		// console.log("loaded Disks:", disks);

	} catch (error) {
		// Handle any errors that may occur during the asynchronous operation
		console.error("An error occurred getting disks:", error);
	}
}

// Helper function to clean disk paths by removing partition numbers but leaving the rest intact
function cleanDiskPath(path) {
	if (!path) return '';

	// Remove partition numbers from standard disks (e.g., /dev/sda1 → /dev/sda)
	if (/\/dev\/sd[a-z][0-9]+$/.test(path)) {
		return path.replace(/[0-9]+$/, '');
	}

	// Remove 'pN' from NVMe paths (e.g., /dev/nvme0n1p2 → /dev/nvme0n1)
	if (/\/dev\/nvme\d+n\d+p\d+$/.test(path)) {
		return path.replace(/p\d+$/, '');
	}

	// Remove '-partN' suffix (e.g., /dev/disk/by-vdev/1-1-part1 → /dev/disk/by-vdev/1-1)
	if (/-part\d+$/.test(path)) {
		return path.replace(/-part\d+$/, '');
	}

	return path; // Return unchanged if no modifications needed
}

export async function loadDisksExtraData(disks, pools) {
	try {
		pools.forEach((pool) => {
			pool.vdevs.forEach((vDev) => {
				vDev.disks.forEach((usedDisk) => {
					// console.log('disk from vdev:', usedDisk);
					const cleanedUsedDiskPath = cleanDiskPath(usedDisk.path);
					const selectedDisk = matchDiskByVdevOrPath(disks, cleanedUsedDiskPath);
					let statsObject;

					if (selectedDisk && selectedDisk.type == 'NVMe' || selectedDisk && selectedDisk.type == 'Disk' || !usedDisk.stats) {
						statsObject = vDev.stats
					} else {
						statsObject = usedDisk.stats
					}

					// Check if the selectedDisk is found
					if (selectedDisk) {
						selectedDisk.guid = usedDisk.guid;
						selectedDisk.path = usedDisk.path;
						selectedDisk.stats = statsObject;
						// console.log('selectedDisk loading data', selectedDisk);

						// Clean the usedDisk.path and compare it with sd_path, phy_path, and vdev_path
						// Find the index of the original disk in the disks array
						const index = disks.findIndex(disk =>
							[cleanDiskPath(disk.sd_path), cleanDiskPath(disk.phy_path), cleanDiskPath(disk.vdev_path)].includes(cleanedUsedDiskPath)
						);

						// Check if the original disk is found in the disks array
						if (index !== -1) {
							// Replace the original disk with the updated selectedDisk
							// disks[index] = { ...selectedDisk }; // Use spread operator to create a new object
							// console.log('Updated disks array:', disks);

							const orig = disks[index];
							disks[index] = {
								...orig,
								guid: usedDisk.guid ?? orig.guid,
								path: usedDisk.path ?? orig.path,
								stats: statsObject ?? orig.stats,
							};
						} else {
							console.error('Original disk not found in the disks array');
						}
					} else {
						console.log('Selected disk not found', usedDisk);
					}
				});
			});
		});

	} catch (error) {
		// Handle any errors that may occur during the asynchronous operation
		console.error("An error occurred getting extra disk data:", error);
	}
}


export function parseVDevData(vDev, poolName, disks, vDevType) {
	const vDevData: VDev = {
		name: vDev.name,
		type: vDevType,
		status: vDev.status,
		stats: vDev.stats,
		guid: vDev.guid,
		selectedDisks: [],
		disks: [],
		poolName: poolName,
		path: vDev.path,
		diskType: determineDiskType(vDev, disks),
		errors: [],
	};

	// console.log("parsedVdevdata: ",vDev, poolName, disks, vDevType )

	if (vDevData.type === 'disk') {
		vDevData.path = 'N/A';  // Default path for VM Disk
	}

	// Regex for various disk path types
	const phyPathRegex = `\/dev\/disk\/by-path\/[0-9a-zA-Z:.\-]+(?:-part[0-9]+)?$`;
	const sdPathRegex = `\/dev\/sd[a-z0-9]+[0-9]*$`;
	const nvmePathRegex = `\/dev\/nvme[0-9]+n[0-9]+(?:p[0-9]+)?$`; // Added regex for NVMe paths
	const vDevPathRegex = `\/dev\/disk\/by-vdev\/[0-9a-zA-Z\-]+(?:-part[0-9]+)?$`;
	const idPathRegex = `\/dev\/disk\/by-id\/[0-9a-zA-Z:\-]+(?:-part[0-9]+)?$`;
	const labelPathRegex = `\/dev\/disk\/by-label\/[0-9a-zA-Z\-]+(?:-part[0-9]+)?$`;
	const partLabelPathRegex = `\/dev\/disk\/by-partlabel\/[0-9a-zA-Z\-]+(?:-part[0-9]+)?$`;
	const partUUIDRegex = `\/dev\/disk\/by-partuuid\/[0-9a-zA-Z\-]+$`;
	const uuidRegex = `\/dev\/disk\/by-uuid\/[0-9a-zA-Z\-]+$`;

	// Prefixes for constructing paths
	const phyPathPrefix = '/dev/disk/by-path/';
	const sdPathPrefix = '/dev/';
	const idPathPrefix = '/dev/disk/by-id/';
	const labelPathPrefix = '/dev/disk/by-label/';
	const partLabelPathPrefix = '/dev/disk/by-partlabel/';
	const partUUIDPrefix = '/dev/disk/by-partuuid/';
	const uuidPrefix = '/dev/disk/by-uuid/';

	// Check if VDev has child disks and if not, stores the disk information as the VDev itself (vdev-level disks) then adds to VDev array
	if (vDev.children.length < 1) {
		const diskVDev = ref();
		const diskName = ref('');
		const diskPath = ref('');

		// diskVDev.value = findDiskByPath(vDevData, disks);
		diskVDev.value = matchDiskByVdevOrPath(disks, vDevData.path!);

		if (!diskVDev.value) {
			console.error(`Disk not found for path: ${vDevData.path}.`);
			diskVDev.value = createMissingDisk(vDev.path, vDev.name, vDevType, poolName);
		}

		if (vDevData.path!.match(phyPathRegex)) {
			diskPath.value = diskVDev.value.phy_path;
			diskName.value = diskVDev.value.phy_path.replace(phyPathPrefix, '');
			// } else if (vDevData.path!.match(nvmePathRegex)) { // Check for NVMe path match
			// 	diskPath.value = diskVDev.value.sd_path; // NVMe paths will use sd_path
			// 	diskName.value = diskVDev.value.sd_path.replace(sdPathPrefix, '');
		} else if (vDevData.path!.match(nvmePathRegex)) { // Check for NVMe path match
			diskPath.value = diskVDev.value.sd_path || diskVDev.value.phy_path || diskVDev.value.vdev_path;
			diskName.value = diskVDev.value.sd_path ? diskVDev.value.sd_path.replace(sdPathPrefix, '') : diskVDev.value.name;
		} else if (vDevData.path!.match(sdPathRegex)) {
			diskPath.value = diskVDev.value.sd_path;
			diskName.value = diskVDev.value.sd_path.replace(sdPathPrefix, '');
		} else if (vDevData.path!.match(vDevPathRegex)) {
			diskPath.value = diskVDev.value.vdev_path;
			diskName.value = diskVDev.value.name;
		} else if (vDevData.path!.match(idPathRegex)) {
			diskPath.value = diskVDev.value.id_path;
			diskName.value = diskVDev.value.id_path.replace(idPathPrefix, '');
		} else if (vDevData.path!.match(labelPathRegex)) {
			diskPath.value = diskVDev.value.label_path;
			diskName.value = diskVDev.value.label_path.replace(labelPathPrefix, '');
		} else if (vDevData.path!.match(partLabelPathRegex)) {
			diskPath.value = diskVDev.value.part_label_path;
			diskName.value = diskVDev.value.part_label_path.replace(partLabelPathPrefix, '');
		} else if (vDevData.path!.match(partUUIDRegex)) {
			diskPath.value = diskVDev.value.part_uuid;
			diskName.value = diskVDev.value.name;
		} else if (vDevData.path!.match(uuidRegex)) {
			diskPath.value = diskVDev.value.uuid;
			diskName.value = diskVDev.value.name;
		}

		const notAChildDisk: VDevDisk = {
			name: diskName!.value,
			path: diskPath.value,
			guid: vDev.guid,
			type: diskVDev.value!.type,
			health: diskVDev.value!.status,
			stats: diskVDev.value!.stats,
			capacity: changeUnitToBinary(
				isCapacityPatternInvalid(diskVDev.value!.capacity)
					? formatCapacityString(diskVDev.value!.capacity)
					: diskVDev.value!.capacity
			),
			model: diskVDev.value!.model,
			phy_path: diskVDev.value!.phy_path,
			sd_path: diskVDev.value!.sd_path,
			// vdev_path: diskVDev.value!.vdev_path,
			vdev_path: diskVDev.value!.vdev_path !== "N/A" ? diskVDev.value!.vdev_path : diskVDev.value!.sd_path,
			serial: diskVDev.value!.serial,
			powerOnHours: diskVDev.value!.powerOnHours,
			powerOnCount: diskVDev.value!.powerOnCount,
			temp: diskVDev.value!.temp,
			rotationRate: diskVDev.value!.rotationRate,
			vDevName: vDev.name,
			poolName: poolName,
			vDevType: vDevType,
			errors: errors
		};

		if (!vDevData.disks.some(disk => disk.guid === notAChildDisk.guid)) {
			vDevData.disks.push(notAChildDisk);
		}

	} else {

		if (vDev.name.startsWith("replacing-")) {
			const result = handleDiskChild(vDev.children[1], vDevData, disks, vDev.name, poolName, vDevType) as VDevDisk & { replacingTargetLabel?: string };
			if (result) {
				const fullOldDisk = disks.value.find(d => d.name === vDev.children[0].name);
				const shortSdPath = fullOldDisk?.sd_path?.replace(sdPathPrefix, "") ?? "";
				result.replacingTargetLabel = `${vDev.children[0].name} (${shortSdPath})`;

				if (!vDevData.disks.some(d => d.guid === result.guid || d.path === result.path || d.name === result.name)) {
					vDevData.disks.push(result);
				}
			}
		} else {
			vDev.children.forEach(child => {
				if (child.type === "disk") {
					const result = handleDiskChild(child, vDevData, disks, vDev.name, poolName, vDevType) as VDevDisk & { replacingTargetLabel?: string };
					if (result && !vDevData.disks.some(d => d.guid === result.guid || d.path === result.path || d.name === result.name)) {
						vDevData.disks.push(result);
					}
				} else if (child.type === "replacing" && child.children?.length >= 2) {
					const [oldDisk, newDisk] = child.children;
					const result = handleDiskChild(newDisk, vDevData, disks, child.name, poolName, child.type) as VDevDisk & { replacingTargetLabel?: string };
					if (result) {
						const fullOldDisk = disks.value.find(d => d.name === oldDisk.name);
						const shortSdPath = fullOldDisk?.sd_path?.replace(sdPathPrefix, "") ?? "";
						result.replacingTargetLabel = `${oldDisk.name} (${cleanDiskPath(shortSdPath)})`;

						if (!vDevData.disks.some(d => d.guid === result.guid || d.path === result.path || d.name === result.name)) {
							vDevData.disks.push(result);
						}
					}
				}
			});
		}

	}
	vDevs.value.push(vDevData);
	// console.log("Updated vDevs Array:", vDevs.value);
}

function handleDiskChild(child, vDevData, disks, vDevName, poolName, vDevType) {
	if (!child || child.path === null) {
		return null;
	}

	const cleanedChildPath = cleanDiskPath(child.path);

	// exact match on base device paths only
	let fullDiskData = disks.value.find(disk => {
		const sdBase = cleanDiskPath(disk.sd_path);
		const phyBase = cleanDiskPath(disk.phy_path);
		const vdevBase = cleanDiskPath(disk.vdev_path);
		const pathBase = cleanDiskPath(disk.path);

		return (
			sdBase === cleanedChildPath ||
			phyBase === cleanedChildPath ||
			vdevBase === cleanedChildPath ||
			pathBase === cleanedChildPath
		);
	});

	// If no matching disk was found, create a missing disk ONLY if the original disk is truly missing
	if (!fullDiskData && (child.path === null || child.path === "")) {
		console.warn(`Disk not found for path: ${child.path}. Creating placeholder.`);
		fullDiskData = createMissingDisk(child.path, vDevName, vDevType, poolName);
		// Ensure the missing disk is added only once
		if (!vDevData.disks.some(disk => disk.path === fullDiskData!.path)) {
			vDevData.disks.push(fullDiskData);
		}
	}
	// If fullDiskData is still null (but child has a valid path), try to recover it
	if (!fullDiskData) {
		// 1) If the child path is a by-vdev partition, match its base by-vdev
		const vdevBase = cleanedChildPath.replace(/-part\d+$/, '');
		fullDiskData = disks.value.find(d =>
			cleanDiskPath(d.vdev_path) === vdevBase ||
			cleanDiskPath(d.sd_path) === vdevBase ||
			cleanDiskPath(d.phy_path) === vdevBase
		);

		if (fullDiskData) {
			console.warn(`Recovered disk via safety net using ${vdevBase}`);
		} else {
			// 2) Still nothing → create a real placeholder
			console.warn(`Disk marked as REMOVED but not found in disks array: ${child.path}`);
			fullDiskData = {
				name: child.name || "Unknown",
				path: child.path,
				guid: child.guid || "N/A",
				type: "N/A",
				health: "REMOVED",
				stats: child.stats || {},
				capacity: "Unknown",
				model: "N/A",
				phy_path: child.path || "N/A",
				sd_path: "N/A",
				vdev_path: "",
				serial: "N/A",
				powerOnHours: 0,
				powerOnCount: "0",
				temp: "0",
				rotationRate: 0,
				vDevName: vDevName,
				poolName: poolName,
				vDevType: vDevType,
				errors: [`Disk was removed from pool: ${poolName}, vDev: ${vDevName}`],
			};
		}
	}

	// console.log("fulldisk stats", fullDiskData)
	// console.log("child.path 2 ", child.path)
	// Construct the disk object
	const childDisk: VDevDisk = {
		name: child.name || fullDiskData.name,
		path: child.path,
		guid: child.guid,
		type: fullDiskData.type,
		health: fullDiskData.health,
		stats: child.stats || {},
		capacity: changeUnitToBinary(fullDiskData.capacity),
		model: fullDiskData.model,
		phy_path: fullDiskData.phy_path,
		sd_path: fullDiskData.sd_path,
		vdev_path: fullDiskData.vdev_path,
		serial: fullDiskData.serial,
		powerOnHours: fullDiskData.powerOnHours,
		powerOnCount: fullDiskData.powerOnCount,
		temp: fullDiskData.temp,
		rotationRate: fullDiskData.rotationRate,
		vDevName: vDevName,
		poolName: poolName,
		vDevType: vDevType,
		errors: [],
		// replacingTarget: null
	};
	// Ensure no duplicates in vDevData
	// if (!vDevData.disks.some(disk => disk.guid === childDisk.guid)) {
	// 	vDevData.disks.push(childDisk);
	// }
	if (!fullDiskData) {
		console.warn('No match for', child.path);
	} else {
		const exp = cleanDiskPath(child.path);
		const got = cleanDiskPath(fullDiskData.vdev_path) || cleanDiskPath(fullDiskData.sd_path);
		if (exp !== got) {
			console.warn('Mismatch:', { child: exp, matched: got, matchedName: fullDiskData.name });
		}
	}
	return childDisk;
}

function createMissingDisk(path, vDevName, vDevType, poolName) {
	// console.log(`Creating placeholder for missing disk at path: ${path}`);
	return {
		name: 'Missing Disk',
		path: path,
		guid: 'N/A',
		type: 'N/A',
		health: 'MISSING',
		stats: {},
		capacity: 'Unknown',
		model: 'N/A',
		phy_path: path,
		sd_path: '',
		vdev_path: '',
		serial: 'N/A',
		powerOnHours: 0,
		powerOnCount: '0',
		temp: '0',
		rotationRate: 0,
		vDevName: vDevName,
		poolName: poolName,
		vDevType: vDevType,
		errors: [`Disk missing from pool: ${poolName}, vDev: ${vDevName}`],
	};
}


export async function loadSnapshots(snapshots) {
	try {
		const rawJSON = await getSnapshots();
		// console.log('Snapshots JSON (all):', parsedJSON);
		const allSnapshots: Snapshot[] = [];

		for (const dataset in rawJSON) {
			rawJSON[dataset].forEach(snapshot => {
				const snap = {
					name: snapshot.name,
					id: snapshot.id,
					snapName: snapshot.snapshot_name,
					dataset: snapshot.dataset,
					pool: snapshot.pool,
					mountpoint: snapshot.mountpoint,
					type: snapshot.type,
					guid: snapshot.properties.guid.value,
					creationTimestamp: snapshot.properties.creation.rawvalue,
					properties: snapshot.properties,
					holds: snapshot.holds
				};
				allSnapshots.push(snap);
			});
		}

		// // Sort the snapshots by creationTimestamp
		// allSnapshots.sort((a, b) => parseFloat(a.creationTimestamp) - parseFloat(b.creationTimestamp));

		// // Push sorted snapshots into the reactive data
		// allSnapshots.forEach(snap => snapshots.value.push(snap));
		snapshots.value = allSnapshots.sort((a, b) => parseFloat(a.creationTimestamp) - parseFloat(b.creationTimestamp));


	} catch (error) {
		console.error("An error occurred getting snapshots:", error);
	}
}

export async function loadSnapshotsInPool(snapshots, poolName) {
	try {
		const rawJSON = await getSnapshotsOfPool(poolName);
		// const parsedJSON = JSON.parse(rawJSON);
		// console.log('Snapshots JSON (loadByPool):', parsedJSON);
		const allSnapshots: Snapshot[] = [];

		for (const dataset in rawJSON) {
			rawJSON[dataset].forEach(snapshot => {
				const snap = {
					name: snapshot.name,
					id: snapshot.id,
					snapName: snapshot.snapshot_name,
					dataset: snapshot.dataset,
					pool: snapshot.pool,
					mountpoint: snapshot.mountpoint,
					type: snapshot.type,
					guid: snapshot.properties.guid.value,
					creationTimestamp: snapshot.properties.creation.rawvalue,
					properties: snapshot.properties,
					holds: snapshot.holds
				};

				allSnapshots.push(snap);

			});
		}

		// Sort the snapshots by creationTimestamp
		snapshots.value = allSnapshots.sort((a, b) => parseFloat(a.creationTimestamp) - parseFloat(b.creationTimestamp));


		console.log('loaded snapshots in:', poolName, '\n', snapshots);
	} catch (error) {
		console.error("An error occurred getting snapshots:", error);
	}
}


export async function loadSnapshotsInDataset(snapshots, datasetName, snapshotNotFound, snapshotFound) {
	try {

		const rawJSON = await getSnapshotsOfDataset(datasetName);
		const allSnapshots: Snapshot[] = [];

		for (const dataset in rawJSON) {
			rawJSON[dataset].forEach(snapshot => {
				const snap = {
					name: snapshot.name,
					id: snapshot.id,
					snapName: snapshot.snapshot_name,
					dataset: snapshot.dataset,
					pool: snapshot.pool,
					mountpoint: snapshot.mountpoint,
					type: snapshot.type,
					guid: snapshot.properties.guid.value,
					creationTimestamp: snapshot.properties.creation.rawvalue,
					properties: {
						clones: snapshot.properties.clones.parsed,
						creation: {
							rawTimestamp: snapshot.properties.creation.rawvalue,
							parsed: convertTimestampToLocal(snapshot.properties.creation.parsed),
							value: snapshot.properties.creation.value,
						},
						referenced: snapshot.properties.referenced,
						used: snapshot.properties.used,
					},
					holds: snapshot.holds
				}

				allSnapshots.push(snap);

			});
		}

		// Sort the snapshots by creationTimestamp
		snapshots.value = allSnapshots.sort((a, b) => parseFloat(a.creationTimestamp) - parseFloat(b.creationTimestamp));
		if (snapshots.value.length === 0) {
			if (snapshotNotFound) {
				snapshotNotFound.value = true;
			}
		} else {
			if (snapshotFound) {
				snapshotFound.value = true;
			}
		}
		console.log('loaded snapshots in:', datasetName, '\n', snapshots);
	} catch (error) {
		console.error("An error occurred getting snapshots:", error);
	}
}


// Function to determine the type of disks in a VDev
function determineDiskType(vDev, disks): string {
	const childDisks = vDev.children.map(child => child.name);

	const diskTypes = childDisks.map(diskName => {
		const disk = disks.value.find(disk => disk.name === diskName);
		return disk ? disk.type : 'MISSING'; // Mark as 'MISSING' if disk not found
	});

	// Determine the disk type based on the types of child disks in the VDev
	const uniqueDiskTypes = new Set(diskTypes);

	if (uniqueDiskTypes.has('MISSING')) {
		return 'MISSING';
	} else if (uniqueDiskTypes.size === 1) {
		return Array.from(uniqueDiskTypes)[0] as string; // Return the single type if all disks are the same
	} else if (uniqueDiskTypes.has('Disk')) {
		return 'Disk'; // All disks in VDev are Disks
	} else if (uniqueDiskTypes.has('SSD') || uniqueDiskTypes.has('HDD') || uniqueDiskTypes.has('NVMe')) {
		return 'Hybrid'; // Mixed SSD, HDD, or NVMe
	} else {
		return 'Unknown';
	}
}
