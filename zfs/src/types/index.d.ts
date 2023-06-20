interface newVDev {
  root: string;
  type: string;
  devices: string[];
}

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
  },
  createFileSystem?: boolean;
  fileSystem?: FileSystem;
}

interface vDevData {
  name: string;
  type: string;
  status: string;
  guid: string;
  stats: {};
  disks: ChildDisk[];
  forceAdd?: boolean;
}

interface ChildDisk {
  name: string;
  path: string;
  guid: string;
  type: string;
  status: string;
  stats: {};
}

interface DiskData {
  name: string;
  capacity: string;
  model: string;
  type: string;
  phy_path: string;
  sd_path: string;
  vdev_path: string;
  serial: string;
  usable: boolean;
}

interface FileSystem {
  name: string;
  encryption: boolean;
  cipher: string;
  passphrase: string?;
  inherit: boolean;
  accessTime: string;
  caseSensitivity: string;
  compression: string;
  deduplication: string;
  dNodeSize: string;
  extendedAttributes: string;
  recordSize: string;
  quota: {
    amount: number;
    size: string;
  };
  readOnly: boolean;
}

interface NavigationItem {
  name: string;
  tag: string;
  current: boolean;
  show: boolean;
}

type NavigationCallback = (item: NavigationItem) => void;

interface StepsNavigationItem {
  name: string;
  id: string;
  tag: string;
  current: boolean;
  status: string;
  show: boolean;
}

type StepNavigationCallback = (item: StepsNavigationItem) => void;