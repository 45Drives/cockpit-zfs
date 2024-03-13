//object for pool
interface PoolData {
	name: string;
	status: string;
	guid: string;
	properties: {
		rawsize: number;
		size: string;
		capacity: number;
		allocated: string;
		free: string;
		readOnly: boolean;
		sector: string;
		record: string;
		compression: boolean;
		deduplication: boolean;
		refreservationPercent?: number;
		refreservationRawSize?: number;
		autoExpand: boolean;
		autoReplace: boolean;
		autoTrim: boolean;
		forceCreate?: boolean;
		delegation?: boolean;
		listSnapshots?: boolean;
		// multiHost?: boolean;
		health?: string;
		altroot?: string;
	}
	vdevs: vDevData[];
	createFileSystem?: boolean;
	fileSystem?: FileSystemData;
	datasets?: Dataset[];
	errors?: string[];
	comment?: string;
	failMode?: 'wait' | 'continue' | 'panic';
	diskType?: 'SSD' | 'HDD' | 'Hybrid';
	scan?: PoolScanObject;
	diskIdentifier?: DiskIdentifier;
}

//object for vdev
interface vDevData {
	name: string;
	// type: 'disk' | 'mirror' | 'raidz1' | 'raidz2' | 'raidz3' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
	type: string;
	status: string;
	guid: string;
	stats: {
		read_errors: number;
		write_errors: number;
		checksum_errors: number;
	};
	disks: DiskData[];
	selectedDisks: string[];
	forceAdd?: boolean;
	poolName?: string;
	isMirror?: boolean;
	diskType?: 'SSD' | 'HDD' | 'Hybrid';
	diskIdentifier?: DiskIdentifier;
	path?: string;
}

//object for disk
interface DiskData {
	name: string;
	capacity: string;
	model: string;
	guid: string;
	type: string;
	health: string;
	stats: {};
	path: string;
	phy_path: string;
	sd_path: string;
	vdev_path: string;
	serial: string;
	temp: string;
	powerOnCount: string;
	powerOnHours: number;
	rotationRate: number;
	vDevName?: string;
	poolName?: string;
	identifier?: DiskIdentifier;
	children?: ChildDiskData[];
	vDevType?: 'data' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
}

interface ChildDiskData {
	name: string;
	guid: string;
	path: string;
	stats: {};
	status: string;
	type: string;
	children?:[];
	vDevType?: 'data' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
}

//object for importing pools
interface ImportedPool {
	poolGUID: string;
	altRoot: string;
	renamePool: boolean;
	newPoolName?: string;
	identifier: DiskIdentifier;
	forceImport: boolean;
	recoveryMode: boolean;
	ignoreMissingLog: boolean;
	mountFileSystems: boolean;
	readOnly: boolean;
	isDestroyed: boolean;
}

//object for importablePoolsData
interface ImportablePoolData {
	name: string;
	status: string;
	guid: string;
	properties: {}
	// vdevs: ImportablePoolvDevData[];
	vdevs: vDevData[];
	scan: {}
	isDestroyed?: boolean;
}

//object for vdev
interface ImportablePoolvDevData {
	name: string;
	type: 'disk' | 'mirror' | 'raidz1' | 'raidz2' | 'raidz3' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
	status: string;
	guid: string;
	stats: {};
	disks: [{}];
	poolName?: string;
}

//object for pool configuration (pool details)
interface PoolEditConfig {
	name: string;
	readonly: string;
	guid: string;
	ashift?: string;
	failmode?: string;
	comment?: string;
	autoexpand?: string;
	autoreplace?: string;
	autotrim?: string;
	// multihost?: string;
	delegation?: string;
	listsnapshots?: string;
}

//pool object for creating new pool command
interface newPoolData {
	name: string;
	vdevs: newVDevData[];
	autoexpand: string;
	autoreplace: string;
	autotrim: string;
	compression: string;
	recordsize: number;
	sectorsize: number;
	dedup: string;
	forceCreate?: boolean;
	refreservationPercent: number;
}

interface newVDevData {
	type: string;
	disks: string[];
	isMirror?: boolean;
	forceAdd?: boolean;
}

type DiskIdentifier = 'vdev_path' | 'phy_path' | 'sd_path';

//object for filesystem
interface FileSystemData {
	name: string;
	id: string;
	mountpoint: string;
	pool: string;
	encrypted: boolean;
	key_loaded: string;
	type: string;
	inherit: boolean;
	passphrase?: string;
	properties: {
		guid: string;
		encryption: string;
		accessTime: string;
		caseSensitivity: string;
		compression: string;
		deduplication: string;
		dNodeSize: string;
		extendedAttributes: string;
		recordSize: string;
		quota: {
			raw: number;
			value: string;
			unit: 'kib' | 'mib' | 'gib' | 'tib';
		}
		isReadOnly?: boolean;
		readOnly: string;
		available: number;
		creation: string;
		snapshotCount: string;
		mounted: string;
		usedbyRefreservation: string;
		usedByDataset: string;
		canMount?: string;
		aclInheritance?: string;
		aclType?: string;
		checksum?: string;
		refreservation?: {
			raw: number;
			value: string;
			unit: 'kib' | 'mib' | 'gib' | 'tib';
		}
		used: number;
	},
	children?: FileSystemData[];
	parentFS?: string;
}

interface FileSystemEditConfig {
	name: string;
	guid: string;
	casesensitivity: string;
	readonly?: string;
	mountpoint?: string;
	canmount?: string;
	atime?: string;
	record?: string;
	aclinherit?: string;
	acltype?: string;
	dedup?: string;
	compression?: string;
	checksum?: string;
	dnodesize?: string;
	xattr?: string;
	quota?: number;
	refreservation?: number;
}

//dataset command data object
interface NewDataset {
	name: string;
	parent: string;
	encrypted: boolean;
	encryption?: string;
	atime: string;
	casesensitivity: string;
	compression: string;
	dedup: string;
	dnodesize: string;
	xattr: string;
	recordsize: string;
	quota: string;
	readonly: string;
}

//object for snapshots
interface Snapshot {
	name: string;
	id: string;
	snapName: string;
	dataset: string;
	pool: string;
	mountpoint: string;
	type: string;
	guid: string;
	creationTimestamp: string;
	properties: any,
	holds: {}
}

interface NewSnapshot {
	filesystem: string;
	isCustomName: boolean;
	name: string;
	snapChildren: boolean;
}

//object for tracking pool scan (scrub/resilver) data
interface PoolScanObject {
	name?: string;
	function: string;
	start_time: string;
	end_time: string;
	state: string;
	errors: number;
	percentage: number;
	pause: string;
	total_secs_left: number;
	bytes_issued: number;
	bytes_processed: number;
	bytes_to_process: number;
}

//object to encapsulate scan data objects
interface PoolScanObjectGroup {
	[poolName: string]: PoolScanObject;
}

//object for disk stats (trim data)
interface DiskStats {
	name: string;
	stats: {
		allocated: number;
		bytes: number[];
		checksum_errors: number;
		configured_ashift: number;
		fragmentation: number;
		logical_ashift: number;
		ops: number[];
		physical_ashift: number;
		read_errors: number;
		self_healed: number;
		size: number;
		timestamp: number;
		trim_action_time: number;
		trim_bytes_done: number;
		trim_bytes_est: number;
		trim_errors: number;
		trim_notsup: number;
		trim_state: number;
		write_errors: number;
	},
	guid: string,
	status: string,
}

//object for encapsulating disk stats objects
interface PoolDiskStats {
	[poolName: string]: DiskStats[];
}

//activity status tracking for pool/disk operations (scrub/resilver/trim)
interface Activity {
	isActive: boolean;
	isPaused: boolean;
	isCanceled: boolean;
	isFinished: boolean;
}

//object for encapsulating disk specific activity (trim)
interface DiskTrimActivity {
	[diskName: string]: Activity;
}

//sending snapshot data
interface SendingDataset {
	sendName: string;
	sendIncName?: string;
	recvName: string;
	recvHost: string;
	recvPort: string;
	sendOpts: {
		compressed: boolean;
		raw: boolean;
		incremental?: boolean;
		forceOverwrite?: boolean;
	}
	recvHostUser?: string;
	mBufferConfig?: {
		size: number;
		unit: string; 
	}
}

//essential data from snapshots used in check functions for remote sends
interface SnapSnippet {
	name: string;
	guid: string;
	creation: string;
}

//object for storing progress of sends
interface SendProgress {
	snapshot: string;
	status: string;
	totalSize: string;
	sent: string;
}

type ConfirmationCallback = () => void;

//object for navigation (generic)
interface NavigationItem {
	name: string;
	tag: string;
	current: boolean;
	show: boolean;
}

type NavigationCallback = (item: NavigationItem) => void;

//object for navigation in wizard
interface StepsNavigationItem {
	name: string;
	id: string;
	tag: string;
	current: boolean;
	status: string;
	show: boolean;
}

type StepNavigationCallback = (item: StepsNavigationItem) => void;