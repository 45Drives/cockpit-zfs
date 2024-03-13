<template>
	<div>
		<!-- POOLS -->
		<div v-if="props.item == 'pool'" class="inline-block min-w-full max-h-max align-middle border border-default border-collapse">
			<tr v-if="snapshots.length < 1 && snapshotsLoaded" class="grid grid-cols-1 items-center justify-center w-full">
				<p class="bg-accent text-default text-center py-2 justify-self-center w-full">No snapshots found.</p>
			</tr>
			<table class="table-auto min-w-full min-h-full divide-y divide-default">
				<thead class="bg-well border-collapse">
					<tr v-if="snapshots.length > 0 && snapshotsLoaded" class="rounded-md grid grid-cols-7 font-semibold text-white">
						<!-- <th class="relative py-2 rounded-tl-md col-span-1">
							<span class="sr-only"></span>
						</th> -->
						<th class="py-2 col-span-2 text-center" :class="truncateText" title="Snapshot">Snapshot</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Created On">Created On</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Used">Used</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Referenced">Referenced</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Clones">Clones</th>
						<th class="relative py-2 sm:pr-6 lg:pr-8 rounded-tr-md col-span-1">
							<span class="sr-only"></span>
						</th>
					</tr>
					<tr v-if="!snapshotsLoaded && snapshotsLoading" class="rounded-md flex bg-well justify-center justify-self-center w-full">
						<LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'"/>
					</tr>
				</thead>
				<tbody class="divide-y divide-default bg-default border-collapse">
					<!-- <tr v-if="snapshots.length < 1 && snapshotsLoaded"  class="grid grid-cols-1 items-center justify-center rounded-md justify-self-center w-full">
						<p class="bg-well text-muted text-center py-2 justify-self-center w-full">No snapshots found.</p>
					</tr> -->
					<tr v-if="snapshots.length > 0 && snapshotsLoaded" v-for="snapshot, snapshotIdx in snapshots" :key="snapshotIdx" class="text-default grid grid-cols-7 justify-center items-center">
						<!-- <td class="relative py-2 col-span-1">
							<span class="sr-only"></span>
						</td> -->
						<td class="py-1 px-3 text-sm font-medium text-default text-left col-span-2" :class="truncateText" :title="snapshot.name"> 
							{{ snapshot.name }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.creation.parsed">
							{{ snapshot.properties.creation.parsed }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.used.value">
							{{ snapshot.properties.used.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.referenced.value">
							{{ snapshot.properties.referenced.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.clones">
							{{ snapshot.properties.clones.length > 0 ? snapshot.properties.clones : '-' }}
						</td>
						<td class="relative py-1 pl-3 pr-4 text-right text-sm font-medium sm:pr-6 lg:pr-8 col-span-1 justify-self-end"> 
							<Menu as="div" class="relative inline-block text-right">
								<div>
									<MenuButton class="flex items-center rounded-full bg-default p-2 text-default hover:text-default focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100">
										<span class="sr-only">Open options</span>
										<EllipsisVerticalIcon class="w-5" aria-hidden="true" />
									</MenuButton>
								</div>

								<transition enter-active-class="transition ease-out duration-100" enter-from-class="transform opacity-0 scale-95" enter-to-class="transform opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="transform opacity-100 scale-100" leave-to-class="transform opacity-0 scale-95">
									<MenuItems @click.stop class="absolute right-0 z-10 mt-2 w-max origin-top-left rounded-md bg-accent shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
										<div class="py-1">
											<!-- <MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="cloneThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Clone Snapshot</a>
											</MenuItem> -->
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="renameThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Rename Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="rollbackThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Roll Back Snapshot</a>
											</MenuItem>
											<!-- <MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="sendThisDataset(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Send Snapshot</a>
											</MenuItem> -->
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="destroyThisSnapshot(snapshot)" :class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Destroy Snapshot</a>
											</MenuItem>
										</div>
									</MenuItems>
								</transition>
							</Menu>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- FILESYSTEMS -->
		<div v-if="props.item == 'filesystem'" class="inline-block min-w-full max-h-max align-middle border-collapse">
			<table class="table-auto min-w-full min-h-full divide-y divide-default">
				<thead class="bg-secondary border-collapse">
					<tr v-if="snapshotsInFilesystem.length > 0 && snapshotsLoaded" class="rounded-md grid grid-cols-7 font-semibold text-white">
						<!-- <th class="relative py-2 rounded-tl-md col-span-1">
							<span class="sr-only"></span>
						</th> -->
						<th class="py-2 col-span-2 text-center" :class="truncateText" title="Snapshot">Snapshot</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Created On">Created On</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Used">Used</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Referenced">Referenced</th>
						<th class="py-2 col-span-1 text-center" :class="truncateText" title="Clones">Clones</th>
						<th class="relative py-2 sm:pr-6 lg:pr-8 rounded-tr-md col-span-1">
							<span class="sr-only"></span>
						</th>
					</tr>
					<tr v-if="!snapshotsLoaded && snapshotsLoading" class="rounded-md flex bg-well justify-center">
						<LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'"/>
					</tr>
				</thead>
				<tbody class="divide-y divide-default bg-accent border-collapse">
					<tr v-if="snapshotsInFilesystem.length < 1 && snapshotsLoaded" class="grid grid-cols-1 items-center justify-center">
						<p class="bg-well text-muted text-center py-2 justify-self-center w-full">No snapshots found.</p>
					</tr>
					<tr v-if="snapshotsInFilesystem.length > 0 && snapshotsLoaded" v-for="snapshot, snapshotIdx in snapshotsInFilesystem" :key="snapshotIdx" class="text-default grid grid-cols-7 justify-center items-center">
						<!-- <td class="relative py-2 col-span-1">
							<span class="sr-only"></span>
						</td> -->
						<td class="py-1 px-3 text-sm font-medium text-default text-left col-span-2" :class="truncateText" :title="snapshot.name"> 
							{{ snapshot.name }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.creation.parsed">
							{{ snapshot.properties.creation.parsed }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.used.value">
							{{ snapshot.properties.used.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.referenced.value">
							{{ snapshot.properties.referenced.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="snapshot.properties.clones">
							{{ snapshot.properties.clones.length > 0 ? snapshot.properties.clones : '-' }}
						</td>
						<td class="relative py-1 pl-3 pr-4 text-right text-sm font-medium sm:pr-6 lg:pr-8 col-span-1 justify-self-end"> 
							<Menu as="div" class="relative inline-block text-right">
								<div>
									<MenuButton class="flex items-center rounded-full bg-accent p-2 text-muted hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100">
										<span class="sr-only">Open options</span>
										<EllipsisVerticalIcon class="w-5" aria-hidden="true" />
									</MenuButton>
								</div>

								<transition enter-active-class="transition ease-out duration-100" enter-from-class="transform opacity-0 scale-95" enter-to-class="transform opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="transform opacity-100 scale-100" leave-to-class="transform opacity-0 scale-95">
									<MenuItems class="absolute right-0 z-10 mt-2 w-max origin-top-left rounded-md bg-accent shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
										<div class="py-1">
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="cloneThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Clone Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="renameThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Rename Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="rollbackThisSnapshot(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Roll Back Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="sendThisDataset(snapshot)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Send Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="destroyThisSnapshot(snapshot)" :class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Destroy Snapshot</a>
											</MenuItem>
										</div>
									</MenuItems>
								</transition>
							</Menu>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- Single Snap -->
		<!-- <div v-if="props.item == 'singleSnap'" class="inline-block min-w-full max-h-max align-middle border-collapse">
			<table class="table-auto min-w-full min-h-full divide-y divide-default">
				<tbody class="divide-y divide-default bg-accent border-collapse">
					<tr v-if="!snapshotsLoaded && snapshotsLoading" class="rounded-md flex bg-well justify-center">
						<LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'"/>
					</tr>
					<tr v-if="snapshotsLoaded" class="text-default grid grid-cols-6 justify-center items-center">
						<td class="py-1 px-3 text-sm text-default text-center col-span-2" :class="truncateText" :title="props.singleSnap!.properties.creation.parsed">
							Created On {{ props.singleSnap!.properties.creation.parsed }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="props.singleSnap!.properties.used.value">
							Used - {{ props.singleSnap!.properties.used.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="props.singleSnap!.properties.referenced.value">
							Referenced - {{ props.singleSnap!.properties.referenced.value }}
						</td>
						<td class="py-1 px-3 text-sm text-default text-center col-span-1" :class="truncateText" :title="props.singleSnap!.properties.clones">
							Clones - {{ props.singleSnap!.properties.clones.length > 0 ? props.singleSnap!.properties.clones : '0' }}
						</td>
						<td class="relative py-1 pl-3 pr-4 text-right text-sm font-medium sm:pr-6 lg:pr-8 col-span-1 justify-self-end"> 
							<Menu as="div" class="relative inline-block text-right">
								<div>
									<MenuButton class="flex items-center rounded-full bg-accent p-2 text-muted hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100">
										<span class="sr-only">Open options</span>
										<EllipsisVerticalIcon class="w-5" aria-hidden="true" />
									</MenuButton>
								</div>

								<transition enter-active-class="transition ease-out duration-100" enter-from-class="transform opacity-0 scale-95" enter-to-class="transform opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="transform opacity-100 scale-100" leave-to-class="transform opacity-0 scale-95">
									<MenuItems class="absolute right-0 z-10 mt-2 w-max origin-top-left rounded-md bg-accent shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
										<div class="py-1">
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="cloneThisSnapshot(props.singleSnap!)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Clone Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="renameThisSnapshot(props.singleSnap!)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Rename Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="rollbackThisSnapshot(props.singleSnap!)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Roll Back Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="sendThisDataset(props.singleSnap!)" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Send Snapshot</a>
											</MenuItem>
											<MenuItem as="div" v-slot="{ active }">
												<a href="#" @click="destroyThisSnapshot(props.singleSnap!)" :class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Destroy Snapshot</a>
											</MenuItem>
										</div>
									</MenuItems>
								</transition>
							</Menu>
						</td>
					</tr>
				</tbody>
			</table>
		</div> -->
	
		<div v-if="showDestroySnapshotModal">
			<component :is="destroySnapshotComponent" :showFlag="showDestroySnapshotModal" @close="updateShowDestroySnapshot" :idKey="'confirm-destroy-snapshot'" :item="'snapshot'" :operation="'destroy'" :snapshot="selectedSnapshot!" :confirmOperation="confirmThisDestroy" :firstOption="'Destroy child snapshots with same name'" :secondOption="'Force Destroy ALL child datasets'" :hasChildren="hasChildren"/>
		</div>

		<div v-if="showCloneSnapshotModal">
			<component :is="cloneSnapshotComponent" @close="updateShowCloneSnapshot" :idKey="'clone-snapshot-modal'" :snapshot="selectedSnapshot!"/>
		</div>

		<div v-if="showRenameSnapshotModal">
			<component :is="renameSnapshotComponent" @close="updateShowRenameSnapshot" :idKey="'rename-snapshot-modal'" :snapshot="selectedSnapshot!"/>
		</div>

		<div v-if="showRollbackSnapshotModal">
			<component :is="rollbackSnapshotComponent" :showFlag="showRollbackSnapshotModal" @close="updateShowRollbackSnapshot" :idKey="'confirm-rollback-snapshot'" :item="'snapshot'" :operation="'rollback'" :snapshot="selectedSnapshot!" :confirmOperation="confirmThisRollback" :firstOption="'Destroy all newer snapshots of file system'" :secondOption="'Force Destroy ALL newer datasets'" :hasChildren="hasChildren"/>
		</div>

		<div v-if="showSendSnapshot">
			<component :is="sendSnapshotComponent" @close="updateShowSendSnapshot" idKey="'show-send-snapshot-modal'" :snapshot="selectedSnapshot!" :name="selectedSnapshot!.name" />
		</div>

	</div>

</template>
<script setup lang="ts">
import { ref, inject, Ref, provide, watch, onMounted } from 'vue';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue';
import { EllipsisVerticalIcon } from '@heroicons/vue/24/outline';
import { loadSnapshots, loadSnapshotsInPool, loadSnapshotsInDataset, loadDatasets } from '../../composables/loadData';
import { destroySnapshot, rollbackSnapshot } from '../../composables/snapshots';
import LoadingSpinner from '../common/LoadingSpinner.vue';

const notifications = inject<Ref<any>>('notifications')!;

interface SnapshotsListProps {
	pool?: PoolData;
	filesystem?: FileSystemData;
	singleSnap?: Snapshot;
	item: 'pool' | 'filesystem' | 'singleSnap';
}

const props = defineProps<SnapshotsListProps>();
const truncateText = inject<Ref<string>>('style-truncate-text')!;

////////////////// Loading Data /////////////////////
/////////////////////////////////////////////////////
const datasets = inject<Ref<FileSystemData[]>>('datasets')!;
const datasetsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const pools = inject<Ref<PoolData[]>>('pools')!;
// const snapshotsLoaded = inject<Ref<boolean>>('snapshots-loaded')!;
const snapshotsLoaded = ref(false);
const snapshotsLoading = ref(false);
const snapshots = inject<Ref<Snapshot[]>>('snapshots')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const snapshotsInFilesystem = ref<Snapshot[]>([]);
const selectedSnapshot = ref<Snapshot>();
const allDatasets = ref<any>([]);
const allDatasetsLoaded = ref(false);

onMounted(() => {
	refreshSnaps();
});

async function refreshSnaps() {
	snapshotsLoaded.value = false;
	snapshotsLoading.value = true;
	if (props.item == 'pool') {
		snapshots.value = [];
		await loadSnapshotsInPool(snapshots, props.pool!.name);
	} else if (props.item == 'filesystem') {
		snapshotsInFilesystem.value = [];
		await loadSnapshotsInDataset(snapshotsInFilesystem, props.filesystem!.name);
	} else if (props.item == 'singleSnap') {
		selectedSnapshot.value = snapshots.value.find(snapshot => snapshot.name == props.singleSnap!.name);
	}
	snapshotsLoaded.value = true;
	snapshotsLoading.value = false;
}

///////// Values for Confirmation Modals ////////////
/////////////////////////////////////////////////////
const operationRunning = ref(false);
const firstOptionToggle = ref(false);
const secondOptionToggle = ref(false);
const thirdOptionToggle = ref(false);
const fourthOptionToggle = ref(false);

///////////////// Destroy Snapshot //////////////////
/////////////////////////////////////////////////////
const showDestroySnapshotModal = ref(false);
const hasChildren = ref(false);
// const confirmDestroy = ref(false);
const confirmDestroy = inject<Ref<boolean>>('confirm-destroy-snap')!;

const destroySnapshotComponent = ref();
const loadDestroySnapshotComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	destroySnapshotComponent.value = module.default;
}

async function destroyThisSnapshot(snapshot) {
	operationRunning.value = false;
	selectedSnapshot.value = snapshot;
	
	if (selectedSnapshot.value!.properties.clones.length > 0) {
		hasChildren.value = true;
	}

	await loadDestroySnapshotComponent();
	showDestroySnapshotModal.value = true;
	console.log('selected for destroy:', selectedSnapshot.value);
}

const confirmThisDestroy : ConfirmationCallback = () => {
	confirmDestroy.value = true;
}

const updateShowDestroySnapshot = (newVal) => {
	showDestroySnapshotModal.value = newVal;
}

watch (confirmDestroy, async (newVal, oldVal) => {
	if (confirmDestroy.value == true) {
		operationRunning.value = true;
		console.log('now destroying:', newVal);

		try {
			const output = await destroySnapshot(selectedSnapshot.value, firstOptionToggle.value, secondOptionToggle.value);

			if (output == null) {
				operationRunning.value = false;
				confirmDestroy.value = false;
				notifications.value.constructNotification('Destroy Snapshot Failed', selectedSnapshot.value!.name + " was not destroyed. Check console output for details.", 'error');
				// showDeletePoolConfirm.value = false;
			} else {
				notifications.value.constructNotification('Snapshot Destroyed', `${selectedSnapshot.value!.name} destroyed.`, 'success');
				await refreshSnaps();
				confirmDestroy.value = false;
				operationRunning.value = false;
				hasChildren.value = false;
				console.log('destroyed:', selectedSnapshot.value);
				firstOptionToggle.value = false;
				secondOptionToggle.value = false;
				showDestroySnapshotModal.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

////////////////// Clone Snapshot ///////////////////
/////////////////////////////////////////////////////
const showCloneSnapshotModal = ref(false);
const cloning = ref(false);
const confirmCloneSnap = inject<Ref<boolean>>('confirm-clone-snap')!;

const cloneSnapshotComponent = ref();
const loadCloneSnapshotComponent = async () => {
	const module = await import('./CloneSnapshot.vue');
	cloneSnapshotComponent.value = module.default;
}

async function cloneThisSnapshot(snapshot) {
	selectedSnapshot.value = snapshot;
	console.log('clone snapshot modal triggered');
	await loadCloneSnapshotComponent();
	showCloneSnapshotModal.value = true;
}

const updateShowCloneSnapshot = (newVal) => {
	showCloneSnapshotModal.value = newVal;
}

watch(confirmCloneSnap, async (newVal, oldVal) => {
	if (confirmCloneSnap.value == true) {
		operationRunning.value = true;
		await refreshSnaps();
		confirmCloneSnap.value = false;
		operationRunning.value = false;
		// notifications.value.constructNotification('Snapshot Cloned', `Cloned snapshot ${selectedSnapshot.value!.name} .`, 'success');
	}
});

/////////////// Rollback Snapshot ///////////////////
/////////////////////////////////////////////////////
const showRollbackSnapshotModal = ref(false);
const confirmRollback = ref(false);

const rollbackSnapshotComponent = ref();
const loadRollbackSnapshotComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	rollbackSnapshotComponent.value = module.default;
}

async function rollbackThisSnapshot(snapshot) {
	selectedSnapshot.value = snapshot;
	console.log('selected to be rolled back:', selectedSnapshot.value);
	await loadRollbackSnapshotComponent();
	showRollbackSnapshotModal.value = true;
}

const confirmThisRollback : ConfirmationCallback = () => {
	confirmRollback.value = true;
}

const updateShowRollbackSnapshot = (newVal) => {
	showRollbackSnapshotModal.value = newVal;
}

watch(confirmRollback, async (newVal, oldVal) => {
	if (confirmRollback.value == true) {
		operationRunning.value = true;

		try {
			const output = await rollbackSnapshot(selectedSnapshot.value, firstOptionToggle.value, secondOptionToggle.value);

			if (output == null) {
				operationRunning.value = false;
				confirmRollback.value = false;
				notifications.value.constructNotification('Rollback Snapshot Failed', selectedSnapshot.value!.name + " was not rolled back. Check console output for details.", 'error');
			} else {
				console.log('rolled back:', selectedSnapshot.value);
				await refreshSnaps();
				confirmRollback.value = false;
				operationRunning.value = false;
				notifications.value.constructNotification('Snapshot Rolled Back', `Rolled back to snapshot ${selectedSnapshot.value!.name} .`, 'success');
				showRollbackSnapshotModal.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

///////////////// Rename Snapshot ///////////////////
/////////////////////////////////////////////////////
const showRenameSnapshotModal = ref(false);
const renaming = ref(false);
const confirmRename = ref(false);

const renameSnapshotComponent = ref();
const loadRenameSnapshotComponent = async () => {
	const module = await import('./RenameSnapshot.vue');
	renameSnapshotComponent.value = module.default;
}

async function renameThisSnapshot(snapshot) {
	selectedSnapshot.value = snapshot;
	console.log('rename snapshot modal triggered');
	await loadRenameSnapshotComponent();
	showRenameSnapshotModal.value = true;
}

const updateShowRenameSnapshot = (newVal) => {
	showRenameSnapshotModal.value = newVal;
}

watch(confirmRename, async (newVal, oldVal) => {
	if (confirmRename.value == true) {
		operationRunning.value = true;
		await refreshSnaps();
		confirmRename.value = false;
		operationRunning.value = false;
	}
});

/////////////////// Send Snapshot ///////////////////
/////////////////////////////////////////////////////
const showSendSnapshot = ref(false);
const sendingSnap = ref(false);
// const confirmSendSnap = ref(false);
const confirmSendSnap = inject<Ref<boolean>>('confirm-send-snap')!;

const sendSnapshotComponent = ref();
const loadSendSnapshotComponent = async () => {
	const module = await import('./SendSnapshot.vue');
	sendSnapshotComponent.value = module.default;
}

async function sendThisDataset(snapshot) {
	selectedSnapshot.value = snapshot;
	confirmSendSnap.value = false;
	console.log('selected to send:', selectedSnapshot.value);
	await loadSendSnapshotComponent();
	showSendSnapshot.value = true;
}

const updateShowSendSnapshot = (newVal) => {
	showSendSnapshot.value = newVal;
}

watch(confirmSendSnap, async (newVal, oldVal) => {
	if (confirmSendSnap.value == true) {
		// await refreshData();
		await refreshSnaps();
		// notifications.value.constructNotification('Snapshot Sent', `Sent snapshot ${selectedSnapshot.value!.name}.`, 'success');
	} else {
		// notifications.value.constructNotification('Failed Snapshot Send', `Failed to send snapshot ${selectedSnapshot.value!.name}.`, 'error');
	}
});

// provide('snapshots-loaded', snapshotsLoaded)!;
provide('cloning', cloning);
// provide('confirm-clone', confirmClone);
provide('show-clone-modal', showCloneSnapshotModal);
provide('renaming', renaming);
provide('confirm-rename', confirmRename);
provide('show-rename-snap-modal', showRenameSnapshotModal);

provide('show-send-dataset', showSendSnapshot);
provide('sending', sendingSnap);
// provide('confirm-send', confirmSendSnap);

provide('modal-confirm-running', operationRunning);
provide('modal-option-one-toggle', firstOptionToggle);
provide('modal-option-two-toggle', secondOptionToggle);
provide('modal-option-three-toggle', thirdOptionToggle);
provide('modal-option-four-toggle', fourthOptionToggle);
</script>