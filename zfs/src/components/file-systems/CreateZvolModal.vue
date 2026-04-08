<template>
	<OldModal :isOpen="showModal" @close="$emit('close')" :marginTop="'mt-28'" :width="'w-3/5'"
		:minWidth="'min-w-3/5'" :closeOnBackgroundClick="false">
		<template v-slot:title>
			<legend class="flex justify-center">Create a New Zvol</legend>
		</template>
		<template v-slot:content>
			<!-- Parent Pool/Dataset -->
			<div>
				<label :for="getIdKey('zvol-parent')"
					class="block text-sm font-medium leading-6 text-default">Parent Dataset</label>
				<select :id="getIdKey('zvol-parent')" name="zvol-parent"
					v-model="zvolConfig.parent"
					class="mt-1 block w-full input-textlike bg-default text-default">
					<option v-for="dataset, idx in parentOptions" :key="idx" :value="dataset.name">{{
						dataset.name }}</option>
				</select>
			</div>

			<!-- Name -->
			<div>
				<label :for="getIdKey('zvol-name')"
					class="mt-2 block text-sm font-medium text-default">Name</label>
				<input :id="getIdKey('zvol-name')" @keydown.enter="createZvol()"
					type="text" name="zvol-name" v-model="zvolConfig.name"
					class="mt-1 block w-full input-textlike bg-default text-default"
					placeholder="Zvol Name" />
			</div>

			<!-- Volume Size -->
			<div>
				<label :for="getIdKey('zvol-size')"
					class="mt-2 block text-sm font-medium text-default">Volume Size</label>
				<div class="flex flex-row mt-1">
					<input :id="getIdKey('zvol-size')" type="number" min="1"
						v-model="zvolConfig.sizeValue"
						class="block w-full input-textlike bg-default text-default"
						placeholder="Size" />
					<select v-model="zvolConfig.sizeUnit"
						class="block bg-default py-1.5 pl-3 pr-10 text-default input-textlike sm:text-sm sm:leading-6 ml-1">
						<option value="M">MiB</option>
						<option value="G">GiB</option>
						<option value="T">TiB</option>
					</select>
				</div>
			</div>

			<!-- Volume Block Size -->
			<div>
				<label :for="getIdKey('zvol-blocksize')"
					class="mt-2 block text-sm font-medium leading-6 text-default">Block Size</label>
				<select :id="getIdKey('zvol-blocksize')" v-model="zvolConfig.volblocksize"
					class="mt-1 block w-full input-textlike bg-default text-default">
					<option value="">Default (8K)</option>
					<option value="4K">4K</option>
					<option value="8K">8K</option>
					<option value="16K">16K</option>
					<option value="32K">32K</option>
					<option value="64K">64K</option>
					<option value="128K">128K</option>
				</select>
			</div>

			<div class="grid grid-cols-2 gap-4 mt-2">
				<!-- Compression -->
				<div>
					<label :for="getIdKey('zvol-compression')"
						class="block text-sm font-medium leading-6 text-default">Compression</label>
					<select :id="getIdKey('zvol-compression')" v-model="zvolConfig.compression"
						class="mt-1 block w-full input-textlike bg-default text-default">
						<option value="off">Off</option>
						<option value="on">On (Default)</option>
						<option value="lz4">LZ4</option>
						<option value="gzip">Gzip</option>
						<option value="zstd">Zstd</option>
						<option value="lzjb">LZJB</option>
						<option value="zle">ZLE</option>
					</select>
				</div>

				<!-- Deduplication -->
				<div>
					<label :for="getIdKey('zvol-dedup')"
						class="block text-sm font-medium leading-6 text-default">Deduplication</label>
					<select :id="getIdKey('zvol-dedup')" v-model="zvolConfig.dedup"
						class="mt-1 block w-full input-textlike bg-default text-default">
						<option value="off">Off</option>
						<option value="on">On</option>
						<option value="verify">Verify</option>
					</select>
				</div>
			</div>
		</template>
		<template v-slot:footer>
			<div class="w-full grid grid-rows-2">
				<div class="w-full row-start-1">
					<div class="button-group-row mt-2 justify-self-center">
						<p class="text-danger" v-if="feedback">{{ feedback }}</p>
					</div>
				</div>
				<div class="button-group-row w-full row-start-2 justify-between mt-2">
					<button class="mt-1 btn btn-danger object-left justify-start h-fit"
						@click="$emit('close')">Cancel</button>
					<button v-if="!saving" @click="createZvol()"
						class="mt-1 btn btn-primary object-right justify-end h-fit">Create Zvol</button>
					<button disabled v-if="saving"
						class="btn btn-danger object-right justify-end">
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
						Creating...
					</button>
				</div>
			</div>
		</template>
	</OldModal>
</template>

<script setup lang="ts">
import { ref, inject, Ref, computed } from 'vue';
import { ZFSManager, ZFSFileSystemInfo, ZvolCreateOptions } from '@45drives/houston-common-lib';
import OldModal from '../common/OldModal.vue';
import { pushNotification, Notification } from '@45drives/houston-common-ui';

interface CreateZvolProps {
	idKey: string;
}

const props = defineProps<CreateZvolProps>();
const emit = defineEmits(['close', 'created']);

const zfsManager = new ZFSManager();
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;
const parentOptions = computed(() => datasets.value.filter(d => d.type === 'FILESYSTEM'));
const showModal = ref(true);
const saving = ref(false);
const feedback = ref('');

const zvolConfig = ref({
	parent: '',
	name: '',
	sizeValue: 1,
	sizeUnit: 'G',
	volblocksize: '',
	compression: 'off',
	dedup: 'off',
});

function validate(): boolean {
	feedback.value = '';

	if (!zvolConfig.value.parent) {
		feedback.value = 'Please select a parent dataset.';
		return false;
	}
	if (!zvolConfig.value.name) {
		feedback.value = 'Name cannot be empty.';
		return false;
	}
	if (!zvolConfig.value.name.match(/^[a-zA-Z0-9][a-zA-Z0-9_.:-]*$/)) {
		feedback.value = 'Name contains invalid characters.';
		return false;
	}
	if (!zvolConfig.value.sizeValue || zvolConfig.value.sizeValue <= 0) {
		feedback.value = 'Volume size must be greater than 0.';
		return false;
	}
	return true;
}

async function createZvol() {
	if (!validate()) return;

	saving.value = true;
	feedback.value = '';

	const options: ZvolCreateOptions = {
		volsize: `${zvolConfig.value.sizeValue}${zvolConfig.value.sizeUnit}`,
	};

	if (zvolConfig.value.volblocksize) {
		options.volblocksize = zvolConfig.value.volblocksize;
	}
	if (zvolConfig.value.compression) {
		options.compression = zvolConfig.value.compression;
	}
	if (zvolConfig.value.dedup) {
		options.dedup = zvolConfig.value.dedup;
	}

	try {
		const output = await zfsManager.addZvol(
			zvolConfig.value.parent,
			zvolConfig.value.name,
			options
		);

		if (output?.getStderr()?.trim()) {
			const errorMessage = output.getStderr().trim();
			saving.value = false;
			pushNotification(new Notification('Error Creating Zvol', `${errorMessage}`, 'error', 5000));
		} else {
			saving.value = false;
			pushNotification(new Notification('Zvol Created!', `Created new zvol: ${zvolConfig.value.parent}/${zvolConfig.value.name}`, 'success', 5000));
			emit('created');
			emit('close');
		}
	} catch (error: any) {
		saving.value = false;
		console.error('Error creating zvol:', error);
		pushNotification(new Notification('Error Creating Zvol', `Unexpected error: ${error.message}`, 'error', 5000));
	}
}

const getIdKey = (name: string) => `${props.idKey}-${name}`;
</script>
