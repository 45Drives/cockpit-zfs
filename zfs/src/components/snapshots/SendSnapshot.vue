<template>
    <Modal :isOpen="showSendDataset" @close="showSendDataset = false" :marginTop="'mt-28'" :width="'w-5/12'" :minWidth="'min-w-5/12'">
        <template v-slot:title>
            <legend class="flex justify-center">Send Dataset</legend>
        </template>
        <template v-slot:content>
            <div class="grid grid-cols-2 justify-between">
                <div class="mt-2 col-span-1">
                    <!-- Sending Snapshot: (self) -->
                    <label :for="getIdKey('sending-dataset-name')" class="mt-1 block text-sm font-medium leading-6 text-default">Snapshot To Send:</label>
                    <label :id="getIdKey('sending-dataset-name')" class="mt-1 block text-sm font-base leading-6 text-default" :class="truncateText" :title="sendName">{{sendName}}</label>
                </div>
                <div class="mt-2 col-span-1 justify-self-center">
                    <button id="test-ssh" class="mt-3 btn btn-secondary h-fit" @click="showTestSSHModal()">Test Passwordless SSH</button>
                </div>
                <div class="mt-2 col-span-2">
                    <!-- Receiving Dataset: [User Supplied] -->
                    <label :for="getIdKey('receiving-dataset-name')" class="mt-1 block text-sm font-medium leading-6 text-default">Receiving Dataset:</label>
                    <input @keydown.enter="" @change="doesRecvDatasetExist()" :id="getIdKey('receiving-dataset-name')" type="text" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default" name="receiving-dataset-name" v-model="destinationName" placeholder="Destination Name Here"/>
                    <p v-if="invalidConfig" class="mt-1 text-sm text-danger">{{ invalidConfigMsg }}</p>
                    <p v-if="invalidDest" class="mt-1 text-sm text-danger">{{ invalidDestMsg }}</p>
                    <p v-if="invalidConfig" class="mt-1 text-sm text-muted"><i>{{ mostRecentDestSnapMsg }}</i></p>
                    <p v-if="invalidConfig" class="mt-1 text-sm text-danger">{{ useForceOverwriteMsg }}</p>
                </div>
                <div class="mt-2 col-span-2">
                    <!-- Receiving Host: (Optional-> If Empty, then Local) -->
                    <label :for="getIdKey('receiving-host-name')" class="mt-1 block text-sm font-medium leading-6 text-default">Receiving Host:</label>
                    <input @keydown.enter="" :id="getIdKey('receiving-host-name')" type="text" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default" name="receiving-host-name" v-model="destinationHost" placeholder="(Leave empty if sending locally.)"/>
                </div>
                <div class="mt-2 col-span-2">
                    <!-- Host User -->
                    <label :for="getIdKey('receiving-host-user')" class="mt-1 block text-sm font-medium leading-6 text-default">Receiving User:</label>
                    <input @keydown.enter="" :id="getIdKey('receiving-host-user')" type="text" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default" name="receiving-host-user" v-model="destinationHostUser" placeholder="Destination Host User"/>
                </div>
                <div class="mt-2 col-span-2">
                    <!-- Receiving Port: [Default -> 22, User Can Change]-->
                    <label :for="getIdKey('receiving-port')" class="mt-1 block text-sm font-medium leading-6 text-default">Receiving Port:</label>
                    <input @keydown.enter="" :id="getIdKey('receiving-port')" type="text" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default" name="receiving-port" v-model="destinationPort"/>
                </div>
                <!-- If Remote Send, have mBuffer size configurable -->
                <div v-if="destinationHost != ''" class="mt-2 grid grid-cols-4 gap-2 col-span-2">
                    <div class="col-span-2 grid grid-cols-2 justify-items-center">
                        <label :for="getIdKey('mbuffer-size')" class="mt-1 text-sm font-medium leading-6 text-default w-full col-span-1">mBuffer Size:</label>
                        <input @keydown.enter="" :id="getIdKey('mbuffer-size')" type="number" class="input-textlike bg-default mt-1 w-full py-1.5 px-1.5 text-default col-span-1" name="mbuffer-size" v-model="mBufferSize"/>
                    </div>
                    <div class="col-span-2 grid grid-cols-2 justify-items-center">
                        <label :for="getIdKey('mbuffer-unit')" class="mt-1 text-sm font-medium leading-6 text-default w-full col-span-1">mBuffer Unit:</label>
                        <select :id="getIdKey('mbuffer-unit')" name="mbuffer-unit" class="text-default bg-default mt-1 w-full input-textlike col-span-1" v-model="mBufferUnit">
                            <option value="b">b</option>
                            <option value="k">k</option>
                            <option value="M">M</option>
                            <option value="G">G</option>
                        </select>
                    </div>
                </div>
              
                <div class="mt-2 grid grid-flow-col col-span-2">
                    <!-- Send Compressed: [Checkbox -> (-Lce) options] *** Cannot be used if Encrypted -->
                    <label :for="getIdKey('send-compressed-toggle')" class="mt-1 block text-sm font-medium leading-6 text-default col-span-1">
                        Send Compressed: 
                        <input :id="getIdKey('send-compressed-toggle')" v-model="sendCompressed" @change="handleCheckboxChange('sendCompressed')" type="checkbox" class="ml-2 w-5 h-5 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2"/>	
                    </label>
                    <!-- Send Raw: [Checkbox -> (-w) option] *** If Encrypted, force this mode -->
                    <label :for="getIdKey('send-raw-toggle')" class="mt-1 block text-sm font-medium leading-6 text-default col-span-1">
                        Send Raw:
                        <input :id="getIdKey('send-raw-toggle')" v-model="sendRaw" @change="handleCheckboxChange('sendRaw')" type="checkbox" class="ml-2 w-5 h-5 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2"/>	
                    </label>
                    <!-- Force Overwrite: [Checkbox -> (-F) option] -->
                    <label v-if="invalidConfig" :for="getIdKey('force-overwrite-toggle')" class="mt-1 block text-sm font-medium leading-6 text-danger col-span-1">
                        Force Overwrite:
                        <input :id="getIdKey('force-overwrite-toggle')" v-model="forceOverwrite" type="checkbox" class="ml-2 w-5 h-5 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2"/>	
                    </label>
                </div>
                <div class="mt-2 col-span-2">
                    <p v-if="invalidFlags" class="mt-1 text-sm text-danger">{{ invalidFlagMsg }}</p>
                </div>
            </div>
        </template>
        <template v-slot:footer>
            <div class="button-group-row w-full row-start-2 justify-between mt-2">
                <button id="cancel" class="mt-1 btn btn-danger object-left justify-start h-fit" @click="showSendDataset = false">Cancel</button>

                <div v-if="sending" class="min-w-max w-full bg-well rounded-full relative flex h-6 mt-3 min-h-min max-h-max overflow-hidden">
                    <div v-if="tracking" class="h-6 min-h-min max-h-max bg-green-600" :style="{ width: `${sendPercentage.toFixed(2)}%` }">
                        <div class="absolute inset-0 flex items-center justify-center text-s font-medium text-default text-center p-1.5 leading-none">
                            {{ sendPercentage.toFixed(2) }}%
                        </div>
                    </div>
                </div>

                <button v-if="!sending && !invalidConfig" @click="sendBtn()" :id="getIdKey('send-btn1')" name="send-btn1" class="mt-1 btn btn-primary object-right justify-end h-fit">Send</button>
                <button v-if="!sending && invalidConfig && !forceOverwrite" disabled @click="sendBtn()" :id="getIdKey('send-btn2')" name="send-btn2" class="mt-1 btn btn-primary object-right justify-end h-fit">Send</button>
                <button v-if="!sending && invalidConfig && forceOverwrite" @click="sendBtn()" :id="getIdKey('send-btn3')" name="send-btn3" class="mt-1 btn btn-primary object-right justify-end h-fit">Send</button>
                <button disabled v-if="sending && !forceOverwrite" :id="getIdKey('sending-progress')" type="button" class="mt-1 btn btn-danger object-right justify-end h-fit">
                    Sending...
                </button>
                <button disabled v-if="sending && forceOverwrite" :id="getIdKey('overwriting-progress')" type="button" class="mt-1 btn btn-danger object-right justify-end h-fit">
                    Overwriting...
                </button>
            </div>
        </template>
    </Modal>

    <div v-if="showTestSSH">
        <component :is="testSSHComponent" @close="updateShowTestSSH" :idKey="'test-ssh-modal'" :showFlag="showTestSSH"/>
    </div>

</template>
<script setup lang="ts">
import Modal from '../common/Modal.vue';
import { BetterCockpitFile } from '@45drives/cockpit-helpers';
import { ref, Ref, inject, computed } from 'vue';
import { sendSnapshot, doesDatasetExist, formatRecentSnaps, doesDatasetHaveSnaps } from '../../composables/snapshots';
import { convertTimestampToLocal, getRawTimestampFromString, convertRawTimestampToString, convertSizeToBytesDecimal } from '../../composables/helpers';

interface SendSnapshotProps {
    idKey: string;
    snapshot: Snapshot;
    name: string;
}

const notifications = inject<Ref<any>>('notifications')!;

const props = defineProps<SendSnapshotProps>();
const pools = inject<Ref<PoolData[]>>('pools')!;
const datasets = inject<Ref<FileSystemData[]>>('datasets')!;
const snapshots = inject<Ref<Snapshot[]>>('snapshots')!;
const showSendDataset = inject<Ref<boolean>>('show-send-dataset')!;
const sending = inject<Ref<boolean>>('sending')!;
const confirmSend = inject<Ref<boolean>>('confirm-send-snap')!;
const sendName = ref(props.name);
const secondNameIncremental = ref('');
const destinationName = ref('');
const destinationHost = ref('');
const destinationPort = ref('22');
const sendCompressed = ref(false);
const sendRaw = ref(false);
const sendIncremental = ref(false);
const forceOverwrite = ref(false);
const lastCommonSnap = ref();
const mostRecentLocalDestSnap = ref<Snapshot>();
const mostRecentRemoteDestSnap = ref<SnapSnippet>();
const mostRecentDestSnapMsg = ref('');
const invalidConfig = ref(false);
const invalidConfigMsg = ref('');
const useForceOverwriteMsg = ref("Use 'Force Overwrite' to force a COMPLETE OVERWRITE of Destination File System - including any Encryption.");
const invalidFlags = ref(false);
const invalidFlagMsg = ref('');
const destinationHostUser = ref('');
const datasetCheckResult = ref();
const snapSnips = ref<SnapSnippet[]>([]);
const sendProgressData = ref<SendProgress[]>([]);
const mBufferSize = ref(1);
const mBufferUnit = ref('G');
const truncateText = inject<Ref<string>>('style-truncate-text')!;
const invalidDest = ref(false);
const invalidDestMsg = ref('');

const showTestSSH = ref(false);

const testSSHComponent = ref();
const loadTestSSHComponent = async () => {
	const module = await import('../file-systems/TestSSHModal.vue');
	testSSHComponent.value = module.default;
}

async function showTestSSHModal() {
    await loadTestSSHComponent();
	showTestSSH.value = true;
	console.log('test ssh modal triggered');
}

const updateShowTestSSH = (newVal) => {
    showTestSSH.value = newVal;
}

const sendingData = ref<SendingDataset>({
    sendName: sendName.value,
    sendIncName: secondNameIncremental.value,
    recvName: destinationName.value,
    recvHost: destinationHost.value,
    recvPort: destinationPort.value,
    sendOpts: {
        compressed: sendCompressed.value,
        raw: sendRaw.value,
        incremental: sendIncremental.value,
        forceOverwrite: forceOverwrite.value,
    },
    recvHostUser: destinationHostUser.value,
    mBufferConfig: {
        size: mBufferSize.value,
        unit: mBufferUnit.value,
    }
});

function handleCheckboxChange(checkbox) {
    // Ensure only one checkbox is selected at a time
    if (checkbox === 'sendCompressed' && sendCompressed.value) {
    sendRaw.value = false;
    } else if (checkbox === 'sendRaw' && sendRaw.value) {
    sendCompressed.value = false;
    }
}

const isSendLocal = computed(() => {
    if (destinationHost.value == "") {
        return true;
    } else {
        return false;
    }
});

function doesRecvDatasetExist() {
    try {
        // Use Array.prototype.some to check if dataset with recvName exists
        return datasets.value.some(dataset => dataset.name === sendingData.value.recvName);
    } catch (error) {
        console.error('Error checking dataset:', error);
        return false; // Return false if an error occurs during the check
    }
}

function isRecvDatasetEncrypted() {
    try {
        console.log('isDatasetEncrypted:', datasets.value.find(dataset => dataset.name === sendingData.value.recvName)!.encrypted);
        return datasets.value.find(dataset => dataset.name === sendingData.value.recvName)!.encrypted;
    } catch (error) {
        console.error('Error checking dataset:', error);
        return false; // Return false if an error occurs during the check
    }
}

async function doesRemoteDatasetExist() {
    try {
        return await doesDatasetExist(sendingData.value);
    } catch (error) {
        console.error('Error checking dataset', error);
        return false; 
    }
}

async function doesRemoteDatasetHaveSnaps() {
    try {
        return await doesDatasetHaveSnaps(sendingData.value);
    } catch (error) {
        console.error('Error checking dataset', error);
        return false; 
    }
}

function doesPoolExist() {
    try {
        const poolName = sendingData.value.recvName.split("/", 1).shift();
        return pools.value.some(pool => pool.name === poolName);
    } catch (error) {
        console.error('Error checking pool', error);
    }
}

async function setSendData() {
    sendingData.value.sendName = sendName.value;

    if (sendCompressed.value && sendRaw.value) {
        invalidFlags.value = true;
        invalidFlagMsg.value = "Cannot have Compressed and Raw selected at the same time.";
    } else {
        invalidConfig.value = false;
        invalidFlags.value = false;

        const sourceDataset = computed(() => {
            const sourceDatasetName = sendName.value.split("@").shift();
            return datasets.value.find(dataset => dataset.name == sourceDatasetName);
        });

        sendingData.value.recvName = destinationName.value;
        sendingData.value.recvHost = destinationHost.value;

        if (destinationPort.value != '22') {
            sendingData.value.recvPort = destinationPort.value;
        } else {
            sendingData.value.recvPort = '22';
        }
       
        if (sourceDataset.value!.encrypted) {
            sendRaw.value = true;
            sendCompressed.value = false;
            sendingData.value.sendOpts.raw = true;
            sendingData.value.sendOpts.compressed = false;
        } else {
            sendingData.value.sendOpts.raw = sendRaw.value;
            sendingData.value.sendOpts.compressed = sendCompressed.value;
        }

        sendingData.value.sendOpts.forceOverwrite = forceOverwrite.value;
        sendingData.value.recvHostUser = destinationHostUser.value;

        if (isSendLocal.value) {
            if (doesRecvDatasetExist()) {
                if (!isRecvDatasetEncrypted()) {
                    lastCommonSnap.value = await checkForLastCommonSnap();
                    console.log('local lastCommonSnap:', lastCommonSnap.value);
                    if (lastCommonSnap.value !== null && lastCommonSnap.value !== false) {
                        sendIncremental.value = true;
                        sendingData.value.sendOpts.incremental = sendIncremental!.value;
                        sendingData.value.sendIncName! = lastCommonSnap.value.name;
                        invalidConfig.value = false;
                    } else if (lastCommonSnap.value === false) {
                        sendIncremental.value = false;
                        invalidConfig.value = true;
                        invalidConfigMsg.value = "Destination already exists (but has no snapshots).";
                    } else {
                        sendIncremental.value = false;
                        sendingData.value.sendIncName! = "";
                        invalidConfig.value = true;
                        invalidConfigMsg.value = "Destination already exists and has been modified since most recent snapshot.";
                        mostRecentDestSnapMsg.value = `Most recent snapshot: ${mostRecentLocalDestSnap.value!.name}`;
                    }
                } else {
                    sendIncremental.value = false;
                    sendingData.value.sendIncName! = "";
                    invalidConfig.value = true;
                    invalidConfigMsg.value = 'Destination is encrypted.';
                }
            } else {
                if (doesPoolExist()) {
                    sendIncremental.value = false;
                    sendingData.value.sendIncName! = "";
                } else {
                    console.error('Pool does not exist');
                    invalidDest.value = true;
                    invalidDestMsg.value = "Destination pool does not exist.";
                }
            }
        } else {
            datasetCheckResult.value = await doesRemoteDatasetExist();
            if (datasetCheckResult.value) {
                const doesRecvHaveSnaps = await doesRemoteDatasetHaveSnaps();
                if (doesRecvHaveSnaps) {
                    lastCommonSnap.value = await checkForLastCommonSnap();
                    console.log('remote lastCommonSnap:', lastCommonSnap.value);
                    if (lastCommonSnap.value !== null && lastCommonSnap.value !== false) {
                        sendIncremental.value = true;
                        sendingData.value.sendOpts.incremental = sendIncremental!.value;
                        sendingData.value.sendIncName! = lastCommonSnap.value.name;
                        invalidConfig.value = false;
                    } else if (lastCommonSnap.value === false) {
                        sendIncremental.value = false;
                        invalidConfig.value = true;
                        invalidConfigMsg.value = "Remote destination already exists (but has no snapshots).";
                    } else {
                        sendIncremental.value = false;
                        sendingData.value.sendIncName! = "";
                        invalidConfig.value = true;
                        invalidConfigMsg.value = "Remote destination already exists and has been modified since most recent snapshot.";
                        mostRecentDestSnapMsg.value = `Most recent remote snapshot: ${mostRecentRemoteDestSnap.value!.name}`;
                    }
                } else {
                    sendIncremental.value = false;
                    sendingData.value.sendIncName! = "";
                    invalidConfig.value = true;
                    invalidConfigMsg.value = "Remote destination already exists.";
                }
            } else {
                sendIncremental.value = false;
                sendingData.value.sendIncName! = "";
            }
            sendingData.value.mBufferConfig!.size = mBufferSize.value;
            sendingData.value.mBufferConfig!.unit = mBufferUnit.value;
        }
    }
}

async function checkForLastCommonSnap() {
    try {
        const sortedSnapshots = computed(() => {
            return snapshots.value.sort((a, b) => {
                return b.creationTimestamp.localeCompare(a.creationTimestamp);
            });
        });

        const sourceDataset = computed(() => {
            return sendName.value.split("@").shift();
        });

        const sourceDatasetSnaps = computed(() => {
            return sortedSnapshots.value.filter(snapshot => snapshot.dataset == sourceDataset.value);
        });

        const sourceSnap = computed(() => {
            return sourceDatasetSnaps.value.find(snap => snap.name == sendName.value);
        });

        if (isSendLocal.value) {
            const destinationDatasetSnaps = computed(() => {
                return sortedSnapshots.value.filter(snapshot => snapshot.dataset == destinationName.value);
            });

            // Check if destinationDatasetSnaps is empty
            if (destinationDatasetSnaps.value.length === 0) {
                // Handle the case where no destinationDatasetSnaps exist
                console.log('No destination dataset snapshots found.');
                return false; // Or return a default value, throw an error, etc.
            }

            return compareLocalTimestamp(destinationDatasetSnaps.value, sourceDatasetSnaps.value, sourceSnap.value!);
        } else {
            await formatRecentSnaps(sendingData.value, snapSnips.value);

            // Check if snapSnips is empty (assuming it corresponds to destinationDatasetSnaps in this context)
            if (snapSnips.value.length === 0) {
                // Handle the case where no destinationDatasetSnaps exist
                console.log('No destination dataset snapshots found.');
                return false; // Or return a default value, throw an error, etc.
            }

            return compareRemoteTimestamp(snapSnips.value, sourceDatasetSnaps.value, sourceSnap.value!);
        }
    } catch (error) {
        console.error('Error checking snapshot', error);
        return null;
    }
}


function compareLocalTimestamp(destinationDatasetSnaps : Snapshot[], sourceDatasetSnaps : Snapshot[], sourceSendSnap : Snapshot) {
    mostRecentLocalDestSnap.value = destinationDatasetSnaps[0];
    console.log('local mostRecentLocalDestSnap:', mostRecentLocalDestSnap.value);

    if (mostRecentLocalDestSnap.value.creationTimestamp) {
        console.log('local sourceSendSnap.creationTimestamp:', sourceSendSnap.creationTimestamp);
        if (sourceSendSnap.creationTimestamp) {
            if (Number(mostRecentLocalDestSnap.value.creationTimestamp) < Number(sourceSendSnap.creationTimestamp)) {
                const sourceSnapMatch = computed(() => {
                    return sourceDatasetSnaps.find(snap => snap.guid == mostRecentLocalDestSnap.value!.guid);
                });
                console.log('local sourceSnapMatch:', sourceSnapMatch.value);
                return sourceSnapMatch.value;
                
            } else if (mostRecentLocalDestSnap.value.guid == sourceSendSnap.guid) {
                console.log('sendSnap is the same as mostRecentDestSnap');
                return null;
            } else {
                console.log('invalid local lastCommonSnap match');
                return null;
            }
        }
    } else {
        console.log('no snaps to match');
        return null;
    }
  
}

async function compareRemoteTimestamp(snapSnips : SnapSnippet[], sourceDatasetSnaps : Snapshot[], sourceSendSnap : Snapshot) {
    console.log('snapSnips', snapSnips);
    // console.log('snapSnips length', snapSnips.length);
    if (snapSnips[0]) {
        mostRecentRemoteDestSnap.value = snapSnips[0];
        console.log('remote mostRecentRemoteDestSnap:', mostRecentRemoteDestSnap.value);

        console.log('mostRecentRemoteDestSnap.value.creation', Number(getRawTimestampFromString(mostRecentRemoteDestSnap.value.creation)));
        console.log('sourceSendSnap.creationTimestamp', Number(getRawTimestampFromString(convertTimestampToLocal(convertRawTimestampToString(sourceSendSnap.creationTimestamp)))));

        if (mostRecentRemoteDestSnap.value.guid == sourceSendSnap.guid) {
            console.log('sendSnap is the same as mostRecentDestSnap');
            return null;
        } else {
            if (Number(getRawTimestampFromString(mostRecentRemoteDestSnap.value.creation)) < Number(getRawTimestampFromString(convertTimestampToLocal(convertRawTimestampToString(sourceSendSnap.creationTimestamp))))) {
                const sourceSnapMatch = computed(() => {
                    const source = sourceDatasetSnaps.find(snap => snap.guid == mostRecentRemoteDestSnap.value!.guid);
                    console.log('source', source);
                    return source; 
                });
                console.log('remote sourceSnapMatch:', sourceSnapMatch.value);
                return sourceSnapMatch.value;
            } else {
                console.log('invalid remote lastCommonSnap match');
                return null;
            }
        }
    } else {
        console.log('No snap snips to compare');
        return null;
    }
    
}

async function sendBtn() {
    try {
        await setSendData();
        console.log('Sending data:', sendingData.value);
        
        if (!invalidConfig.value && !invalidFlags.value && !invalidDest.value) {
            sending.value = true;
    
            await sendAndReadProgress(sendingData.value, sendProgressData.value);
            sending.value = false;
            confirmSend.value = true;
            tracking.value = false;
            
            // Show success notification
            notifications.value.constructNotification('Snapshot Sent', `Sent snapshot ${props.snapshot!.name} to ${sendingData.value.recvName}.`, 'success');
         
            showSendDataset.value = false;
        } else if (invalidConfig.value) {
            if (forceOverwrite.value) {
                sending.value = true;
                invalidConfig.value = false;
                await sendAndReadProgress(sendingData.value, sendProgressData.value);
                sending.value = false;
                confirmSend.value = true;
                tracking.value = false;

                // Show success notification
                notifications.value.constructNotification('Snapshot Sent', `Sent snapshot ${props.snapshot!.name} to ${sendingData.value.recvName}.`, 'success');
            
                showSendDataset.value = false;
            } else {
                confirmSend.value = false;
            }
        } else {

            confirmSend.value = false;
        }
    } catch (error) {
        console.error(error);

        // Show error notification
        notifications.value.constructNotification('Failed Snapshot Send', `Failed to send snapshot ${props.snapshot!.name} to ${sendingData.value.recvName}.`, 'error');
    }
   
}

const totalSendSize = ref(0);
const sendProgressAmount = ref(0);
const tracking = ref(false);

function getTotalSendSize(contentTotal) {
    return (convertSizeToBytesDecimal(contentTotal));
}

function getSendProgress(contentProgress) {
    return (convertSizeToBytesDecimal(contentProgress));
}

const sendPercentage = computed(() => {
    if (!tracking.value) {
        return 0;
    } else {
        return (sendProgressAmount.value / totalSendSize.value) * 100;
    }
});

async function readSendProgress(sendProgressData : SendProgress[], fileReader : BetterCockpitFile) {
    try {
        let initialRun = true;
        let nullRun = true;
       
        function fillProgressArray(content, sendProgressData : SendProgress[]) {
            if (initialRun && nullRun) {
                initialRun = false;
            } else if (!initialRun && nullRun) {
                nullRun = false;
            } else {
                // console.log('file changed')
                tracking.value = true;
                if (content == null) {
                    console.log('error: content null, send data too small to track');
                } else {
                    sendProgressData.push(content)
                    totalSendSize.value = getTotalSendSize(content.totalSize)!;
                    sendProgressAmount.value = getSendProgress(content.sent)!;
                    console.log(`content.totalSize: ${content.totalSize}, content.sent: ${content.sent}`);
                    console.log(`totalSendSize: ${totalSendSize.value}, sendProgAmount: ${sendProgressAmount.value}`);
                }    
            }
        }

        fileReader.watch((content) => {
            fillProgressArray(content, sendProgressData);
            console.log('fileReaderContent:', content);
        });

    } catch (error) {
        console.error("An error occurred loading send progress:", error);
        return null;
    }
}

// Function to run both functions concurrently
async function sendAndReadProgress(sendingData : SendingDataset, sendProgress : SendProgress[]) {
    try {
        const fileReader = new BetterCockpitFile('/run/user/0/full_output.json', { syntax: JSON });
        // Run both functions concurrently using Promise.all
        const [snapshotResult, sendProgressData] = await Promise.all([
            sendSnapshot(sendingData),
            readSendProgress(sendProgress, fileReader),
        ]);

        console.log('Progress data:', sendProgress);
        console.log('Sent snapshot result:', snapshotResult);

        fileReader.close();
        // return snapshotResult;

        // return true;
    } catch (error) {
        console.error("An error occurred in sendAndReadProgress:", error);
        // return null;
        
        // return false;
    }
}

const getIdKey = (name: string) => `${props.idKey}-${name}`;
</script>