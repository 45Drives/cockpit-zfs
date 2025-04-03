import { PoolScanObject } from "@45drives/houston-common-lib";

//object for importing pools
interface ImportedPool {
	name: string;
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
	errors?: string[];
}

//object for importablePoolsData
interface ImportablePoolData {
	name: string;
	status: string;
	guid: string;
	properties: Record<string, any>
	// vdevs: ImportablePoolvDevData[];
	vdevs: VDev[];
	scan: Record<string, any>
	isDestroyed?: boolean;
	errors?: string[];
}

//object for vdev
interface ImportablePoolvDevData {
	name: string;
	type: 'disk' | 'mirror' | 'raidz1' | 'raidz2' | 'raidz3' | 'cache' | 'log' | 'dedup' | 'special' | 'spare';
	status: string;
	guid: string;
	stats: Record<string, any>;
	disks: [Record<string, any>];
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
	holds: Record<string, any>
}

interface NewSnapshot {
	filesystem: string;
	isCustomName: boolean;
	name: string;
	snapChildren: boolean;
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

//object for warning levels
interface WarningConfig {
	scrubFinish: string;
	vdevCleared: string;
	resilverFinish: string;
	clearPoolErrors: string;
	snapshotCreation: string;
	stateChange: string; // even though not user-editable, can still be tracked
	poolImport: string;
	storageThreshold: string;
	replicationTask: string;
	snapshotFailure: string;

  }
type StepNavigationCallback = (item: StepsNavigationItem) => void;

interface Notification {
	id: number;
	timestamp: string;
	event: string;
	pool?: string;
	text: string;
	state?: string;
	vdev?: string;
	error?: string;
	description?: string;
	guid?: string;
	health?: string;
	errors?: string;
	severity?: string;
	fileSystem?: string;
	snapShot?: string;
	replicationDestination?: string
  }
  interface AuthEmailConfig {
	email: string;
	recieversEmail: string[];
	authMethod: string;
	oauthAccessToken: string;
	tokenExpiry: string;
	oauthRefreshToken: string;
  }

  interface SmtpEmailConfig {
	email: string;
	smtpServer: string;
	smtpPort: number;
	username: string;
	password: string;
	recieversEmail: string[];
	tls: boolean;
	authMethod: string;
	oauthAccessToken: string;
	tokenExpiry: string;
  }