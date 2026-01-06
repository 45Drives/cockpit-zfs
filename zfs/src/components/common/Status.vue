<!-- Status component for showing progress of Scrub/Resilver and Trim operations -->
<template>
	<div>
		<div v-if="!isDisk">
			<div v-if="!isPoolList">
				<div v-if="!isTrim">
					<div class="grid grid-cols-4 gap-1 justify-items-center w-full">
						<span class="col-span-4 mt-0.5 font-semibold" :class="stateMessageClass()">
							{{ displayStateMessage }}
						</span>

						<div class="col-span-4">
							<div v-if="poolScan && poolScan.state !== null"
								class="col-span-4 grid grid-cols-4 justify-items-center w-full">
								<div
									class="col-span-4 w-full bg-well rounded-full relative flex h-6 min-h-min overflow-hidden">
									<div :class="progressBarClass()" class="h-6 min-h-min w-full"
										:style="{ width: `${adjustedScanPercentage}%` }">
										<div
											class="absolute inset-0 flex items-center justify-center text-s font-medium text-white text-center p-1.5 leading-none">
											{{ adjustedScanPercentage }}%
										</div>
									</div>
								</div>

								<span class="text-muted col-span-4">
									{{ amountProcessed }} of {{ amountTotal }} processed. <br />
								</span>

								<span v-if="isScanning && !isPaused && !isCanceled && !isFinished" class="col-span-4">
									Completes in {{ timeRemaining }}.
								</span>
								<span v-if="isScanning && isPaused && !isCanceled && !isFinished" class="col-span-4">
									Resume to continue or cancel to stop.
								</span>
							</div>
						</div>
					</div>
				</div>

				<div v-else>
					<div class="grid grid-cols-4 gap-1 justify-items-center w-full">
						<div v-for="(disk, idx) in poolDisks" :key="idx" class="col-span-4">
							<div v-if="disk?.stats?.trim_notsup === 0 && getIsTrimmable(disk)" class="col-span-4">
								<div v-if="isTrimActive || isTrimSuspended || isTrimFinished || isTrimCanceled"
									class="col-span-4">
									<div
										class="grid grid-cols-4 justify-items-center w-full whitespace-nowrap text-ellipsis">
										<span class="col-span-4 font-semibold"
											:class="[trimMessageClass(disk), truncateText]">
											{{ trimMessage(disk) }}
										</span>

										<span class="col-span-4" :class="trimMessageClass(disk)" :title="disk?.name">
											Disk: {{ disk?.name }}
											({{ upperCaseWord(vdevTypeForDisk(disk?.name)) }})
										</span>
									</div>

									<div class="col-span-4">
										<div class="col-span-4 grid grid-cols-4 justify-items-center w-full">
											<div
												class="col-span-4 w-full bg-well rounded-full relative flex h-6 min-h-min overflow-hidden">
												<div :class="trimProgressBarClass(disk)" class="h-6 min-h-min w-full"
													:style="{
														width: `${handleTrimPercentage(parseFloat(getTrimPercentage(disk).toFixed(2)))}%`,
													}">
													<div
														class="absolute inset-0 flex items-center justify-center text-s font-medium text-default text-center p-1.5 leading-none">
														{{
															handleTrimPercentage(parseFloat(getTrimPercentage(disk).toFixed(2)))
														}}%
													</div>
												</div>
											</div>
										</div>

										<span class="text-muted col-span-4">
											{{ getTrimmedAmount(disk) }} of {{ getTrimmedTotal(disk) }} processed.
											<br />
										</span>
									</div>
								</div>
							</div>

							<div v-else-if="disk?.stats?.trim_notsup === 0 && !getIsTrimmable(disk)" class="col-span-4">
								<span class="col-span-4 font-base text-default" :class="truncateText"
									:title="disk?.name">
									Trim not suppported on {{ disk?.name }} ({{
										upperCaseWord(vdevTypeForDisk(disk?.name)) }})
								</span>
							</div>
						</div>

						<div v-if="poolDisks.some(d => d?.stats?.trim_notsup === 1)" class="col-span-4">
							<div>
								<span class="text-default col-span-4">
									Trim not supported on disks: <br />
									<div :class="poolDisks.filter(d => d?.stats?.trim_notsup === 1).length < 5
											? `grid-cols-${poolDisks.filter(d => d?.stats?.trim_notsup === 1).length}`
											: 'grid-cols-4'
										" class="grid col-span-4 gap-1 mt-1 justify-center">
										<span v-for="(d, i) in poolDisks.filter(d => d?.stats?.trim_notsup === 1)"
											:key="i" :title="d?.name" :class="truncateText">
											{{ d?.name }}
										</span>
									</div>
								</span>
							</div>
						</div>

						<div v-if="isTrimSuspended" class="col-span-4">
							Resume to continue or cancel to stop.
						</div>
					</div>
				</div>
			</div>

			<div v-else>
				<div class="grid grid-cols-2 gap-1 justify-center items-center">
					<div v-if="poolScan && poolScan.state !== null" class="col-span-2">
						<div :class="[stateMessageClass(), truncateText]" class="font-semibold text-sm"
							:title="displayMiniStateMsg">
							{{ displayMiniStateMsg }}
						</div>
						<div
							class="min-w-max w-full bg-well rounded-full relative flex h-3 min-h-min max-h-max overflow-hidden">
							<div :class="progressBarClass()" class="h-3"
								:style="{ width: `${parseFloat(scanPercentage.toFixed(2))}%` }">
								<div
									class="absolute inset-0 flex items-center justify-center text-xs font-medium text-white text-center p-0.5 leading-none">
									{{ amountProcessed }}/{{ amountTotal }}
								</div>
							</div>
						</div>
					</div>

					<div v-else class="col-span-2 mt-2" :class="truncateText" :title="displayMiniStateMsg">
						<span :class="stateMessageClass()">
							{{ displayMiniStateMsg }}
						</span>
					</div>
				</div>
			</div>
		</div>

		<div v-else>
			<div v-if="selectedDisk" class="grid grid-cols-2 gap-1 justify-center items-center">
				<div v-if="selectedDisk.stats?.trim_notsup === 0 && getIsTrimmable(selectedDisk)"
					class="col-span-2 flex flex-col items-center justify-center">
					<span v-if="getTrimState(selectedDisk.stats.trim_state) !== 'none'"
						:class="[trimMessageClass(selectedDisk), truncateText]" class="font-semibold text-sm">
						Trim {{ upperCaseWord(getTrimState(selectedDisk.stats.trim_state)) }}
						({{ handleTrimPercentage(parseFloat(getTrimPercentage(selectedDisk).toFixed(2))) }}%)
					</span>
					<span v-else :class="[trimMessageClass(selectedDisk), truncateText]" class="mt-2">
						No Trim Activity
					</span>

					<div v-if="getTrimState(selectedDisk.stats.trim_state) !== 'none'"
						class="min-w-max w-full bg-well rounded-full relative flex h-3 min-h-min max-h-max overflow-hidden">
						<div :class="trimProgressBarClass(selectedDisk)" class="h-3"
							:style="{ width: `${handleTrimPercentage(parseFloat(getTrimPercentage(selectedDisk).toFixed(2)))}%` }">
							<div
								class="absolute inset-0 flex items-center justify-center text-xs font-medium text-default text-center p-0.5 leading-none">
								{{ getTrimmedAmount(selectedDisk) }}/{{ getTrimmedTotal(selectedDisk) }}
							</div>
						</div>
					</div>
				</div>

				<div v-else-if="selectedDisk.stats?.trim_notsup === 1"
					class="col-span-2 flex items-center justify-center mt-2">
					<span class="text-muted" :class="truncateText">
						Trim not suppported ({{ props.disk?.type ?? 'unknown' }}).
					</span>
				</div>

				<div v-else class="col-span-2 flex items-center justify-center mt-2">
					<span class="text-muted" :class="truncateText">
						Trim not suppported ({{ upperCaseWord(vdevTypeForDisk(selectedDisk?.name)) }}).
					</span>
				</div>
			</div>

			<div v-else class="col-span-2 flex items-center justify-center mt-2">
				<span class="text-muted" :class="truncateText">
					Disk is missing or being replaced.
				</span>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, inject, Ref, computed, ComputedRef, onMounted, watch } from "vue";
import { convertBytesToSize, convertSecondsToString, convertRawTimestampToString, upperCaseWord, convertTimestampToLocal } from "../../composables/helpers";
import { loadScanObjectGroup, loadDiskStats } from "../../composables/loadData";
import { ZPool, VDevDisk } from "@45drives/houston-common-lib";
import { PoolScanObjectGroup, Activity, PoolDiskStats } from "../../types";

interface StatusProps {
	pool: ZPool;
	disk?: VDevDisk;
	isPoolList: boolean;
	isPoolDetail: boolean;
	isDisk: boolean;
	isTrim: boolean;
	isTrimmableDisk?: boolean;
}

const props = defineProps<StatusProps>();
const poolID = ref(props.pool.name);
const truncateText = inject<Ref<string>>("style-truncate-text")!;

function getIsTrimmable(disk: any) {
	if (!disk || !props.pool?.vdevs) return false;
	const vdev = props.pool.vdevs.find(
		v => Array.isArray((v as any).disks) && (v as any).disks.some((d: any) => d?.name === disk?.name)
	);
	switch ((vdev as any)?.type) {
		case "data":
		case "log":
		case "special":
		case "dedup":
			return true;
		default:
			return false;
	}
}

function vdevTypeForDisk(diskName?: string) {
	if (!diskName || !Array.isArray(props.pool?.vdevs)) return "unknown";
	const vdev = props.pool.vdevs.find(
		v => Array.isArray((v as any).disks) && (v as any).disks.some((d: any) => d?.name === diskName)
	);
	return (vdev as any)?.type ?? "unknown";
}

const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>("scan-object-group")!;
const scanActivities = inject<Ref<Map<string, Activity>>>("scan-activities")!;
const scanIntervalID = inject<Ref<any>>("scan-interval")!;

const poolName = computed(() => props.pool?.name);

type PoolScan = PoolScanObjectGroup[string];

const poolScan = computed<PoolScan | null>(() => {
	const name = poolName.value;
	if (!name) return null;
	return (scanObjectGroup.value as any)?.[name] ?? null;
});

const scanActivity = computed(() => scanActivities.value.get(poolID.value));

function getScanStateBool(state: string): ComputedRef<boolean> {
	return computed(() => {
		const poolState = (poolScan.value as any)?.state;
		if (!poolState) return false;
		return poolState !== "null" && poolState === state;
	});
}

function getScanPauseBool(pause: string): ComputedRef<boolean> {
	return computed(() => {
		const poolPause = (poolScan.value as any)?.pause;
		if (!poolPause) return false;
		return poolPause !== "null" && poolPause !== pause;
	});
}

const isScanning = ref(false);
const isFinished = ref(false);
const isCanceled = ref(false);
const isPaused = ref(false);

async function getScanComputedProps() {
	isScanning.value = getScanStateBool("SCANNING").value;
	isFinished.value = getScanStateBool("FINISHED").value;
	isCanceled.value = getScanStateBool("CANCELED").value;
	isPaused.value = getScanPauseBool("None").value;
}

async function setScanActivity(activity: Activity) {
	await getScanComputedProps();
	activity.isActive = isScanning.value;
	activity.isPaused = isPaused.value;
	activity.isFinished = isFinished.value;
	activity.isCanceled = isCanceled.value;
}

const scanning = ref(false);

async function scanNow() {
	await loadScanObjectGroup(scanObjectGroup);
}

async function pollScanStatus() {
	await scanNow();

	const act = scanActivity.value;
	if (!act) {
		scanning.value = false;
		return;
	}

	await setScanActivity(act);

	if (act.isActive) {
		scanning.value = !act.isPaused;
	} else {
		scanning.value = false;
	}
}

function startScanInterval() {
	if (!scanIntervalID.value) {
		scanIntervalID.value = setInterval(pollScanStatus, 3000);
	}
}

function stopScanInterval() {
	if (scanIntervalID.value) {
		clearInterval(scanIntervalID.value);
		scanIntervalID.value = null;
	}
}

watch(
	scanning,
	() => {
		if (scanning.value) startScanInterval();
		else stopScanInterval();
	},
	{ immediate: true }
);

const scanFunction = computed(() => {
	const fn = (poolScan.value as any)?.function;
	switch (fn) {
		case "RESILVER":
			return "Resilvering";
		case "SCRUB":
			return "Scrubbing";
		case "NONE":
			return "N/A";
		default:
			return "";
	}
});

const stateMessage = computed(() => {
	const s = poolScan.value as any;
	if (!s) return "Loading scrub/resilver data...";
	if (s.state === null) return "No scrub/resilver data found.";
	if (s.pause && s.pause !== "None") return `${scanFunction.value} paused at  ${s.pause}`;

	switch (s.state) {
		case "SCANNING":
			return `${scanFunction.value} started at ${convertTimestampToLocal(s.start_time)}`;
		case "FINISHED":
			return `${scanFunction.value} finished at ${convertTimestampToLocal(s.end_time)}`;
		case "CANCELED":
			return `${scanFunction.value} canceled at ${convertTimestampToLocal(s.end_time)}`;
		case "NONE":
			return "N/A";
		default:
			return "";
	}
});

const miniStateMsg = computed(() => {
	const s = poolScan.value as any;
	if (!s) return "Loading...";
	if (s.state === null) return "No scrub/resilver data found.";
	if (s.pause && s.pause !== "None")
		return `${scanFunction.value} Paused (${parseFloat(scanPercentage.value.toFixed(1))}%)`;

	switch (s.state) {
		case "SCANNING":
			return `${scanFunction.value}... (${parseFloat(scanPercentage.value.toFixed(1))}%)`;
		case "FINISHED":
			return `${scanFunction.value} Complete`;
		case "CANCELED":
			return `${scanFunction.value} Canceled (${parseFloat(scanPercentage.value.toFixed(1))}%)`;
		case "NONE":
			return "N/A";
		default:
			return "";
	}
});

const displayStateMessage = computed(() => {
	if (props.pool?.statusCode !== "OK") return `${props.pool?.statusDetail ?? ""}`;
	return stateMessage.value;
});

const displayMiniStateMsg = computed(() => {
	if (props.pool?.statusCode !== "OK") return `${props.pool?.statusDetail ?? ""}`;
	return miniStateMsg.value;
});

const scanPercentage = computed(() => (poolScan.value as any)?.percentage ?? 0);

const adjustedScanPercentage = computed(() => {
	const pct = parseFloat(scanPercentage.value.toFixed(2));
	if (isFinished.value && pct > 90) return 100;
	return pct;
});

const amountProcessed = computed(() => convertBytesToSize((poolScan.value as any)?.bytes_issued ?? 0));
const amountTotal = computed(() => convertBytesToSize((poolScan.value as any)?.bytes_processed ?? 0));
const timeRemaining = computed(() => convertSecondsToString((poolScan.value as any)?.total_secs_left ?? 0));

function stateMessageClass() {
	const s = poolScan.value as any;
	if (s && s.pause === "None") {
		switch (s.state) {
			case "SCANNING":
				return "text-default";
			case "FINISHED":
				return "text-success";
			case "CANCELED":
				return "text-danger";
			case "NONE":
				return "text-muted";
			default:
				return "text-default";
		}
	}
	return "text-orange-600";
}

function progressBarClass() {
	const s = poolScan.value as any;
	if (s && s.pause === "None") {
		switch (s.state) {
			case "SCANNING":
				return "bg-blue-600";
			case "FINISHED":
				return "bg-green-600";
			case "CANCELED":
				return "bg-danger";
			case "NONE":
				return "text-muted";
			default:
				return "text-default";
		}
	}
	return "bg-orange-600";
}

const poolDiskStats = inject<Ref<PoolDiskStats>>("pool-disk-stats")!;
const trimActivities = inject<Ref<Map<string, Activity>>>("trim-activities")!;
const diskStatsIntervalID = inject<Ref<any>>("disk-stats-interval")!;

const poolDisks = computed<any[]>(() => {
	const name = poolName.value;
	if (!name) return [];
	const disks = (poolDiskStats.value as any)?.[name];
	return Array.isArray(disks) ? disks : [];
});

const trimActivity = computed(() => {
	const key = props.disk?.name ?? poolID.value;
	return trimActivities.value.get(key);
});

const selectedDisk = computed<any | null>(() => {
	if (!props.disk?.name) return null;
	return poolDisks.value.find(d => d?.name === props.disk!.name) ?? null;
});

const isTrimActive = computed(() => poolDisks.value.some(d => d?.stats?.trim_notsup !== 1 && d?.stats?.trim_state === 1));

const isTrimCanceled = computed(() => poolDisks.value.some(d => d?.stats?.trim_notsup !== 1 && d?.stats?.trim_state === 2));

const isTrimSuspended = computed(() => poolDisks.value.some(d => d?.stats?.trim_notsup !== 1 && d?.stats?.trim_state === 3));

const isTrimFinished = computed(() => poolDisks.value.some(d => d?.stats?.trim_notsup !== 1 && d?.stats?.trim_state === 4));

async function setTrimActivity(activity: Activity) {
	activity.isActive = isTrimActive.value;
	activity.isPaused = isTrimSuspended.value;
	activity.isFinished = isTrimFinished.value;
	activity.isCanceled = isTrimCanceled.value;
}

const checkingDiskStats = ref(false);

async function checkDiskStats() {
	await loadDiskStats(poolDiskStats);
}

function checkActivityState(activity: Activity) {
	if (activity.isActive) return "active";
	if (activity.isPaused) return "paused";
	if (activity.isCanceled) return "canceled";
	if (activity.isFinished) return "finished";
	return undefined;
}

async function pollTrimStatus() {
	await checkDiskStats();

	const act = trimActivity.value;
	if (!act) {
		checkingDiskStats.value = false;
		return;
	}

	await setTrimActivity(act);

	switch (checkActivityState(act)) {
		case "active":
			checkingDiskStats.value = true;
			break;
		case "paused":
		case "canceled":
		case "finished":
			checkingDiskStats.value = false;
			break;
		default:
			break;
	}
}

function startDiskStatsInterval() {
	if (!diskStatsIntervalID.value) {
		diskStatsIntervalID.value = setInterval(pollTrimStatus, 3000);
	}
}

function stopDiskStatsInterval() {
	if (diskStatsIntervalID.value) {
		clearInterval(diskStatsIntervalID.value);
		diskStatsIntervalID.value = null;
	}
}

watch(
	checkingDiskStats,
	() => {
		if (checkingDiskStats.value) startDiskStatsInterval();
		else stopDiskStatsInterval();
	},
	{ immediate: true }
);

function getTrimTimestamp(disk: any) {
	return convertTimestampToLocal(convertRawTimestampToString(disk?.stats?.trim_action_time));
}

function getTrimPercentage(disk: any) {
	const st = disk?.stats;
	if (!st) return 0;
	if (st.trim_state === 4) return 100;

	const est = st.trim_bytes_est ?? 0;
	const done = st.trim_bytes_done ?? 0;
	if (est <= 0) return 0;

	return (done / est) * 100;
}

function handleTrimPercentage(percentage: number) {
	if (percentage <= 0) return 0;
	if (percentage >= 99.95) return 100;
	if (percentage > 0 && percentage < 99.5) return percentage;
	return 0;
}

function getTrimmedAmount(disk: any) {
	return convertBytesToSize(disk?.stats?.trim_bytes_done ?? 0);
}

function getTrimmedTotal(disk: any) {
	return convertBytesToSize(disk?.stats?.trim_bytes_est ?? 0);
}

function getTrimState(state_num: number) {
	switch (state_num) {
		case 0:
			return "none";
		case 1:
			return "active";
		case 2:
			return "canceled";
		case 3:
			return "suspended";
		case 4:
			return "finished";
		default:
			return "none";
	}
}

function trimMessage(disk: any) {
	switch (getTrimState(disk?.stats?.trim_state)) {
		case "none":
			return "Trim Information N/A";
		case "active":
			return `Trim active, started at ${getTrimTimestamp(disk)}`;
		case "canceled":
			return "Trim canceled";
		case "suspended":
			return "Trim is suspended";
		case "finished":
			return `Trim finished at ${getTrimTimestamp(disk)}`;
		default:
			return "";
	}
}

function trimMessageClass(disk: any) {
	switch (getTrimState(disk?.stats?.trim_state)) {
		case "none":
			return "";
		case "active":
			return "text-default";
		case "canceled":
			return "text-danger";
		case "suspended":
			return "text-orange-600";
		case "finished":
			return "text-success";
		default:
			return "";
	}
}

function trimProgressBarClass(disk: any) {
	switch (getTrimState(disk?.stats?.trim_state)) {
		case "none":
			return "";
		case "active":
			return "bg-blue-600";
		case "canceled":
			return "bg-danger";
		case "suspended":
			return "bg-orange-600";
		case "finished":
			return "bg-green-600";
		default:
			return "";
	}
}

onMounted(() => {
	pollScanStatus();
	pollTrimStatus();
});

defineExpose({
	pollScanStatus,
	pollTrimStatus,
});
</script>