<template>
	<div class="border-b border-t border-collapse border-default ">
		<div class="grid grid-cols-9 grid-flow-cols w-full text-center bg-accent text-default ">
			<!-- <div class="relative py-1 pl-3 pr-4 text-right font-medium sm:pr-6 lg:pr-8">
				<span class="sr-only"></span>
			</div> -->
			<!-- <div name="disk-name" class="py-1 mt-1 col-span-2" :class="truncateText" :title="props.disk.name">{{ props.disk.name }} {{ diskSdName }}</div> -->
			<div name="disk-name" class="py-1 mt-1 col-span-2" :class="truncateText" :title="props.disk.name">
				{{ props.disk.name }} {{ diskSdName }} <span v-if="props.disk.replacingTarget">
					<span class="text-orange-600">replacing</span> {{ props.disk.replacingTargetLabel }}</span>
			</div>
			<div name="disk-state" class="py-1 mt-1 col-span-1 font-semibold"
				:class="[formatStatus(diskState), truncateText]" :title="diskState">{{ diskState }}</div>
			<div name="disk-type" class="py-1 mt-1 col-span-1" :class="truncateText" :title="props.disk.type">{{
				props.disk.type }}</div>
			<div name="disk-temp" class="py-1 mt-1 col-span-1" :class="truncateText" :title="props.disk.temp">{{
				props.disk.temp }}</div>
			<div name="disk-capacity" class="py-1 mt-1 col-span-1" :class="truncateText" :title="props.disk.capacity">{{
				props.disk.capacity }}</div>
			<div name="disk-message" class="py-1 -mt-1 col-span-2">
				<Status :isTrim="false" :disk="props.disk" :pool="props.pool" :isDisk="true" :isPoolList="true"
					:isPoolDetail="false" :idKey="'trim-status-box'" ref="trimStatusBox"
					:isTrimmable="getIsTrimmable()" />
			</div>
			<div name="disk-" class="col-span-1">
				<div class="relative py-1 pl-3 pr-4 text-right font-medium sm:pr-6 lg:pr-8">
					<Menu as="div" class="relative inline-block text-right">
						<div>
							<MenuButton @click.stop :disabled="!canDestructive" :aria-disabled="!canDestructive"
								:title="!canDestructive ? 'Requires administrative privileges' : ''" :class="[
									'flex items-center rounded-full p-2 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100',
									canDestructive ? 'bg-accent hover:text-white cursor-pointer'
										: 'bg-accent/60 text-muted cursor-not-allowed'
								]">
								<span class="sr-only">Open options</span>
								<EllipsisVerticalIcon class="w-5" aria-hidden="true" />
							</MenuButton>
						</div>

						<transition enter-active-class="transition ease-out duration-100"
							enter-from-class="transform opacity-0 scale-95"
							enter-to-class="transform opacity-100 scale-100"
							leave-active-class="transition ease-in duration-75"
							leave-from-class="transform opacity-100 scale-100"
							leave-to-class="transform opacity-0 scale-95">
							<MenuItems
								class="absolute right-0 z-10 w-max origin-top-right rounded-md bg-accent shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
								<div class="py-1">
									<!-- <MenuItem as="div" v-slot="{ active }">
                                        <a href="#" @click="clearDiskErrors(props.pool.name, props.disk.name)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Clear Disk Errors</a>
                                    </MenuItem> -->
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="props.vDev.disks.length > 1 && diskState !== 'REMOVED'" href="#"
										@click="detachThisDisk(props.pool, props.disk)"
										:class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Detach
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="diskState == 'ONLINE'" href="#"
										@click="offlineThisDisk(props.pool, props.disk)"
										:class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Offline
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="diskState == 'OFFLINE'" href="#"
										@click="onlineThisDisk(props.pool, props.disk)"
										:class="[active ? 'bg-green-600 text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Online
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="diskState !== 'REMOVED'" href="#"
										@click="replaceThisDisk(props.pool, props.vDev, props.disk)"
										:class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Replace
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="!trimActivity!.isActive && !trimActivity!.isPaused && props.pool.diskType != 'HDD' && getIsTrimmable() && diskState !== 'REMOVED'"
										href="#" @click="trimThisDisk(props.pool, props.disk)"
										:class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">TRIM
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="trimActivity!.isPaused && props.pool.diskType != 'HDD' && getIsTrimmable() && diskState !== 'REMOVED'"
										href="#" @click="resumeTrim(props.pool, props.disk)"
										:class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">TRIM
										Disk</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="trimActivity!.isActive && props.pool.diskType != 'HDD' && getIsTrimmable() && diskState !== 'REMOVED'"
										href="#" @click="pauseTrim(props.pool, props.disk)"
										:class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Pause
										TRIM (Disk)</a>
									</MenuItem>
									<MenuItem as="div" v-slot="{ active }" >
									<a v-if="trimActivity!.isActive || trimActivity!.isPaused && props.pool.diskType != 'HDD' && getIsTrimmable() && diskState !== 'REMOVED'"
										href="#" @click="stopTrim(props.pool, props.disk)"
										:class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Cancel
										TRIM (Disk)</a>
									</MenuItem>
								</div>
							</MenuItems>
						</transition>
					</Menu>
				</div>
			</div>
		</div>
		<div v-if="diskState == 'REPLACING' || diskState == 'MISSING'" class="border border-collapse border-default ">
			<div v-for="disk in props.disk.children!"
				class="grid grid-cols-9 grid-flow-cols w-full text-center bg-accent text-default">
				<div class="py-1 mt-1 col-span-3" :class="truncateText" :title="disk.name">{{ props.disk.name }}</div>
				<div class="py-1 mt-1 col-span-3"></div>
				<div class="py-1 mt-1 col-span-3"></div>
			</div>
		</div>
	</div>

	<div v-if="showDetachDiskModal">
		<component :is="detachDiskComponent" :showFlag="showDetachDiskModal" @close="updateShowDetachDisk"
			:idKey="'confirm-detach-disk'" :item="'disk'" :operation="'detach'" :pool="selectedPool!"
			:disk="selectedDisk!" :confirmOperation="confirmThisDetach" :secondOption="'clear disk labels'"
			:hasChildren="false" />
	</div>

	<div v-if="showOfflineDiskModal">
		<component :is="offlineDiskComponent" :showFlag="showOfflineDiskModal" @close="updateShowOfflineDisk"
			:idKey="'confirm-offline-disk'" :item="'disk'" :operation="'offline'" :pool="selectedPool!"
			:disk="selectedDisk!" :confirmOperation="confirmThisOffline" :firstOption="'forcefully offline'"
			:secondOption="'temporarily offline until next reboot'" :hasChildren="false" />
	</div>

	<div v-if="showOnlineDiskModal">
		<component :is="onlineDiskComponent" :showFlag="showOnlineDiskModal" @close="updateShowOnlineDisk"
			:idKey="'confirm-online-disk'" :item="'disk'" :operation="'online'" :pool="selectedPool!"
			:disk="selectedDisk!" :confirmOperation="confirmThisOnline"
			:firstOption="'expand devices to use whole disk'" :secondOption="'scrub pool after coming online'"
			:hasChildren="false" />
	</div>

	<div v-if="showTrimDiskModal">
		<component :is="trimDiskComponent" :showFlag="showTrimDiskModal" @close="updateShowTrimDisk"
			:idKey="'confirm-trim-disk'" :item="'disk'" :operation="'trim'" :pool="selectedPool!" :disk="selectedDisk!"
			:confirmOperation="confirmThisDiskTrim" :firstOption="'secure TRIM'" :hasChildren="false" />
	</div>

	<div v-if="showPauseTrimConfirm">
		<component :is="trimPauseDiskComponent" :showFlag="showPauseTrimConfirm" @close="updateShowPauseTrim"
			:idKey="'confirm-pause-trim'" :item="'pool'" :operation="'pause'" :operation2="'trim'" :pool="selectedPool!"
			:confirmOperation="confirmPauseThisTrim" :hasChildren="false" />
	</div>

	<div v-if="showStopTrimConfirm">
		<component :is="trimStopDiskComponent" :showFlag="showStopTrimConfirm" @close="updateShowStopTrim"
			:idKey="'confirm-stop-trim'" :item="'pool'" :operation="'stop'" :operation2="'trim'" :pool="selectedPool!"
			:confirmOperation="confirmStopThisTrim" :hasChildren="false" />
	</div>

	<div v-if="showReplaceDiskModal">
		<component :is="replaceDiskComponent" :showFlag="showReplaceDiskModal" @close="updateShowReplaceDisk"
			:idKey="'show-replace-modal'" :pool="selectedPool!" :vDev="selectedVDev!" :disk="selectedDisk!" />
	</div>

</template>
<script setup lang="ts">
import { ref, inject, Ref, watch, computed, provide, onMounted } from "vue";
import { EllipsisVerticalIcon } from '@heroicons/vue/24/outline';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue';
import { scrubPool, clearErrors } from "../../composables/pools";
import { labelClear, detachDisk, offlineDisk, onlineDisk, trimDisk } from "../../composables/disks";
import { formatStatus } from '../../composables/helpers'
import Status from "../common/Status.vue";
import { ZPool, VDev, VDevDisk, ZFSFileSystemInfo } from "@45drives/houston-common-lib";
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { PoolScanObjectGroup, PoolDiskStats, Activity, ConfirmationCallback } from "../../types";
import { useRefreshAllData } from "../../composables/useRefreshAllData";

interface DiskListElementProps {
	pool: ZPool;
	poolIdx: number;
	vDev: VDev;
	vDevIdx: number;
	disk: VDevDisk;
    diskIdx: number;
}

const props = defineProps<DiskListElementProps>();
const canDestructive = inject<Ref<boolean>>('can-destructive')!;

const selectedPool = ref<ZPool>();
const selectedDisk = ref<VDevDisk>();
const selectedVDev = ref<VDev>();

const operationRunning = ref(false);
const firstOptionToggle = ref(false);
const secondOptionToggle = ref(false);
const truncateText = inject<Ref<string>>('style-truncate-text')!;

function getIsTrimmable() {
	selectedPool.value = props.pool;
	if (selectedPool.value.diskType! != 'HDD') {
		if (props.disk.vDevType! == 'data' || props.disk.vDevType! == 'log' || props.disk.vDevType! == 'special' || props.disk.vDevType! == 'dedup') {
			return true;
		} else {
			return false;
		}
	} else {
		return false;
	}
}

const diskSdName = computed(() => {
	if (!props.disk.sd_path!.includes(props.disk.name!)) {
		return `(${props.disk.sd_path!.replace(/^\/dev\//, '')})`;
	}
});

onMounted(() => {
	getIsTrimmable();
});

/////////////// Loading/Refreshing //////////////////
/////////////////////////////////////////////////////
const poolData = inject<Ref<ZPool[]>>("pools")!;
const diskData = inject<Ref<VDevDisk[]>>("disks")!;
const filesystemData = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const { refreshAllData } = useRefreshAllData({
	poolData,
	diskData,
	filesystemData,
	disksLoaded,
	poolsLoaded,
	fileSystemsLoaded,
	scanObjectGroup,
	poolDiskStats,
	scanActivities,
	trimActivities
});


const starting = ref(false);

const scanStatusBox = inject<Ref<any>>('scan-status-box')!;

async function getScanStatus() {
	// console.log('scanStatusBox', scanStatusBox.value);
	await scanStatusBox.value.pollScanStatus();
}

const diskState = computed(() => {
	const diskArray = poolDiskStats.value[props.pool.name];
	const diskState = diskArray.find(disk => disk.name === props.disk.name);

	if (diskState) {
		return diskState.status;
	} else {
		return 'MISSING';
	}

});


/////////////////// Detach Disk /////////////////////
/////////////////////////////////////////////////////
const showDetachDiskModal = ref(false);
const confirmDetach = ref(false);
const detaching = ref(false);

const detachDiskComponent = ref();
const loadDetachDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	detachDiskComponent.value = module.default;
}

async function detachThisDisk(pool : ZPool, disk: VDevDisk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	await loadDetachDiskComponent();
	showDetachDiskModal.value = true;
	console.log("Preparing to detach:", selectedDisk.value!.name, "from:", selectedPool.value!.name);
}

const confirmThisDetach : ConfirmationCallback = () => {
	confirmDetach.value = true;
}

const updateShowDetachDisk = (newVal) => {
	showDetachDiskModal.value = newVal;
}

watch(confirmDetach, async (newValue, oldValue) => {
	if (confirmDetach.value == true) {
		detaching.value = true;
		operationRunning.value = true;
		console.log("now detaching:", selectedDisk.value!.name, "from:", selectedPool.value!.name);

		try {
			const output: any = await detachDisk(selectedPool.value!.name, selectedDisk.value!.name!);

			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				operationRunning.value = false;
				confirmDetach.value = false;
				pushNotification(new Notification('Detach Disk Failed', `${selectedDisk.value!.name} was not detached: ${errorMessage}`, 'error', 5000));

			} else {
				if (secondOptionToggle.value == true) {
					await labelClear(selectedDisk.value!);
				}

				await refreshAllData();
				confirmDetach.value = false;
				detaching.value = false;
				operationRunning.value = false;
				pushNotification(new Notification('Detach Completed', `${selectedDisk.value!.name} was detached from ${selectedPool.value!.name}`, 'success', 5000));

				showDetachDiskModal.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

////////////////// Offline Disk /////////////////////
/////////////////////////////////////////////////////
const showOfflineDiskModal = ref(false);
const confirmOffline = ref(false);
const offlining = ref(false);

const offlineDiskComponent = ref();
const loadOfflineDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	offlineDiskComponent.value = module.default;
}

async function offlineThisDisk(pool: ZPool, disk: VDevDisk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	// console.log('selected pool:', selectedPool.value, 'selected disk:', selectedDisk.value);
	await loadOfflineDiskComponent();
	showOfflineDiskModal.value = true;
}

const confirmThisOffline : ConfirmationCallback = () => {
	confirmOffline.value = true;
}

const updateShowOfflineDisk = (newVal) => {
	showOfflineDiskModal.value = newVal;
}

watch(confirmOffline, async (newVal, oldVal) => {
	if (confirmOffline.value == true) {
		offlining.value = true;
		operationRunning.value = true;
		console.log('now offlining:', selectedDisk.value);

		try {
			const output: any = await offlineDisk(selectedPool.value!.name, selectedDisk.value!.name!, firstOptionToggle.value, secondOptionToggle.value);
			
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				operationRunning.value = false;
				confirmOffline.value = false;
				pushNotification(new Notification('Offline Failed', `Offlining of disk ${selectedDisk.value!.name} failed: ${errorMessage}`, 'error', 5000));

			} else {
				await refreshAllData();
				confirmOffline.value = false;
				offlining.value = false;
				operationRunning.value = false;
				pushNotification(new Notification('Offline Completed', 'Offlining of disk ' + selectedDisk.value!.name + " completed.", 'success', 5000));

				showOfflineDiskModal.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

/////////////////// Online Disk /////////////////////
/////////////////////////////////////////////////////
const showOnlineDiskModal = ref(false);
const confirmOnline = ref(false);
const onlining = ref(false);

const onlineDiskComponent = ref();
const loadOnlineDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	onlineDiskComponent.value = module.default;
}

async function onlineThisDisk(pool: ZPool, disk: VDevDisk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	// console.log('selected pool:', selectedPool.value, 'selected disk:', selectedDisk.value);
	await loadOnlineDiskComponent();
	showOnlineDiskModal.value = true;
}

const confirmThisOnline : ConfirmationCallback = () => {
	confirmOnline.value = true;
}

const updateShowOnlineDisk = (newVal) => {
	showOnlineDiskModal.value = newVal;
}

watch(confirmOnline, async (newVal, oldVal) => {
	if (confirmOnline.value == true) {
		onlining.value = true;
		operationRunning.value = true;
		console.log('now onlining:', selectedDisk.value);

		try {
			const output: any = await onlineDisk(selectedPool.value!.name, selectedDisk.value!.name!, firstOptionToggle.value);

			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				operationRunning.value = false;
				confirmOnline.value = false;
				pushNotification(new Notification('Online Failed', `Onlining of disk ${selectedDisk.value!.name} failed: ${errorMessage}`, 'error', 5000));

			} else {
				if (secondOptionToggle.value == true) {
					starting.value = true;
					try {
						const output2: any = await scrubPool(selectedPool.value!);

						if (output2 == null || output2.error) {
							const errorMessage2 = output2?.error || 'Unknown error';
							pushNotification(new Notification('Scrub Failed', `Scrub on ${selectedDisk.value!.name} failed: ${errorMessage2}.`, 'error', 5000));

						} else {
							await getScanStatus();
							pushNotification(new Notification('Scrub Started', 'Scrub on ' + selectedPool.value!.name + " started.", 'success', 5000));

						}
					} catch (error) {
						console.error(error);
					}

					
					starting.value = false;
				}

				onlining.value = false;
				confirmOnline.value = false;
				operationRunning.value = false;
				pushNotification(new Notification('Online Completed', 'Onlining of disk ' + selectedDisk.value!.name + " completed.", 'success', 5000));

				showOnlineDiskModal.value = false;
			}

			await refreshAllData();

		} catch (error) {
			console.error(error);
		}

	}
});

///////////////////// TRIM Disk /////////////////////
/////////////////////////////////////////////////////
const showTrimDiskModal = ref(false);
const confirmTrimDisk = ref(false);
const startingDiskTrim = ref(false);
const pausingDiskTrim = ref(false);
const stoppingDiskTrim = ref(false);
const resumingDiskTrim = ref(false);

const trimDiskComponent = ref();
const loadTrimDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	trimDiskComponent.value = module.default;
}

const trimPauseDiskComponent = ref();
const loadTrimPauseDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	trimPauseDiskComponent.value = module.default;
}

const trimStopDiskComponent = ref();
const loadTrimStopDiskComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	trimStopDiskComponent.value = module.default;
}

async function trimThisDisk(pool: ZPool, disk: VDevDisk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	// console.log('selected pool:', selectedPool.value, 'selected disk:', selectedDisk.value);
	await loadTrimDiskComponent();
	showTrimDiskModal.value = true;
}

const confirmThisDiskTrim : ConfirmationCallback = () => {
	confirmTrimDisk.value = true;
}

const updateShowTrimDisk = (newVal) => {
	showTrimDiskModal.value = newVal;
}

watch(confirmTrimDisk, async (newValue, oldValue) => {
	if (confirmTrimDisk.value == true) {
		operationRunning.value = true;
		console.log('now trimming:', selectedPool.value);
		try {
			const output: any = await trimDisk(selectedPool.value!.name,  selectedDisk.value!.name!, (firstOptionToggle.value ? firstOptionToggle.value : false));
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				confirmTrimDisk.value = false
				pushNotification(new Notification('Trim Failed', `Trim failed to start: ${errorMessage}`, 'error', 5000));

			} else {
				getDiskTrimStatus();
				confirmTrimDisk.value = false
				pushNotification(new Notification('Trim Started', 'Trim on ' + selectedDisk.value!.name + " started.", 'success', 5000));

				showTrimDiskModal.value = false;
			}
		} catch (error) {
			console.error(error);
		}
		operationRunning.value = false;
	}
});

async function pauseTrim(pool, disk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	await loadTrimPauseDiskComponent();
	showPauseTrimConfirm.value = true;
	console.log('trim to pause:', selectedPool.value);
}

async function resumeTrim(pool, disk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	resumingDiskTrim.value = true;
	try {
		const output: any = await trimDisk(selectedPool.value!.name, selectedDisk.value!.name!);

		if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				pushNotification(new Notification('Trim Resume Failed', "Trim failed to resume:${errorMessage}", 'error', 5000));

			// operationRunning.value = false;
		} else {
			getDiskTrimStatus();
			pushNotification(new Notification('Trim Resumed', 'Trim on ' + selectedDisk.value!.name + " resumed.", 'success', 5000));

			// operationRunning.value = false;
		}
	} catch (error) {
		console.error(error)
	}
	resumingDiskTrim.value = false
}


async function stopTrim(pool, disk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	await loadTrimStopDiskComponent();
	showStopTrimConfirm.value = true;
	console.log('trim to stop:', selectedPool.value);
}

const showPauseTrimConfirm = ref(false);
const confirmPauseTrim = ref(false);

const confirmPauseThisTrim : ConfirmationCallback = () => {
	confirmPauseTrim.value = true;
}

const updateShowPauseTrim = (newVal) => {
	showPauseTrimConfirm.value = newVal;
}

watch(confirmPauseTrim, async (newVal, oldVal) => {
	if (confirmPauseTrim.value == true) {
		console.log('now pausing trim:', selectedPool.value);
		pausingDiskTrim.value = true;
		try {
			const output: any = await trimDisk(selectedPool.value!.name, selectedDisk.value!.name!, false, 'pause');
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				confirmPauseTrim.value = false;
				pushNotification(new Notification('Trim Pause Failed', `Trim failed to pause: ${errorMessage}`, 'error', 5000));

				// operationRunning.value = false;
			} else {
				getDiskTrimStatus();
				confirmPauseTrim.value = false;
				pushNotification(new Notification('Trim Paused', 'Trim on ' + selectedDisk.value!.name + " paused.", 'success', 5000));

				// operationRunning.value = false;
				showPauseTrimConfirm.value = false;
			}
			
		} catch (error) {
			console.error(error);
		}
		
		pausingDiskTrim.value = false;
	}
});

const showStopTrimConfirm = ref(false);
const confirmStopTrim = ref(false);

const confirmStopThisTrim : ConfirmationCallback = () => {
	confirmStopTrim.value = true;
}

const updateShowStopTrim = (newVal) => {
	showStopTrimConfirm.value = newVal;
}

watch(confirmStopTrim, async (newVal, oldVal) => {
	if (confirmStopTrim.value == true) {
		console.log('now stopping trim:', selectedPool.value);
		stoppingDiskTrim.value = true;
		try {
			const output: any = await trimDisk(selectedPool.value!.name, selectedDisk.value!.name!, false, 'stop');
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				confirmStopTrim.value = false;
				pushNotification(new Notification('Trim Stop Failed', `Trim failed to stop: ${errorMessage}`, 'error', 5000));

				// operationRunning.value = false;
			} else {
				getDiskTrimStatus();
				confirmStopTrim.value = false;
				pushNotification(new Notification('Trim Stopped', 'Trim on ' + selectedDisk.value!.name + " stopped.", 'success', 5000));

				showStopTrimConfirm.value = false;
			}
		} catch (error) {
			console.error(error);
		}

		stoppingDiskTrim.value = false;
	}
});

/////////////////// Replace Disk ////////////////////
/////////////////////////////////////////////////////
const showReplaceDiskModal = ref(false);

const replaceDiskComponent = ref();
const loadReplaceDiskComponent = async () => {
	const module = await import('../disks/ReplaceDiskModal.vue');
	replaceDiskComponent.value = module.default;
}

const updateShowReplaceDisk = (newVal) => {
	showReplaceDiskModal.value = newVal;
}

async function replaceThisDisk(pool: ZPool,  vdev: VDev, disk: VDevDisk) {
	selectedPool.value = pool;
	selectedDisk.value = disk;
	selectedVDev.value = vdev;
	// console.log('selected pool:', selectedPool.value, 'selectedVDev:', selectedVDev, 'selected disk:', selectedDisk.value);
	await loadReplaceDiskComponent();
	showReplaceDiskModal.value = true;
}

/////////////////// Clear Errors ////////////////////
/////////////////////////////////////////////////////
// const cleared = ref(false);

async function clearDiskErrors(poolName, diskName) {
	// cleared.value = false;
	await clearErrors(poolName, diskName);
	// cleared.value = true;
}

//////////// Checking Disk Stats (Trim) /////////////
/////////////////////////////////////////////////////
const trimStatusBox = ref();

async function getDiskTrimStatus() {
	// console.log('trimStatusBox', trimStatusBox.value);
	await trimStatusBox.value.pollTrimStatus();
}

/////////////////////////////////////////////////////

const diskID = ref(props.disk.name);

const trimActivity = computed(() => {
	return trimActivities.value.get(diskID.value!);
});


defineExpose({
    getDiskTrimStatus,
});

provide('modal-confirm-running', operationRunning);
provide('show-replace-modal', showReplaceDiskModal);
provide('modal-option-one-toggle', firstOptionToggle);
provide('modal-option-two-toggle', secondOptionToggle);
</script>