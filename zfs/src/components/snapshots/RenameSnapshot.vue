<template>
    <OldModal :isOpen="showRenameSnapModal" @close="showRenameSnapModal = false" :marginTop="'mt-28'" :width="'w-4/12'" :minWidth="'min-w-4/12'" :closeOnBackgroundClick="false">
        <template v-slot:title>
            <legend class="flex justify-center">Rename Snapshot</legend>
        </template>
        <template v-slot:content>
            <div class="grid grid-cols-1">
                <!-- Parent File System -->
                <div class="mt-2 col-span-1">
                    <label :for="getIdKey('parent-filesystem')" class="block text-sm font-medium leading-6 text-default">Parent File System</label>
                    <p :class="truncateText" :title="props.snapshot.dataset">{{ props.snapshot.dataset }}</p>
                </div>

                <!-- Set name as creation date -->
                <div class="mt-2 col-span-1">
                    <div class="flex flex-row justify-between">
                        <label :for="getIdKey('set-name-creation-date')" class="mt-2 mr-2 block text-sm font-medium leading-6 text-default">Creation Date</label>
                        <Switch v-model="creationDate" :id="getIdKey('set-name-creation-date')" :class="[creationDate! ? 'bg-primary' : 'bg-accent', 'mt-2 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span :class="[creationDate! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span :class="[creationDate! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span :class="[creationDate! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>
                </div>

                <!-- New Name -->
                <div class="mt-2 col-span-1">
                    <label :for="getIdKey('new-name')" class="mt-1 block text-sm font-medium leading-6 text-default">New Name</label>
                    <input v-if="creationDate" disabled :id="getIdKey('new-name')" type="text" v-model="newName" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default placeholder:text-muted sm:text-sm sm:leading-6" :placeholder="`${convertRawTimestampToString(props.snapshot.properties.creation.rawTimestamp)}`" />
                    <input v-else :id="getIdKey('new-name')" type="text" v-model="newName" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default placeholder:text-muted sm:text-sm sm:leading-6" placeholder="New Name" />
                </div>

                <!-- Rename child snapshots with same name -->
                <div class="mt-2 col-span-1">
                    <div class="flex flex-row justify-between">
                        <label :for="getIdKey('rename-children')" class="mt-2 mr-2 block text-sm font-medium leading-6 text-default">Rename child snapshots with same name</label>
                        <Switch v-model="renameChildSnaps" :id="getIdKey('rename-children')" :class="[renameChildSnaps! ? 'bg-primary' : 'bg-accent', 'mt-2 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span :class="[renameChildSnaps! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span :class="[renameChildSnaps! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span :class="[renameChildSnaps! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>
                </div>
            </div>
        </template>
        <template v-slot:footer>
            <div class="w-full grid grid-rows-2">
                <div class="w-full row-start-1">
                    <p class="text-danger" v-if="nameFeedback">{{ nameFeedback }}</p>
                </div>
                <div class="button-group-row justify-between">
                    <button @click="showRenameSnapModal = false" :id="getIdKey('confirm-rename-no')" name="rename-button-no" class="btn btn-secondary object-left justify-start h-fit">Cancel</button>

                    <div class="button-group-row">
                        <button v-if="!renaming" id="rename-snapshot-btn" class="btn btn-primary object-right justify-end h-fit w-full" @click="renameBtn()">Rename</button>
                        <button disabled v-if="renaming" id="finish" type="button" class="btn btn-primary object-right justify-end">
                            <svg aria-hidden="true" role="status" class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
                                <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="text-success" />
                            </svg>
                            Renaming...
                        </button>
                    </div>
                </div>
            </div>
        </template>
    </OldModal>
</template>
<script setup lang="ts">
import { ref, Ref, inject } from 'vue';
import { convertRawTimestampToString } from '../../composables/helpers';
import { renameSnapshot } from '../../composables/snapshots';
import { Switch } from '@headlessui/vue';
import OldModal from '../common/OldModal.vue';
import {ZFSFileSystemInfo} from "../../../../houston-common/houston-common-lib/lib/managers/index"
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { Snapshot } from '../../types';


interface RenameSnapshotProps {
    idKey: string;
    snapshot: Snapshot;
}


const props = defineProps<RenameSnapshotProps>();
const showRenameSnapModal = inject<Ref<boolean>>('show-rename-snap-modal')!;
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;
const truncateText = inject<Ref<string>>('style-truncate-text')!;

const renaming = inject<Ref<boolean>>('renaming')!;
const confirmRename = inject<Ref<boolean>>('confirm-rename')!;
const nameFeedback = ref('');

const parentFS = ref(props.snapshot.dataset!);
const newName = ref('');
const creationDate = ref(false);
const renameChildSnaps = ref(false);

async function renameBtn() {
    if (creationDate.value == true) {
        newName.value = convertRawTimestampToString(props.snapshot.properties.creation.rawTimestamp);
    }

    if (nameCheck(newName.value, parentFS.value)) {   
        renaming.value = true;

        try {
			const output: any = await renameSnapshot(props.snapshot.name, newName.value);
 
			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				renaming.value = false;
                pushNotification(new Notification('Rename Dataset Failed', `${props.snapshot.name} was not renamed: ${errorMessage}`, 'error', 5000));

			} else {
                confirmRename.value = true;
                pushNotification(new Notification('Snapshot Renamed', `Renamed snapshot ${props.snapshot.name} to ${newName.value}.`, 'success', 5000));

                renaming.value = false;
                showRenameSnapModal.value = false;
			}
		} catch (error) {
			console.error(error);
		}
    }
}

const nameCheck = (snapshotName, fileSystemParent) => {
    let result = true;
    nameFeedback.value = '';
    if (!creationDate) {
        if (snapshotName == '') {
            result = false;
            nameFeedback.value = 'Name cannot be empty.';
        } else if (!snapshotName.match(/^[a-zA-Z0-9]/) ) {
            result = false;
            nameFeedback.value = 'Name must begin with alphanumeric characters.';
        } else if (snapshotName.match(/^[ ]/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with whitespace.';
        } else if (snapshotName.match(/[ ]$/)) {
            result = false;
            nameFeedback.value = 'Name cannot end with whitespace.';
        } else if (!snapshotName.match(/^[a-zA-Z0-9_.:-]*$/)) {
            result = false;
            nameFeedback.value = 'Name contains invalid characters.';
        } else if (snapshotNameExists(snapshotName, fileSystemParent, datasets.value)) {
            result = false;
            nameFeedback.value = `Name already exists in this location: ${fileSystemParent}.`;
        }
    } else {
        if (snapshotNameExists(snapshotName, fileSystemParent, datasets.value)) {
            result = false;
            nameFeedback.value = `Name already exists in this location: ${fileSystemParent}.`;
        }
    }
	
    return result;
}

function snapshotNameExists(snapshotName, fileSystemParent, datasets : ZFSFileSystemInfo[]) {
	const newParentPath = fileSystemParent;
	for (const dataset of datasets) {
		const existingParentPath = dataset.parentFS;
		const existingDatasetName = dataset.name.split('/').pop();
	
		if (existingParentPath === newParentPath && existingDatasetName === snapshotName) {
			return true;
		}
	}

	return false;
}

const getIdKey = (name: string) => `${name}`;
</script>