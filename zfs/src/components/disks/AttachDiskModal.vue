<template>
    <OldModal :isOpen="showFlag" @close="closeModal()" :marginTop="'mt-28'" :width="'w-3/5'" :minWidth="'min-w-3/5'" :closeOnBackgroundClick="false">
        <template v-slot:title>
            Attach Disk
        </template>
        <template v-slot:content>
            <div>
                <!-- Disk ID (Select) -->
                <div>
                    <label :for="getIdKey('disk-identifier')"
                        class="block text-sm font-medium leading-6 text-default">Disk Identifier</label>
                    <select :id="getIdKey('disk-identifier')" v-model="diskIdentifier" name="disk-identifier"
                        class="text-default bg-default mt-1 block w-full input-textlike sm:text-sm sm:leading-6">
                        <option value="sd_path">Block Device</option>
                        <option value="phy_path">Hardware Path</option>
                        <option value="vdev_path">Device Alias</option>
                    </select>
                </div>

                <!-- Disk selection, shows disks that are not in use and as they are selected it hides them from any additional VDevs so they cannot be selected twice -->
                <label :for="getIdKey('available-disk-list')"
                    class="my-1 block text-sm font-medium leading-6 text-default">Select Disks</label>
                <ul v-if="availableDisks.length > 0" :id="getIdKey('available-disk-list')" role="list"
                    class="flex flex-row flex-wrap gap-2">
                    <li v-for="(disk, diskIdx) in availableDisks" :key="diskIdx" class="my-2">
                        <button class="flex min-w-fit w-full h-full border border-default rounded-lg"
                            :title="disk.hasPartitions! ? 'Disk already has partitions. Proceed with caution.' : getDiskIDName(allDisks, diskIdentifier, disk.name!)"
                            :class="diskCardClass(disk.name)">
                            <label :for="getIdKey(`disk-${diskIdx}`)"
                                class="flex flex-col w-full py-4 mx-2 text-sm gap-0.5 justify-start">
                                <span class="flex flex-row flex-grow w-full justify-between">
                                    <input :id="getIdKey(`disk-${diskIdx}`)" type="checkbox" :value="disk.name"
                                        :name="`disk-${disk.name}`" :checked="selectedDisk === disk.name"
                                        @change="selectSingleDisk(disk.name)"
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
                                    {{ truncateName((getDiskIDName(allDisks, diskIdentifier, disk.name!)), 8) }}</h3>
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
        </template>
        <template v-slot:footer>
            <div class="w-full grid grid-rows-2">
                <div class="w-full row-start-1 justify-center items-center">
                    <div class="justify-self-start mt-2">
                        <p class="text-danger" v-if="diskSizeFeedback">{{ diskSizeFeedback }}</p>
                        <p class="text-danger" v-if="diskBelongsFeedback">{{ diskBelongsFeedback }}</p>
                    </div>
                </div>

                <div class="button-group-row w-full justify-between row-start-2">
                    <div class="button-group-row mt-2">
                        <button @click="closeModal" :id="getIdKey('close-attach-disk-btn')" name="close-attach-disk-btn"
                            class="btn btn-danger">Close</button>

                        <div class="flex flex-row">
                            <label :for="getIdKey('force-add-vdev')"
                                class="mt-2 mr-2 block text-sm font-medium leading-6 text-default">Forcefully Attach
                                Disk</label>
                            <Switch v-model="diskVDevPoolData.forceAttach" :id="getIdKey('force-add-vdev')"
                                :class="[diskVDevPoolData.forceAttach! ? 'bg-primary' : 'bg-accent', 'mt-2 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                                <span class="sr-only">Use setting</span>
                                <span
                                    :class="[diskVDevPoolData.forceAttach! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                    <span
                                        :class="[diskVDevPoolData.forceAttach! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                        aria-hidden="true">
                                        <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                            <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                                stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                        </svg>
                                    </span>
                                    <span
                                        :class="[diskVDevPoolData.forceAttach! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
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
                        <button v-if="!adding" id="attach-disk-btn"
                            class="btn btn-primary object-right justify-end mr-4 h-fit w-full"
                            @click="attachDiskBtn">Attach Disk</button>
                        <button disabled v-if="adding" id="finish" type="button"
                            class="btn btn-primary object-right justify-end">
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
                            Attaching...
                        </button>
                    </div>
                </div>
            </div>
        </template>
    </OldModal>
</template>

<script setup lang="ts">
import { ref, inject, Ref, computed, onMounted } from 'vue';
import { Switch } from '@headlessui/vue';
import OldModal from '../common/OldModal.vue';
import { ExclamationCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import { convertSizeToBytes, getDiskIDName, truncateName } from '../../composables/helpers';
import { attachDisk } from '../../composables/disks';
import { loadImportablePools } from '../../composables/loadImportables';
import { ZPool, VDev, VDevDisk, ZFSFileSystemInfo, DiskIdentifier } from '@45drives/houston-common-lib';
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { PoolScanObjectGroup, PoolDiskStats, Activity } from '../../types';
import { useRefreshAllData } from '../../composables/useRefreshAllData';

interface AttachDiskModalProps {
	idKey: string;
    pool: ZPool;
    vDev: VDev;
    showFlag: boolean;
}

const props = defineProps<AttachDiskModalProps>();
const showFlag = ref(props.showFlag);
const truncateText = inject<Ref<string>>('style-truncate-text')!;

const emit = defineEmits(['close']);

const closeModal = () => {
    emit('close');
}

onMounted(() => {
    // debuggingInfo();
});

function debuggingInfo() {
    console.log('pool:', props.pool);
    console.log('vDev:', props.vDev);
    console.log('allDisks:', allDisks.value);
    availableDisks.value.forEach(availableDisk => {
        console.log(getDiskIDName(allDisks.value, diskIdentifier.value, availableDisk.name!));
    });
}

const showAttachDiskModal = inject<Ref<boolean>>('show-attach-modal')!;

const selectedDisk = ref(''); // Holds the name of the selected disk

function selectSingleDisk(diskName) {
    // If the same disk is clicked again, deselect it; otherwise, select the new disk
    selectedDisk.value = selectedDisk.value === diskName ? '' : diskName;
}

const pools = inject<Ref<ZPool[]>>('pools')!;
const allDisks = inject<Ref<VDevDisk[]>>('disks')!;
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;

const diskIdentifier = ref<DiskIdentifier>('vdev_path');
const diskSizeFeedback = ref('')

const phyPathPrefix = '/dev/disk/by-path/';
const sdPathPrefix = '/dev/';
const newDisk = ref();
const oldDisk = ref();
const diskNewName = ref('');
const diskNewPath = ref('');
const diskExistPath = ref('');
const diskExistName = ref('');
const diskBelongsFeedback = ref('');

const adding = ref(false);

const poolData = inject<Ref<ZPool[]>>("pools")!;
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;

const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const diskVDevPoolData = ref({
    existingDiskName: '',
    newDiskName: '',
    vDevName: props.vDev.name,
    poolName: props.pool.name,
    forceAttach: false,
});


const availableDisks = computed<VDevDisk[]>(() => {
    return allDisks.value.filter(disk => disk.guid === "");
});

//change color of disk when selected
const diskCardClass = (diskName) => {
    return selectedDisk.value === diskName ? 'bg-green-300 dark:bg-green-700' : '';
};

function setDiskNamePath() {
    const oldDisks = props.vDev.disks;
    // console.log('setting oldDisks:', oldDisks);
    oldDisk.value = oldDisks.pop();
    // console.log('setting oldDisk.value:', oldDisk.value);
    // console.log('getting selectedDisk.value:', selectedDisk.value);
    newDisk.value = allDisks.value.find(disk => disk.name === selectedDisk.value);
    // console.log('setting newDisk.value:', newDisk.value);
    switch (diskIdentifier.value) {
        case 'vdev_path':
            diskNewPath.value = newDisk.value!.vdev_path;
            diskNewName.value = selectedDisk.value;
            diskExistPath.value = oldDisk.value!.path;
            diskExistName.value = oldDisk.value!.name;
            // console.log('diskNewPath:', diskNewPath.value, 'diskNewName:', diskNewName.value);
            // console.log('diskExistPath:', diskExistPath.value, 'diskExistName:', diskExistName.value);
            break;
        case 'phy_path':
            diskNewPath.value = newDisk.value!.phy_path;
            diskNewName.value = diskNewPath.value.replace(phyPathPrefix, '');
            diskExistPath.value = oldDisk.value!.path;
            diskExistName.value = diskExistPath.value.replace(phyPathPrefix, '');
            // console.log('diskNewPath:', diskNewPath.value, 'diskNewName:', diskNewName.value);
            // console.log('diskExistPath:', diskExistPath.value, 'diskExistName:', diskExistName.value);
            break;
        case 'sd_path':
            diskNewPath.value = newDisk.value!.sd_path;
            diskNewName.value = diskNewPath.value.replace(sdPathPrefix, '');
            diskExistPath.value = oldDisk.value!.path;
            diskExistName.value = diskExistPath.value.replace(sdPathPrefix, '');
            // console.log('diskNewPath:', diskNewPath.value, 'diskNewName:', diskNewName.value);
            // console.log('diskExistPath:', diskExistPath.value, 'diskExistName:', diskExistName.value);
            break;
        default:
            console.log('error with set diskName/paths');
            break;
    }
}

async function attachDiskBtn() {
    if (diskSizeMatch()) {
        if (!diskBelongsToImportablePool() || diskVDevPoolData.value.forceAttach) {
            setDiskNamePath();
            diskVDevPoolData.value.newDiskName = diskNewName.value;
            diskVDevPoolData.value.existingDiskName = diskExistName.value;
            // console.log('all data of disk being attached:', diskVDevPoolData.value);
                
            adding.value = true;
            try {
                const output: any = await attachDisk(diskVDevPoolData.value);

                if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
                    adding.value = false;
                    pushNotification(new Notification('Disk Attach Failed', `There was an error attaching this disk: ${errorMessage}`, 'error', 5000));
                } else {
                    showAttachDiskModal.value = false;
                    adding.value = false;
                    await refreshAllData();
                    pushNotification(new Notification('Disk Attached', `Attached disk to virtual device successfully.`, 'success', 5000));
                }
            } catch (error) {
                console.error(error);
            }

          
        }
       
    }
}

const diskSizeMatch = () => {
    let result = true;
    diskSizeFeedback.value = '';
    // console.log("Checking disk:", selectedDisk.value);
    
    if (selectedDisk.value == '') {
        diskSizeFeedback.value = 'At least one disk is required.'
        return false;
    }

    const newDiskData = allDisks.value.find(fullDisk => fullDisk.name === selectedDisk.value);

    if (newDiskData) {
        const newCapacity = convertSizeToBytes(newDiskData!.capacity!);
        // console.log('newCapacity:', newCapacity);

        const oldDisks = props.vDev.disks;
        // console.log('oldDisks:', oldDisks);

        for (const oldDisk of oldDisks) {
            const currentCapacity = convertSizeToBytes(oldDisk.capacity!);
            // console.log('currentCapacity:', currentCapacity);

            if (newCapacity < currentCapacity) {
                diskSizeFeedback.value = "Cannot Attach. Please select a disk that has capacity greater than or equal to current disks."
                result = false;
                break;
            }
        }
    }

    return result;
};

const importablePools = inject<Ref<ZPool[]>>('importable-pools')!;
const diskBelongsToImportablePool = () => {
	let result = false;
	diskBelongsFeedback.value = '';

	if (diskVDevPoolData.value.forceAttach) {
		return false;
	}
        const selectedNewDisk = allDisks.value.find(fullDisk => fullDisk.name == selectedDisk.value);
        // console.log('selectedDisk:', selectedDisk);
        importablePools.value.forEach(pool => {
            // console.log('importablePool:', pool);
            pool.vdevs.forEach(importableVDev => {
                // console.log('importableVDev:', importableVDev);
                importableVDev.disks.forEach(disk => {
                    // console.log('importableDisk:', disk);
                    if (selectedNewDisk!.name == disk.name) {
                        result = true;
                        diskBelongsFeedback.value = `This disk was used in exported pool '${pool.name}'.\n Use Force Add to override and use disk in new Vdev.`;
                        console.log(`Disk belongs to importable pool: ${pool.name}`);
                    }
                });
            });
        });

	// console.log('diskBelongsFeedback:', diskBelongsFeedback.value);
	return result;
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

onMounted(() => {
	loadImportablePools(importablePools.value, allDisks, pools);
});

const getIdKey = (name: string) => `${props.idKey}-${name}`;
</script>