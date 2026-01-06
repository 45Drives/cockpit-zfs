<template>
    <Modal @clickOutside="closeModal()" :show="showAddVDevModal" class=" !w-3/5 !mt-28 rounded-lg">
        <!-- <OldModal @close="closeModal" :isOpen="showAddVDevModal" :marginTop="props.marginTop" :width="'w-3/5'"
        :minWidth="'min-w-3/5'" :closeOnBackgroundClick="false"> -->
        <CardContainer class="!w-3/5 !mt-28 mx-auto rounded-lg">
            <template v-slot:header>
                Add Virtual Device
            </template>
            <!-- <template v-slot:content> -->
            <div>
                <!-- Virtual Device (Select) -->
                <div>
                    <label :for="getIdKey('virtual-device')"
                        class="block text-sm font-medium leading-6 text-default">Type</label>
                    <!-- if first VDev, always either DISK, MIRROR, RAIDZ1-3 -->
                    <!-- if NOT first VDev, always either CACHE, LOG, SPECIAL, SPARE, DEDUP, or TYPE OF FIRST VDEV -->
                    <select id="virtual-device" v-model="newVDev.type" name="virtual-device"
                        class="text-default bg-default mt-1 block w-full input-textlike sm:text-sm sm:leading-6">
                        <option v-if="props.pool.vdevs[0].type == 'data' && firstVDevType == 'disk'" value="disk">
                            Disk
                        </option>
                        <option v-if="props.pool.vdevs[0].type == 'data' && firstVDevType == 'mirror'" value="mirror">
                            Mirror</option>
                        <option v-if="props.pool.vdevs[0].type == 'data' && firstVDevType == 'raidz1'" value="raidz1">
                            RaidZ1</option>
                        <option v-if="props.pool.vdevs[0].type == 'data' && firstVDevType == 'raidz2'" value="raidz2">
                            RaidZ2</option>
                        <option v-if="props.pool.vdevs[0].type == 'data' && firstVDevType == 'raidz3'" value="raidz3">
                            RaidZ3</option>
                        <option value="cache">Cache</option>
                        <option value="log">Log</option>
                        <option value="special">Special</option>
                        <option value="spare">Spare</option>
                        <option value="dedup">Dedup</option>
                    </select>
                </div>

                <!-- If (Log, Special, Dedup) -->
                <!-- If secondary VDev is LOG or SPECIAL or DEDUP, have option for them to be MIRROR also -->
                <!-- If Primary VDev is MIRROR or RAIDZ(x) then SPECIAL, LOG and DEDUP must be MIRROR -->
                <div v-if="newVDev.type == 'log' || newVDev.type == 'special' || newVDev.type == 'dedup'">
                    <label :for="getIdKey('mirror-enabled')"
                        class="mt-1 block text-sm font-medium leading-6 text-default">{{
                        upperCaseWord(newVDev.type) }}
                        (Mirror)</label>
                    <Switch v-model="newVDev.isMirror"
                        :class="[newVDev.isMirror ? 'bg-primary' : 'bg-accent', 'mt-1  relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                        <span class="sr-only">Use setting</span>
                        <span
                            :class="[newVDev.isMirror ? 'translate-x-5' : 'translate-x-0', ' relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                            <span
                                :class="[newVDev.isMirror ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                aria-hidden="true">
                                <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                    <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2"
                                        stroke-linecap="round" stroke-linejoin="round" />
                                </svg>
                            </span>
                            <span
                                :class="[newVDev.isMirror ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                aria-hidden="true">
                                <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                    <path
                                        d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                </svg>
                            </span>
                        </span>
                    </Switch>
                </div>

                <!-- Disk ID (Select) -->
                <div>
                    <label :for="getIdKey('disk-identifier')"
                        class="block text-sm font-medium leading-6 text-default">Disk
                        Identifier</label>
                    <select :id="getIdKey('disk-identifier')" v-model="diskIdentifier" name="disk-identifier"
                        class="text-default bg-default mt-1 block w-full input-textlike sm:text-sm sm:leading-6">
                        <option value="sd_path">Block Device</option>
                        <!-- <option value="">Disk/WWN</option> -->
                        <option value="phy_path">Hardware Path</option>
                        <option value="vdev_path">Device Alias</option>
                    </select>
                </div>

                <!-- Disk selection, shows disks that are not in use and as they are selected it hides them from any additional VDevs so they cannot be selected twice -->
                <label :for="getIdKey('available-disk-list')"
                    class="my-1 block text-sm font-medium leading-6 text-default">Select
                    Disks</label>
                <ul v-if="availableDisks.length > 0" :id="getIdKey('available-disk-list')" role="list"
                    class="flex flex-row flex-wrap gap-2">
                    <li v-for="(disk, diskIdx) in availableDisks" :key="diskIdx" class="my-2">
                        <button class="flex min-w-fit w-full h-full border border-default rounded-lg"
                            :title="disk.hasPartitions! ? 'Disk already has partitions. Proceed with caution.' : getDiskIDName(allDisks, diskIdentifier, disk.name!)"
                            :class="diskCardClass(disk.name)">
                            <label :for="getIdKey(`disk-${diskIdx}`)"
                                class="flex flex-col w-full py-4 mx-2 text-sm gap-0.5 justify-start">
                                <span class="flex flex-row flex-grow w-full justify-between">
                                    <input :id="getIdKey(`disk-${diskIdx}`)" v-model="selectedDisks" type="checkbox"
                                        :value="`${disk.name}`" :name="`disk-${disk.name}`"
                                        class="justify-start w-4 h-4 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2" />
                                    <div v-if="disk.hasPartitions!"
                                        title="Disk already has partitions. Proceed with caution."
                                        class="flex items-center justify-center h-6 w-6 bg-default rounded-full ml-2">
                                        <ExclamationCircleIcon class="h-6 text-orange-700" />
                                    </div>
                                    <div v-if="disk.errors && disk.errors!.length > 0"
                                        title="This disk belongs to an exported pool. Force Add to override."
                                        class="flex items-center justify-center h-6 w-6 bg-default rounded-full ml-2">
                                        <ExclamationTriangleIcon class="h-6 text-danger" />
                                    </div>
                                </span>
                                <h3 class="truncate text-sm font-medium text-default">
                                    {{ truncateName((getDiskIDName(allDisks, diskIdentifier, disk.name!)), 8) }}
                                </h3>
                                <p class="mt-1 truncate text-sm text-default">{{ disk.type }}</p>
                                <p class="mt-1 truncate text-sm text-default">Capacity: {{ disk.capacity }}</p>
                            </label>
                        </button>
                    </li>
                </ul>
                <div v-if="availableDisks.length == 0">
                    No Disks Available
                </div>

            </div>
            <!-- </template> -->
            <template v-slot:footer>
                <div class="w-full grid grid-rows-2">
                    <div class="w-full row-start-1 justify-center items-center">
                        <div class="justify-self-start mt-2">
                            <p class="text-danger" v-if="diskFeedback">{{ diskFeedback }}</p>
                            <p class="text-danger" v-if="diskSizeFeedback">{{ diskSizeFeedback }}</p>
                            <p class="text-danger" v-if="isProperReplicationFeedback">{{ isProperReplicationFeedback }}
                            </p>
                            <p class="text-danger" v-if="diskBelongsFeedback">{{ diskBelongsFeedback }}</p>
                        </div>
                    </div>

                    <!-- <div class="button-group-row w-full justify-center row-start-2">
                        <div class="button-group-row mt-2">
                            <button @click="showAddVDevModal = false" :id="getIdKey('close-add-vdev-btn')"
                                name="close-add-vdev-btn" class="btn btn-danger h-fit w-full">Close</button>

                            <div class="flex flex-row w-full">
                                <label :for="getIdKey('force-add-vdev')"
                                    class="mr-2 block text-sm font-medium leading-6 text-default grow">Forcefully
                                    Add</label>
                                <Switch @click="toggleForceAdd" :id="getIdKey('force-add-vdev')"
                                    :class="[newVDev.forceAdd! ? 'bg-primary' : 'bg-accent', ' mt-2 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                                    <span class="sr-only">Use setting</span>
                                    <span
                                        :class="[newVDev.forceAdd! ? 'translate-x-5' : 'translate-x-0', ' relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                        <span
                                            :class="[newVDev.forceAdd! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                            aria-hidden="true">
                                            <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                                <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                            </svg>
                                        </span>
                                        <span
                                            :class="[newVDev.forceAdd! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                            aria-hidden="true">
                                            <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                                <path
                                                    d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                            </svg>
                                        </span>
                                    </span>
                                </Switch>
                            </div>
                        </div>
                        <div class="button-group-row mt-2">
                            <button v-if="!adding" id="add-vdev-btn"
                                class="btn btn-primary object-right justify-end mr-4 h-fit w-full"
                                @click="addVDevBtn">Add
                                VDev</button>
                            <button disabled v-if="adding" id="finish" type="button"
                                class="btn btn-primary object-right justify-end h-fit w-full">
                                <svg aria-hidden="true" role="status"
                                    class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default"
                                    viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                        fill="currentColor" />
                                    <path
                                        d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                        fill="text-success" />
                                </svg>
                                Adding...
                            </button>
                        </div>
                    </div> -->
                    <div class="flex w-full items-center">
                        <!-- Left Button -->
                        <div class="button-group-row mt-2">
                            <button @click="showAddVDevModal = false" :id="getIdKey('close-add-vdev-btn')"
                                name="close-add-vdev-btn" class="btn btn-danger h-fit">
                                Close
                            </button>
                        </div>
                        <!-- Middle Expandable Section -->
                        <div class="flex flex-row items-center justify-center flex-grow text-center">
                            <label :for="getIdKey('force-add-vdev')"
                                class="mr-2 block text-sm font-medium leading-6 text-default">
                                Forcefully Add
                            </label>
                            <Switch @click="toggleForceAdd" :id="getIdKey('force-add-vdev')"
                                :class="[newVDev.forceAdd!.force ? 'bg-primary' : 'bg-accent', 'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                                <span class="sr-only">Use setting</span>
                                <span
                                    :class="[newVDev.forceAdd!.force ? 'translate-x-5' : 'translate-x-0', ' relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                    <span
                                        :class="[newVDev.forceAdd!.force ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                        aria-hidden="true">
                                        <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                            <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                                stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                        </svg>
                                    </span>
                                    <span
                                        :class="[newVDev.forceAdd!.force ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                        aria-hidden="true">
                                        <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                            <path
                                                d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                        </svg>
                                    </span>
                                </span>
                            </Switch>
                        </div>

                        <!-- Right Button -->
                        <div class="button-group-row mt-2">
                            <button v-if="!adding" id="add-vdev-btn"
                                class="btn btn-primary object-right justify-end mr-4 h-fit w-full"
                                @click="addVDevBtn">Add
                                VDev</button>
                            <button disabled v-if="adding" id="finish" type="button"
                                class="btn btn-primary object-right justify-end h-fit w-full">
                                <svg aria-hidden="true" role="status"
                                    class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default"
                                    viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                        fill="currentColor" />
                                    <path
                                        d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                        fill="text-success" />
                                </svg>
                                Adding...
                            </button>
                        </div>
                    </div>

                </div>
            </template>
        </CardContainer>
        <!-- </OldModal> -->
    </Modal>
</template>

<style>
.switch-class,
input[type="checkbox"] {
    pointer-events: auto !important;
}
</style>

<script setup lang="ts">
import { ref, inject, Ref, computed, onMounted } from 'vue';
import { Switch } from '@headlessui/vue';
import { ExclamationCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import { upperCaseWord, convertSizeToBytes } from '../../composables/helpers';
import { setRefreservation } from '../../composables/pools';
import { getDiskIDName, truncateName, getFullDiskInfo } from '../../composables/helpers';
import { loadImportablePools } from '../../composables/loadImportables';
import { ZFSManager, ZPool, ZFSFileSystemInfo, VDev, DiskIdentifier, VDevDisk } from "@45drives/houston-common-lib"
import { pushNotification, Notification, Modal, CardContainer } from '@45drives/houston-common-ui';
// import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { PoolScanObjectGroup, PoolDiskStats, Activity } from '../../types';
import { useRefreshAllData } from '../../composables/useRefreshAllData';

interface AddVDevModalProps {
    idKey: string;
    pool: ZPool;
    marginTop: string;
}

const zfsManager = new ZFSManager();
const props = defineProps<AddVDevModalProps>();

const showAddVDevModal = inject<Ref<boolean>>('show-vdev-modal')!;

const firstVDevType = ref('');
const firstVDevIsDisk = ref(false);

function toggleForceAdd() {
    newVDev.value = {
        ...newVDev.value, // spread the existing properties
        forceAdd: { force: !newVDev.value.forceAdd!.force } // explicitly create a new object
    };
}


function getVDevType() {
    const firstVDevName = props.pool.vdevs[0].name;
    firstVDevIsDisk.value = (props.pool.vdevs[0].disks.length == 1) ? true : false;
    if (!firstVDevIsDisk.value) {
        const strippedType = firstVDevName!.substring(0, firstVDevName!.indexOf('-'));
        firstVDevType.value = strippedType;
    } else {
        firstVDevType.value = 'disk';
    }

    // console.log('firstVDevType:', firstVDevType.value);
    newVDev.value.type = firstVDevType.value;
}

const newVDev = ref<VDev>({
    type: firstVDevType.value,
    disks: [],
    isMirror: false,
    forceAdd: { force: false },
});


const selectedDisks = ref<string[]>([])!;
const truncateText = inject<Ref<string>>('style-truncate-text')!;

const diskFeedback = ref('');
const diskSizeFeedback = ref('');
const isProperReplicationFeedback = ref('');
const diskBelongsFeedback = ref('');

const pools = inject<Ref<ZPool[]>>('pools')!;
const allDisks = inject<Ref<VDevDisk[]>>('disks')!;
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;

const diskIdentifier = ref<DiskIdentifier>('vdev_path');

const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;

const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const availableDisks = computed<VDevDisk[]>(() => {
    return allDisks.value.filter(disk => disk.guid === "");
});

// watch(selectedDisks, (newVal, oldVal) => {
//     console.log('selectedDisks:', selectedDisks.value);
// });

//change color of disk when selected
const diskCardClass = (diskName) => {
    const isSelected = selectedDisks.value.includes(diskName);
    return isSelected ? 'bg-green-300 dark:bg-green-700' : '';
};

const adding = ref(false);

async function addVDevBtn() {
    newVDev.value.disks = [];   
    if (replicationLevelCheck() && diskSizeMatch() && diskCheck()) {
        if (!diskBelongsToImportablePool() || newVDev.value.forceAdd!) {

            for (const selectedDisk of selectedDisks.value) {
                const diskNameFinal = getDiskIDName(allDisks.value, diskIdentifier.value, selectedDisk);
                const diskFinal = getFullDiskInfo(allDisks.value, diskNameFinal);
                if (diskFinal) newVDev.value.disks.push(diskFinal);
            }

            // dedupe just in case (by a stable key; vdev_path is safest here)
            const seen = new Set<string>();
            newVDev.value.disks = newVDev.value.disks.filter(d => {
                const key = d.vdev_path || d.phy_path || d.sd_path || d.name;
                if (!key || seen.has(key)) return false;
                seen.add(key);
                return true;
            });

            adding.value = true;

            try {
                const output: any = await zfsManager.addVDevsToPool(props.pool, [newVDev.value], newVDev.value.forceAdd!);
                if (output == null || output.error) {
                    const errorMessage = output?.error || 'Unknown error';
                    pushNotification(new Notification('Add VDev Failed', `There was an error adding this virtual device: ${errorMessage}`, 'error', 5000));

                } else {
                    pushNotification(new Notification('Added VDev', `Virtual device added successfully.`, 'success', 5000));

                    if (props.pool.properties.refreservationRawSize!) {
                        const output: any = await setRefreservation(props.pool, props.pool.properties.refreservationPercent!);
                        if (output == null || output.error) {
                            const errorMessage = output?.error || 'Unknown error';
                            pushNotification(new Notification('Refreservation Update Failed', `There was an error updating pools refreservation value: ${errorMessage}`, 'error', 5000));
                        } else {
                            pushNotification(new Notification('Refreservation Updated', `Refreservation of pool was updated successfully.`, 'success', 5000));
                            resetModalState();
                            showAddVDevModal.value = false;
                        }
                    } else {
                        showAddVDevModal.value = false;
                    }
                }

            } catch (error) {
                pushNotification(new Notification('Add VDev Failed', `There was an error adding this virtual device: ${error}`, 'error', 5000));
                adding.value = false;
                console.error(error);
            } finally {
                adding.value = false;
                await refreshAllData();
            }

        }
    }
}

function resetModalState() {
    newVDev.value = { type: firstVDevType.value, disks: [], isMirror: false, forceAdd: { force: false } };
    selectedDisks.value = [];
    diskFeedback.value = '';
    diskSizeFeedback.value = '';
    isProperReplicationFeedback.value = '';
    diskBelongsFeedback.value = '';
}

const { refreshAllData } = useRefreshAllData({
    poolData: pools,
    diskData: allDisks,
    filesystemData: datasets,
    disksLoaded,
    poolsLoaded,
    fileSystemsLoaded,
    scanObjectGroup,
    poolDiskStats,
    scanActivities,
    trimActivities
});


/////////////////// Validation //////////////////////
/////////////////////////////////////////////////////

const replicationLevelCheck = () => {
    let result = true;
    isProperReplicationFeedback.value = '';

    if ((newVDev.value.type == 'dedup' || newVDev.value.type == 'special') && !newVDev.value.forceAdd && !newVDev.value.isMirror) {
        result = false;
        isProperReplicationFeedback.value = 'Mismatched replication level. Forcefully create to override.';
    } else if (newVDev.value.isMirror && (newVDev.value.type == 'special' || newVDev.value.type == 'dedup' || newVDev.value.type == 'log') && selectedDisks.value.length < 2) {
        result = false;
        isProperReplicationFeedback.value = `Two or more Disks are required for Mirror (${upperCaseWord(newVDev.value.type)}).`;
    }

    return result;
}

const diskSizeMatch = () => {
    let result = true;
    diskSizeFeedback.value = '';

    if (newVDev.value!.forceAdd) {
        return true;
    }
    if (newVDev.value.type === 'disk') {
        return true;
    }
    let previousCapacity = 0;

    selectedDisks.value.forEach(selDisk => {
        const disk = allDisks.value.find(fullDisk => fullDisk.name == selDisk);

        if (disk) {
            const currentCapacity = convertSizeToBytes(disk.capacity!);

            if (previousCapacity != 0 && currentCapacity != previousCapacity) {
                diskSizeFeedback.value = `Mirror contains devices of different sizes. Forcefully create to override.\n`;
                result = false;
            }

            previousCapacity = currentCapacity;
        }

    });

    return result;
}

const importablePools = inject<Ref<ZPool[]>>('importable-pools')!;
const diskBelongsToImportablePool = () => {
    let result = false;
    diskBelongsFeedback.value = '';

    if (newVDev.value.forceAdd) {
        return false;
    }

    selectedDisks.value.forEach(diskName => {
        const selectedDisk = allDisks.value.find(fullDisk => fullDisk.name == diskName);
        // console.log('selectedDisk:', selectedDisk);
        importablePools.value.forEach(pool => {
            // console.log('importablePool:', pool);
            pool.vdevs.forEach(importableVDev => {
                // console.log('importableVDev:', importableVDev);
                importableVDev.disks.forEach(disk => {
                    // console.log('importableDisk:', disk);
                    if (selectedDisk!.name == disk.name) {
                        result = true;
                        diskBelongsFeedback.value = `This disk was used in exported pool '${pool.name}'.\n Use Force Add to override and use disk in new Vdev.`;
                        // console.log(`Disk belongs to importable pool: ${pool.name}`);
                    }
                });
            });
        });
    });

    // console.log('diskBelongsFeedback:', diskBelongsFeedback.value);
    return result;
}

//method for validating disk selection per vdev type
const diskCheck = () => {
    let result = true;
    diskFeedback.value = '';

    if (newVDev.value.type == 'mirror' && selectedDisks.value.length < 2) {
        diskFeedback.value = 'Two or more Disks are required for Mirror.';
        result = false;
    } else if (newVDev.value.type == 'raidz1' && selectedDisks.value.length < 3) {
        result = false;
        diskFeedback.value = 'Three or more Disks are required for RaidZ1.';
    } else if (newVDev.value.type == 'raidz2' && selectedDisks.value.length < 4) {
        result = false;
        diskFeedback.value = 'Four or more Disks are required for RaidZ2.';
    } else if (newVDev.value.type == 'raidz3' && selectedDisks.value.length < 5) {
        result = false;
        diskFeedback.value = 'Five or more Disks are required for RaidZ3.';
    } else if (newVDev.value.type == 'disk' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required.';
        result = false;
    } else if (newVDev.value.type == 'log' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required for Log.';
        result = false;
    } else if (newVDev.value.type == 'cache' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required for Cache.';
        result = false;
    } else if (newVDev.value.type == 'special' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required for Special.';
        result = false;
    } else if (newVDev.value.type == 'spare' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required for Spare.';
        result = false;
    } else if (newVDev.value.type == 'dedup' && selectedDisks.value.length < 1) {
        diskFeedback.value = 'At least one Disk is required for Dedup.';
        result = false;
    }

    return result;
}

const closeModal = () => {
    resetModalState();
    showAddVDevModal.value = false;
    emit('close');
}
const emit = defineEmits(['close']);

onMounted(() => {
    getVDevType();
    loadImportablePools(importablePools.value, allDisks, pools);
});

const getIdKey = (name: string) => `${props.idKey}-${name}`;
</script>