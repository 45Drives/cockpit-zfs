<template>
	<div class="inline-block min-w-full min-h-full py-4 align-middle sm:px-4 lg:px-6 overflow-visible bg-accent rounded-md border border-default">
		<div class="flex bg-well justify-between rounded-md p-2 shadow text-default rounded-b-md ring-1 ring-black ring-opacity-5">
			<div class="button-group-row justify-start">
				<button id="createPool" class="btn btn-primary" @click="newPoolWizardBtn">Create Storage Pool</button>
				<button id="importPool" class="btn btn-secondary" @click="importNewPoolBtn">Import Storage Pool</button>
			</div>
			<div class="button-group-row justify-end">
				<button id="refreshPools" class="btn btn-secondary " @click="refreshAllData"><ArrowPathIcon class="w-5 h-5 m-1"/></button>
			</div>
		</div>

		<div class="mt-4 rounded-md max-w-full">
			<div class="inline-block min-w-full min-h-full shadow align-middle rounded-md border border-default">
				<div class="whitespace-nowrap text-ellipsis ring-1 ring-black ring-opacity-5 rounded-md">

					<table class="min-w-full divide-y divide-default rounded-md">
						<thead class="rounded-md">
							<tr class="bg-well rounded-t-md grid grid-cols-10">
								<th class="relative py-2 rounded-tl-md col-span-1">
									<span class="sr-only"></span>
								</th>
								<th class="py-2 font-semibold text-default col-span-1 flex flex-row justify-start" :class="truncateText" title="Name">Name</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Status">Status</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Used (%)">Used (%)</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Used">Used</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Free">Free</th>
								<th class="py-2 font-semibold text-default col-span-1" :class="truncateText" title="Total">Total</th>
								<th class="py-2 font-semibold text-default col-span-2" :class="truncateText" title="Message">Message</th>
								<th class="relative py-2 sm:pr-6 lg:pr-8 rounded-tr-md col-span-1">
									<span class="sr-only"></span>
								</th>

							</tr>
						</thead>
						
						<tbody class="">
							<tr class="border border-collapse border-default ">
								<div v-if="poolData.length > 0 && poolsLoaded == true" class="">
									<div v-for="pool, poolIdx in poolData" :key="poolIdx" class="">
										<PoolListElement :poolIdx="poolIdx" :pool="pool"/>
									</div>
								</div>
							</tr>
						</tbody>
					</table>
									
					<div v-if="poolsLoaded == false" class="p-2 flex justify-center bg-default ">
						<LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'"  class="font-semibold text-lg my-0.5"/>
					</div>
					<div v-if="poolData.length < 1 && poolsLoaded == true" class="p-2 flex bg-default justify-center ">
						<span class="font-semibold text-lg my-2">No Pools Found</span>
					</div>
	
				</div>
			</div>
		</div>
	</div>

	<div v-if="showNewPoolWizard">
		<component :is="createPoolComponent" @close="showNewPoolWizard = false"/>
	</div>

	<div v-if="showImportModal">
		<component :is="importPoolComponent" :idKey="'import-pool'"/>
	</div>
</template>

<script setup lang="ts">
import { ref, inject, Ref, provide } from "vue";
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import { loadDatasets, loadDisksThenPools, loadScanObjectGroup, loadDiskStats } from '../../composables/loadData';
import { loadScanActivities, loadTrimActivities } from '../../composables/helpers';
import PoolListElement from './PoolListElement.vue';
import LoadingSpinner from '../common/LoadingSpinner.vue';

/////////////// Loading/Refreshing //////////////////
/////////////////////////////////////////////////////
const poolData = inject<Ref<PoolData[]>>("pools")!;
const diskData = inject<Ref<DiskData[]>>("disks")!;
const filesystemData = inject<Ref<FileSystemData[]>>('datasets')!;
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;
const truncateText = inject<Ref<string>>('style-truncate-text')!;

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
	console.log('PoolList trimActivities', trimActivities.value);
}

/////////////// Create/Import Pool //////////////////
/////////////////////////////////////////////////////
const showNewPoolWizard = ref(false);

const createPoolComponent = ref();
const loadCreatePoolComponent = async () => {
	const module = await import('../pool-creation-wizard/CreatePool.vue');
	createPoolComponent.value = module.default;
}

async function newPoolWizardBtn() {
	await loadCreatePoolComponent();
	showNewPoolWizard.value = true;
}

const showImportModal = ref(false);

const importPoolComponent = ref();
const loadImportPoolComponent = async () => {
	const module = await import('./ImportPool.vue');
	importPoolComponent.value = module.default;
}

async function importNewPoolBtn() {
	await loadImportPoolComponent();
	showImportModal.value = true;
}

provide('show-wizard', showNewPoolWizard);
provide("show-import-modal", showImportModal);
</script>