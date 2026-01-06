<template>
	<div class="min-w-full max-w-full max-h-full py-2 pb-4 align-middle sm:px-4 lg:px-6 sm:rounded-lg bg-accent rounded-md border border-default">
		<div name="pools">
			<!-- Pools summary -->
			<div v-if="pools.length > 0 && poolsLoaded == true" class="grid grid-flow-col bg-well text-center items-center rounded-md shadow text-default my-2 rounded-b-md ring-1 ring-black ring-opacity-5">
				<div class="p-2 flex justify-start mt-1">
					<span class="px-3 font-semibold text-lg mt-1 justify-self-start">Pools</span>
				</div>
				<div class="p-2 flex justify-start mt-1">
					<h6 class="mt-2"> {{ pools.length }} Pool(s) </h6>
				</div>
				<div class="p-2 flex justify-start mt-1">
					<h6 class="mt-2"> Total Effective Space: {{ totalEffectivePoolSpace }} </h6>
				</div>
				<div class="p-2 flex justify-end">
					<button class="btn btn-secondary" @click="refreshAllData">
						<ArrowPathIcon class="h-5 w-5 m-1" aria-hidden="true"/>
					</button>
				</div>
			</div>

			<!-- pools summary loading spinner -->
			<div v-if="poolsLoaded == false" class="grid grid-flow-col grid-cols-3 bg-well gap-2 justify-items-center rounded-md shadow text-default my-2 rounded-b-md ring-1 ring-black ring-opacity-5 ">
				<LoadingSpinner :width="'w-11'" :height="'h-11'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'" class="col-span-4 my-2"/>
			</div>

			<!-- no pools found -->
			<div v-if="pools.length < 1 && poolsLoaded == true" class="grid grid-flow-col grid-cols-3 bg-well rounded-md shadow text-default my-2 rounded-b-md ring-1 ring-black ring-opacity-5">
				<div class="p-2 flex justify-center col-start-2">
					<span class="font-semibold text-lg mt-1">No Pools Found</span>
				</div>
				<div class="p-2 flex justify-end col-start-3">
					<button class="btn btn-primary" @click="refreshAllData">
						<ArrowPathIcon class="h-5 w-5" aria-hidden="true"/>
					</button>
				</div>
			</div>

			<!-- pools card layout -->
			<div v-if="pools.length > 0 && poolsLoaded == true"
				class="grid gap-2 mb-2 items-stretch [grid-template-columns:repeat(auto-fit,minmax(18rem,1fr))]">
				<div v-for="(pool, index) in pools" :key="index" class="w-full h-full">
					<DashPoolCard :pool="pool" class="h-full" />
				</div>
			</div>

			<!-- pools card loading skeleton -->
			<div v-if="poolsLoaded == false" class="grid grid-cols-3 justify-items-center">
				<DashboardLoadingSkeleton color="bg-plugin-header" class="col-span-4"/>
			</div>
		</div>
	</div>

</template>

<script setup lang="ts">
import {computed, Ref, inject} from 'vue';
import { convertBytesToSize } from '../../composables/helpers';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import DashPoolCard from "./DashPoolCard.vue";
import DashboardLoadingSkeleton from './DashboardLoadingSkeleton.vue';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import { ZPool, VDevDisk, ZFSFileSystemInfo } from '@45drives/houston-common-lib';
import { PoolScanObjectGroup, PoolDiskStats, Activity } from '../../types';
import { useRefreshAllData } from "../../composables/useRefreshAllData";

const pools = inject<Ref<ZPool[]>>("pools")!;
const disks = inject<Ref<VDevDisk[]>>("disks")!;

const datasets = inject<Ref<ZFSFileSystemInfo[]>>("datasets")!;
const datasetsLoaded = inject<Ref<boolean>>("datasets-loaded")!;
	
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;

const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const { refreshAllData } = useRefreshAllData({
	poolData: pools,
	diskData: disks,
	filesystemData: datasets,
	disksLoaded,
	poolsLoaded,
	fileSystemsLoaded: datasetsLoaded,
	scanObjectGroup,
	poolDiskStats,
	scanActivities,
	trimActivities
});

//determine total effective space of pools
const totalEffectivePoolSpace = computed(() => {
	let totalCapacity = 0;
	pools.value.forEach(pool => {
		totalCapacity += pool.properties.rawsize;
	});

	return(convertBytesToSize(totalCapacity));
});
</script>