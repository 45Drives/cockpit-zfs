<template>
    <OldModal :isOpen="showFlag" @close="updateShowFlag" :marginTop="'mt-60'" :width="'w-96'" :minWidth="'min-w-min'" :closeOnBackgroundClick="false">
        <template v-slot:title>
            <legend class="flex justify-center">Test Passwordless SSH Connection</legend>
        </template>
        <template v-slot:content>
            <label :for="getIdKey('ssh-test')" class="mt-1 block text-sm font-medium leading-6 text-default">SSH Target:</label>
            <input @keydown.enter="" :id="getIdKey('ssh-test')" type="text" class="input-textlike bg-default mt-1 block w-full py-1.5 px-1.5 text-default" name="ssh-target" v-model="sshTarget" placeholder="user@hostname or just hostname" />
            <p v-if="result" class="text-success mt-2">{{ resultMsg }}</p>
            <p v-if="!result" class="text-danger mt-2">{{ resultMsg }}</p>
        </template>
        <template v-slot:footer>
            <div class="w-full grid grid-rows-1">
                <div class="button-group-row mt-2 justify-between">
                    <button @click="closeModal" :id="getIdKey('confirm-no')" name="button-no" class="mt-1 btn btn-secondary object-left justify-start h-fit">Cancel</button>

                    <button v-if="!testing" @click="confirmTest(sshTarget)" :id="getIdKey('confirm-yes-A')" name="button-yes-A" class="mt-1 btn btn-danger object-right justify-end h-fit">Test</button>

                    <button disabled v-if="testing" :id="getIdKey('confirm-spinner')" type="button" class="btn btn-danger object-right justify-end h-fit">
                        <svg aria-hidden="true" role="status" class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
                            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="text-success" />
                        </svg>
                        Testing...
                    </button>
                </div>
            </div>
        </template>
    </OldModal>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import OldModal from '../common/OldModal.vue';
import { testSSH } from '../../composables/helpers';

interface TestSSHModalProps {
    idKey: string;
    showFlag: boolean;
}

const props = defineProps<TestSSHModalProps>();
const emit = defineEmits(['close']);

const showFlag = ref(props.showFlag);

const updateShowFlag = () => {
    if (props.showFlag != showFlag.value) {
        showFlag.value = props.showFlag;
    }
}

const closeModal = () => {
    emit('close');
}

const sshTarget = ref('');
const testing = ref(false);
const resultMsg = ref('');
const result = ref(false);

async function confirmTest(sshTarget) {
    testing.value = true;
    resultMsg.value = "";

    result.value = await testSSH(sshTarget);

    if (result.value) {
        resultMsg.value = 'Connection Successful!';
    } else {
        resultMsg.value = `Connection Failed: Could not resolve hostname ${sshTarget}: Name or service not known.`;
    }
    testing.value = false;
}

const getIdKey = (name: string) => `${props.idKey}-${name}`;
</script>