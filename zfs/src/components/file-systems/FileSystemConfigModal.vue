<template>
    <OldModal :isOpen="showFSConfig" @close="showFSConfig = false" :marginTop="'mt-28'" :width="'w-3/5'" :minWidth="'min-w-3/5'" :closeOnBackgroundClick="false">
        <template v-slot:title>
            <legend class="flex justify-center">Configure File System</legend>
        </template>
        <template v-slot:content>
            <div>
                <div class="grid grid-cols-4 gap-2">
                    <div class="mt-2 ">
                        <label :for="getIdKey('fs-config-name')" name="fs-config-name" class="mt-1 block text-sm leading-6 text-default">File System Name</label>
                        <p :class="truncateText" :title="props.filesystem.name">{{ props.filesystem.name }}</p>
                    </div>
                    <div class="mt-2">
                        <label :for="getIdKey('fs-config-guid')" name="fs-config-guid" class="mt-1 block text-sm leading-6 text-default">GUID</label>
                        <p>{{ props.filesystem.properties.guid }}</p>
                    </div>
                    <div class="mt-2">
                        <label :for="getIdKey('fs-config-case-sensitivity')" name="fs-config-case-sensitivity" class="mt-1 block text-sm leading-6 text-default">Case Sensitivity</label>
                        <p>{{ upperCaseWord(props.filesystem.properties.caseSensitivity) }}</p>
                    </div>
                    <div class="mt-2">
                        <label for="fs-config-readonly" :id="getIdKey('fs-config-readonly')" name="fs-config-readonly" class="mt-1 block text-sm leading-6 text-default">Read Only</label>
                        <Switch v-model="fileSystemConfig.properties.isReadOnly" :id="getIdKey('fs-config-readonly')" :class="[fileSystemConfig.properties.isReadOnly! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span :class="[fileSystemConfig.properties.isReadOnly! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span :class="[fileSystemConfig.properties.isReadOnly! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span :class="[fileSystemConfig.properties.isReadOnly! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-mountpoint')" name="fs-config-mountpoint" class="mt-1 block text-sm leading-6 text-default">Mountpoint</label>
                    <input type="text" v-model="fileSystemConfig.mountpoint" name="fs-config-mountpoint" :id="getIdKey('fs-config-mountpoint')" class="mt-1 block w-full input-textlike bg-default" placeholder="Mountpoint" />
                </div>
                <div class="mt-2">
                    <label :for="getIdKey('fs-config-can-mount')" class="bg-default block text-base leading-6 text-default">Can Mount</label>
                    <select :id="getIdKey('fs-config-can-mount')" v-model="fileSystemConfig.properties.canMount" name="fs-config-can-mount" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                        <option value="noauto">No Auto</option>
                    </select>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-quota')" class="mb-1 block text-sm font-medium leading-6 text-default">Quota</label>
                    <div class="flex flex-row">
                        <input v-model="fileSystemConfig.properties.quota.raw" :id="getIdKey('fs-config-quota-amount')" name="fs-config-quota-slider" type="range" min="0" max="1000" step="1" class="text-default mt-5 w-3/4 h-2 bg-accent rounded-lg appearance-none cursor-pointer " />
                        <input v-model="fileSystemConfig.properties.quota.raw" type="number" name="fs-config-quota-num" :id="getIdKey('fs-config-quota-num')" min="0" max="1000" class="text-default bg-default mt-1 w-fit block py-1.5 px-1.5 ml-1 text-default placeholder:text-muted input-textlike sm:text-sm sm:leading-6" />
                        <select v-model="fileSystemConfig.properties.quota.unit" :id="getIdKey('fs-config-quota-size')" name="fs-config-quota-size" class="block sm:col-span-1 bg-default py-1.5 pl-3 pr-10 text-default input-textlike sm:text-sm sm:leading-6">
                            <option value="kib">KiB</option>
                            <option value="mib">MiB</option>
                            <option value="gib">GiB</option>
                            <option value="tib">TiB</option>
                        </select>
                    </div>
                    <div class="flex flex-row justify-between">
                        <div v-if="fileSystemConfig.properties.quota.raw !== null" class="mt-2 justify-self-start">
                            <p class="text-muted">Used Space: {{ convertBytesToSize(fileSystemConfig.properties.used!) }}</p>
                        </div>
                        <div v-if="fileSystemConfig.properties.quota.raw === null || !fileSystemConfig.properties.quota.raw" class="mt-2 justify-self-end">
                            <p class="text-muted">There is no quota currently set.</p>
                        </div>
                    </div>

                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-recordsize')" class="block text-sm font-medium leading-6 text-default">Record Size</label>
                    <select :id="getIdKey('fs-config-recordsize')" v-model="fileSystemConfig.properties.recordSize" name="fs-config-recordsize" class="mt-1 block w-full input-textlike bg-default">
                        <option value="512">512 B</option>
                        <option value="4K">4 KiB</option>
                        <option value="8K">8 KiB</option>
                        <option value="16K">16 KiB</option>
                        <option value="32K">32 KiB</option>
                        <option value="64K">64 KiB</option>
                        <option value="128K">128 KiB</option>
                        <option value="256K">256 KiB</option>
                        <option value="512K">512 KiB</option>
                        <option value="1M">1 MiB</option>
                    </select>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-refreservation')" class="mb-1 block text-sm font-medium leading-6 text-default">Refreservation</label>
                    <div class="flex flex-row">
                        <input v-model="fileSystemConfig.properties.refreservation!.raw" :id="getIdKey('fs-config-refreservation-amount')" name="fs-config-refreservation-slider" type="range" min="0" max="1000" step="1" class="text-default mt-5 w-3/4 h-2 bg-accent rounded-lg appearance-none cursor-pointer " />
                        <input v-model="fileSystemConfig.properties.refreservation!.raw" type="number" name="fs-config-refreservation-num" :id="getIdKey('fs-config-refreservation-num')" min="0" max="1000" class="text-default bg-default mt-1 w-fit block py-1.5 px-1.5 ml-1 text-default placeholder:text-muted input-textlike sm:text-sm sm:leading-6" />
                        <select v-model="fileSystemConfig.properties.refreservation!.unit" :id="getIdKey('fs-config-refreservation-size')" name="fs-config-refreservation-size" class="block sm:col-span-1 bg-default py-1.5 pl-3 pr-10 text-default input-textlike sm:text-sm sm:leading-6">
                            <option value="kib">KiB</option>
                            <option value="mib">MiB</option>
                            <option value="gib">GiB</option>
                            <option value="tib">TiB</option>
                        </select>
                    </div>
                    <div class="flex flex-row justify-between">

                        <div v-if="fileSystemConfig.properties.refreservation!.raw !== null" class="mt-2 justify-self-start">
                            <p class="text-muted">Available Space: {{ convertBytesToSize(fileSystemConfig.properties.available) }}</p>
                        </div>
                        <div v-if="fileSystemConfig.properties.refreservation!.raw === null || !fileSystemConfig.properties.refreservation!.raw" class="mt-2 justify-self-end">
                            <p class="text-muted">There is no refreservation currently set.</p>
                        </div>
                    </div>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-acl-inherit')" class="bg-default block text-base leading-6 text-default">ACL Inheritance</label>
                    <select :id="getIdKey('fs-config-acl-inherit')" v-model="fileSystemConfig.properties.aclInheritance" name="fs-config-acl-inherit" class="mt-1 block w-full input-textlike bg-default">
                        <option value="discard">Discard</option>
                        <option value="noallow">No Allow</option>
                        <option value="restricted">Restricted</option>
                        <option value="passthrough">Passthrough</option>
                        <option value="passthrough-x">Passthrough-X</option>
                    </select>
                </div>
                <div class="mt-2">
                    <label :for="getIdKey('fs-config-acl-type')" class="bg-default block text-base leading-6 text-default">ACL Type</label>
                    <select :id="getIdKey('fs-config-acl-type')" v-model="fileSystemConfig.properties.aclType" name="fs-config-acl-type" class="mt-1 block w-full input-textlike bg-default">
                        <option value="off">Off/No ACL</option>
                        <option value="posix">POSIX ACL</option>
                    </select>
                </div>
                <div class="mt-2">
                    <label :for="getIdKey('fs-config-access-time')" class="bg-default block text-base leading-6 text-default">Access Time</label>
                    <select :id="getIdKey('fs-config-access-time')" v-model="fileSystemConfig.properties.accessTime" name="fs-config-access-time" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                    </select>
                </div>
                <div class="mt-2">
                    <label :for="getIdKey('fs-config-dedup')" class="bg-default block text-base leading-6 text-default">Deduplication</label>
                    <select :id="getIdKey('fs-config-dedup')" v-model="fileSystemConfig.properties.deduplication" name="fs-config-dedup" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                        <option value="edonr,verify">Edon-R + Verify</option>
                        <option value="sha256">SHA-256</option>
                        <option value="sha256,verify">SHA-256 + Verify</option>
                        <option value="sha512">SHA-512</option>
                        <option value="sha512,verify">SHA-512 + Verify</option>
                        <option value="skein">Skein</option>
                        <option value="skein,verify">Skein + Verify</option>
                        <option value="verify">Verify</option>
                    </select>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-compression')" class="bg-default block text-base leading-6 text-default">Compression</label>
                    <select :id="getIdKey('fs-config-compression')" v-model="fileSystemConfig.properties.compression" name="fs-config-compression" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                        <option value="gzip">GZIP</option>
                        <option value="lz4">LZ4</option>
                        <option value="lzjb">LZJB</option>
                        <option value="zle">ZLE</option>
                    </select>
                </div>
                <div class="mt-2">
                    <label :for="getIdKey('fs-config-checksum')" class="bg-default block text-base leading-6 text-default">Checksum</label>
                    <select :id="getIdKey('fs-config-checksum')" v-model="fileSystemConfig.properties.checksum" name="fs-config-checksum" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                        <option value="edonr">Edon-R</option>
                        <option value="fletcher2">Fletcher2</option>
                        <option value="fletcher4">Fletcher4</option>
                        <option value="noparity">No Parity</option>
                        <option value="sha256">SHA-256</option>
                        <option value="sha512">SHA-512</option>
                        <option value="skein">Skein</option>
                    </select>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-dnode-size')" class="bg-default block text-base leading-6 text-default">DNode Size</label>
                    <select :id="getIdKey('fs-config-dnode-size')" v-model="fileSystemConfig.properties.dNodeSize" name="fs-config-dnode-size" class="mt-1 block w-full input-textlike bg-default">
                        <option value="1k">1 KiB</option>
                        <option value="2k">2 KiB</option>
                        <option value="4k">4 KiB</option>
                        <option value="8k">8 KiB</option>
                        <option value="16k">16 KiB</option>
                        <option value="auto">Auto</option>
                        <option value="legacy">Legacy</option>
                    </select>
                </div>

                <div class="mt-2">
                    <label :for="getIdKey('fs-config-xattr')" class="bg-default block text-base leading-6 text-default">Extended Attributes</label>
                    <select :id="getIdKey('fs-config-xattr')" v-model="fileSystemConfig.properties.extendedAttributes" name="fs-config-xattr" class="mt-1 block w-full input-textlike bg-default">
                        <option value="on">On</option>
                        <option value="off">Off</option>
                        <option value="sa">System Attribute</option>
                    </select>
                </div>

                <div v-if="props.filesystem.encrypted" class="mt-2">
                    <label :for="getIdKey('fs-config-encryption')" name="fs-config-encryption" class="bg-default block text-base leading-6 text-default">Encryption</label>
                    <p class="mt-1 block w-full bg-default">{{ props.filesystem.properties.encryption.toUpperCase() }}</p>
                </div>
            </div>

        </template>

        <template v-slot:footer>
            <div class="w-full grid grid-rows-2">
                <div class="w-full row-start-1">
                    <div class="mt-2">
                        <p class="text-danger" v-if="quotaFeedback">{{ quotaFeedback }}</p>
                        <p class="text-danger" v-if="refreservationFeedback">{{ refreservationFeedback }}</p>
                    </div>
                </div>
                <div class="button-group-row w-full row-start-2 justify-between mt-2">
                    <button @click="showFSConfig = false" :id="getIdKey('cancel-configure-btn')" name="cancel-configure-btn" class="mt-1 btn btn-danger object-left justify-start h-fit">Cancel</button>
                    <button v-if="fileSystemsLoaded && saving == false" @click="fsConfigureBtn()" :id="getIdKey('edit-fs-btn')" name="edit-fs-btn" class="mt-1 btn btn-primary object-right justify-end h-fit">Configure</button>
                    <button disabled v-if="fileSystemsLoaded && saving !== false" :id="getIdKey('edit-fs-spinner')" type="button" class="btn btn-danger object-right justify-end">
                        <svg aria-hidden="true" role="status" class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
                            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="text-success" />
                        </svg>
                        Saving...
                    </button>
                </div>
            </div>
        </template>
    </OldModal>
</template>

<script setup lang="ts">
import { ref, Ref, inject } from 'vue';
import { onOffToBool, isBoolOnOff, upperCaseWord, convertBytesToSize, convertSizeToBytes, getSizeNumberFromString, getSizeUnitFromString, getQuotaRefreservUnit } from '../../composables/helpers';
import { configureDataset } from '../../composables/datasets';
import { Switch } from '@headlessui/vue';
import OldModal from '../common/OldModal.vue';
import { loadDatasets } from '../../composables/loadData';
import { ZFSFileSystemInfo, ZPool } from '@45drives/houston-common-lib';
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { FileSystemEditConfig } from '../../types';


interface FileSystemConfigModalProps {
    idKey: string;
    filesystem: ZFSFileSystemInfo;
}

const props = defineProps<FileSystemConfigModalProps>();
const truncateText = inject<Ref<string>>('style-truncate-text')!;
const showFSConfig = inject<Ref<boolean>>('show-fs-config')!;
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;

const pools = inject<Ref<ZPool[]>>('pools')!;

const quotaFeedback = ref('');
const refreservationFeedback = ref('');
const saving = ref(false);

const fileSystemConfig = ref<ZFSFileSystemInfo>({
    parentFS: props.filesystem.parentFS,
    name: props.filesystem.name,
    id: props.filesystem.id,
    mountpoint: props.filesystem.mountpoint,
    pool: props.filesystem.pool,
    encrypted: props.filesystem.encrypted,
    key_loaded: props.filesystem.key_loaded,
    type: props.filesystem.type,
    inherit: props.filesystem.inherit,
    properties: {
        guid: props.filesystem.properties.guid,
		encryption: props.filesystem.properties.encryption,
        accessTime: props.filesystem.properties.accessTime,
        caseSensitivity: props.filesystem.properties.caseSensitivity,
        compression: props.filesystem.properties.compression,
        deduplication: props.filesystem.properties.deduplication,
        dNodeSize: props.filesystem.properties.dNodeSize,
        extendedAttributes: props.filesystem.properties.extendedAttributes,
        recordSize: props.filesystem.properties.recordSize,
        quota: {
            raw: getSizeNumberFromString(convertBytesToSize(props.filesystem.properties.quota.raw)),
            value: props.filesystem.properties.quota.value,
            unit: getSizeUnitFromString(getQuotaRefreservUnit(props.filesystem.properties.quota.raw)),
        },
		usedByDataset: props.filesystem.properties.usedByDataset,
		usedbyRefreservation: props.filesystem.properties.usedbyRefreservation,
        readOnly: props.filesystem.properties.readOnly,
        isReadOnly: onOffToBool(props.filesystem.properties.readOnly),
        available: props.filesystem.properties.available,
        creation: props.filesystem.properties.creation,
        snapshotCount: props.filesystem.properties.snapshotCount,
        mounted: props.filesystem.properties.mounted,
        refreservation: {
            raw: getSizeNumberFromString(convertBytesToSize(props.filesystem.properties.refreservation!.raw)),
            value: props.filesystem.properties.refreservation!.value,
            unit: getSizeUnitFromString(getQuotaRefreservUnit(props.filesystem.properties.refreservation!.raw)),
        },
        canMount: props.filesystem.properties.canMount,
        aclInheritance: props.filesystem.properties.aclInheritance,
        aclType: props.filesystem.properties.aclType,
        checksum: props.filesystem.properties.checksum,
        used: props.filesystem.properties.used,
    },
    children: props.filesystem.children,
});

const newChangesToFileSystem = ref<FileSystemEditConfig>({
	name: fileSystemConfig.value.name,
	guid: fileSystemConfig.value.properties.guid,
	casesensitivity: fileSystemConfig.value.properties.caseSensitivity,
});

const updatedProperties: Partial<FileSystemEditConfig> = {
	name: fileSystemConfig.value.name,
	guid: fileSystemConfig.value.properties.guid,
	casesensitivity: fileSystemConfig.value.properties.caseSensitivity,
};

async function checkForChanges(fileSystemCheck) {
    //readonly
    if (fileSystemCheck.properties.isReadOnly != props.filesystem.properties.isReadOnly) {
        updatedProperties.readonly = isBoolOnOff(fileSystemCheck.properties.isReadOnly);
    }
    //mountpoint
    if (fileSystemCheck.mountpoint != props.filesystem.mountpoint) {
        updatedProperties.mountpoint = fileSystemCheck.mountpoint;
    }
    //canmount
    if (fileSystemCheck.properties.canMount != props.filesystem.properties.canMount) {
        updatedProperties.canmount = fileSystemCheck.properties.canMount;
    }
    //record
    if (fileSystemCheck.properties.recordSize != props.filesystem.properties.recordSize) {
        updatedProperties.record = fileSystemCheck.properties.recordSize;
    }
    //aclinherit
    if (fileSystemCheck.properties.aclInheritance != props.filesystem.properties.aclInheritance) {
        updatedProperties.aclinherit = fileSystemCheck.properties.aclInheritance;
    }
    //acltype
    if (fileSystemCheck.properties.aclType != props.filesystem.properties.aclType) {
        updatedProperties.acltype = fileSystemCheck.properties.aclType;
    }
    //atime
    if (fileSystemCheck.properties.accessTime != props.filesystem.properties.accessTime) {
        updatedProperties.atime = fileSystemCheck.properties.accessTime;
    }
    //dedup
    if (fileSystemCheck.properties.deduplication != props.filesystem.properties.deduplication) {
        updatedProperties.dedup = fileSystemCheck.properties.deduplication;
    }
    //compression
    if (fileSystemCheck.properties.compression != props.filesystem.properties.compression) {
        updatedProperties.compression = fileSystemCheck.properties.compression;
    }
    //checksum
    if (fileSystemCheck.properties.checksum != props.filesystem.properties.checksum) {
        updatedProperties.checksum = fileSystemCheck.properties.checksum;
    }
    //dnodesize
    if (fileSystemCheck.properties.dNodeSize != props.filesystem.properties.dNodeSize) {
        updatedProperties.dnodesize = fileSystemCheck.properties.dNodeSize;
    }
    //xattr
    if (fileSystemCheck.properties.extendedAttributes != props.filesystem.properties.extendedAttributes) {
        updatedProperties.xattr = fileSystemCheck.properties.extendedAttributes;
    }
    //quota
    if (Number(fileSystemCheck.properties.quota.raw)) {
        if (convertSizeToBytes(fileSystemCheck.properties.quota.raw + fileSystemCheck.properties.quota.unit) != props.filesystem.properties.quota.raw) {
            updatedProperties.quota = convertSizeToBytes(fileSystemCheck.properties.quota.raw + fileSystemCheck.properties.quota.unit);
        }
    }
    //refreservation
    if (Number(fileSystemCheck.properties.refreservation.raw)) {
        if (convertSizeToBytes(fileSystemCheck.properties.refreservation.raw + fileSystemCheck.properties.refreservation.unit) != props.filesystem.properties.refreservation!.raw) {
            updatedProperties.refreservation = convertSizeToBytes(fileSystemCheck.properties.refreservation.raw + fileSystemCheck.properties.refreservation.unit);
        }
    }

    const newChanges = {
        ...newChangesToFileSystem.value,
        ...updatedProperties,
    }

    newChangesToFileSystem.value = newChanges;
}

const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;

async function fsConfigureBtn() {
    if (checkSizes()) {
        // console.log('filesystem:', fileSystemConfig.value);
        await checkForChanges(fileSystemConfig.value);
        // console.log('newChanges:', newChangesToFileSystem.value);
        try {
            saving.value = true;
            const output: any =  await configureDataset(newChangesToFileSystem.value);

			if (output == null || output.error) {
				const errorMessage = output?.error || 'Unknown error';
				console.log('configureFS failed');
                pushNotification(new Notification('Save File System Config Failed', `There was an error saving this file system: ${errorMessage}`, 'error', 5000));

			} else {
				console.log('configureFS succeeded');
                pushNotification(new Notification('File System Config Saved', "Successfully saved this file system's configuration.", 'success', 5000));
                datasets.value = [];
                fileSystemsLoaded.value = false;
                await loadDatasets(datasets);
                fileSystemsLoaded.value = true;
                showFSConfig.value = false;
			}
            saving.value = false;
        } catch (error) {
            console.error(error);
        }
    }
}

const checkSizes = () => {
    let result = true;
    quotaFeedback.value = '';
    refreservationFeedback.value = '';

    //console.log('pools.value', pools.value);
    //console.log('filesystem.config.pool', fileSystemConfig.value.pool);
    const parentPool = pools.value.find(pool => pool.name == fileSystemConfig.value.pool)!;
    //console.log('parentPool', parentPool);

    if (!parentPool) {
        console.log("Pool not found", fileSystemConfig.value.pool);
        return;
    }

    if (fileSystemConfig.value.properties.quota.value != 'none') {
        if (convertSizeToBytes(fileSystemConfig.value.properties.quota.raw + fileSystemConfig.value.properties.quota.unit) > convertSizeToBytes(parentPool.properties.free)) {
            result = false;
            quotaFeedback.value = 'Quota cannot be greater than available space in pool.';
        }
    }

    if (fileSystemConfig.value.properties.refreservation!.value != 'none') {
        if (convertSizeToBytes(fileSystemConfig.value.properties.refreservation!.raw + fileSystemConfig.value.properties.refreservation!.unit) > convertSizeToBytes(parentPool.properties.free)) {
            result = false;
            refreservationFeedback.value = 'Refreservation cannot be greater than available space in pool.';
        }
    }

    return result;
}

const getIdKey = (name: string) => `${name}`;
</script>