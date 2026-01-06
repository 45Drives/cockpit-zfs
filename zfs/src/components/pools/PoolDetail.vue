<template>
	<OldModal @close="closeModal" :close-on-background-click="false" :isOpen="showPoolDetails" :marginTop="'mt-28'"
		:width="'w-7/12'" :minWidth="'min-w-7/12'" :initialFocus="null">
		<template v-slot:title>
			<Navigation :navigationItems="navigation" :currentNavigationItem="currentNavigationItem"
				:navigationCallback="navigationCallback" :show="show" />
		</template>
		<template v-slot:content>
			<div v-if="navTag == 'stats'">
				<div class="mt-6 grid grid-cols-3 grid-rows-2 text-default">
					<PoolCapacity :id="getIdKey('pool-visual-capacity')" :fillColor="capacityColor"
						:name="props.pool.name" :totalSize="props.pool.properties.size"
						:percentage="props.pool.properties.capacity" :radius="50" :coordX="60" :coordY="60"
						:strokeWidth="10" :percentFontSize="'text-2xl'" class="w-full col-span-3 grow" />
					<div
						class="mt-2 px-8 col-span-3 row-start-2 grid grid-cols-3 justify-items-center min-w-fit max-w-fit">
						<div class="m-2 col-span-1">
							<p :id="getIdKey('pool-health')" name="pool-health" class="text-lg">Health: <span
									:class="formatStatus(props.pool.status)" class="">{{ props.pool.status }}</span></p>
							<p :id="getIdKey('pool-errors')" name="pool-errors" class="text-sm">Errors: <span
									:class="formatStatus(props.pool.status)" class="">{{ props.pool.errorCount }}</span>
								<br />as of {{ getTimestampString() }}
							</p>
							<p :id="getIdKey('pool-refreservation')" name="pool-refreservation" class="text-sm">
								Refreservation: {{
								convertBytesToSize(props.pool.properties.refreservationRawSize!) }} ({{
								convertBytesToSize(props.pool.properties.refreservationRawSize!) }} ({{
								props.pool.properties.refreservationPercent }}%)</p>
						</div>
						<div class="m-2 col-span-1">
							<p :id="getIdKey('pool-altroot')" name="pool-altroot" class="text-base"
								:title="props.pool.properties.altroot == '' || props.pool.properties.altroot == '-' ? 'None' : props.pool.properties.altroot"
								:class="truncateText">Alt Root: {{ props.pool.properties.altroot == '' ||
								props.pool.properties.altroot == '-' ? 'None' : props.pool.properties.altroot }}</p>
							<p :id="getIdKey('pool-devices')" name="pool-devices" class="text-base">Devices: {{
								getNumDevices }}</p>
							<p :id="getIdKey('pool-disks')" name="pool-disks" class="text-base">Disks: {{ getNumDisks }}
							</p>
						</div>
						<div class="m-2 col-span-1">
							<p :id="getIdKey('pool-allocated')" name="pool-allocated" class="text-base">Used: {{
								props.pool.properties.allocated }}</p>
							<p :id="getIdKey('pool-free')" name="pool-free" class="text-base">RAW Space Available: {{
								props.pool.properties.free }}</p>
							<p :id="getIdKey('pool-free')" name="pool-free" class="text-base">Actual Space Available: {{
								props.pool.properties.available }}</p>
							<p :id="getIdKey('pool-size')" name="pool-size" class="text-base">Total: {{
								props.pool.properties.size }}</p>
						</div>
					</div>
				</div>
			</div>

			<div v-if="navTag == 'topology'" class="mt-2 grid" :class="`grid-cols-${props.pool.vdevs.length}`">
				<div v-for="vDev, vDevIdx in props.pool.vdevs" :key="vDevIdx"
					class="p-2 m-2 rounded-md border border-default bg-accent">
					<legend class="mb-1 text-base font-medium leading-6 text-default">{{ vDev.name }} ({{ vDev.type }})
					</legend>

					<div class="grid" :class="vDev.disks.length < 2 ? 'grid-cols-1' : 'grid-cols-2'">
						<div v-for="disk, diskIdx in vDev.disks" :key="diskIdx" class="m-1">
							<PoolDetailDiskCard :disk="vDev.disks[diskIdx]" />
						</div>
					</div>
				</div>
			</div>


			<div v-if="navTag == 'snapshots'" class="w-full text-center min-w-fit">
				<component :is="snapshotListComponent" :pool="props.pool" :item="'pool'" />
			</div>

			<div v-if="navTag == 'settings'">
				<div class="grid grid-cols-4 gap-2">
					<div class="mt-2 col-span-1 col-start-1 row-start-1">
						<p :id="getIdKey('settings-pool-name')" name="settings-pool-name"
							class="text-base text-default">Pool</p>
						<p class="mt-1 py-1.5" :class="truncateText" :title="poolConfig.name">{{ poolConfig.name }}</p>
					</div>
					<div class="mt-2 col-span-1 col-start-2 row-start-1">
						<p :id="getIdKey('settings-pool-readonly')" name="settings-pool-readonly"
							class="text-base text-default">Read Only</p>
						<p class="mt-1 py-1.5">{{ upperCaseWord(isBoolOnOff(poolConfig.properties.readOnly)) }}</p>
					</div>
					<div class="mt-2 col-span-1 col-start-3 row-start-1">
						<p :id="getIdKey('settings-pool-guid')" name="settings-pool-guid"
							class="text-base text-default">GUID</p>
						<p class="mt-1 py-1.5">{{ poolConfig.guid }}</p>
					</div>

					<div class="mt-2 col-span-1 col-start-4 row-start-1">
						<label :for="getIdKey('settings-pool-sector-size')"
							class="bg-default block text-base leading-6 text-default">Sector Size</label>
						<p :id="getIdKey('settings-pool-sector-size')" name="settings-pool-sector-size"
							class="mt-1 py-1.5">{{ calculateSectorSize(Number(poolConfig.properties.sector)) }}</p>
					</div>

					<div class="mt-2 col-span-1 col-start-1 row-start-2">
						<label :for="getIdKey('settings-pool-fail-mode')"
							class="bg-default block text-base leading-6 text-default">Fail Mode</label>
						<select :id="getIdKey('settings-pool-fail-mode')" v-model="poolConfig.failMode"
							:disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''" name="pool-fail-mode"
							class="mt-1 block w-full rounded-md border-0 py-1.5 text-default bg-default ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-slate-600 sm:text-sm sm:leading-6">
							<option value="wait">Wait</option>
							<option value="continue">Continue</option>
							<option value="panic">Panic</option>
						</select>
					</div>


					<div class="mt-2 col-span-3 col-start-2 row-start-2">
						<p :for="getIdKey('settings-pool-comment')" class="text-base text-default">Comment</p>
						<input :id="getIdKey('settings-pool-comment')" v-model="poolConfig.comment"
							name="setting-pool-comment" placeholder="Enter a comment here" type="text"
							class="input-textlike mt-1 block w-full rounded-md border-0 py-1.5 px-1.5 text-default shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-muted focus:ring-2 focus:ring-inset focus:ring-slate-300 sm:text-sm sm:leading-6" />
					</div>

					<!-- auto-expand -->
					<div class="col-span-1 col-start-1 row-start-3">
						<label :for="getIdKey('settings-pool-auto-expand')"
							class="mt-1 block text-sm leading-6 text-default">Auto-Expand Pool</label>
						<Switch v-model="poolConfig.properties.autoExpand" :id="getIdKey('settings-pool-auto-expand')"
							:disabled="settingsLocked" :aria-disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''" :class="[
								settingsLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
								poolConfig.properties.autoExpand ? 'bg-secondary' : 'bg-accent',
								'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2'
							]">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.properties.autoExpand ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.properties.autoExpand ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.properties.autoExpand ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
										<path
											d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
									</svg>
								</span>
							</span>
						</Switch>
					</div>

					<!-- auto-replace -->
					<div class="col-span-1 col-start-2 row-start-3">
						<label :for="getIdKey('settings-pool-auto-replace')"
							class="mt-1 block text-sm leading-6 text-default">Auto-Replace Drives</label>
						<Switch v-model="poolConfig.properties.autoReplace" :id="getIdKey('settings-pool-auto-replace')"
							:disabled="settingsLocked" :aria-disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''"
							:class="[
								settingsLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer', poolConfig.properties.autoReplace ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.properties.autoReplace ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.properties.autoReplace ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.properties.autoReplace ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
										<path
											d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
									</svg>
								</span>
							</span>
						</Switch>
					</div>

					<!-- display snapshots in filesystem list -->
					<div class="col-span-2 col-start-3 row-start-3">
						<label :for="getIdKey('settings-pool-display-snapshots')"
							class="mt-1 block text-sm leading-6 text-default">List Snapshots With File Systems</label>
						<Switch v-model="poolConfig.properties.listSnapshots"
							:id="getIdKey('settings-pool-display-snapshots')" :disabled="settingsLocked"
							:aria-disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''"
							:class="[
								settingsLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer', poolConfig.properties.listSnapshots ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.properties.listSnapshots ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.properties.listSnapshots ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.properties.listSnapshots ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
										<path
											d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
									</svg>
								</span>
							</span>
						</Switch>
					</div>

					<!-- delegation (Allow non-privileged user access based on the dataset permissions)-->
					<div class="col-span-2 col-start-1 row-start-4">
						<div class="col-span-1 flex flex-row gap-2 mt-1 text-center leading-6">
							<label :for="getIdKey('settings-pool-delegation')"
								class="block text-sm text-default">Delegation</label>
							<p class="text-xs text-muted mt-0.5">(Access based on dataset permissions)</p>
						</div>
						<Switch :initialFocus="null" v-model="poolConfig.properties.delegation"
							:id="getIdKey('settings-pool-delegation')" :disabled="settingsLocked"
							:aria-disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''"
							:class="[
								settingsLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer', poolConfig.properties.delegation ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.properties.delegation ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.properties.delegation ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.properties.delegation ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
										<path
											d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
									</svg>
								</span>
							</span>
						</Switch>
					</div>

					<!-- auto-trim -->
					<div v-if="props.pool.diskType == 'SSD' || props.pool.diskType == 'Hybrid'"
						class="col-span-1 col-start-3 row-start-4">
						<label :for="getIdKey('settings-pool-auto-trim')"
							class="mt-1 block text-sm leading-6 text-default">Auto-TRIM Pool</label>
						<Switch v-model="poolConfig.properties.autoTrim" :id="getIdKey('settings-pool-auto-trim')"
							:disabled="settingsLocked" :aria-disabled="settingsLocked"
							:title="settingsLocked ? 'Requires administrative privileges' : ''"
							:class="[
								settingsLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer', poolConfig.properties.autoTrim ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
							<span class="sr-only">Use setting</span>
							<span
								:class="[poolConfig.properties.autoTrim ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
								<span
									:class="[poolConfig.properties.autoTrim ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
									aria-hidden="true">
									<svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
										<path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
											stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
									</svg>
								</span>
								<span
									:class="[poolConfig.properties.autoTrim ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
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
		</template>
		<template v-slot:footer>
			<div class="button-group-row w-full justify-between">
				<div class="mt-2 justify-self-start">
					<button @click="showPoolDetails = false" :id="getIdKey('close-details-btn')"
						name="close-details-btn" class="mt-1 btn btn-danger">Close</button>
				</div>
				<div class="justofy-self-center">
					<div class="button-group-row mt-2 justify-self-center">
						<p class="text-danger" v-if="commentFeedback">{{ commentFeedback }}</p>

					</div>
				</div>
				<div class="justify-self-end">
					<div v-if="navTag == 'topology'">
						<div class="mt-2">
							<button v-if="canDestructive" @click="addVDevButton()" :id="getIdKey('add-vdev-btn')"
								name="add-vdev-btn" class="mt-1 btn btn-primary">Add Virtual Device</button>
						</div>
					</div>
					<div v-if="navTag == 'snapshots'">
						<div class="mt-2">
							<button v-if="canDestructive" @click="createSnapshotBtn()"
								:id="getIdKey('create-snap-wizard-btn')" name="create-snap-wizard-btn"
								class="mt-1 btn btn-primary">Create Snapshot</button>
						</div>
					</div>
					<div v-if="navTag == 'settings'">
						<div class="button-group-row mt-2">
							<button v-if="!saving" @click="poolConfigureBtn(); props.confirmation;"
								:id="getIdKey('settings-save-btn')" name="settings-save-btn"
								class="mt-1 btn btn-primary">Save Changes</button>
							<button disabled v-if="saving" id="finish" type="button"
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
								Saving...
							</button>
						</div>

					</div>
				</div>
			</div>
		</template>
	</OldModal>

	<div v-if="showSnapshotModal">
		<component :is="createSnapshotComponent" @close="updateShowNewSnapshot" :poolName="props.pool.name"
			:item="'pool'" />
	</div>
	<div v-if="showAddVDevModal">
		<component :is="addVDevComponent" @close="updateShowAddVDev" :key="showAddVDevModal"
			:idKey="getIdKey(`show-vdev-modal`)" :pool="poolConfig" :marginTop="'mt-48'" />
	</div>

</template>


<script setup lang="ts">
import { reactive, ref, inject, Ref, computed, provide, watch } from 'vue';
import { Switch } from '@headlessui/vue';
import { configurePool } from '../../composables/pools';
import { getTimestampString, upperCaseWord, isBoolOnOff, loadScanActivities, loadTrimActivities, formatStatus, getCapacityColor, convertBytesToSize } from '../../composables/helpers';
import { loadDisksThenPools, loadScanObjectGroup, loadDiskStats } from '../../composables/loadData';
import OldModal from '../common/OldModal.vue';
import PoolCapacity from '../common/PoolCapacity.vue';
import Navigation from '../common/Navigation.vue';
import PoolDetailDiskCard from '../disks/PoolDetailDiskCard.vue';

const canDestructive = inject<Ref<boolean>>('can-destructive')!;
const settingsLocked = computed(() => !canDestructive.value);

interface PoolDetailsProps {
	pool: ZPool;
	confirmation: ConfirmationCallback;
	showFlag: boolean;
}

const emit = defineEmits(['close']);

const closeModal = () => {
	emit('close');
}

const props = defineProps<PoolDetailsProps>();
const truncateText = inject<Ref<string>>('style-truncate-text')!;

const poolConfig = ref<ZPool>({
	name: props.pool.name,
	status: props.pool.status,
	guid: props.pool.guid,
	properties: {
		rawsize: props.pool.properties.rawsize,
		size: props.pool.properties.size,
		allocated: props.pool.properties.allocated,
		capacity: props.pool.properties.capacity,
		free: props.pool.properties.free,
		sector: props.pool.properties.sector,
		record: props.pool.properties.record,
		compression: props.pool.properties.compression,
		deduplication: props.pool.properties.deduplication,
		refreservationPercent: props.pool.properties.refreservationPercent,
		autoExpand: props.pool.properties.autoExpand,
		autoReplace: props.pool.properties.autoReplace,
		autoTrim: props.pool.properties.autoTrim,
		forceCreate: props.pool.properties.forceCreate,
		delegation: props.pool.properties.delegation,
		listSnapshots: props.pool.properties.listSnapshots,
		readOnly: props.pool.properties.readOnly,
		available:props.pool.properties.available
	},
	vdevs: props.pool.vdevs,
	failMode: props.pool.failMode,
	comment: props.pool.comment!,
	statusCode: props.pool.statusCode,
	statusDetail: props.pool.statusDetail,
	errorCount: props.pool.errorCount
});

const capacityColor = computed(() =>
	getCapacityColor('text', props.pool.properties.capacity, props.pool.properties.refreservationPercent!)
);


////////////////// Loading Data /////////////////////
/////////////////////////////////////////////////////
const pools = inject<Ref<ZPool[]>>('pools')!;
const disks = inject<Ref<VDevDisk[]>>('disks')!;
const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;
const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;
const snapshots = inject<Ref<Snapshot[]>>('snapshots')!;
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { ZPool, VDevDisk } from '@45drives/houston-common-lib';
import { Activity, ConfirmationCallback, NavigationCallback, NavigationItem, PoolDiskStats, PoolEditConfig, PoolScanObjectGroup, Snapshot } from '../../types';

const snapshotListComponent = ref();
// const loadSnapshotListComponent = async () => {
// 	const module = await import('../snapshots/SnapshotsList.vue');
// 	snapshotListComponent.value = module.default;
// }

const showPoolDetails = inject<Ref<boolean>>("show-pool-deets")!;

const getNumDevices = props.pool.vdevs.length;

const getNumDisks = computed(() =>  {
	let disks = 0;
	props.pool.vdevs.forEach(vdev => {
		vdev.disks.forEach(disk => {
			disks++;
		});
	});
	return disks;
});

//displaying sector size in bytes/kb
function calculateSectorSize(exponent) {
	const bytes = Math.pow(2, exponent);
	const result = ref('');

	if (bytes > 1024) {
		const kiB = bytes / 1024;
		result.value = `${kiB} KiB`;
	} else {
		result.value = `${bytes} B`;
	}
	  return result.value;
}

///////// Values for Confirmation Modals ////////////
/////////////////////////////////////////////////////
const operationRunning = ref(false);
const firstOptionToggle = ref(false);
const secondOptionToggle = ref(false);
const thirdOptionToggle = ref(false);
const fourthOptionToggle = ref(false);

///////////////////// Add VDev //////////////////////
/////////////////////////////////////////////////////
const showAddVDevModal = ref(false);

const addVDevComponent = ref();
const loadAddVDevComponent = async () => {
	const module = await import('./AddVDevModal.vue');
	addVDevComponent.value = module.default;
}

async function addVDevButton() {
	await loadAddVDevComponent();
	showAddVDevModal.value = true;
	// console.log('add vdev modal triggred');
}

const updateShowAddVDev = (newVal) => {
	showAddVDevModal.value = newVal;
}

///////////////// Create Snapshots //////////////////
/////////////////////////////////////////////////////
const showSnapshotModal = ref(false);
const creating = ref(false);
const confirmCreate = ref(false);

const createSnapshotComponent = ref();
const loadCreateSnapshotComponent = async () => {
	const module = await import('../snapshots/CreateSnapshotModal.vue');
	createSnapshotComponent.value = module.default;
}

async function createSnapshotBtn() {
	await loadCreateSnapshotComponent();
	showSnapshotModal.value = true;
	// console.log('create snapshot modal triggered');
}

const updateShowNewSnapshot = (newVal) => {
	showSnapshotModal.value = newVal;
}

/////////////////// Pool Changes ////////////////////
/////////////////////////////////////////////////////
const saving = ref(false);
const commentFeedback = ref('');

const newChangesToPool = ref<PoolEditConfig>({
	name: poolConfig.value.name,
	guid: poolConfig.value.guid,
	readonly: isBoolOnOff(poolConfig.value.properties.readOnly),
});

const updatedProperties: Partial<PoolEditConfig> = ({
	name: poolConfig.value.name,
	guid: poolConfig.value.guid,
	readonly: isBoolOnOff(poolConfig.value.properties.readOnly),
});


async function checkForChanges() {
	const changes: Partial<PoolEditConfig> = {};

	// Always allow comment (non-destructive)
	if (poolConfig.value.comment !== props.pool.comment) {
		changes.comment = poolConfig.value.comment;
	}

	// Only include the rest if we are allowed to make destructive/admin changes
	if (!settingsLocked.value) {
		if (poolConfig.value.failMode !== props.pool.failMode) changes.failmode = poolConfig.value.failMode;
		if (poolConfig.value.properties.autoExpand !== props.pool.properties.autoExpand) changes.autoexpand = isBoolOnOff(poolConfig.value.properties.autoExpand);
		if (poolConfig.value.properties.autoReplace !== props.pool.properties.autoReplace) changes.autoreplace = isBoolOnOff(poolConfig.value.properties.autoReplace);
		if (poolConfig.value.properties.autoTrim !== props.pool.properties.autoTrim) changes.autotrim = isBoolOnOff(poolConfig.value.properties.autoTrim);
		if (poolConfig.value.properties.delegation !== props.pool.properties.delegation) changes.delegation = isBoolOnOff(poolConfig.value.properties.delegation!);
		if (poolConfig.value.properties.listSnapshots !== props.pool.properties.listSnapshots) changes.listsnapshots = isBoolOnOff(poolConfig.value.properties.listSnapshots!);
	}

	newChangesToPool.value = { ...newChangesToPool.value, ...changes };
	return Object.keys(changes).length > 0;
}

const commentLengthCheck = (poolData) => {
	let result = true;
	commentFeedback.value = '';	

	if (poolData.comment.length > 32) {
		result = false;
		commentFeedback.value = 'Comment cannot exceed 32 characters.';
	}

	return result;
}

const confirmSavePool = inject<Ref<boolean>>('confirm-save-pool')!;
	
async function poolConfigureBtn() {
	if (commentLengthCheck(poolConfig.value)) {
		if (!(await checkForChanges())) {
			pushNotification(new Notification('No Changes', 'No modifications detected in the pool configuration.', 'info', 5000));
			showPoolDetails.value = false;
			return;
		}

		saving.value = true;
		try {
			const result = await configurePool(newChangesToPool.value);

			if (result.success === false) { 
				pushNotification(new Notification('Save Pool Config Failed', `There was an error saving this pool: ${result.error || 'Unknown error occurred'}.`, 'error', 5000));
				confirmSavePool.value = false;
			} else if (result.success === true) {
				// pushNotification(new Notification('Pool Config Saved', "Successfully saved this pool's configuration.", 'success', 5000));
				confirmSavePool.value = true;
				showPoolDetails.value = false;
			}
		} catch (error: any) {
			pushNotification(new Notification('Operation Failed', `An unexpected error occurred: ${error.message}`, 'error', 5000));
		} finally {
			saving.value = false;
		}

	}
}

/////////////////// Navigation //////////////////////
/////////////////////////////////////////////////////
const navTag = ref('stats');
const show = ref(true);

const currentNavigationItem = computed<NavigationItem | undefined>(() => navigation.find(item => item.current));

const navigationCallback: NavigationCallback = (item: NavigationItem) => {
	navTag.value = item.tag;
};

watch(navTag, (newVal, oldVal) => {
	if (navTag.value == 'snapshots') {
		// loadSnapshotListComponent();
		import('../snapshots/SnapshotsList.vue').then(module => {
			snapshotListComponent.value = module.default;
		});
	}
}, {immediate: true});


const navigation = reactive<NavigationItem[]>([
	{ name: 'Stats', tag: 'stats', current: computed(() => navTag.value == 'stats') as unknown as boolean, show: true, },
	{ name: 'Topology', tag: 'topology', current: computed(() => navTag.value == 'topology') as unknown as boolean, show: true, },
	{ name: 'Snapshots', tag: 'snapshots', current: computed(() => navTag.value == 'snapshots') as unknown as boolean, show: true, },
	{ name: 'Settings', tag: 'settings', current: computed(() => navTag.value == 'settings') as unknown as boolean, show: true, },
].filter(item => item.show));

const getIdKey = (name: string) => `${name}`;

provide('create-snap-modal', showSnapshotModal);
provide('current-pool-config', poolConfig);
provide('show-vdev-modal', showAddVDevModal);
provide("saving", saving);
provide('create-snap-modal', showSnapshotModal);
provide("snapshots", snapshots);
provide('confirm-create-snap', confirmCreate);
provide('creating', creating);
provide('modal-confirm-running', operationRunning);
provide('modal-option-one-toggle', firstOptionToggle);
provide('modal-option-two-toggle', secondOptionToggle);
provide('modal-option-three-toggle', thirdOptionToggle);
provide('modal-option-four-toggle', fourthOptionToggle);
</script>
