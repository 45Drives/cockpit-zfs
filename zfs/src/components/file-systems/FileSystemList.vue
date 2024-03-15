<template>
	<div class="inline-block min-w-full min-h-full py-4 align-middle sm:px-4 lg:px-6 overflow-visible sm:rounded-lg bg-accent rounded-md border border-default">	
		<div class="flex bg-well justify-between rounded-md p-2 shadow text-default rounded-b-md ring-1 ring-black ring-opacity-5">
			<div class="button-group-row justify-start">
				<button id="createFS" class="btn btn-primary object-left justify-start" @click="newFileSystemWizard()">Create File System</button>
			</div>
			<div class="button-group-row justify-end">
				<button id="refreshFS" class="btn btn-secondary object-right justify-self-end" @click="refreshData()"><ArrowPathIcon class="w-5 h-5 m-1"/></button>
			</div>
		</div>

		<div class="mt-4 overflow-visible rounded-md max-w-full">
			<div class="inline-block min-w-full min-h-full shadow align-middle rounded-md border border-default">
				<div class="overflow-visible ring-1 ring-black ring-opacity-5 rounded-md">

					<table class="min-w-full divide-y divide-default rounded-md">
						<thead class="rounded-md">
							<tr class="bg-well rounded-t-md grid grid-cols-12">
								<!-- <tr class="bg-well rounded-t-md grid grid-cols-11"> -->
								<th class="relative py-2 rounded-tl-md col-span-1">
									<span class="sr-only"></span>
								</th>
								<th class="py-2 font-semibold text-left text-default col-span-2" :class="truncateText" title="Dataset">Dataset</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Available">Available</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Used">Used</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Refreservation">Refres.</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Compression">Compression</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Deduplication">Dedup.</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Encrypted">Encrypted</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Mounted">Mounted</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Read Only">Read Only</th>
								<th class="relative py-2 sm:pr-6 lg:pr-8 rounded-tr-md col-span-1">
									<span class="sr-only"></span>
								</th>
								
							</tr>
						</thead>

						<tbody class="">
							<tr class="">
								<div v-if="allDatasets.length > 0 && allDatasetsLoaded == true">
									<div v-for="dataset, datasetIdx in allDatasets" :key="dataset.name">

										<div v-if="dataset.type == 'FILESYSTEM'" class="border border-default">
											<Disclosure v-slot="{ open }">
												<DisclosureButton class="bg-default grid grid-cols-12 grid-flow-cols w-full justify-center text-center">
													<div class="py-1 mt-1 mr-2 col-span-1 ml-4 justify-self-start" :title="dataset.name">
														<ChevronUpIcon
															class="-mt-2 h-10 w-10 text-default transition-all duration-200 transform" :class="{ 'rotate-90': !open, 'rotate-180': open, }"
														/> 
													</div>
													<div class="py-1 mt-1 col-span-2 text-left" :class="[truncateText, `ml-${getNestingLevel(dataset)}`]" :title="dataset.name">{{ dataset.name }}</div>
													<div class="py-1 mt-1 col-span-1" :class="truncateText" :title="convertBytesToSize(dataset.properties.available) ? convertBytesToSize(dataset.properties.available) : 'N/A'">{{ convertBytesToSize(dataset.properties.available) ? convertBytesToSize(dataset.properties.available) : 'N/A' }}</div>
													<div class="py-1 mt-1 col-span-1" :class="truncateText" :title="dataset.properties.usedByDataset">{{ dataset.properties.usedByDataset }}</div>
													<div class="py-1 mt-1 col-span-1" :class="truncateText" :title="dataset.properties.usedbyRefreservation ? dataset.properties.usedbyRefreservation : 'N/A'">{{ dataset.properties.usedbyRefreservation ? dataset.properties.usedbyRefreservation : 'N/A' }}</div>
													<div v-if="dataset.properties.compression == 'off' || dataset.properties.compression == 'on'" class="py-1 mt-1 col-span-1" :class="truncateText" :title="upperCaseWord(dataset.properties.compression) ? upperCaseWord(dataset.properties.compression) : 'N/A'">{{ upperCaseWord(dataset.properties.compression) ? upperCaseWord(dataset.properties.compression) : 'N/A' }}</div>
													<div v-else class="py-1 mt-1 col-span-1" :class="truncateText" :title="upperCaseWord(dataset.properties.compression).toUpperCase() ? upperCaseWord(dataset.properties.compression).toUpperCase() : 'N/A'">{{ dataset.properties.compression.toUpperCase() ? dataset.properties.compression.toUpperCase() : 'N/A' }}</div>
													<div class="py-1 mt-1 col-span-1" :class="truncateText" :title="getValue('dedup', dataset.properties.deduplication) ? getValue('dedup', dataset.properties.deduplication) : 'N/A'">{{ getValue('dedup', dataset.properties.deduplication) ? getValue('dedup', dataset.properties.deduplication) : 'N/A' }}</div>
												
													<div v-if="dataset.encrypted && dataset.key_loaded" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Encrypted & Unlocked">
														<LockOpenIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>
													<div v-if="dataset.encrypted && !dataset.key_loaded" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Encrypted & Locked">
														<LockClosedIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>
													<div v-if="!dataset.encrypted" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Not Encrypted">
														<NoSymbolIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>

													<div v-if="yesNoToBool(dataset.properties.mounted)" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Mounted">
														<CheckIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>
													<div v-if="!yesNoToBool(dataset.properties.mounted)" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Not Mounted">
														<NoSymbolIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>

													<div v-if="dataset.properties.isReadOnly!" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Read Only ON">
														<CheckIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>
													<div v-if="!dataset.properties.isReadOnly!" class="py-1 mt-1 col-span-1 justify-self-center items-center text-center" title="Read Only OFF">
														<NoSymbolIcon class="w-5 mt-0.5" aria-hidden="true"/>
													</div>

													<div class="relative py-1 mt-1 p-3 text-right font-medium sm:pr-6 lg:pr-8">
														<Menu as="div" class="relative inline-block text-right -mt-1">
															<div>		
																<MenuButton class="flex items-center rounded-full bg-default p-2 text-default hover:text-default focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-gray-100">
																	<span class="sr-only">Open options</span>
																	<EllipsisVerticalIcon class="w-5" aria-hidden="true" />
																</MenuButton>
															</div>

															<transition enter-active-class="transition ease-out duration-100" enter-from-class="transform opacity-0 scale-95" enter-to-class="transform opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="transform opacity-100 scale-100" leave-to-class="transform opacity-0 scale-95">
																<MenuItems @click.stop class="absolute right-0 z-10 w-56 origin-top-right rounded-md bg-accent shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
																	<div class="py-1">
																		<MenuItem as="div" v-slot="{ active }">
																			<a href="#" @click="loadFileSystemConfig(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Configure File System</a>
																		</MenuItem>
																		<MenuItem as="div" v-if="!findPoolDataset(allDatasets[datasetIdx])" v-slot="{ active }">
																			<a href="#" @click="renameThisDataset(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Rename File System</a>
																		</MenuItem>
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].properties.mounted == 'yes'" v-slot="{ active }">
																			<a href="#" @click="unmountThisFileSystem(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Unmount File System</a>
																		</MenuItem>														
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].properties.mounted == 'no' && !allDatasets[datasetIdx].encrypted" v-slot="{ active }">
																			<a href="#" @click="mountThisFileSystem(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Mount File System</a>
																		</MenuItem>
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].properties.mounted == 'no' && allDatasets[datasetIdx].encrypted && allDatasets[datasetIdx].key_loaded" v-slot="{ active }">
																			<a href="#" @click="mountThisFileSystem(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Mount File System</a>
																		</MenuItem>
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].properties.mounted == 'no' && allDatasets[datasetIdx].encrypted && !allDatasets[datasetIdx].key_loaded" v-slot="{ active }">
																			<a href="#" @click="handleFileSystemEncryption(allDatasets[datasetIdx], 'unlock')" :class="[active ? 'bg-green-600 text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Unlock File System</a>
																		</MenuItem>
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].properties.mounted == 'no' && allDatasets[datasetIdx].encrypted && allDatasets[datasetIdx].key_loaded" v-slot="{ active }">
																			<a href="#" @click="handleFileSystemEncryption(allDatasets[datasetIdx], 'lock')" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Lock File System</a>
																		</MenuItem>	
																		<MenuItem as="div" v-if="allDatasets[datasetIdx].encrypted && allDatasets[datasetIdx].key_loaded" v-slot="{ active }">
																			<a href="#" @click="changeThisPassphrase(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Change Passphrase</a>
																		</MenuItem>
																		<MenuItem as="div" v-slot="{ active }">
																			<a href="#" @click="createSnapshotBtn(allDatasets[datasetIdx])" :class="[active ? 'bg-default text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Create Snapshot</a>
																		</MenuItem>					
																		<MenuItem as="div" v-if="!findPoolDataset(allDatasets[datasetIdx])" v-slot="{ active }">
																			<a href="#" @click="deleteFileSystem(allDatasets[datasetIdx])" :class="[active ? 'bg-danger text-default' : 'text-muted', 'block px-4 py-2 text-sm']">Destroy File System</a>
																		</MenuItem>											
																	</div>
																</MenuItems>
															</transition>
														</Menu>
													</div>
												</DisclosureButton>
												<DisclosurePanel>
													<div>
														<SnapshotsList :filesystem="allDatasets[datasetIdx]" :item="'filesystem'"/>
													</div>
												</DisclosurePanel>
											</Disclosure>
										</div>
										<div v-if="dataset.type == 'SNAPSHOT'" class="border border-default">
											<div class="bg-primary grid grid-cols-12 grid-flow-cols w-full justify-center text-center">
												<div class="py-1 mt-1 mr-2 col-span-1 ml-4 justify-self-start" :title="dataset.name">
													<CameraIcon
														class="-mt-1 mx-2 h-8 w-8 text-muted"
													/>
												</div>
												<div class="py-1 mt-1 col-span-2 text-left text-white" :class="[truncateText, `ml-${getNestingLevel(dataset)}`]" :title="dataset.name">{{ dataset.name }}</div>
												<div class="py-1 mt-1 col-span-1 text-white">N/A</div>
												<div class="py-1 mt-1 col-span-1 text-white" :class="truncateText" :title="convertBytesToSize(dataset.properties.used.parsed)">{{ convertBytesToSize(dataset.properties.used.parsed) }}</div>
												<div class="py-1 mt-1 col-span-1 text-white">N/A</div>
												<div class="py-1 mt-1 col-span-1 text-white">N/A</div>
												<div class="py-1 mt-1 col-span-1 text-white">N/A</div>
												<div v-if="dataset.properties.encryption.value !== 'off' && dataset.properties.keystatus.value == 'available'" class="py-1 mt-1 col-span-1 text-white justify-self-center items-center text-center" title="Encrypted & Unlocked">
													<LockOpenIcon class="w-5 mt-0.5" aria-hidden="true"/>
												</div>
												<div v-if="dataset.properties.encryption.value !== 'off' && dataset.properties.keystatus.value == 'unavailable'" class="py-1 mt-1 col-span-1 text-white justify-self-center items-center text-center" title="Encrypted & Locked">
													<LockClosedIcon class="w-5 mt-0.5" aria-hidden="true"/>
												</div>
												<div v-if="dataset.properties.encryption.value === 'off' && dataset.properties.keystatus.value == ''" class="py-1 mt-1 col-span-1 text-white justify-self-center items-center text-center" title="Not Encrypted">
													<NoSymbolIcon class="w-5 mt-0.5" aria-hidden="true"/>
												</div>
												<div class="py-1 mt-1 col-span-1 text-white justify-self-center items-center text-center">N/A</div>
												<div class="py-1 mt-1 col-span-1 text-white justify-self-center items-center text-center">N/A</div>
												<div class="relative py-1 mt-1 p-3 text-right font-medium sm:pr-6 lg:pr-8"></div>
											</div>
										</div>
									</div>
								</div> 
							</tr>
						</tbody>
					</table>

					<div v-if="fileSystemsLoaded == false" class="p-2 flex justify-center bg-default">
						<LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'" class="font-semibold text-lg my-0.5"/>
					</div>
					<div v-if="fileSystems.length < 1 && fileSystemsLoaded == true" class="p-2 flex bg-default justify-center">
						<span class="font-semibold text-lg my-2">No File Systems Found</span>
					</div>
					
				</div>
			</div>

			<!-- div for dynamic style rendering -->
			<div id="debug" class="hidden">
				<div id="dummy" class="hidden">
					<div class="ml-0"></div>
					<div class="ml-4"></div>
					<div class="ml-8"></div>
					<div class="ml-12"></div>
					<div class="ml-16"></div>
					<div class="ml-20"></div>
					<div class="ml-24"></div>
					<div class="ml-28"></div>
					<div class="ml-32"></div>
					<div class="ml-36"></div>
				</div>
				<!-- <div v-for="dataset in debugNestingLevel" :key="dataset.name" :class="`ml-${dataset.nestingLevel}`">
					{{ dataset.name }} ({{ dataset.type }}) - Nesting Level: {{ dataset.nestingLevel }}
				</div> -->
			</div>
		
		</div>
	</div>

	<div v-if="showNewFSWizard">
		<component :is="newFileSystemComponent" :isStandalone="true" idKey="fs-wizard" @close="showNewFSWizard = false"/> 
	</div>

	<div v-if="showFSConfig">
		<component :is="configFileSystemComponent" ref="fileSystemConfiguration" :filesystem="selectedDataset!" idKey="fs-config" @close="showFSConfig = false"/>
	</div>

	<div v-if="showDeleteFileSystemConfirm">
		<component :is="deleteFileSystemComponent" :showFlag="showDeleteFileSystemConfirm" @close="updateShowDestroyFileSystem" :idKey="'confirm-destroy-filesystem'" :item="'filesystem'" :operation="'destroy'" :filesystem="selectedDataset!" :confirmOperation="confirmThisDestroy" :firstOption="'force unmount'" :hasChildren="hasChildren"/>
	</div>

	<div v-if="showUnmountFileSystemConfirm">
		<component :is="unmountFileSystemComponent" v-if="selectedDataset!.encrypted" :showFlag="showUnmountFileSystemConfirm" @close="updateShowUnmountFileSystem" :idKey="'confirm-unmount-filesystem'" :item="'filesystem'" :operation="'unmount'" :filesystem="selectedDataset!" :confirmOperation="confirmThisUnmount" :firstOption="'force unmount'" :secondOption="'lock file system'" :hasChildren="hasChildren"/>
		<component :is="unmountFileSystemComponent" v-else :showFlag="showUnmountFileSystemConfirm" @close="updateShowUnmountFileSystem" :idKey="'confirm-unmount-filesystem'" :item="'filesystem'" :operation="'unmount'" :filesystem="selectedDataset!" :confirmOperation="confirmThisUnmount" :firstOption="'force unmount'" :hasChildren="hasChildren"/>
	</div>

	<div v-if="showMountFileSystemConfirm">
		<component :is="mountFileSystemComponent" :showFlag="showMountFileSystemConfirm" @close="updateShowMountFileSystem" :idKey="'confirm-mount-filesystem'" :item="'filesystem'" :operation="'mount'" :filesystem="selectedDataset!" :confirmOperation="confirmThisMount" :firstOption="'force mount'" :hasChildren="hasChildren"/>
	</div>

	<div v-if="showLockUnlockModal">
		<component :is="lockUnlockFileSystemComponent" :showFlag="showLockUnlockModal" @close="showLockUnlockModal = false" :idKey="'confirm-lock-or-unlock'" :mode="modeSelected!" :filesystem="selectedDataset!"/>
	</div>

	<div v-if="showRenameModal">
		<component :is="renameFileSystemComponent" :idKey="'show-rename-modal'" :filesystem="selectedDataset!" @close="showRenameModal = false" />
	</div>

	<div v-if="showSnapshotModal">
		<component :is="createSnapshotComponent" :idKey="'show-create-snap-modal'" @close="showSnapshotModal = false" :item="'filesystem'" />
	</div>

	<div v-if="showChangePassphrase">
		<component :is="changePassphraseComponent" :idKey="'show-change-passphrase-modal'" @close="showChangePassphrase = false" :filesystem="selectedDataset!"/>
	</div>
	
</template>

<script setup lang="ts">
import { ref, inject, Ref, provide, watch, onMounted, computed } from "vue";
import { EllipsisVerticalIcon, ArrowPathIcon, ChevronUpIcon, LockClosedIcon, LockOpenIcon, NoSymbolIcon, CheckIcon, } from '@heroicons/vue/24/outline';
import { CameraIcon } from '@heroicons/vue/24/solid'
import { Menu, MenuButton, MenuItem, MenuItems, Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue';
import { loadDatasets, loadSnapshots, loadSnapshotsInDataset } from "../../composables/loadData";
import { getValue, convertBytesToSize, upperCaseWord, yesNoToBool } from '../../composables/helpers';
import { destroyDataset, unmountFileSystem, mountFileSystem, lockFileSystem } from "../../composables/datasets";
import LoadingSpinner from "../common/LoadingSpinner.vue";
import SnapshotsList from "../snapshots/SnapshotsList.vue";

const notifications = inject<Ref<any>>('notifications')!;
const truncateText = inject<Ref<string>>('style-truncate-text')!;

///////// Values for Confirmation Modals ////////////
/////////////////////////////////////////////////////
const operationRunning = ref(false);
const firstOptionToggle = ref(false);
const secondOptionToggle = ref(false);
const thirdOptionToggle = ref(false);
const fourthOptionToggle = ref(false);

/////////////// Loading/Refreshing //////////////////
/////////////////////////////////////////////////////
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const fileSystemConfiguration = ref();
const showNewFSWizard = ref(false);
const showFSConfig = ref(false);

const pools = inject<Ref<PoolData[]>>('pools')!;
const fileSystems = inject<Ref<FileSystemData[]>>('datasets')!;
const selectedDataset = ref<FileSystemData>();
const snapshots = inject<Ref<Snapshot[]>>('snapshots')!;
// const snapshotsInDataset = ref<Snapshot[]>([]);
const snapshotsLoaded = inject<Ref<boolean>>('snapshots-loaded')!;
const allDatasets = ref<any>([]);
const allDatasetsLoaded = ref(false);

async function refreshData() {
	fileSystemsLoaded.value = false;
	snapshotsLoaded.value = false;
	allDatasetsLoaded.value = false;

	fileSystems.value = [];
	snapshots.value = [];
	allDatasets.value = [];

	await loadDatasets(fileSystems);
	await loadSnapshots(snapshots);
	await populateDatasetList();

	fileSystemsLoaded.value = true;
	snapshotsLoaded.value = true;
	allDatasetsLoaded.value = true;
}

///////////////////////////////////////////////////////////
async function populateDatasetList() {
    try {
		// console.log('fileSystems:', fileSystems.value);
		// console.log('snapshots:', snapshots.value);
		const combinedData = ref<any>([]);

		for (const pool of pools.value) {
			// console.log('Pool Name:', pool.name);
            const poolFileSystems = fileSystems.value.filter(filesystem => filesystem.pool === pool.name);
			// console.log('Filtered File Systems:', poolFileSystems);
			const poolSnapshots = snapshots.value.filter(snapshot => snapshot.pool === pool.name);
			// console.log('Filtered Snapshots:', poolSnapshots);
            if (pool.properties.listSnapshots) {
                combinedData.value.push(...poolFileSystems, ...poolSnapshots);
				console.log(`Added datasets & snaps from ${pool.name}`);
            } else {
				combinedData.value.push(...poolFileSystems);
				console.log(`Added only datasets from ${pool.name}`);
			}
        }
	
		// Sort the combined array alphabetically by name
		combinedData.value.sort((a, b) => a.name.localeCompare(b.name));

		combinedData.value.forEach(data => {
			allDatasets.value.push(data);
		});

		console.log('Final allDatasets:', allDatasets.value);

    } catch (error) {
        console.error('Error in populateDatasetList:', error);
    }
}

function getNestingLevel(dataset) {
    let level = 0;

    if (dataset.type === 'SNAPSHOT') {
        // Extract the dataset name from the snapshot's name using regex
        const datasetNameRegex = /^(.+?)@[\w.-]+$/;
        const match = dataset.name.match(datasetNameRegex);
        if (match && match[1]) {
            const datasetName = match[1]; // Extracted dataset name
            // Split the dataset name into parts to calculate the nesting level
            const parts = datasetName.split('/');
            // Each level of hierarchy increases indentation by 4
            level = parts.length * 4;
        }
    } else {
        let currentDataset = dataset;
        // Traverse up the hierarchy until reaching the root node
        while (currentDataset && currentDataset.parentFS !== "") {
            level += 4; // Increase the indentation level by 4 for each level of hierarchy
            currentDataset = findDatasetByName(currentDataset.parentFS); // Move to the parent
        }
    }

    return level;
}

function findDatasetByName(name) {
	return allDatasets.value.find(dataset => dataset.name === name);
}

const debugNestingLevel = computed(() => {
	return allDatasets.value.map(dataset => ({
		name: dataset.name,
		nestingLevel: getNestingLevel(dataset),
		type: dataset.type
	}));
});

onMounted(async () => {
	await refreshData();
});

function findPoolDataset(fileSystem) {
	try {
		return pools.value.find(pool => pool.name == fileSystem.name);
	} catch (error) {
		console.log('error finding pool:', error);
	}
}

function findSnapDataset(fileSystem) {
    try {
        console.log('Searching for snapshot dataset:', fileSystem.name);
        const foundSnapshot = snapshots.value.some(snapshot => {
            console.log('Checking snapshot:', snapshot.dataset);
            return snapshot.dataset === fileSystem.name;
        });
        
        console.log('Snapshot dataset found:', foundSnapshot);
        
        return foundSnapshot;
    } catch (error) {
        console.error('Error finding snapshot:', error);
        return false;
    }
}

// async function refreshDatasetSnaps(filesystem) {
// 	snapshots.value = [];
// 	await loadSnapshotsInDataset(snapshots, filesystem);
// }

///////////////// New File System ///////////////////
/////////////////////////////////////////////////////
const confirmCreateFS = ref(false);
const newFileSystemComponent = ref();
const loadNewFileSystemComponent = async () => {
	const module = await import('../pool-creation-wizard/FileSystem.vue');
	newFileSystemComponent.value = module.default;
}

async function newFileSystemWizard() {
	await loadNewFileSystemComponent();
	showNewFSWizard.value = true;
}

////////////// Configure File System ////////////////
/////////////////////////////////////////////////////
const configFileSystemComponent = ref();
const loadConfigFileSystemComponent = async () => {
	const module = await import('./FileSystemConfigModal.vue');
	configFileSystemComponent.value = module.default;
}

async function loadFileSystemConfig(fileSystem) {
	selectedDataset.value = fileSystem;
	console.log('loading:', selectedDataset);
	await loadConfigFileSystemComponent();
	showFSConfig.value = true
}

///////////////// Create Snapshots //////////////////
/////////////////////////////////////////////////////
const showSnapshotModal = ref(false);
const creating = ref(false);
const confirmCreateSnap = ref(false);

const createSnapshotComponent = ref();
const loadCreateSnapshotComponent = async () => {
	const module = await import('../snapshots/CreateSnapshotModal.vue');
	createSnapshotComponent.value = module.default;
}

async function createSnapshotBtn(filesystem) {
	selectedDataset.value = filesystem;
	await loadCreateSnapshotComponent();
	showSnapshotModal.value = true;
	console.log('create snapshot modal triggered');
}

watch(confirmCreateSnap, async (newVal, oldVal) => {
	if (confirmCreateSnap.value == true) {
		operationRunning.value = true;
		await refreshData();
		// await refreshDatasetSnaps(selectedDataset.value);
		confirmCreateSnap.value = false;
		operationRunning.value = false;
	}
});

////////////// Destroy File System //////////////////
/////////////////////////////////////////////////////
const hasChildren = ref(false);

// const forceDestroy = ref(false);
const destroyChildren = ref(false);
const destroyAllDependents = ref(false);
const showDeleteFileSystemConfirm = ref(false);
const confirmDelete = ref(false);
const confirmDestroySnap = ref(false);

const deleteFileSystemComponent = ref();
const loadDeleteFileSystemComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	deleteFileSystemComponent.value = module.default;
}

async function deleteFileSystem(fileSystem) {
	operationRunning.value = false;
	selectedDataset.value = fileSystem;
	
	const datasetHasChildren = computed(() => {
		if (selectedDataset.value && selectedDataset.value.children) {
			const hasPoolDataset = findPoolDataset(selectedDataset.value);
			const hasSnapDataset = findSnapDataset(selectedDataset.value);
			console.log('hasPoolDataset:', hasPoolDataset);
			console.log('hasSnapDataset:', hasSnapDataset);

			// Check if hasPoolDataset is undefined and assign it false in that case
			const hasPool = typeof hasPoolDataset !== 'undefined' ? hasPoolDataset : false;

			return !hasPool && selectedDataset.value.children.length > 0 || hasSnapDataset;
		}

		return false;
	});
	console.log(`dataset ${selectedDataset.value?.name} HasChildren: ${datasetHasChildren.value}`);
	hasChildren.value = datasetHasChildren.value!;
	// await refreshDatasetSnaps(selectedDataset.value);
	// console.log('snapshots', snapshots.value);
	console.log('hasChildren', hasChildren.value);
	// if (selectedDataset.value) { 
	// 	if ((!findPoolDataset(selectedDataset.value) && selectedDataset.value!.children!.length > 0) || findSnapDataset(selectedDataset.value)) {
	// 		hasChildren.value = true;
	// 	} else {
	// 		hasChildren.value = false;
	// 	}
	// }
	await loadDeleteFileSystemComponent();
	showDeleteFileSystemConfirm.value = true;
	console.log('selected for deletion:', selectedDataset.value);
}

const confirmThisDestroy : ConfirmationCallback = () => {
	confirmDelete.value = true;
}

const updateShowDestroyFileSystem = (newVal) => {
	showDeleteFileSystemConfirm.value = newVal;
}

watch(confirmDelete, async (newValue, oldValue) => {
	if (confirmDelete.value == true) {
		operationRunning.value = true;
		console.log('now deleting:', newValue);

		try {
			const output = await destroyDataset(selectedDataset.value!, firstOptionToggle.value, thirdOptionToggle.value, fourthOptionToggle.value);
			
			if (output == null) {
				operationRunning.value = false;
				notifications.value.constructNotification('Destroy Dataset Failed', selectedDataset.value!.name + " was not destroyed. Check console output for details.", 'error');
				confirmDelete.value = false;
			} else {
				operationRunning.value = false;
			
				console.log('deleted:', selectedDataset.value!);
				firstOptionToggle.value = false;
				thirdOptionToggle.value = false;
				fourthOptionToggle.value = false;
				confirmDelete.value = false;

				// await refreshDatasetSnaps(selectedDataset.value);
				await refreshData();
				
				notifications.value.constructNotification('File System Destroyed', selectedDataset.value!.name + " destroyed.", 'success');
				await refreshData();
				// await refreshDatasetSnaps(selectedDataset.value);
				showDeleteFileSystemConfirm.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

/////////////// Unmount File System /////////////////
/////////////////////////////////////////////////////
const showUnmountFileSystemConfirm = ref(false);
const forceUnmount = ref(false);
// const lockThisFileSystem = ref(secondOptionToggle.value);
const unmounting = ref(false);
const confirmUnmount = ref(false);

const unmountFileSystemComponent = ref();
const loadUnmountFileSystemComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	unmountFileSystemComponent.value = module.default;
}

async function unmountThisFileSystem(fileSystem) {
	selectedDataset.value = fileSystem;
	console.log('selected to be unmounted:', selectedDataset.value);
	await loadUnmountFileSystemComponent();
	showUnmountFileSystemConfirm.value = true;
}

const confirmThisUnmount : ConfirmationCallback = () => {
	confirmUnmount.value = true;
}

const updateShowUnmountFileSystem = (newVal) => {
	showUnmountFileSystemConfirm.value = newVal;
}

watch(confirmUnmount, async (newValue, oldValue) => {
	console.log('confirmUnmount changed:', newValue);
	
	if (confirmUnmount.value == true) {
		unmounting.value = true;
		operationRunning.value = true;

		try {
			const output = await unmountFileSystem(selectedDataset.value!, forceUnmount.value);

			if (output == null) {
				operationRunning.value = false;
				unmounting.value = false;
				confirmUnmount.value = false;
				notifications.value.constructNotification('Unmount Dataset Failed', selectedDataset.value!.name + " was not unmounted. Check console output for details.", 'error');
			} else {
				console.log('unmounted:', selectedDataset.value!);
				if (selectedDataset.value?.encrypted && secondOptionToggle.value) {
					try {
						const lockOutput = await lockFileSystem(selectedDataset.value!);

						if (lockOutput == null) {
							notifications.value.constructNotification('Lock Dataset Failed', `Failed to lock ${selectedDataset.value!.name}. Check console output for details.`, 'error');
						} else {
							notifications.value.constructNotification('Dataset Locked', `Successfully locked ${selectedDataset.value!.name}.`, 'success');
							// showLockUnlockModal.value = false;
						}

					} catch (error) {
						console.error(error);
					}
				}
				confirmUnmount.value = false;
				forceUnmount.value = false;
				await refreshData();
				// await refreshDatasetSnaps(selectedDataset.value);
				unmounting.value = false;
				operationRunning.value = false;
				// lockThisFileSystem.value = false;
				notifications.value.constructNotification('File System Unmounted', selectedDataset.value!.name + " unmounted.", 'success');
				showUnmountFileSystemConfirm.value = false;
			}

		} catch (error) {
			console.error(error);
		}
	}
});

//////////////// Mount File System //////////////////
/////////////////////////////////////////////////////
const showMountFileSystemConfirm = ref(false);
const forceMount = ref(true);
const mounting = ref(false);
const confirmMount = ref(false);

const mountFileSystemComponent = ref();
const loadMountFileSystemComponent = async () => {
	const module = await import('../common/UniversalConfirmation.vue');
	mountFileSystemComponent.value = module.default;
}

async function mountThisFileSystem(fileSystem) {
	selectedDataset.value = fileSystem;
	console.log('selected to be mounted:', selectedDataset.value);
	await loadMountFileSystemComponent();
	showMountFileSystemConfirm.value = true;
}

const confirmThisMount : ConfirmationCallback = () => {
	confirmMount.value = true;
}

const updateShowMountFileSystem = (newVal) => {
	showMountFileSystemConfirm.value = newVal;
}

watch(confirmMount, async (newValue, oldValue) => {
	console.log('confirmMount changed:', newValue);
	
	if (confirmMount.value == true) {
		mounting.value = true;
		operationRunning.value = true;

		try {
			const output = await mountFileSystem(selectedDataset.value!, forceMount.value);
		
			if (output == null) {
				operationRunning.value = false;
				mounting.value = false;
				notifications.value.constructNotification('Mount Dataset Failed', selectedDataset.value!.name + " was not mounted. Check console output for details.", 'error');
				confirmMount.value = false;
			} else {
				console.log('mounted:', selectedDataset.value!);
				confirmMount.value = false;
				forceMount.value = false;
				await refreshData();
				// await refreshDatasetSnaps(selectedDataset.value);
				mounting.value = false;
				operationRunning.value = false;
				notifications.value.constructNotification('File System Mounted', selectedDataset.value!.name + " mounted.", 'success');
				showMountFileSystemConfirm.value = false;
			}
		} catch (error) {
			console.error(error);
		}

	}
});

//////////////// Rename File System /////////////////
/////////////////////////////////////////////////////
const showRenameModal = ref(false);
const renaming = ref(false);
const confirmRename = ref(false);

const renameFileSystemComponent = ref();
const loadRenameFileSystemComponent = async () => {
	const module = await import('./RenameFileSystem.vue');
	renameFileSystemComponent.value = module.default;
}

async function renameThisDataset(fileSystem) {
	selectedDataset.value = fileSystem;
	console.log('selected to be renamed:', selectedDataset.value);
	await loadRenameFileSystemComponent();
	showRenameModal.value = true;
}

watch(confirmRename, async (newVal, oldVal) => {
	if (confirmRename.value == true) {
		operationRunning.value = true;
		await refreshData();
		confirmRename.value = false;
		operationRunning.value = false;
	}
});


/////////////// Change Passphrase ///////////////////
/////////////////////////////////////////////////////
const showChangePassphrase = ref(false);
const changing = ref(false);
const confirmChange = ref(false);

const changePassphraseComponent = ref();
const loadChangePassphraseComponent = async () => {
	const module = await import('./ChangePassphrase.vue');
	changePassphraseComponent.value = module.default;
}

async function changeThisPassphrase(fileSystem) {
	selectedDataset.value = fileSystem;
	console.log('selected to change passphrase:', selectedDataset.value);
	await loadChangePassphraseComponent();
	showChangePassphrase.value = true;
}

watch(confirmChange, async (newVal, oldVal) => {
	if (confirmChange.value == true) {
		operationRunning.value = true;
		await refreshData();
		confirmRename.value = false;
		operationRunning.value = false;
	}
});

/////////// Locking/Unlocking File System ///////////
/////////////////////////////////////////////////////
const showLockUnlockModal = ref(false);
const confirmLockOrUnlock = ref(false);
const lockingOrUnlocking = ref(false);
const modeSelected = ref('');

const lockUnlockFileSystemComponent = ref();
const loadlockUnlockFileSystemComponent = async () => {
	const module = await import('./LockUnlockFileSystem.vue');
	lockUnlockFileSystemComponent.value = module.default;
}

async function handleFileSystemEncryption(fileSystem : FileSystemData, mode : 'lock' | 'unlock') {
	selectedDataset.value = fileSystem;
	modeSelected.value = mode;
	console.log(`selected to be ${mode}ed: ${selectedDataset.value.name}`);
	await loadlockUnlockFileSystemComponent();
	showLockUnlockModal.value = true;
}

watch(confirmLockOrUnlock, async (newVal, oldVal) => {
	if (confirmLockOrUnlock.value == true) {
		operationRunning.value = true;
		await refreshData();
		confirmLockOrUnlock.value = false;
		operationRunning.value = false;
	}
});

watch(confirmDestroySnap, async (newVal, oldVal) => {
	if (confirmDestroySnap.value == true) {
		await refreshData();
	}
});

watch(confirmCreateFS, async (newVal, oldVal) => {
	if (confirmCreateFS.value == true) {
		await refreshData();
	}
});

const confirmSendSnap = ref(false);
watch(confirmSendSnap, async (newVal, oldVal) => {
	if (confirmSendSnap.value == true) {
		await refreshData();
	}
});

const confirmCloneSnap = ref(false);
watch(confirmCloneSnap, async (newVal, oldVal) => {
	if (confirmCloneSnap.value == true) {
		await refreshData();
	}
});

provide('confirm-clone-snap', confirmCloneSnap);
provide('confirm-send-snap', confirmSendSnap);
provide('all-datasets', allDatasets);
provide('all-datasets-loaded', allDatasetsLoaded);
provide('show-fs-wizard', showNewFSWizard);
provide('show-fs-config', showFSConfig);
provide('confirm-create-filesystem', confirmCreateFS);
provide('show-delete-filesystem-confirm', showDeleteFileSystemConfirm);
provide('confirm-delete-filesystem', confirmDelete);
provide('destroy-children', destroyChildren);
provide('destroy-dependents', destroyAllDependents);
provide('confirm-destroy-snap', confirmDestroySnap);
provide('has-children', hasChildren);
provide('selected-dataset', selectedDataset);

provide('show-mount-filesystem-confirm', showMountFileSystemConfirm);
provide('confirm-mount-filesystem', confirmMount);
provide('mounting', mounting);
provide('force-mount', forceMount);

provide('show-unmount-filesystem-confirm', showUnmountFileSystemConfirm);
provide('confirm-unmount-filesystem', confirmUnmount);
provide('unmounting', unmounting);
provide('force-unmount', forceUnmount);

provide('show-rename-modal', showRenameModal);
provide('renaming', renaming);
provide('confirm-rename', confirmRename);

provide('create-snap-modal', showSnapshotModal);
provide('creating', creating);
provide('confirm-create-snap', confirmCreateSnap);

provide('show-change-passphrase', showChangePassphrase);
provide('changing', changing);
provide('confirm-change', confirmChange);

provide('show-lock-unlock-modal', showLockUnlockModal);
provide('locking-or-unlocking', lockingOrUnlocking);
provide('confirm-lock-or-unlock', confirmLockOrUnlock);
provide('mode-selected', modeSelected);

provide('modal-confirm-running', operationRunning);
provide('modal-option-one-toggle', firstOptionToggle);
provide('modal-option-two-toggle', secondOptionToggle);
provide('modal-option-three-toggle', thirdOptionToggle);
provide('modal-option-four-toggle', fourthOptionToggle);
</script>