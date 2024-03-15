<template>
    <Modal :isOpen="showSnapshotModal" :marginTop="'mt-48'" :width="'w-4/12'" :minWidth="'min-w-4/12'" class="z-20">
        <template v-slot:title>
            <legend class="flex justify-center">Create Snapshot</legend>
        </template>
        <template v-slot:content>
            <div>
                <div>
					<label :for="getIdKey('file-system')" class="block text-sm font-medium leading-6 text-default">File System</label>
					<select v-if="props.item == 'pool'" id="file-system" v-model="newSnapshot.filesystem" name="file-system" :class="truncateText" class="text-default bg-default mt-1 block w-full rounded-md border-0 py-1.5 pl-3 pr-10 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-slate-600 sm:text-sm sm:leading-6">
						<option v-for="dataset in datasetsInSamePool" :value="dataset.name" :class="truncateText" :title="dataset.name">{{ dataset.name }}</option>
					</select>
                    <select v-if="props.item == 'filesystem'" id="file-system" v-model="newSnapshot.filesystem" name="file-system" :class="truncateText" class="text-default bg-default mt-1 block w-full rounded-md border-0 py-1.5 pl-3 pr-10 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-slate-600 sm:text-sm sm:leading-6">
						<option v-for="dataset in datasets" :value="dataset.name" :class="truncateText" :title="dataset.name">{{ dataset.name }}</option>
					</select>
				</div>
                <div>
                    <label :for="getIdKey('custom-name')" class="mt-1 block text-sm font-medium leading-6 text-default">Custom Name</label>
                    <Switch :id="getIdKey('custom-name')" v-model="newSnapshot.isCustomName" :class="[newSnapshot.isCustomName ? 'bg-primary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                        <span class="sr-only">Use setting</span>
                        <span :class="[newSnapshot.isCustomName ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                            <span :class="[newSnapshot.isCustomName ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                    <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                </svg>
                            </span>
                            <span :class="[newSnapshot.isCustomName ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                    <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                </svg>
                            </span>
                        </span>
                    </Switch>
                </div>
                <div>
					<label :for="getIdKey('snapshot-name')" class="block text-sm font-medium leading-6 text-default">Snapshot Name</label>
                    <input v-if="!newSnapshot.isCustomName" type="text" v-model="newSnapshot.name" name="snapshot-name" :id="getIdKey('snapshot-name')" class="mt-1 block w-full input-textlike bg-default" placeholder="YYYY.MM.DD-HH.MM.SS" disabled/>
                    <input v-if="newSnapshot.isCustomName" @keydown.enter="createSnapButton(newSnapshot)" type="text" v-model="newSnapshot.name" name="snapshot-name" :id="getIdKey('snapshot-name')" class="mt-1 block w-full input-textlike bg-default" placeholder="Enter Name Here" />
                </div>
                <div>
                    <label :for="getIdKey('snap-children')" class="mt-1 block text-sm font-medium leading-6 text-default">Create snapshots of child file systems</label>
                    <Switch :id="getIdKey('snap-children')" v-model="newSnapshot.snapChildren" :class="[newSnapshot.snapChildren ? 'bg-primary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                        <span class="sr-only">Use setting</span>
                        <span :class="[newSnapshot.snapChildren ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                            <span :class="[newSnapshot.snapChildren ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                    <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                </svg>
                            </span>
                            <span :class="[newSnapshot.snapChildren ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                    <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                </svg>
                            </span>
                        </span>
                    </Switch>
                </div>
            </div>
        </template>
        <template v-slot:footer>
            <div class="w-full grid grid-rows-2">
                <div class="w-full">
                    <p class="text-danger" v-if="nameFeedback">{{ nameFeedback }}</p>
                    <p class="text-danger" v-if="filesystemFeedback">{{ filesystemFeedback }}</p>
                </div>
                <div class="button-group-row mt-2 justify-between">
                    <button @click="showSnapshotModal = false" :id="getIdKey('confirm-no')" name="button-no" class="mt-1 btn btn-danger object-left justify-start h-fit">Cancel</button>
        
                    <button v-if="!creating" @click="createSnapButton(newSnapshot)" :id="getIdKey('create-snapshot-btn')" name="create-snapshot-btn" class="mt-1 btn btn-primary">Create</button>
                    <button disabled v-if="creating" :id="getIdKey('create-snapshot-spinner')" type="button" class="btn btn-danger object-right justify-end h-fit">
                        <svg aria-hidden="true" role="status" class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
                            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="text-success"/>
                        </svg>
                        Creating...
                    </button> 
                </div>
            </div>
 
        </template>
    </Modal>
</template>

<script setup lang="ts">
import { ref, inject, Ref, computed } from 'vue';
import { Switch } from '@headlessui/vue';
import Modal from '../common/Modal.vue';
import { getSnapshotTimestamp } from '../../composables/helpers';
import { createSnapshot } from '../../composables/snapshots';
import { loadSnapshotsInDataset, loadSnapshotsInPool, loadDatasets, loadSnapshots } from '../../composables/loadData';

interface CreateSnapshotModalProps {
    item: 'pool' | 'filesystem';
    poolName?: string;
}
const notifications = inject<Ref<any>>('notifications')!;
    
const props = defineProps<CreateSnapshotModalProps>();
const truncateText = inject<Ref<string>>('style-truncate-text')!;
const datasets = inject<Ref<FileSystemData[]>>('datasets')!;
const datasetsInSamePool = computed<FileSystemData[]>(() => {
    return datasets.value.filter(dataset => dataset.pool === props.poolName);
});

const defaultFileSystem = ref();
const selectedDataset= inject<Ref<FileSystemData>>('selected-dataset')!;
const snapshots = inject<Ref<Snapshot[]>>('snapshots')!;

const showSnapshotModal = inject<Ref<boolean>>('create-snap-modal')!;
const creating = inject<Ref<boolean>>('creating')!;
const snapshotsLoaded = inject<Ref<boolean>>('snapshots-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const allDatasetsLoaded = inject<Ref<boolean>>('all-datasets-loaded')!;
const allDatasets = inject<Ref<any>>('all-datasets')!;
const pools = inject<Ref<PoolData[]>>('pools')!;

initialize();

function refreshSnapshots() {
    clearSnapshots();
    loadTheseSnapshots();
}

function clearSnapshots() {
    snapshots.value = [];
}

function loadTheseSnapshots() {
    if (props.item == 'pool') {
        loadSnapshotsInPool(snapshots, props.poolName);
    } else if (props.item == 'filesystem') {
        loadSnapshotsInDataset(snapshots, selectedDataset.value.name);
    }
}

function initialize() {
    clearSnapshots();
    loadTheseSnapshots();
    if (props.item == 'pool') {
        defaultFileSystem.value = datasetsInSamePool.value[0];
    } else if (props.item == 'filesystem') {
        defaultFileSystem.value = selectedDataset.value;
    }
}

const newSnapshot = ref<NewSnapshot>({
    name: '',
    filesystem: defaultFileSystem.value.name,
    isCustomName: false,
    snapChildren: false,
}); 

const nameFeedback = ref('');
const filesystemFeedback = ref('');
const confirmCreate = inject<Ref<boolean>>('confirm-create-snap')!;

const filesystemCheck = (newSnapshot : NewSnapshot) => {
	let result = true;
	filesystemFeedback.value = '';

	if (newSnapshot.filesystem == '') {
		result = false;
		filesystemFeedback.value = 'Please select a File System.';
	}

	return result;
}

const nameCheck = (newSnapshot : NewSnapshot) => {
	let result = true;
	nameFeedback.value = '';

	if (newSnapshot.name == '') {
		result = false;
		nameFeedback.value = 'Name cannot be empty.';
	} else if (!newSnapshot.name.match(/^[a-zA-Z0-9]/) ) {
		result = false;
		nameFeedback.value = 'Name must begin with alphanumeric characters.';
	} else if (newSnapshot.name.match(/^[ ]/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with whitespace.';
	} else if (newSnapshot.name.match(/[ ]$/)) {
		result = false;
		nameFeedback.value = 'Name cannot end with whitespace.';
	} else if (!newSnapshot.name.match(/^[a-zA-Z0-9_.:-]*$/)) {
		result = false;
		nameFeedback.value = 'Name contains invalid characters.';
	} else if (nameExists(newSnapshot, snapshots.value)) {
        result = false;
        nameFeedback.value = 'A snapshot with that name already exists.';
    } 

    return result;
}

function nameExists(newSnapshot : NewSnapshot, snapshots : Snapshot[]) {
    const newSnapName = newSnapshot.name;
    for (const snapshot of snapshots) {
        const existingSnapName = snapshot.name;

        if (existingSnapName === newSnapName) {
            return true;
        }
    }
    return false;
}

function createSnapButton(newSnapshot) {
    if (newSnapshot.isCustomName) {
        if (nameCheck(newSnapshot)) {
            if (filesystemCheck(newSnapshot)) {
                create(newSnapshot);
            }
        }
    } else if (!newSnapshot.isCustomName) {
        newSnapshot.name = getSnapshotTimestamp();
        if (filesystemCheck(newSnapshot)) {
            create(newSnapshot);
        }
    }
}

async function create(newSnapshot) {
    creating.value = true;
    try {
        const output = await createSnapshot(newSnapshot);
        
        if (output == null) {
            notifications.value.constructNotification('Create Snapshot Failed', 'There was an error creating this snapshot. Check console output.', 'error'); 
            confirmCreate.value = false;
            confirmCreate.value = true;
        } else {
            confirmCreate.value = true;
            // snapshotsLoaded.value = false;
            // refreshSnapshots();
            // await refreshData();
            // snapshotsLoaded.value = true;
            newSnapshot.isCustomName = false;
            newSnapshot.snapChildren = false;
            notifications.value.constructNotification('Snapshot Created', `Created new snapshot.`, 'success');
            showSnapshotModal.value = false;
        }
    } catch (error) {
        console.error(error);
    }
    creating.value = false;
}

const getIdKey = (name: string) => `${name}`;
</script>