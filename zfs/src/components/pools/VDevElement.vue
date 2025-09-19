<template>
	<div class="">
		<div class="">
			<Disclosure v-slot="{ open }" :defaultOpen="true">
				<DisclosureButton
					class="grid grid-cols-8 grid-flow-cols w-full text-center bg-primary text-sm text-white">
					<div name="vdev-chevron" class="p-1 mt-1 col-span-1 flex flex-row justify-center text-center">
						<ChevronUpIcon class="-mt-2 h-10 w-10 text-white transition-all duration-200 transform"
							:class="{ 'rotate-90': !open, 'rotate-180': open, }" />
					</div>
					<div name="vdev-name" class="p-1 mt-1 col-span-1 text-base text-left" :class="truncateText"
						:title="props.vDev.name">{{ props.vDev.name }}</div>
					<div name="vdev-status" class="p-1 mt-1 col-span-1 font-semibold text-base"
						:class="[formatStatus(props.vDev.status), truncateText]" :title="props.vDev.status">{{
						props.vDev.status }}</div>
					<div name="vdev-type" class="p-1 mt-1 col-span-1 text-base" :class="truncateText"
						:title="upperCaseWord(props.vDev.type) + ' Device'">{{ upperCaseWord(props.vDev.type) }} Device
					</div>
					<div name="vdev-read-err" class="p-1 mt-1 col-span-1 text-base" :class="truncateText"
						:title="props.vDev.stats!.read_errors + ' Read Errors'">{{ props.vDev.stats!.read_errors }} Read
						Errors</div>
					<div name="vdev-write-err" class="p-1 mt-1 col-span-1 text-base" :class="truncateText"
						:title="props.vDev.stats!.write_errors + ' Write Errors'">{{ props.vDev.stats!.write_errors }}
						Write Errors</div>
					<div name="vdev-checksum-err" class="p-1 mt-1 col-span-1 text-base" :class="truncateText"
						:title="props.vDev.stats!.checksum_errors + ' Checksum Errors'">{{
						props.vDev.stats!.checksum_errors }} Checksum Errors</div>
					<div name="vdev-menu"
						class="col-span-1 relative p-1 pl-3 pr-4 text-right font-medium sm:pr-6 lg:pr-8 justify-self-end justify-items-end">
						<Menu as="div" class="relative inline-block text-right">
							<div>
								<MenuButton @click.stop :disabled="!canDestructive" :aria-disabled="!canDestructive"
									:title="!canDestructive ? 'Requires administrative privileges' : ''" :class="[
										'flex items-center rounded-full p-2 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100',
										canDestructive ? 'bg-primary hover:text-white cursor-pointer'
											: 'bg-primary/60 text-muted cursor-not-allowed'
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
								<MenuItems @click.stop
									class="absolute right-0 z-10 w-max origin-top-right rounded-md bg-primary shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
									<div class="py-1">
										<!-- <MenuItem as="div" v-slot="{ active }">
											<a href="#" @click.stop="clearVDevErrors(props.pool.name, props.vDev.name)" :class="[active ? 'bg-primary text-white' : 'text-white', 'block px-4 py-2 text-sm']">Clear Virtual Device Errors</a>
										</MenuItem> -->
										<MenuItem
											v-if="pool.vdevs.length !== 1 && vDev !== pool.vdevs[0] && !vDev.type.includes('raid')"
											as="div" v-slot="{ active }">
										<a href="#" @click="removeVDev(props.pool, props.pool.vdevs[vDevIdx])"
											:class="[active ? 'bg-danger text-white' : 'text-white', 'block px-4 py-2 text-sm']">Remove
											Virtual Device</a>
										</MenuItem>
										<MenuItem as="div" v-slot="{ active }">
										<a href="#" @click="showAttachDisk(props.pool, props.vDev)"
											:class="[active ? 'bg-primary text-white' : 'text-white', 'block px-4 py-2 text-sm']">Attach
											Disk</a>
										</MenuItem>
									</div>
								</MenuItems>
							</transition>
						</Menu>
					</div>
				</DisclosureButton>
				<DisclosurePanel>
					<table class="min-w-full bg-secondary text-default">
						<thead>
							<tr :key="props.vDevIdx" class=" grid grid-cols-9 font-semibold text-white">
								<!-- <th class="relative py-2 pl-3 pr-4 sm:pr-6 lg:pr-8 col-span-1">
									<span class="sr-only"></span>
								</th> -->
								<th class="py-2 col-span-2" :class="truncateText" title="Disk">Disk</th>
								<th class="py-2 col-span-1" :class="truncateText" title="State">State</th>
								<th class="py-2 col-span-1" :class="truncateText" title="Type">Type</th>
								<th class="py-2 col-span-1" :class="truncateText" title="Temperature">Temperature</th>
								<th class="py-2 col-span-1" :class="truncateText" title="Capacity">Capacity</th>
								<th class="py-2 col-span-2" :class="truncateText" title="Message">Message</th>
								<th class="relative py-2 pl-3 pr-4 sm:pr-6 lg:pr-8 col-span-1">
									<span class="sr-only"></span>
								</th>
							</tr>
						</thead>
					</table>
					<div v-for="disk, diskIdx in props.vDev.disks" :key="diskIdx" class="">
						<DiskElement :pool="poolData[props.poolIdx]" :poolIdx="props.poolIdx" :vDev="props.vDev"
							:vDevIdx="props.vDevIdx" :disk="disk" :diskIdx="diskIdx" ref="diskElement" />
					</div>
				</DisclosurePanel>
			</Disclosure>
		</div>
	</div>
	<div v-if="showAttachDiskModal">
		<component :is="showAttachDiskComponent" :showFlag="showAttachDiskModal" @close="updateShowAttachDisk"
			:idKey="'show-attach-disk-modal'" :pool="selectedPool!" :vDev="selectedVDev!" />
	</div>

	<div v-if="showRemoveVDevConfirm">
		<component :is="showRemoveVDevComponent" :showFlag="showRemoveVDevConfirm" @close="updateShowRemoveVDev"
			:idKey="'confirm-remove-vdev'" :item="'vdev'" :operation="'remove'" :pool="selectedPool!"
			:vdev="selectedVDev!" :confirmOperation="confirmThisRemove" :hasChildren="false" />
	</div>

</template>
<script setup lang="ts">
import { ref, inject, Ref, watch, provide, onMounted } from "vue";
import { EllipsisVerticalIcon, ChevronUpIcon } from '@heroicons/vue/24/outline';
import { Menu, MenuButton, MenuItem, MenuItems, Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue';
import { clearErrors, removeVDevFromPool, setRefreservation } from "../../composables/pools";
import { loadDatasets, loadDisksThenPools, loadScanObjectGroup, loadDiskStats } from '../../composables/loadData';
import { formatStatus, loadScanActivities, loadTrimActivities, upperCaseWord,  } from '../../composables/helpers';
import DiskElement from '../pools/DiskElement.vue';
import { ZPool, VDev, VDevDisk, ZFSFileSystemInfo } from "@45drives/houston-common-lib";
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { Activity, PoolScanObjectGroup, PoolDiskStats, ConfirmationCallback } from "../../types";


interface VDevElementProps {
	pool: ZPool;
	poolIdx: number;
	vDev: VDev;
	vDevIdx: number;
}

const props = defineProps<VDevElementProps>();
const truncateText = inject<Ref<string>>('style-truncate-text')!;
const canDestructive = inject<Ref<boolean>>('can-destructive')!;

const selectedPool = ref<ZPool>();
const selectedVDev = ref<VDev>();

const operationRunning = ref(false);


/////////////// Loading/Refreshing //////////////////
/////////////////////////////////////////////////////
const poolData = inject<Ref<ZPool[]>>("pools")!;
const diskData = inject<Ref<VDevDisk[]>>("disks")!;
const filesystemData = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;

async function refreshAllData() {
	disksLoaded.value = false;
	poolsLoaded.value = false;
	fileSystemsLoaded.value = false;
	diskData.value = [];
	poolData.value = [];
	filesystemData.value = [];
	await loadDisksThenPools(diskData, poolData);
	await loadDatasets(filesystemData);
	await loadScanObjectGroup(scanObjectGroup);
	await loadScanActivities(poolData, scanActivities);
	await loadDiskStats(poolDiskStats);
	await loadTrimActivities(poolData, trimActivities);
	disksLoaded.value = true;
	poolsLoaded.value = true;
	fileSystemsLoaded.value = true;
	// console.log('VDevElement trimActivities', trimActivities.value);
}

/////////////////// Clear Errors ////////////////////
/////////////////////////////////////////////////////
// const cleared = ref(false);

async function clearVDevErrors(poolName, vDevName) {
	// cleared.value = false;
	await clearErrors(poolName, vDevName);
	// cleared.value = true;
}


/////////////////// Remove VDev /////////////////////
/////////////////////////////////////////////////////
const showRemoveVDevConfirm = ref(false);
const confirmRemove = ref(false);

const showRemoveVDevComponent = ref();
const loadShowRemoveVDevComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	showRemoveVDevComponent.value = module.default;
}

async function removeVDev(pool: ZPool, vDev : VDev) {
	selectedPool.value = pool;
	selectedVDev.value = vDev;
	await loadShowRemoveVDevComponent();
	showRemoveVDevConfirm.value = true;

	// console.log('preparing to remove:', selectedVDev.value, 'from pool:', selectedPool.value);
}

const confirmThisRemove : ConfirmationCallback = () => {
	confirmRemove.value = true;
}

const updateShowRemoveVDev = (newVal) => {
	showRemoveVDevConfirm.value = newVal;
}

watch(confirmRemove, async (newValue, oldValue) => {
	if (confirmRemove.value == true) {
		operationRunning.value = true;
		console.log('now removing:', selectedVDev.value, 'from pool:', selectedPool.value);

		try {
			const output: any = await removeVDevFromPool(selectedVDev.value, selectedPool.value);
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				pushNotification(new Notification('Remove Failed', `Failed to remove Virtual Device: ${errorMessage}`, 'error', 5000));


			} else {
				pushNotification(new Notification('Remove Completed', `Removed VDev ${selectedVDev.value!.name} from Pool ${selectedPool.value!.name}`, 'success', 5000));


				if (props.pool.properties.refreservationRawSize!) {
					const output: any = await setRefreservation(props.pool, props.pool.properties.refreservationPercent!);
					if (output == null || output.error) {
						const errorMessage = output?.error || 'Unknown error';
						pushNotification(new Notification('Refreservation Update Failed', `Error updating refreservation: ${errorMessage}`, 'error', 5000));

					} else {
						pushNotification(new Notification('Refreservation Updated', `Refreservation of pool was updated successfully.`, 'success', 5000));

						showRemoveVDevConfirm.value = false;
					}
				} else {
					showRemoveVDevConfirm.value = false;
				}
				
				confirmRemove.value = false;
				showRemoveVDevConfirm.value = false;
			}

			confirmRemove.value = false;
			await refreshAllData();

		} catch (error) {
			console.error(error);
		}

		await refreshAllData();
	
		operationRunning.value = false;
	}
});

/////////////////// Attach Disk /////////////////////
/////////////////////////////////////////////////////
const showAttachDiskModal = ref(false);

const showAttachDiskComponent = ref();
const loadShowAttachDiskComponent = async () => {
	const module = await import('../disks/AttachDiskModal.vue');
	showAttachDiskComponent.value = module.default;
}

const updateShowAttachDisk = (newVal) => {
	showAttachDiskModal.value = newVal;
}

async function showAttachDisk(pool: ZPool, vdev: VDev) {
	selectedPool.value = pool;
	selectedVDev.value = vdev;
	// console.log('selectedPool:', selectedPool, 'selectedVDev:', selectedVDev)
	await loadShowAttachDiskComponent();
	showAttachDiskModal.value = true;
}

//////////// Checking Disk Stats (Trim) /////////////
/////////////////////////////////////////////////////
const diskElement = ref();

async function getDiskStatus() {
	// console.log('diskElement', diskElement.value);

	// Needed to specify index to work properly (treating as an array due to multiple pools error)
	await diskElement.value[0].getDiskTrimStatus();
}

/////////////////////////////////////////////////////
defineExpose({
    getDiskStatus,
});

provide('show-attach-modal', showAttachDiskModal);
provide('modal-confirm-running', operationRunning);
</script>