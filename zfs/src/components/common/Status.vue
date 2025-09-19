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

                            <div v-if="scanObjectGroup[props.pool.name].state !== null"
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
                <div v-if="isTrim">
                    <div class="grid grid-cols-4 gap-1 justify-items-center w-full">
                        <div v-for="disk, idx in poolDiskStats[props.pool.name]" :key="idx" class="col-span-4">

                            <div v-if="disk.stats.trim_notsup === 0 && getIsTrimmable(disk)" class="col-span-4">
                                <div v-if="isTrimActive || isTrimSuspended || isTrimFinished || isTrimCanceled"
                                    class="col-span-4">
                                    <div
                                        class="grid grid-cols-4 justify-items-center w-full whitespace-nowrap text-ellipsis">
                                        <span class="col-span-4 font-semibold"
                                            :class="[trimMessageClass(disk), truncateText]">
                                            {{ trimMessage(disk) }}
                                        </span>
                                        <span class="col-span-4" :class="trimMessageClass(disk)" :title="disk.name">
                                            Disk: {{ disk.name }} ({{ upperCaseWord((props.pool.vdevs.find(vdev =>
                                            vdev.disks.some(vDevDisk => vDevDisk.name == disk.name)))!.type) }})
                                        </span>
                                    </div>

                                    <div class="col-span-4">
                                        <div class="col-span-4 grid grid-cols-4 justify-items-center w-full">
                                            <div
                                                class="col-span-4 w-full bg-well rounded-full relative flex h-6 min-h-min overflow-hidden">
                                                <div :class="trimProgressBarClass(disk)" class="h-6 min-h-min w-full"
                                                    :style="{ width: `${handleTrimPercentage(parseFloat(getTrimPercentage(disk).toFixed(2)))}%` }">
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

                            <div v-if="disk.stats.trim_notsup === 0 && !getIsTrimmable(disk)" class="col-span-4">
                                <span class="col-span-4 font-base text-default" :class="truncateText"
                                    :title="disk!.name!">
                                    Trim not suppported on {{ disk!.name }} ({{
                                    upperCaseWord((props.pool.vdevs.find(vdev => vdev.disks.some(vDevDisk =>
                                    vDevDisk.name == disk.name)))!.type) }})
                                </span>
                            </div>

                        </div>

                        <div v-if="poolDiskStats[props.pool.name].some(disk => disk.stats.trim_notsup == 1)"
                            class="col-span-4">
                            <div class="">
                                <span class="text-default col-span-4">
                                    Trim not supported on disks: <br />
                                    <div :class="(poolDiskStats[props.pool.name].filter(disk => disk.stats.trim_notsup === 1)).length < 5 ? `grid-cols-${poolDiskStats[props.pool.name].filter(disk => disk.stats.trim_notsup === 1).length}` : 'grid-cols-4'"
                                        class="grid col-span-4 gap-1 mt-1 justify-center">
                                        <span
                                            v-for="disk, idx in (poolDiskStats[props.pool.name].filter(disk => disk.stats.trim_notsup === 1))"
                                            :title="disk.name" :class="truncateText" class="">{{ disk.name }} </span>
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

            <div v-if="isPoolList">
                <div class="grid grid-cols-2 gap-1 justify-center items-center">

                    <div v-if="scanObjectGroup[props.pool.name].state !== null" class="col-span-2">
                        <div :class="[stateMessageClass(), truncateText]" class="font-semibold text-sm"
                            :title="displayMiniStateMsg">
                            {{ displayMiniStateMsg }}
                        </div>
                        <div
                            class="min-w-max w-full bg-well rounded-full relative flex h-3 min-h-min max-h-max overflow-hidden">
                            <div :class="progressBarClass()" class="h-3"
                                :style="{ width: `${ parseFloat(scanPercentage.toFixed(2)) }%` }">
                                <div
                                    class="absolute inset-0 flex items-center justify-center text-xs font-medium text-white text-center p-0.5 leading-none">
                                    {{ amountProcessed }}/{{ amountTotal }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-if="scanObjectGroup[props.pool.name].state === null" class="col-span-2 mt-2"
                        :class="truncateText" :title="displayMiniStateMsg">
                        <span :class="stateMessageClass()">
                            {{ displayMiniStateMsg }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="isDisk">
            <div v-if="selectedDisk!" class="grid grid-cols-2 gap-1 justify-center items-center">

                <div v-if="selectedDisk!.stats.trim_notsup === 0 && getIsTrimmable(disk)!"
                    class="col-span-2 flex flex-col items-center justify-center">
                    <span v-if="getTrimState(selectedDisk!.stats.trim_state) !== 'none'"
                        :class="[trimMessageClass(selectedDisk!), truncateText]" class="font-semibold text-sm">
                        Trim {{ upperCaseWord(getTrimState(selectedDisk!.stats.trim_state)) }} ({{
                        handleTrimPercentage(parseFloat(getTrimPercentage(selectedDisk!).toFixed(2))) }}%)
                    </span>
                    <span v-if="getTrimState(selectedDisk!.stats.trim_state) == 'none'"
                        :class="[trimMessageClass(selectedDisk!), truncateText]" class="mt-2">
                        No Trim Activity
                    </span>
                    <div v-if="getTrimState(selectedDisk!.stats.trim_state) !== 'none'"
                        class="min-w-max w-full bg-well rounded-full relative flex h-3 min-h-min max-h-max overflow-hidden">
                        <div :class="trimProgressBarClass(selectedDisk!)" class="h-3"
                            :style="{ width: `${handleTrimPercentage(parseFloat(getTrimPercentage(selectedDisk!).toFixed(2)))}%` }">
                            <div
                                class="absolute inset-0 flex items-center justify-center text-xs font-medium text-default text-center p-0.5 leading-none">
                                {{ getTrimmedAmount(selectedDisk!) }}/{{ getTrimmedTotal(selectedDisk!) }}
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="selectedDisk!.stats.trim_notsup === 1"
                    class="col-span-2 flex items-center justify-center mt-2">
                    <span class="text-muted" :class="truncateText">
                        Trim not suppported ({{ props.disk!.type }}).
                    </span>
                </div>

                <div v-if="selectedDisk!.stats.trim_notsup === 0 && !getIsTrimmable(disk)"
                    class="col-span-2 flex items-center justify-center mt-2">
                    <span class="text-muted" :class="truncateText">
                        Trim not suppported ({{ upperCaseWord((props.pool.vdevs.find(vdev => vdev.disks.some(vDevDisk =>
                        vDevDisk.name == selectedDisk!.name)))!.type) }}).
                    </span>
                </div>
            </div>
            <div v-if="!selectedDisk" class="col-span-2 flex items-center justify-center mt-2">
                <span class="text-muted" :class="truncateText">
                    Disk is missing or being replaced.
                </span>
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, inject, Ref, computed, ComputedRef, onMounted, watch, defineExpose } from "vue";
import { convertBytesToSize, convertSecondsToString, convertRawTimestampToString, upperCaseWord, convertTimestampToLocal } from "../../composables/helpers";
import { loadScanObjectGroup, loadDiskStats } from "../../composables/loadData";
import { ZPool, VDevDisk} from "@45drives/houston-common-lib";
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
const truncateText = inject<Ref<string>>('style-truncate-text')!;

function getIsTrimmable(disk) {
    if (!disk || !props.pool?.vdevs) return false;
    const vdev = props.pool.vdevs.find(v =>
        Array.isArray(v.disks) && v.disks.some(d => d?.name === disk.name)
    );
    switch (vdev?.type) {
        case 'data':
        case 'log':
        case 'special':
        case 'dedup':
            return true;
        default:
            return false;
    }
}


const adjustedScanPercentage = computed(() => {
    if (isFinished.value && parseFloat(scanPercentage.value.toFixed(2)) > 90) {
        return 100;
    }
    return parseFloat(scanPercentage.value.toFixed(2));
});

///////////////////// Scanning //////////////////////
/////////////////////////////////////////////////////
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
// const scanActivity = inject<Ref<Activity>>('scan-activity')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const scanActivity = computed(() => {
	return scanActivities.value.get(poolID.value);
});

function getScanStateBool(state) : ComputedRef<boolean> {
    return computed(() => {
        // return scanObjectGroup.value[props.pool.name].state === state;
        const poolState = scanObjectGroup.value[props.pool.name].state;
        // console.log('poolState:', poolState);
        return poolState !== 'null' && poolState === state;
    });
}

function getScanPauseBool(pause) : ComputedRef<boolean> {
	return computed(() => {
		// return scanObjectGroup.value[props.pool.name].pause !== pause;
        const poolPause = scanObjectGroup.value[props.pool.name].pause;
        return poolPause !== 'null' && poolPause !== pause;
	});
}

const isScanning = ref(false);
const isFinished = ref(false);
const isCanceled = ref(false);
const isPaused = ref(false);

async function getScanComputedProps() {
	isScanning.value = getScanStateBool('SCANNING').value;
	isFinished.value = getScanStateBool('FINISHED').value;
	isCanceled.value = getScanStateBool('CANCELED').value;
	isPaused.value = getScanPauseBool('None').value;
}

async function setScanActivity(activity : Activity) {
    // console.log(`activity for ${props.pool.name}:`, activity);
    await getScanComputedProps();
    activity.isActive = isScanning.value;
    activity.isPaused = isPaused.value;
    activity.isFinished = isFinished.value;
    activity.isCanceled = isCanceled.value;

    // console.log('setScanActivity fired');
}

const scanIntervalID = inject<Ref<any>>('scan-interval')!;
const scanning = ref(false);

async function scanNow() {
	await loadScanObjectGroup(scanObjectGroup);
    // console.log(`polling scanObject...`);
}

function displayScanBools() {
    console.log(`Status scan values for ${props.pool.name}: \n 
        isActive:${scanActivity!.value!.isActive}\n
        isPaused:${scanActivity!.value!.isPaused}\n
        isFinished:${scanActivity!.value!.isFinished}\n
        isCanceled:${scanActivity!.value!.isCanceled}\n
        ------`);
}

async function pollScanStatus() {
	// console.log('pollScanStatus fired');
	await scanNow();
	await setScanActivity(scanActivity!.value!);
    // console.log(`scanActivity for ${props.pool.name} set`);

    if (scanActivity!.value!.isActive) {
		if (!scanActivity!.value!.isPaused) {
			// console.log('scan active');
			scanning.value = true;
		} else if (scanActivity!.value!.isPaused) {
			// console.log('scan paused');
			scanning.value = false;
		}
	} else if (scanActivity!.value!.isCanceled) {
		// console.log('scan canceled');
		scanning.value = false;
	} else if (scanActivity!.value!.isFinished) {
		// console.log('scan finished');
		scanning.value = false;
	}

	// console.log('scan set:', scanning.value);
    // console.log(`scan for ${props.pool.name} set: ${scanning.value}`)
	// displayScanBools();
    // console.log('polling scanStats...', scanning.value);
}

function startScanInterval() {
	if (!scanIntervalID.value) {
		scanIntervalID.value = setInterval(pollScanStatus, 3000);
        // console.log('----scan interval set----', scanIntervalID.value);
	}
}

function stopScanInterval() {
	if (scanIntervalID.value) {
		clearInterval(scanIntervalID.value);
        // console.log('----scan interval cleared----', scanIntervalID.value);
		scanIntervalID.value = null;
	}
}

watch(scanning, (newVal, oldVal) => {
	if (scanning.value) {
		startScanInterval();
	} else if (!scanning.value) {
		stopScanInterval();
	}
}, {immediate: true});

//////////////////////////////////////////////////////////////////

const scanFunction = computed(() => {
    switch (scanObjectGroup.value[props.pool.name].function) {
        case 'RESILVER':
            return 'Resilvering';
        case 'SCRUB':
            return 'Scrubbing';
        case 'NONE':
            return 'N/A';
        default:
            return;
    }
});

const stateMessage = computed(() => {
    if (scanObjectGroup.value[props.pool.name].state === null) {
        return `No scrub/resilver data found.`;
    } else {
        if (scanObjectGroup.value[props.pool.name] && scanObjectGroup.value[props.pool.name].pause !== 'None') {
           return `${scanFunction.value} paused at  ${scanObjectGroup.value[props.pool.name].pause}`;
        } else {
            // const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            // console.log('timeZone:', userTimeZone);
            if (scanObjectGroup.value[props.pool.name]) {
                switch (scanObjectGroup.value[props.pool.name].state) {
                    case 'SCANNING':
                        return `${scanFunction.value} started at ${convertTimestampToLocal(scanObjectGroup.value[props.pool.name].start_time)}`;
                    case 'FINISHED':
                        return `${scanFunction.value} finished at ${convertTimestampToLocal(scanObjectGroup.value[props.pool.name].end_time)}`;
                    case 'CANCELED':
                        return `${scanFunction.value} canceled at ${convertTimestampToLocal(scanObjectGroup.value[props.pool.name].end_time)}`;
                    case 'NONE':
                        return 'N/A';
                    default:
                        return '';
                }
            }
        }
    }
});

const miniStateMsg = computed(() => {
    if (scanObjectGroup.value[props.pool.name] && scanObjectGroup.value[props.pool.name].state === null) {
        return `No scrub/resilver data found.`;
    } else {
        if (scanObjectGroup.value[props.pool.name] && scanObjectGroup.value[props.pool.name].pause !== 'None') {
            return `${scanFunction.value} Paused (${ parseFloat(scanPercentage.value.toFixed(1)) }%)`;
        } else {
            switch (scanObjectGroup.value[props.pool.name].state) {
                case 'SCANNING':
                    return `${scanFunction.value}... (${ parseFloat(scanPercentage.value.toFixed(1)) }%)`;
                case 'FINISHED':
                    return `${scanFunction.value} Complete`;
                case 'CANCELED':
                    return `${scanFunction.value} Canceled (${ parseFloat(scanPercentage.value.toFixed(1)) }%)`;
                case 'NONE':
                    return 'N/A';
                default:
                    return '';
            }
        }
    }
});

// Computed property to determine the state message based on pool health
const displayStateMessage = computed(() => {
    if (props.pool.statusCode !== 'OK') {
        return `${props.pool.statusDetail}`;
    } else {
        return stateMessage.value;
    }
});

// Computed property for a shorter message in pool list view
const displayMiniStateMsg = computed(() => {
    if (props.pool.statusCode !== 'OK') {
        return `${props.pool.statusDetail}`;
    } else {
        return miniStateMsg.value;
    }
});

const scanPercentage = computed(() => {
    return scanObjectGroup.value[props.pool.name].percentage;
});

const amountProcessed = computed(() => {
    return convertBytesToSize(scanObjectGroup.value[props.pool.name].bytes_issued);
});

const amountTotal = computed(() => {
    return convertBytesToSize(scanObjectGroup.value[props.pool.name].bytes_processed);
});

const timeRemaining = computed(() => {
    return convertSecondsToString(scanObjectGroup.value[props.pool.name].total_secs_left);
});

function stateMessageClass() {
    if (scanObjectGroup.value[props.pool.name] && scanObjectGroup.value[props.pool.name].pause === 'None') {
        switch (scanObjectGroup.value[props.pool.name].state) {
            case 'SCANNING':
                return 'text-default';
            case 'FINISHED':
                return 'text-success'; 
            case 'CANCELED':
                return 'text-danger'; 
            case 'NONE':
                return 'text-muted';
            default:
                return 'text-default'; 
        } 
    } else {
        return 'text-orange-600'
    }
}

function progressBarClass() {
     if (scanObjectGroup.value[props.pool.name] && scanObjectGroup.value[props.pool.name].pause === 'None') {
        switch (scanObjectGroup.value[props.pool.name].state) {
            case 'SCANNING':
                return 'bg-blue-600';
            case 'FINISHED':
                return 'bg-green-600'; 
            case 'CANCELED':
                return 'bg-danger'; 
            case 'NONE':
                return 'text-muted';
            default:
                return 'text-default'; 
        }
    } else {
        return 'bg-orange-600';
    }
}

//////////// Checking Disk Stats (Trim) /////////////
/////////////////////////////////////////////////////
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const trimActivity = computed(() => {
    if (props.disk!) {
        return trimActivities.value.get(props.disk!.name!);
    } else {
        return trimActivities.value.get(poolID.value);
    }
});

const selectedDisk = computed(() => {
    return poolDiskStats.value[props.pool.name].find(disk => disk.name == props.disk!.name);
});

const isTrimActive = computed(() => {
    return poolDiskStats.value[props.pool.name].some(disk => disk.stats.trim_notsup !== 1 && disk.stats.trim_state === 1);
});

const isTrimCanceled = computed(() => {
    return poolDiskStats.value[props.pool.name].some(disk => disk.stats.trim_notsup !== 1 && disk.stats.trim_state === 2);
});

const isTrimSuspended = computed(() => {
    return poolDiskStats.value[props.pool.name].some(disk => disk.stats.trim_notsup !== 1 && disk.stats.trim_state === 3);
});

const isTrimFinished = computed(() => {
    return poolDiskStats.value[props.pool.name].some(disk => disk.stats.trim_notsup !== 1 && disk.stats.trim_state === 4);
});


async function setTrimActivity(activity: Activity) {
    if (activity) {
        activity.isActive = isTrimActive.value;
        activity.isPaused = isTrimSuspended.value;
        activity.isFinished = isTrimFinished.value;
        activity.isCanceled = isTrimCanceled.value;
    }

    // console.log('setTrimActivity fired');
}

const diskStatsIntervalID = inject<Ref<any>>('disk-stats-interval')!;
const checkingDiskStats = ref(false);

async function checkDiskStats() {
	await loadDiskStats(poolDiskStats);
    // console.log(`polling poolDiskStats...`);
}

function displayTrimBools() {
    console.log(`Status trim values for ${props.pool.name}: \n 
        isActive:${trimActivity!.value!.isActive}\n
        isPaused:${trimActivity!.value!.isPaused}\n
        isFinished:${trimActivity!.value!.isFinished}\n
        isCanceled:${trimActivity!.value!.isCanceled}\n
        ******`);
}

async function pollTrimStatus() {
	// console.log('pollTrimStatus fired');
	await checkDiskStats();
	await setTrimActivity(trimActivity!.value!);
    // console.log(`trimActivity for ${props.pool.name} set`);

    switch(checkActivityState(trimActivity!.value!)) {
        case 'active':
            // console.log('trim active');
		    checkingDiskStats.value = true;
            break;
        case 'paused':
            // console.log('trim paused');
		    checkingDiskStats.value = false;
            break;
        case 'canceled':
            // console.log('trim canceled');
		    checkingDiskStats.value = false;
            break;
        case 'finished':
            // console.log('trim finished');
		    checkingDiskStats.value = false;
            break;
        default:
            break;
    }

	// console.log('checkingDiskStats set:', checkingDiskStats.value);
    // console.log(`checkDiskStats for ${props.pool.name} set: ${checkingDiskStats.value}`)
    // displayTrimBools();
    // console.log('polling diskStats...', checkingDiskStats.value);
}

function checkActivityState(activity : Activity) {
    if (activity.isActive) {
        return 'active';
    } else if (activity.isPaused) {
        return 'paused';
    } else if (activity.isCanceled) {
        return 'canceled';
    } else if (activity.isFinished) {
        return 'finished';
    }
}

function startDiskStatsInterval() {
	if (!diskStatsIntervalID.value) {
		diskStatsIntervalID.value = setInterval(pollTrimStatus, 3000);
        // console.log('****trim interval set****', diskStatsIntervalID.value);
	}
}

function stopDiskStatsInterval() {
	if (diskStatsIntervalID.value) {
		clearInterval(diskStatsIntervalID.value);
        // console.log('****trim interval cleared****', diskStatsIntervalID.value);
		diskStatsIntervalID.value = null;
	}
}

watch(checkingDiskStats, (newVal, oldVal) => {
	if (checkingDiskStats.value) {
		startDiskStatsInterval();
	} else if (!checkingDiskStats.value) {
		stopDiskStatsInterval();
	}
}, {immediate: true});

//////////////////////////////////////////////////////////////////

function getTrimTimestamp(disk) {
    return (convertTimestampToLocal(convertRawTimestampToString(disk.stats.trim_action_time)));
}

function getTrimPercentage(disk) {
    // console.log('disk stats (for trim percentage):', disk.stats);

    if (disk.stats.trim_state == 4) {
        return 100;
    } else {
        return (disk.stats.trim_bytes_done / disk.stats.trim_bytes_est) * 100;
    }
}

function handleTrimPercentage(percentage : number) {
    if (percentage <= 0) {
        return 0;
    } else if (percentage >= 99.95) {
        return 100;
    } else if (percentage > 0 && percentage < 99.5){
        return percentage;
    } else {
        return 0;
    }
}

function getTrimmedAmount(disk) {
    return convertBytesToSize(disk.stats.trim_bytes_done);
}

function getTrimmedTotal(disk) {
    return convertBytesToSize(disk.stats.trim_bytes_est);
}

function trimMessage(disk) {
    switch (getTrimState(disk.stats.trim_state)) {
        case 'none':
            return `Trim Information N/A`; 
        case 'active':
            return `Trim ${getTrimState(disk.stats.trim_state)}, started at ${getTrimTimestamp(disk)}`; 
        case 'canceled':
            return `Trim ${getTrimState(disk.stats.trim_state)}`;
        case 'suspended':
            return `Trim is ${getTrimState(disk.stats.trim_state)}`;
        case 'finished':
            return `Trim ${getTrimState(disk.stats.trim_state)} at ${getTrimTimestamp(disk)}`;
        default:
            break;
    }
}

function getTrimState(state_num) {
    switch (state_num) {
        case 0:
            return 'none';
        case 1:
            return 'active';
        case 2:
            return 'canceled';
        case 3:
            return 'suspended';
        case 4:
            return 'finished';
        default:
            break;
    }
}

function trimMessageClass(disk) {
    switch (getTrimState(disk.stats.trim_state)) {
        case 'none':
            return ``; 
        case 'active':
            return 'text-default';
        case 'canceled':
            return 'text-danger';
        case 'suspended':
            return 'text-orange-600';
        case 'finished':
            return 'text-success';
        default:
            break;
    }
}

function trimProgressBarClass(disk) {
    switch (getTrimState(disk.stats.trim_state)) {
        case 'none':
            return ``; 
        case 'active':
            return 'bg-blue-600';
        case 'canceled':
            return 'bg-danger';
        case 'suspended':
            return 'bg-orange-600';
        case 'finished':
            return 'bg-green-600';
        default:
            break;
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