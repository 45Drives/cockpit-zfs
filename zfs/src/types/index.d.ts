//object for create-pools.py
interface newVDev {
	root: string;
	type: string;
	devices: string[];
}

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
		readOnly?: string;
	}
	vdevs: vDevData[];
	settings?: {
		sector: string;
		record: string;
		compression: boolean;
		deduplication: boolean;
		refreservation: number;
		autoExpand: boolean;
		autoReplace: boolean;
		autoTrim: boolean;
		forceCreate: boolean;
		delegation?: boolean;
		displaySnapshots?: boolean;
		multiHost?: boolean;
	},
	createFileSystem?: boolean;
	fileSystem?: FileSystemData;
	datasets?: Dataset[];
	errors?: string[];
	comment?: string;
	failMode?: 'wait' | 'continue' | 'panic';
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
	dedup: string;
	forceCreate?: boolean;
}

interface newVDevData {
	type: string;
	disks: string[];
	isMirror?: boolean;
	// forceAdd?: boolean;
}

//object for vdev
interface vDevData {
	name: string;
	type: 'disk' | 'mirror' | 'raidz1' | 'raidz2' | 'raidz3' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
	status: string;
	guid: string;
	stats: {};
	disks: DiskData[];
	selectedDisks: string[];
	//forceAdd?: boolean;
	poolName?: string;
	isMirror?: boolean;
}

//object for disk
interface DiskData {
	name: string;
	capacity: string;
	model: string;
	guid: string;
	type: string;
	status: string;
	stats: {};
	path: string;
	phy_path: string;
	sd_path: string;
	vdev_path: string;
	serial: string;
	usable: boolean;
	temp: string;
	powerOnCount: string;
	powerOnHours: number;
	rotationRate: number;
	vDevName?: string;
	poolName?: string;
}

//object for filesystem
interface FileSystemData {
	parentFS?: string;
	name: string;
	id: string;
	mountpoint: string;
	pool: string;
	isEncrypted: boolean
	encrypted: string;
	cipher: string;
	passphrase: string?;
	key_loaded: string;
	type: string;
	inherit: boolean;
	properties: {
		accessTime: boolean;
		caseSensitivity: string;
		compression: string;
		deduplication: string;
		dNodeSize: string;
		extendedAttributes: string;
		recordSize: number;
		quota: {
			raw: number;
			value: string;
			size: 'kib' | 'mib' | 'gib';
		};
		isReadOnly?: boolean;
		readOnly: string;
		available: string;
		creation: string;
		snapshotCount: string;
		used: string;
		mounted: string;
	},
	children?: FileSystemData[];
}

interface InheritedProperties {
	id: string;
	atime: boolean;
	casesensitivity: string;
	compression: string;
	dedup: string;
	dnodesize: string;
	recordsize: number;
	xattr: string;
}

//object for dataset (replace filesystem object?)
interface Dataset {
	name: string;
	id: string;
	mountpoint: string;
	pool: string;
	encrypted: string;
	key_loaded: string;
	type: string;
	properties: {
		available: string;
		creation: string;
		snapshotCount: string;
		usedbyRefreservation: string;
		usedByDataset: string;
		accessTime: boolean;
		caseSensitivity: string;
		compression: string;
		deduplication: string;
		dNodeSize: string;
		extendedAttributes: string;
		readOnly: string;
		recordSize: number;
		quota: string;
		mounted: string;
	}
	children?: Dataset[];
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
	properties: {
		clones: string;
		creation: {
			rawTimestamp: string;
			parsed: string;
			value: string;
		}
		referenced: {
			value: string;
			rawNum: number;
		}
		used: {
			value: string;
			rawNum: number;
		}
	}
	holds: {}
}

interface NewSnapshot {
	filesystem: string;
	isCustomName: boolean;
	name: string;
	options: {
		snapFileSystems: boolean;
	}
}

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