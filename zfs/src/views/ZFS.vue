<template>
	<div>
		<div class="w-full h-dvh min-h-dvh overflow-visible bg-default text-default">

			<div v-if="props.tag === 'dashboard'" class="p-2">
			   	<component :is="dashboardComponent"/> 
			</div>

			<div v-if="props.tag === 'pools'" class="p-2">
				<component :is="poolListComponent"/>
			</div>

			<div v-if="props.tag === 'filesystems'" class="p-2">
				<component :is="fileSystemListComponent"/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, Ref, provide, watchEffect, onMounted, onBeforeUnmount } from 'vue';
import { getUserCaps } from "../auth/capabilities";
import { loadDisksThenPools, loadDatasets, loadScanObjectGroup, loadDiskStats, loadSnapshots } from '../composables/loadData';
import { loadScanActivities, loadTrimActivities } from '../composables/helpers';
import { ZPool, VDevDisk, ZFSFileSystemInfo } from '@45drives/houston-common-lib';
import { notificationStore } from "../store/notification";
import { ImportablePoolData, Snapshot, Activity, PoolScanObjectGroup, PoolDiskStats } from '../types';

interface ZFSProps {
  	tag: string;
}


const props = defineProps<ZFSProps>();

const truncateText = ref('overflow-hidden whitespace-nowrap text-ellipsis');

const pools = ref<ZPool[]>([]);
const disks = ref<VDevDisk[]>([]);
const datasets = ref<ZFSFileSystemInfo[]>([]);
const importablePools = ref<ImportablePoolData[]>([]);
const importableDestroyedPools = ref<ImportablePoolData[]>([]);
const snapshots = ref<Snapshot[]>([]);

const disksLoaded = ref(false);
const poolsLoaded = ref(false);
const fileSystemsLoaded = ref(false);

const clearLabels = ref(false);

const scanActivities = ref<Map<string, Ref<Activity>>>(new Map());
const scanObjectGroup = ref<PoolScanObjectGroup>({});
const scanIntervalID = ref();

const trimActivities = ref<Map<string, Ref<Activity>>>(new Map());
const poolDiskStats = ref<PoolDiskStats>({});
const diskStatsIntervalID = ref();

async function initialLoad(disks, pools, datasets, snapshots) {
	disksLoaded.value = false;
	poolsLoaded.value = false;
	fileSystemsLoaded.value = false;
	await loadDisksThenPools(disks, pools);
	await loadDatasets(datasets);
	//await loadSnapshots(snapshots);
	
	await scanNow();
	await loadScanActivities(pools, scanActivities);
	await checkDiskStats();
	await loadTrimActivities(pools, trimActivities);
	disksLoaded.value = true;
	poolsLoaded.value = true;
	fileSystemsLoaded.value = true;
	// console.log('ZFS.vue scanActivities', scanActivities.value);
	// console.log('ZFS.vue trimActivities', trimActivities.value);
	setUpMessageHandler((message) => {
        //console.log("Received DBus Message:", message);
    });
}

// D-Bus message handler state — stored so we can clean up on unmount
let houstonDbusClient: ReturnType<typeof cockpit.dbus> | null = null;
let houstonMessageHandler: ((event: any, message: any) => void) | null = null;
let houstonProxy: any = null;
let isUnmounted = false;

async function setUpMessageHandler(handler) {
    try {
        console.log("Setting up ZFS Notification DBus message handler...");

        const client = cockpit.dbus("org._45drives.Houston");
        const proxy = await client.proxy("org._45drives.Houston", "/org/_45drives/Houston");

        // If the component was unmounted while we were awaiting the proxy,
        // close immediately and bail out.
        if (isUnmounted) {
            try { client.close(); } catch {}
            return;
        }

        houstonDbusClient = client;
        houstonProxy = proxy;

        console.log("Connected to ZFS Notification DBus. Subscribing to Message signal...");

        houstonMessageHandler = (_, message) => {
			notificationStore.addNotification(message);
            handler(message);
        };
        houstonProxy.addEventListener("Message", houstonMessageHandler);

        console.log("ZFS Notification DBus message handler successfully set up.");
    } catch (error) {
        console.error("Error setting up ZFS Notification DBus message handler:", error);
    }
}

// setUpMessageHandler((message) => {
//     console.log("hello")
// })

onMounted(() => {
	isUnmounted = false;
	initialLoad(disks, pools, datasets, snapshots);
});

onBeforeUnmount(() => {
	isUnmounted = true;

	// Clean up D-Bus listener + connection
	if (houstonProxy && houstonMessageHandler) {
		try { houstonProxy.removeEventListener("Message", houstonMessageHandler); } catch {}
	}
	if (houstonDbusClient) {
		try { houstonDbusClient.close(); } catch {}
		houstonDbusClient = null;
	}
	houstonProxy = null;
	houstonMessageHandler = null;

	// Clean up any leaked Status.vue intervals
	if (scanIntervalID.value) {
		clearInterval(scanIntervalID.value);
		scanIntervalID.value = null;
	}
	if (diskStatsIntervalID.value) {
		clearInterval(diskStatsIntervalID.value);
		diskStatsIntervalID.value = null;
	}
});


/////////////////////////////////////////////////////
async function scanNow() {
	await loadScanObjectGroup(scanObjectGroup);
}

/////////////////////////////////////////////////////
async function checkDiskStats() {
	await loadDiskStats(poolDiskStats);
}

/////////////////////////////////////////////////////
const dashboardComponent = ref();
const loadDashboardComponent = async () => {
	const module = await import('../components/dashboard/Dashboard.vue');
	dashboardComponent.value = module.default;
}

const poolListComponent = ref();
const loadPoolListComponent = async () => {
	const module = await import('../components/pools/PoolsList.vue');
	poolListComponent.value = module.default;
}

const fileSystemListComponent = ref();
const loadFileSystemListComponent = async () => {
	const module = await import('../components/file-systems/FileSystemList.vue');
	fileSystemListComponent.value = module.default;
}

const canDestructive = ref(false);

onMounted(async () => {
	const caps = await getUserCaps();
	canDestructive.value = caps.isRoot || caps.isAdminGroup;
});

watchEffect(() => {
	if (props.tag === 'dashboard') {
		loadDashboardComponent();
	}
	if (props.tag === 'pools') {
		loadPoolListComponent();
	}
	if (props.tag === 'filesystems') {
		loadFileSystemListComponent();
	}
});
/////////////////////////////////////////////////////

//provide data for other components to inject
provide("can-destructive", canDestructive);
provide("pools", pools);
provide("importable-pools", importablePools);
provide("importable-destroyed-pools", importableDestroyedPools);
provide("disks", disks);
provide("style-truncate-text", truncateText);
provide("datasets", datasets);
provide('disks-loaded', disksLoaded);
provide('datasets-loaded', fileSystemsLoaded);
provide('pools-loaded', poolsLoaded);
provide('clear-labels', clearLabels);
provide("snapshots", snapshots);
provide('scan-object-group', scanObjectGroup);
provide('pool-disk-stats', poolDiskStats);
provide('scan-interval', scanIntervalID);
provide('disk-stats-interval', diskStatsIntervalID);
provide('scan-activities', scanActivities);
provide('trim-activities', trimActivities);
</script>