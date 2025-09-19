<template>
	<div>
		<div v-if="!finishPressed" class="grid grid-cols-1 gap-1">
			<legend v-if="!creatingPool && !poolCreated" class="mb-1 text-base font-semibold leading-6 text-default">Review Configuration</legend>

			<div v-if="!creatingPool && !poolCreated" class="">
				<Card :bgColor="'bg-accent'" :titleSection="true" :contentSection="true" :footerSection="true" class="mt-2 mb-4 truncate rounded-lg border border-default text-default">
					<template v-slot:title>
						<div>
							<p class="text-md" :class="truncateText" :title="poolConfig.name">Pool Name: <b :class="truncateText" :title="poolConfig.name">{{ poolConfig.name }}</b></p>	
						</div>
					</template>
					<template v-slot:content>
						<div>
							<p>Compression: <b>{{ poolConfig.compression!.toUpperCase() }}</b></p>
							<p>Sector Size: <b>{{ getValue('sector', poolConfig.sectorsize!.toString()) }}</b></p>
							<p>Record Size: <b>{{ getValue('record', poolConfig.recordsize!.toString()) }}</b></p>
							<div class="rounded-lg mt-1 border border-default bg-default">
								<Disclosure v-slot="{ open }">
									<DisclosureButton class="bg-default grid grid-cols-8 w-full justify-start text-center rounded-lg">
										<div class="m-1 col-span-1">
											<ChevronUpIcon
												class="h-7 w-7 text-default transition-all duration-200 transform" :class="{ 'rotate-90': !open, 'rotate-180': open, }"
											/>
										</div>
										<div class="-ml-8 mt-1.5 col-span-1">
											<span class="text-start whitespace-nowrap text-base text-default">Advanced Settings</span>
										</div>
									</DisclosureButton>
									<DisclosurePanel>
										<div class="p-2 rounded-lg bg-default">
											<p>Refreservation: <b>{{ poolConfig.refreservationPercent! }}%</b></p>
											<p>Deduplication: <b>{{ upperCaseWord(poolConfig.dedup!) }}</b></p>
											<p>Auto-Expand: <b>{{ upperCaseWord(poolConfig.autoexpand!) }}</b></p>
											<p>Auto-Replace: <b>{{ upperCaseWord(poolConfig.autoreplace!) }}</b></p>
											<p>Auto-TRIM: <b>{{ upperCaseWord(poolConfig.autotrim!) }}</b></p>
										</div>
									</DisclosurePanel>
								</Disclosure>
							</div>	
						</div>
					</template>
					<template v-slot:footer>
						<div class="bg-default rounded-lg mt-1 border border-default">
							<Disclosure v-slot="{ open }">
								<DisclosureButton class="bg-default grid grid-cols-8 w-full justify-start text-center rounded-lg">
									<div class="m-1 col-span-1">
										<ChevronUpIcon
											class="h-7 w-7 text-default transition-all duration-200 transform" :class="{ 'rotate-90': !open, 'rotate-180': open, }"
										/>
									</div>
									<div class="-ml-8 mt-1.5 col-span-1">
										<span class="text-start whitespace-nowrap text-base text-default">Virtual Devices  <b>({{ poolConfig.vdevs.length }})</b></span>
									</div>
								</DisclosureButton>
								<DisclosurePanel>
									<Card v-for="vDev, vDevIdx in poolConfig.vdevs" :key="vDevIdx" :bgColor="'bg-default'" :titleSection="true" :contentSection="false" :footerSection="true" class="truncate rounded-lg text-default">
										<template v-slot:title>
											<div class="">
												<p>Type: <b>{{ upperCaseWord(vDev.type) }}</b></p>
											</div>
										</template>
										<template v-slot:footer>
											<div class="flex flex-row gap-1">
												<p class="mt-3">Disks:</p>
												<Card v-for="disk, diskIdx in vDev.selectedDisks" :key="diskIdx" :bgColor="'bg-well'" :titleSection="true" :contentSection="false" :footerSection="false" class="rounded-lg text-default border border-default">
													<template v-slot:title>
														<div class="flex flex-col justify-center items-center text-center">
															<div><b :class="truncateText" :title="getDiskIDName(disks, vDev.diskIdentifier!, disk)">{{ getDiskIDName(disks, vDev.diskIdentifier!, disk) }}</b></div>
															<br/>
															<div><b>{{ getFullDiskInfo(disks, disk)!.capacity! }}</b></div>
														</div>
													</template>
												</Card>
											</div>
										</template>
									</Card>			
								</DisclosurePanel>
							</Disclosure>
						</div>
						
					</template>
				</Card>
			</div>
			
			<div v-if="poolConfig.createFileSystem! && !creatingFilesystem && !filesystemCreated" class="">
				<Card :bgColor="'bg-accent'" :titleSection="true" :contentSection="false" :footerSection="true" class="mt-2 mb-4 truncate rounded-lg border border-default text-default" :class="truncateText" :title="fileSystemData.name">
					<template v-slot:title>
						<div class="rounded-lg">						
							<p :class="truncateText" :title="fileSystemData.name">File System Name: <b :class="truncateText" :title="fileSystemData.name">{{ fileSystemData.name }}</b></p>
						</div>
					</template>
					<template v-slot:footer>
						<div>
							<p>Quota: <b>{{ convertBytesToSize(convertSizeToBytes((fileSystemData.properties.quota.raw.toString()) + fileSystemData.properties.quota.unit)) }}</b></p>
							<p>Read Only: <b>{{ upperCaseWord(isBoolOnOff(fileSystemData.properties.isReadOnly!)) }}</b></p>	
							<p v-if="fileSystemData.encrypted">Encryption: <b>{{ fileSystemData.properties.encryption.toUpperCase() }}</b></p>
							<p class="mt-1 border rounded-lg border-default bg-default">
								<Disclosure v-slot="{ open }">
									<DisclosureButton class="bg-default grid grid-cols-8 w-full justify-start text-center rounded-lg">
										<div class="m-1 col-span-1">
											<ChevronUpIcon
												class="h-7 w-7 text-default transition-all duration-200 transform" :class="{ 'rotate-90': !open, 'rotate-180': open, }"
											/>
										</div>
										<div class="-ml-8 mt-1.5 col-span-1">
											<span class="text-start whitespace-nowrap text-base text-default">Settings: <b v-if="fileSystemData.inherit">Inherited</b></span>
										</div>
									</DisclosureButton>
									<DisclosurePanel>
										<div v-if="fileSystemData.inherit" class="p-2 rounded-lg">
											<p>Compression: <b>{{ upperCaseWord(fileSystemData.properties.compression) }} ({{ poolConfig.compression!.toUpperCase() }})</b></p>
											<p>Deduplication: <b>{{ upperCaseWord(fileSystemData.properties.deduplication) }} ({{ upperCaseWord(poolConfig.dedup!) }})</b></p>
											<p>Record Size: <b>{{ upperCaseWord(fileSystemData.properties.recordSize) }} ({{ getValue('record', poolConfig.recordsize!.toString()) }})</b></p>
											<p>Access Time: <b>{{ upperCaseWord(fileSystemData.properties.accessTime) }} (On)</b></p>
											<p>Case Sensitivity: <b>{{ upperCaseWord(fileSystemData.properties.caseSensitivity) }} (Sensitive)</b></p>
											<p>DNode Size: <b>{{ upperCaseWord(fileSystemData.properties.dNodeSize) }} (Legacy)</b></p>
											<p>Extended Attributes: <b>{{ upperCaseWord(fileSystemData.properties.extendedAttributes) }} (System Attribute)</b></p>
										</div>
										<div v-else class="p-2 rounded-lg">
											<p>Compression: <b>{{ checkInheritance('compression', fileSystemData.properties.compression, poolConfig) }}</b></p>
											<p>Deduplication: <b>{{ checkInheritance('dedup', fileSystemData.properties.deduplication, poolConfig) }}</b></p>
											<p>Record Size: <b>{{ checkInheritance('record', fileSystemData.properties.recordSize, poolConfig) }}</b></p>
											<p>Access Time: <b>{{ checkInheritance('atime', fileSystemData.properties.accessTime, poolConfig) }}</b></p>
											<p>Case Sensitivity: <b>{{ checkInheritance('case', fileSystemData.properties.caseSensitivity, poolConfig) }}</b></p>
											<p>DNode Size: <b>{{ checkInheritance('dnode', fileSystemData.properties.dNodeSize, poolConfig) }}</b></p>
											<p>Extended Attributes: <b>{{ checkInheritance('xattr', fileSystemData.properties.extendedAttributes, poolConfig) }}</b></p>
										</div>
									</DisclosurePanel>
								</Disclosure>
							</p>					
						</div>
					</template>
				</Card>
			</div>
		</div>

		<div v-if="finishPressed" class="grid grid-cols-1 gap-1 bg-well rounded-md border border-default p-2">
			<div v-if="creatingPool && !poolCreated">
				<div class="grid justify-center justify-items-center">
					<legend class="text-lg text-default animate-pulse">Creating Pool...</legend>
					<LoadingSpinner :width="'w-24'" :height="'h-24'" :baseColor="'text-gray-200'" :fillColor="'fill-green-500'" class="font-semibold text-lg my-0.5"/>
				</div>
			</div>
			<div v-if="!creatingPool && poolCreated" class="">
				<div class="grid justify-center justify-items-center">
					<legend class="text-lg text-success">Pool Created!</legend>
					<CheckCircleIcon class="aspect-square w-10 h-10 text-green-400"/>
				</div>
			</div>
		</div>
		<div v-if="finishPressed && poolConfig.createFileSystem!" class="mt-2 p-2 grid grid-cols-1 gap-1 bg-well rounded-md border border-default">
			<div v-if="creatingPool">
				<div class="grid justify-center justify-items-center">
					<legend class="text-lg text-muted animate-pulse">Waiting for Pool...</legend>
					<LoadingSpinner :width="'w-24'" :height="'h-24'" :baseColor="'text-gray-200'" :fillColor="'fill-gray-300'" class="font-semibold text-lg my-0.5"/>
				</div>
			</div>
			<div v-if="!creatingPool && creatingFilesystem && !filesystemCreated">
				<div class="grid justify-center justify-items-center">
					<legend class="text-lg text-default animate-pulse">Creating File System...</legend>
					<LoadingSpinner :width="'w-24'" :height="'h-24'" :baseColor="'text-gray-200'" :fillColor="'fill-green-500'" class="font-semibold text-lg my-0.5"/>
				</div>
			</div>
			<div v-if="!creatingPool && !creatingFilesystem && filesystemCreated" class="">
				<div class="grid justify-center justify-items-center">
					<legend class="text-lg text-success">File System Created!</legend>
					<CheckCircleIcon class="aspect-square w-10 h-10 text-green-400"/>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { inject, Ref} from 'vue';
import Card from '../common/Card.vue';
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue';
import { CheckCircleIcon, ChevronUpIcon } from '@heroicons/vue/24/outline';
import { getFullDiskInfo, isBoolOnOff, convertBytesToSize, upperCaseWord, getValue, checkInheritance, convertSizeToBytes, getDiskIDName } from '../../composables/helpers';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import { VDevDisk, ZFSFileSystemInfo, ZPoolBase, ZpoolCreateOptions } from '@45drives/houston-common-lib';

const poolConfig = inject<Ref<ZPoolBase & ZpoolCreateOptions>>("pool-config-data")!;
const disks = inject<Ref<VDevDisk[]>>('disks')!;
const fileSystemData = inject<Ref<ZFSFileSystemInfo>>('file-system-data')!;

const finishPressed = inject<Ref<boolean>>('finish-pressed')!;
const creatingPool = inject<Ref<boolean>>('creating-pool')!;
const poolCreated = inject<Ref<boolean>>('pool-created')!;
const creatingFilesystem = inject<Ref<boolean>>('creating-filesystem')!;
const filesystemCreated = inject<Ref<boolean>>('filesystem-created')!;

const truncateText = inject<Ref<string>>('style-truncate-text')!;

// console.log('ReviewTab -> poolConfig:', poolConfig.value);
// console.log('ReviewTab -> fileSystemData:', fileSystemData.value);
// console.log('ReviewTab -> all disks:', disks.value);

</script>