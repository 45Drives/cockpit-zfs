<template>
	<!-- first tab: name entry -->
	<div v-if="props.tag ==='name-entry'">
		<legend class="mb-1 text-base font-semibold leading-6 text-default">Name this Pool</legend>
		<input type="text" @keydown.enter="onEnterPress" v-model="poolConfig.name" name="pool-name"
			:id="getIdKey('pool-name')" class="mt-1 block w-full input-textlike bg-default text-default"
			placeholder="Pool Name" />
	</div>

	<!-- second tab: vDev + disk selection -->
	<div v-if="props.tag ==='virtual-devices'">
		<fieldset>
			<legend class="mb-1 text-base font-semibold leading-6 text-default">Create a Virtual Device</legend>

			<div v-for="(vDev, vDevIdx) in poolConfig.vdevs" :key="vDevIdx" class="my-1 py-1">
				<!-- Virtual Device (Select) -->
				<div>
					<label :for="getIdKey('virtual-device')"
						class="block text-sm font-medium leading-6 text-default">Type</label>
					<!-- if first VDev, always either DISK, MIRROR, RAIDZ1-3 -->
					<!-- if NOT first VDev, always either CACHE, LOG, SPECIAL, SPARE, DEDUP, or TYPE OF FIRST VDEV -->
					<select :id="getIdKey('virtual-device')" v-model="poolConfig.vdevs[vDevIdx].type"
						name="virtual-device"
						class="text-default bg-default mt-1 block w-full input-textlike sm:text-sm sm:leading-6">
						<option v-if="vDevIdx === 0" value="disk">Disk</option>
						<option v-if="vDevIdx === 0" value="mirror">Mirror</option>
						<option v-if="vDevIdx === 0" value="raidz1">RaidZ1</option>
						<option v-if="vDevIdx === 0" value="raidz2">RaidZ2</option>
						<option v-if="vDevIdx === 0" value="raidz3">RaidZ3</option>
						<option v-if="vDevIdx !== 0" :value="additionalVDevType">{{upperCaseWord(additionalVDevType)}}
						</option>
						<option v-if="vDevIdx !== 0" value="cache">Cache</option>
						<option v-if="vDevIdx !== 0" value="log">Log</option>
						<option v-if="vDevIdx !== 0" value="special">Special</option>
						<option v-if="vDevIdx !== 0" value="spare">Spare</option>
						<option v-if="vDevIdx !== 0" value="dedup">Dedup</option>
					</select>
				</div>

				<!-- Disk ID (Select) -->
				<div>
					<label :for="getIdKey('disk-identifier')"
						class="block text-sm font-medium leading-6 text-default">Disk Identifier</label>
					<select :id="getIdKey('disk-identifier')" v-model="poolConfig.vdevs[vDevIdx].diskIdentifier"
						name="disk-identifier"
						class="text-default bg-default mt-1 block w-full input-textlike sm:text-sm sm:leading-6">
						<option value="sd_path">Block Device</option>
						<!-- <option value="">Disk/WWN</option> -->
						<option value="phy_path">Hardware Path</option>
						<option value="vdev_path">Device Alias</option>
						<option value="wwn_path">World Wide Name (WWN)</option>
					</select>
				</div>

				<!-- Disk selection, shows disks that are not in use and as they are selected it hides them from any additional VDevs so they cannot be selected twice -->
				<label :for="getIdKey('available-disk-list')"
					class="my-1 block text-sm font-medium leading-6 text-default">Select Disks</label>
				<ul v-if="vDevAvailDisks.length > 0" :id="getIdKey('available-disk-list')" role="list"
					class="flex flex-row flex-wrap gap-2">
					<li v-for="(disk, diskIdx) in vDevAvailDisks[vDevIdx]" :key="diskIdx" class="my-1">
						<button class="flex min-w-fit w-full h-full border border-default rounded-lg py-2 px-4"
							:class="diskCardClass(disk.name, vDevIdx)">
							<label :for="getIdKey(`vdev-${vDevIdx}-disk-${diskIdx}`)"
								class="flex flex-col w-full py-4 px-2 text-sm gap-0.5">
								<span class="flex flex-row flex-grow w-full justify-between">

									<input :id="getIdKey(`vdev-${vDevIdx}-disk-${diskIdx}`)"
										v-model="poolConfig.vdevs[vDevIdx].selectedDisks" type="checkbox"
										:value="`${disk.name}`" :name="`disk-${disk.name}`"
										class="justify-start w-4 h-4 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2" />
									<div v-if="disk.hasPartitions!"
										title="Disk already has partitions. Proceed with caution."
										class="flex items-center justify-center h-6 w-6 bg-default rounded-full ml-2">
										<ExclamationCircleIcon class="h-6 text-orange-700" />
									</div>
									<div v-if="disk.errors && disk.errors!.length > 0"
										title="This disk belongs to an exported pool. Force Create to override."
										class="flex items-center justify-center h-6 w-6 bg-default rounded-full ml-2">
										<ExclamationTriangleIcon class="h-6 text-danger" />
									</div>
								</span>
								<h3 class="truncate text-sm font-medium text-default"
									:title="getDiskIDName(disks, vDev.diskIdentifier!, disk.name!)">{{
									truncateName(getDiskIDName(disks, vDev.diskIdentifier!, disk.name!), 8) }}</h3>
								<p class="mt-1 truncate text-sm text-default">{{ disk.type }}</p>
								<p class="mt-1 truncate text-sm text-default">Capacity: {{ disk.capacity }}</p>
							</label>
						</button>
					</li>
				</ul>

				<!-- <span>{{ poolConfig.vdevs[vDevIdx].selectedDisks }}</span> -->

				<div v-if="vDevAvailDisks[vDevIdx].length == 0">
					No Disks Available
				</div>

				<!-- buttons to add/remove vdevs -->
				<div class="button-group-row mt-2">
					<!-- <button :id="getIdKey('add-vdev')" class="btn btn-primary object-right justify-end" @click="addVDev()">Add VDev</button> -->
					<button v-if="poolConfig.vdevs.length > 0" :id="getIdKey('remove-vdev')"
						class="btn btn-primary object-right justify-start mt-0.5" @click="removeVDev(vDevIdx)">Remove
						VDev</button>

					<!-- If (Log, Special, Dedup) -->
					<!-- If secondary VDev is LOG or SPECIAL or DEDUP, have option for them to be MIRROR also -->
					<!-- If Primary VDev is MIRROR or RAIDZ(x) then SPECIAL, LOG and DEDUP must be MIRROR -->
					<div v-if="poolConfig.vdevs[vDevIdx].type == 'log' || poolConfig.vdevs[vDevIdx].type == 'special' || poolConfig.vdevs[vDevIdx].type == 'dedup'"
						class="flex flex-row">
						<label :for="getIdKey('mirror-enabled')"
							class="mt-2 mr-2 block text-sm font-medium leading-6 text-default">Mirror ({{
							upperCaseWord(poolConfig.vdevs[vDevIdx].type) }})</label>

						<Switch v-model="poolConfig.vdevs[vDevIdx].isMirror"
							:class="[poolConfig.vdevs[vDevIdx].isMirror ? 'bg-primary' : 'bg-accent', 'mt-2 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.vdevs[vDevIdx].isMirror ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.vdevs[vDevIdx].isMirror ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.vdevs[vDevIdx].isMirror ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
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
			</div>

			<!-- if user accidentally removes all vdevs, shows add vdev button to add another (would like to change this so its impossible to remove 1st vDev and ensure there is always at least 1) -->
			<div v-if="poolConfig.vdevs.length < 1" class="button-group-row">
				<button :id="getIdKey('add-vdev')" class="btn btn-primary object-right justify-end"
					@click="initialVDev()">Add VDev</button>
			</div>
		</fieldset>
	</div>

	<!-- third tab: pool settings + advanced settings -->
	<div v-if="props.tag ==='pool-settings'">
		<fieldset>
			<legend class="mb-1 text-base font-semibold leading-6 text-default">Pool Settings</legend>

			<!-- Sector Size (Select) -->
			<div>
				<label :for="getIdKey('sector-size')" class="block text-sm font-medium leading-6 text-default">Sector
					Size</label>
				<select :id="getIdKey('sector-size')" v-model="poolConfig.sectorsize" name="sector-size"
					class="text-default bg-default mt-1 block w-full py-1.5 pl-3 pr-10 input-textlike sm:text-sm sm:leading-6">
					<option value="auto">Auto Detect</option>
					<option value="9">512 B</option>
					<option value="12">4 KiB</option>
					<option value="13">8 KiB</option>
					<option value="14">16 KiB</option>
					<option value="15">32 KiB</option>
					<option value="16">64 KiB</option>
				</select>
			</div>

			<!-- Record Size (Select) -->
			<div>
				<label :for="getIdKey('record-size')" class="block text-sm font-medium leading-6 text-default">Record
					Size</label>
				<select :id="getIdKey('record-size')" v-model="poolConfig.recordsize" name="record-size"
					class="text-default bg-default mt-1 block w-full py-1.5 pl-3 pr-10 input-textlike sm:text-sm sm:leading-6">
					<option :value="convertSizeToBytes('512b')">512 B</option>
					<option :value="convertSizeToBytes('4kib')">4 KiB</option>
					<option :value="convertSizeToBytes('8kib')">8 KiB</option>
					<option :value="convertSizeToBytes('16kib')">16 KiB</option>
					<option :value="convertSizeToBytes('32kib')">32 KiB</option>
					<option :value="convertSizeToBytes('64kib')">64 KiB</option>
					<option :value="convertSizeToBytes('128kib')">128 KiB</option>
					<option :value="convertSizeToBytes('256kib')">256 KiB</option>
					<option :value="convertSizeToBytes('512kib')">512 KiB</option>
					<option :value="convertSizeToBytes('1mib')">1 MiB</option>
				</select>
			</div>

			<!-- LZ4 Compression (Toggle) -->
			<div>
				<label :for="getIdKey('lz4-enabled')" class="mt-1 block text-sm font-medium leading-6 text-default">LZ4
					Compression</label>
				<Switch :id="getIdKey('lz4-enabled')" :modelValue="poolConfig.compression === 'lz4'"
					@update:modelValue="poolConfig.compression = $event ? 'lz4' : 'off'"
					:class="[poolConfig.compression === 'lz4' ? 'bg-primary' : 'bg-accent',
						'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
					<span class="sr-only">Use setting</span>
					<span
						:class="[poolConfig.compression === 'lz4' ? 'translate-x-5' : 'translate-x-0',
							'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
						<span :class="[poolConfig.compression === 'lz4' ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in',
							'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
							<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
								<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor" stroke-width="2"
									stroke-linecap="round" stroke-linejoin="round" />
							</svg>
						</span>
						<span :class="[poolConfig.compression === 'lz4' ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out',
							'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
							<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
								<path
									d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
							</svg>
						</span>
					</span>
				</Switch>
			</div>

			<!-- Advanced Settings (hidden for better UI/UX) -->
			<div class="bg-well rounded-md">
				<Disclosure v-slot="{ open }">
					<DisclosureButton class="bg-well mt-2 w-full justify-start text-center rounded-md flex flex-row">
						<div class="m-1">
							<ChevronUpIcon class="h-7 w-7 text-default transition-all duration-200 transform"
								:class="{ 'rotate-90': !open, 'rotate-180': open, }" />
						</div>
						<div class="ml-3 mt-1.5">
							<span class="text-start whitespace-nowrap text-base text-default"><b><u>Advanced
										Settings</u></b></span>
						</div>
					</DisclosureButton>
					<DisclosurePanel>
						<div class="bg-well rounded-md p-2">
							<!-- Deduplication (Toggle) -->
							<div class="ml-3 w-full">
								<label :for="getIdKey('deduplication-enabled')"
									class="mt-1 block text-sm font-medium leading-6 text-default">Deduplication</label>
								<Switch :id="getIdKey('deduplication-enabled')" :modelValue="poolConfig.dedup === 'on'"
									@update:modelValue="poolConfig.dedup = $event ? 'on' : 'off'"
									:class="[poolConfig.dedup === 'on' ? 'bg-primary' : 'bg-accent',
										'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
									<span class="sr-only">Use setting</span>
									<span
										:class="[poolConfig.dedup === 'on' ? 'translate-x-5' : 'translate-x-0',
											'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
										<span :class="[poolConfig.dedup === 'on' ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
												<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
													stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
											</svg>
										</span>
										<span :class="[poolConfig.dedup === 'on' ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
												<path
													d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
											</svg>
										</span>
									</span>
								</Switch>
							</div>

							<!-- Refreservation (Slider) -->
							<div class="ml-3 w-full">
								<label :for="getIdKey('steps-range')"
									class="mt-1 block text-sm font-medium text-default">Refreservation</label>
								<div class="flex flex-row">
									<input :id="getIdKey('steps-range')" v-model="poolConfig.refreservationPercent"
										type="range" min="0" max="20" step="1"
										class="text-default mt-5 w-3/4 h-2 bg-accent rounded-lg appearance-none cursor-pointer ">
									<input :id="getIdKey('steps-range')" v-model="poolConfig.refreservationPercent"
										type="number" min="0" max="20"
										class="text-default bg-default mt-1 w-fit block py-1.5 px-1.5 ml-2 text-default placeholder:text-muted input-textlike sm:text-sm sm:leading-6" />
									<p class="mt-3 pl-1">%</p>
								</div>
							</div>

							<!-- Auto-Expand Pool (Toggle) -->
							<div class="ml-3 w-full">
								<label :for="getIdKey('auto-expand-enabled')"
									class="mt-1 block text-sm font-medium leading-6 text-default">Auto-Expand Pool (When
									Larger Devices are Added)</label>
								<Switch :id="getIdKey('auto-expand-enabled')"
									:modelValue="poolConfig.autoexpand === 'on'"
									@update:modelValue="poolConfig.autoexpand = $event ? 'on' : 'off'"
									:class="[poolConfig.autoexpand === 'on' ? 'bg-primary' : 'bg-accent',
										'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
									<span class="sr-only">Use setting</span>
									<span
										:class="[poolConfig.autoexpand === 'on' ? 'translate-x-5' : 'translate-x-0',
											'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
										<span :class="[poolConfig.autoexpand === 'on' ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
												<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
													stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
											</svg>
										</span>
										<span :class="[poolConfig.autoexpand === 'on' ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
												<path
													d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
											</svg>
										</span>
									</span>
								</Switch>
							</div>

							<!-- Auto-Replace Devices (Toggle) -->
							<div class="ml-3 w-full">
								<label :for="getIdKey('auto-replace-enabled')"
									class="mt-1 block text-sm font-medium leading-6 text-default">Auto-Replace
									Devices</label>
								<Switch :id="getIdKey('auto-replace-enabled')"
									:modelValue="poolConfig.autoreplace === 'on'"
									@update:modelValue="poolConfig.autoreplace = $event ? 'on' : 'off'"
									:class="[poolConfig.autoreplace === 'on' ? 'bg-primary' : 'bg-accent',
										'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
									<span class="sr-only">Use setting</span>
									<span
										:class="[poolConfig.autoreplace === 'on' ? 'translate-x-5' : 'translate-x-0',
											'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
										<span :class="[poolConfig.autoreplace === 'on' ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
												<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
													stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
											</svg>
										</span>
										<span :class="[poolConfig.autoreplace === 'on' ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']" aria-hidden="true">
											<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
												<path
													d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
											</svg>
										</span>
									</span>
								</Switch>
							</div>

							<!-- Auto-TRIM (Toggle) -->
							<div class="ml-3 w-full">
								<label :for="getIdKey('auto-trim-enabled')"
									class="mt-1 block text-sm font-medium leading-6 text-default">Automatic TRIM</label>
								<Switch :id="getIdKey('auto-trim-enabled')" :modelValue="poolConfig.autotrim === 'on'"
									@update:modelValue="poolConfig.autotrim = $event ? 'on' : 'off'"
									:class="[poolConfig.autotrim === 'on' ? 'bg-primary' : 'bg-accent',
										'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
									<span class="sr-only">Use setting</span>
									<span
										:class="[poolConfig.autotrim === 'on' ? 'translate-x-5' : 'translate-x-0',
											'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
										<span :class="[poolConfig.autotrim === 'on' ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
											aria-hidden="true">
											<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
												<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
													stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
											</svg>
										</span>
										<span :class="[poolConfig.autotrim === 'on' ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out',
											'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
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
					</DisclosurePanel>
				</Disclosure>
			</div>


		</fieldset>
	</div>

	<!-- tab four: file system creation (so user does not have a naked pool) -->
	<!-- component has a toggle so user can choose if they want to create a file system at pool creation, or not if they do in fact want a naked pool -->
	<div v-show="props.tag ==='file-system'">
		<fieldset>
			<legend class="mb-1 text-base font-semibold leading-6 text-default">File System Settings</legend>

			<!-- Create a File System (Checkbox) -> Enables all fields underneath -->
			<button :class="createFileSystemCardClass(poolConfig.createFileSystem!)"
				class="box-border rounded-lg shadow-md focus:outline-none focus:ring-0 w-full h-full bg-45d mb-2">
				<label :for="getIdKey('create-filesystem')"
					:class="createFileSystemCardClass(poolConfig.createFileSystem!)"
					class="block py-3 w-full h-full font-medium text-white justify-center rounded">
					Create a File System?
					<input :id="getIdKey('create-filesystem')" v-model="poolConfig.createFileSystem"
						aria-describedby="create-filesystem" name="create-filesystem" type="checkbox"
						class="ml-2 h-4 w-4 rounded text-success" />
				</label>
			</button>

			<component v-show="poolConfig.createFileSystem" :is="createFileSystemComponent" ref="fsConfig"
				idKey="file-system" :isStandalone="false" />

		</fieldset>
	</div>

	<!-- tab five: final tab - review all data selected -->
	<div v-if="props.tag ==='review'">
		<fieldset>
			<!-- <ReviewTab/> -->
			<component :is="reviewTabComponent" />
		</fieldset>
	</div>

</template>

<script setup lang="ts">
import { inject, ref, Ref, computed, watchEffect, onMounted, watch } from 'vue';
import { ChevronUpIcon, ExclamationCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import { Switch, Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue';
import { isBoolOnOff, convertSizeToBytes, upperCaseWord, isBoolCompression, getDiskIDName, truncateName, getFullDiskInfo } from '../../composables/helpers';
import { loadImportablePools } from '../../composables/loadImportables';
import { ZPool ,VDevDisk, ZFSFileSystemInfo, ZpoolCreateOptions, ZPoolBase, VDev } from '@45drives/houston-common-lib';
import { NavigationCallback, StepsNavigationItem } from '../../types';

interface PoolConfigProps {
	tag: string;
	idKey: string;
	navCallback: NavigationCallback;
	currentNavigationItem: StepsNavigationItem;
}

const props = defineProps<PoolConfigProps>();

const poolConfig = inject<Ref<ZPoolBase & ZpoolCreateOptions>>('pool-config-data')!;
const disks = inject<Ref<VDevDisk[]>>('disks')!;
const allPools = inject<Ref<ZPool[]>>('pools')!;
const fileSystemConfig = inject<Ref<ZFSFileSystemInfo>>('file-system-data')!;

const nameFeedback = inject<Ref<string>>('feedback-name')!;
const vDevFeedback = inject<Ref<string>>('feedback-vdev')!;
const diskFeedback = inject<Ref<string>>('feedback-disk')!;
const diskSizeFeedback = inject<Ref<string>>('feedback-disk-size')!;
const diskBelongsFeedback = inject<Ref<string>>('feedback-disk-belongs')!;
const isProperReplicationFeedback = inject<Ref<string>>('feedback-replication-level')!;

const onEnterPress = (event: KeyboardEvent) => {
	// Handle navigation only if the 'Enter' key is pressed
	if (event.key === 'Enter') {
		if (props.currentNavigationItem) {
			props.navCallback(props.currentNavigationItem);  // Pass the item to navCallback
		} else {
			console.error('No matching navigation item found');
		}
	}
};


const createFileSystemComponent = ref();
const loadCreateFileSystemComponent = async () => {
	const module = await import('./FileSystem.vue');
	createFileSystemComponent.value = module.default;
}

const reviewTabComponent = ref();
const loadReviewTabComponent = async () => {
	const module = await import('./ReviewTab.vue');
	reviewTabComponent.value = module.default;
}

watchEffect(() => {
	if (props.tag === 'file-system' && poolConfig.value.createFileSystem) {
		loadCreateFileSystemComponent();
	}
	if (props.tag === 'review') {
		loadReviewTabComponent();
	}
});

const additionalVDevType = computed(() => {
	return poolConfig.value.vdevs[0].type;
});

//computed property to determine which disks are in use and which ones are not in use and therefore available for selection
const vDevAvailDisks = computed<VDevDisk[][]>(() => {
	return poolConfig.value.vdevs.map((vdev, vdevIdx) => {
		const claimed = poolConfig.value.vdevs
		.filter((_, idx) => idx !== vdevIdx)
		.flatMap(vdev => vdev.selectedDisks);
		console.log('claimed:', claimed);
		console.log('disks filtered:', disks.value.filter(disk => disk.guid === "" && !claimed.includes(disk.name)));
		return disks.value.filter(disk => disk.guid === "" && !claimed.includes(disk.name));
	});
});


//change color of disk when selected
const diskCardClass = (diskName, vDevIdx) => {
  const isSelected = poolConfig.value.vdevs[vDevIdx].selectedDisks!.includes(diskName);
  return isSelected ? 'bg-green-300 dark:bg-green-700' : '';
};

const createFileSystemCardClass = (createFileSystem : boolean) => {
	const isCreateFS = createFileSystem;
	return isCreateFS ? 'bg-green-300 dark:bg-green-700' : '';
};

//method for adding initial vdev with default values 
function initialVDev() {
	const vDevConfig: VDev = {
		name: '',
		type: 'raidz2',
		status: '',
		guid: '',
		stats: {
			write_errors: 0,
			read_errors: 0,
			checksum_errors: 0,
		},
		disks: [],
		selectedDisks: [],
		diskIdentifier: 'vdev_path',
	}

	poolConfig.value.vdevs.push(vDevConfig);
}

//method for adding additional vdev
function addVDev() {
	const vDevConfig: VDev = {
		name: '',
		type: poolConfig.value.vdevs[0].type,
		status: '',
		guid: '',
		stats: {
			write_errors: 0,
			read_errors: 0,
			checksum_errors: 0,
		},
		disks: [],
		selectedDisks: [],
		diskIdentifier: 'vdev_path',
		isMirror: false,
	}

  	poolConfig.value.vdevs.push(vDevConfig);
}

//method for validating pool name fits the criteria
const nameCheck = () => {
	let result = true;
	nameFeedback.value = '';
	
	if (poolConfig.value.name == '') {
		result = false;
		nameFeedback.value = 'Name cannot be empty.';
	} else if (poolConfig.value.name.match(/^[0-9]/) ) {
		result = false;
		nameFeedback.value = 'Name cannot begin with numbers.';
	} else if (poolConfig.value.name.match(/^[.]/ )) {
		result = false;
		nameFeedback.value = 'Name cannot begin with a period (.).';
	} else if (poolConfig.value.name.match(/^[_]/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with an underscore (_).';
	} else if (poolConfig.value.name.match(/^[-]/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with a hyphen (-).';
	} else if (poolConfig.value.name.match(/^[:]/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with a colon (:).';
	} else if (poolConfig.value.name.match(/^[ ]/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with whitespace.';
	} else if (poolConfig.value.name.match(/[ ]$/)) {
		result = false;
		nameFeedback.value = 'Name cannot end with whitespace.';
	} else if (poolConfig.value.name.match(/^c[0-9]|^log|^mirror|^raidz|^raidz1|^raidz2|^raidz3|^spare/)) {
		result = false;
		nameFeedback.value = 'Name cannot begin with a reserved name.';
	} else if (!poolConfig.value.name.match(/^[a-zA-Z0-9_.:-]*$/)) {
		result = false;
		nameFeedback.value = 'Name contains invalid characters.';
	} else if (nameExists()) {
		result = false;
		nameFeedback.value = 'A pool with that name already exists.';
	}
	return result;
}

function nameExists() {
  return allPools.value.some((pool) => {
    return poolConfig.value.name === pool.name;
  });
}

const replicationLevelCheck = () => {
	let result = true;
	isProperReplicationFeedback.value = '';

	poolConfig.value.vdevs.forEach(vDev => {
		if ((vDev.type == 'dedup' || vDev.type == 'special') && poolConfig.value.vdevs[0].type != 'disk' && !poolConfig.value.forceCreate && !vDev.isMirror) {
			result = false;
			isProperReplicationFeedback.value = 'Mismatched replication level. Forcefully create to override.';
		} else if (vDev.isMirror && (vDev.type == 'special' || vDev.type == 'dedup' || vDev.type == 'log') && vDev.selectedDisks!.length < 2) {
			result = false;
			isProperReplicationFeedback.value = `Two or more Disks are required for Mirror (${upperCaseWord(vDev.type)}).`;
		}
	});

	return result;
}

const diskSizeMatch = () => {
	let result = true;
	diskSizeFeedback.value = '';

	if (poolConfig.value.forceCreate) {
		return true;
	}

	poolConfig.value.vdevs.forEach(vDev => {
		let previousCapacity = 0;

		vDev.selectedDisks!.forEach(selDisk => {
			const disk = disks.value.find(fullDisk => fullDisk.name == selDisk);
			if (vDev.type === 'disk' || vDev.type === 'cache') {
				return;
			}
			if (disk) {
				const currentCapacity = convertSizeToBytes(disk.capacity!);

				if (previousCapacity != 0 && currentCapacity != previousCapacity) {
					result = false;
					diskSizeFeedback.value = `Mirror contains devices of different sizes. Forcefully create to override.\n`;
				}

				previousCapacity = currentCapacity;
			}
		});
	});

	return result;
}

watch(
	() => poolConfig.value.vdevs.map(vdev => vdev.selectedDisks), // Watch the selectedDisks in each vDev
	() => {
		// Run the check whenever selectedDisks change
		diskBelongsToImportablePool();
	},
	{ deep: true } // Ensure the watcher deeply watches the selectedDisks arrays
);

const importablePools = inject<Ref<ZPool[]>>('importable-pools')!;
const diskBelongsToImportablePool = () => {
	let result = false;
	diskBelongsFeedback.value = '';

	if (!disks.value || disks.value.length === 0) {
		console.error('Disks not loaded.');
		return false;
	}

	if (poolConfig.value.forceCreate) {
		return false;
	}

	poolConfig.value.vdevs.forEach(vdev => {
		vdev.selectedDisks!.forEach(diskName => {
			const selectedDisk = disks.value.find(fullDisk => fullDisk.name == diskName);
			if (!selectedDisk) return;

			// Reset errors for each disk before checking
			selectedDisk.errors = [];

			importablePools.value.forEach(pool => {
				pool.vdevs.forEach(importableVDev => {
					importableVDev.disks.forEach(disk => {
						if (selectedDisk.name === disk.name) {
							result = true;
							selectedDisk.errors!.push(`Disk belongs to ${pool.name}`);
							diskBelongsFeedback.value = 'There are disks belonging to exported pools. Use Force Create to override and use disk in new pool.';
						}
					});
				});
			});
		});
	});

	return result;
};


//method for validating disk selection per vdev type
const diskCheck = () => {
	let result = true;
	diskFeedback.value = '';
	poolConfig.value.vdevs.forEach(vdev => {
		console.log("diskCheck selectedDisks: ", vdev.selectedDisks! )

		if (vdev.type == 'mirror' && vdev.selectedDisks!.length < 2) {
			result = false;
			diskFeedback.value = 'Two or more Disks are required for Mirror.';
		} else if (vdev.type == 'raidz1' && vdev.selectedDisks!.length < 3) {
			result = false;
			diskFeedback.value = 'Three or more Disks are required for RaidZ1.';
		} else if (vdev.type == 'raidz2' && vdev.selectedDisks!.length < 4) {
			result = false;
			diskFeedback.value = 'Four or more Disks are required for RaidZ2.';
		} else if (vdev.type == 'raidz3' && vdev.selectedDisks!.length < 5) {
			result = false;
			diskFeedback.value = 'Five or more Disks are required for RaidZ3.';
		} else if (vdev.type == 'disk' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required.';
		} else if (vdev.type == 'log' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required for Log.';
		} else if (vdev.type == 'cache' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required for Cache.';		
		} else if (vdev.type == 'special' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required for Special.';
		} else if (vdev.type == 'spare' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required for Spare.';
		} else if (vdev.type == 'dedup' && vdev.selectedDisks!.length < 1) {
			result = false;
			diskFeedback.value = 'At least one Disk is required for Dedup.';
		} 
	});

	return result;
}

//method for checking that there is at least 1 vdev selected
const vDevCheck = () => {
	let result = true;
	vDevFeedback.value = '';
	
	if (poolConfig.value.vdevs.length < 1) {
		result = false;
		vDevFeedback.value = 'At least one Virtual Device is required.';
	}
	return result;
}

//method for validating all tabs and allowing user to proceed if valid
const validateAndProceed = (tabTag: string): boolean => {
	if (tabTag === 'name-entry') {
		return nameCheck();
	} else if (tabTag == 'virtual-devices') {
		if (nameCheck()) {
			if (vDevCheck()) {
				if (diskCheck() && diskSizeMatch()) {
					if (!diskBelongsToImportablePool() || poolConfig.value.forceCreate) {
						return replicationLevelCheck();
					}
				}
			}
		}
	} else if (tabTag == 'pool-settings') {
		if (nameCheck()) {
			if (vDevCheck()) {
				if (diskCheck()) {
					return true;
				}
			}
		}
	} else if (tabTag == 'file-system') {
		if (nameCheck()) {
			if (vDevCheck()) {
				if (diskCheck()) {
					if (poolConfig.value.createFileSystem!) {
						if (fsConfig.value.nameCheck(fileSystemConfig.value)) {
							return true;
						}
					}
				}
			}
		}
	} else if (tabTag == 'review') {
		if (nameCheck()) {
			if (vDevCheck()) {
				if (diskCheck()) {
					return true;
				}
			}
		}
	}
	return false;
}

//method for removing vdev
function removeVDev(index: number) {
  	poolConfig.value.vdevs = poolConfig.value.vdevs.filter((_, idx) => idx !== index) ?? [];
}

const newPoolData = inject<Ref<ZPoolBase & ZpoolCreateOptions>>('new-pool-data')!;
// const newVDevs = ref<VDev[]>([]);
const newVDevDisks = ref<VDevDisk[]>([]);

function fillNewPoolData() {
	console.log("fillData function's poolConfig:", poolConfig.value);

	newPoolData.value.name = poolConfig.value.name;
	poolConfig.value.vdevs.forEach(vDev => {
		const newVDev : VDev = {
			type: 'disk',
			disks: [],
		}
		newVDev.type = vDev.type;
		newVDev.isMirror = vDev.isMirror;
		console.log("fillNewPoolData vDev before disks: ", vDev)

		vDev.selectedDisks!.forEach(selectedDisk => {
			// const diskNameFinal = getDiskIDName(disks.value, vDev.diskIdentifier!, diskObject.path.toString());
			console.log('selectedDisk being checked:', selectedDisk);
			const diskNameFinal = getDiskIDName(disks.value, vDev.diskIdentifier!, selectedDisk);
			// const fullDisk = disks.value.find(disk => disk.path === diskNameFinal);
			const fullDisk = getFullDiskInfo(disks.value, selectedDisk);

			if (fullDisk) {
				newVDevDisks.value.push(fullDisk);
				console.log('fullVDevDisk:', fullDisk);
			} else {
				console.error(`Disk with path ${diskNameFinal} not found in available disks.`);
			}
		});
		
		console.log("fillNewPoolData vDev after disks: ", vDev)

		newVDev.disks = newVDevDisks.value;
		newVDevDisks.value = [];
		// newVDevs.value.push(newVDev);
		newPoolData.value.vdevs.push(newVDev);
	});

	// newPoolData.value.vdevs = newVDevs.value;

	newPoolData.value.autoexpand = poolConfig.value.autotrim;
	newPoolData.value.autoreplace = poolConfig.value.autoreplace;
	newPoolData.value.autotrim = poolConfig.value.autotrim;
	newPoolData.value.compression = poolConfig.value.compression;
	newPoolData.value.recordsize = Number(poolConfig.value.recordsize);
	newPoolData.value.dedup = poolConfig.value.dedup;
	newPoolData.value.forceCreate = poolConfig.value.forceCreate;
	newPoolData.value.refreservationPercent = poolConfig.value.refreservationPercent!;
	newPoolData.value.sectorsize = Number(poolConfig.value.sectorsize);

	console.log("newPoolData sent:", newPoolData);
}

onMounted(() => {
	loadImportablePools(importablePools.value, disks, allPools);
});

const fsConfig = ref();

async function createNewFileSystem() {
	console.log('fsConfig', fsConfig.value);

	await fsConfig.value.newFileSystemInPoolWizard();
}

const getIdKey = (name: string) => `${props.idKey}-${name}`;

if (poolConfig.value.vdevs.length < 1) initialVDev();

defineExpose({
	validateAndProceed,
	fillNewPoolData,
	addVDev,
	createNewFileSystem,
});
</script>