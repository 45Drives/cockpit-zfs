<template>
    <OldModal :isOpen="showImportModal" @close="showImportModal = false" :marginTop="'mt-28'" :width="'w-3/5'"
        :minWidth="'min-w-3/5'" :closeOnBackgroundClick="false">
        <template v-slot:title>
            <legend class="flex justify-center">Import Pool</legend>
        </template>
        <template v-slot:content>
            <div>
                <div class="grid grid-cols-3">

                    <!-- Pool selection box (select box or checkbox?) -->
                    <div class="mt-2 col-span-3">
                        <label :for="getIdKey('available-pool-list')"
                            class="my-1 block text-sm font-medium leading-6 text-default">Select Pool</label>
                        <ul :id="getIdKey('available-pool-list')" role="list"
                            class="grid gap-1 grid-cols-1 p-1 border border-default rounded-md bg-accent overflow-y-auto h-56 min-h-min">
                            <div v-if="!loading">
                                <div v-if="!showDeletedPools">
                                    <li v-if="importablePools.length > 0" v-for="pool, idx in importablePools"
                                        :key="idx" class="col-span-1">
                                        <button
                                            class="flex min-w-fit w-full h-fit min-h-fit border border-default bg-well rounded-md"
                                            :class="poolSelectedClass(pool.guid)">
                                            <label :for="getIdKey(`pool-${idx}`)"
                                                class="flex flex-col w-full py-2 mb-1 mx-2 text-default">
                                                <input v-model="importedPool.poolGUID"
                                                    @change="updateImportedPoolData(pool)" :id="getIdKey(`pool-${idx}`)"
                                                    type="radio" :value="`${pool.guid}`"
                                                    :name="`pool-${pool.name}-${pool.guid}`"
                                                    class="w-4 h-4 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-1" />
                                                <p>Name: {{pool.name}}</p>
                                                <p>GUID: {{ pool.guid }}</p>
                                                <p>Status: {{ pool.status }}</p>
                                                <p>Destroyed: {{ pool.isDestroyed }}</p>
                                                <span v-if="pool.errors!.length > 0" title="Pool has errors. Must Forcefully Import">
                                                    <ExclamationCircleIcon class="text-danger h-6" />
                                                </span>
                                                <!-- <p v-if="pool.errors!.length > 0" class="text-danger">
                                                    <li v-for="error in pool.errors!" :key="error">
                                                        {{ error }}
                                                    </li>
                                                </p> -->
                                            </label>
                                        </button>
                                    </li>
                                    <div v-else class="relative flex justify-center items-stretch">
                                        <p
                                            class="absolute inset-0 grow text-center text-xl font-medium text-default p-10">
                                            No Importable Pools Found</p>
                                    </div>
                                </div>
                                <div v-if="showDeletedPools">
                                    <li v-if="importableDestroyedPools.length > 0"
                                        v-for="pool, idx in importableDestroyedPools" :key="idx" class="col-span-1">
                                        <button
                                            class="flex min-w-fit w-full h-fit min-h-fit border border-default bg-well rounded-md"
                                            :class="poolSelectedClass(pool.guid)">
                                            <label :for="getIdKey(`pool-${idx}`)"
                                                class="flex flex-col w-full py-2 mb-1 mx-2 text-default">
                                                <input v-model="importedPool.poolGUID"
                                                    @change="updateImportedPoolData(pool)" :id="getIdKey(`pool-${idx}`)"
                                                    type="radio" :value="`${pool.guid}`"
                                                    :name="`pool-${pool.name}-${pool.guid}`"
                                                    class="w-4 h-4 text-success bg-well border-default rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-1" />
                                                <p>Name: {{pool.name}}</p>
                                                <p>GUID: {{ pool.guid }}</p>
                                                <p>Status: {{ pool.status }}</p>
                                                <p>Destroyed: {{ pool.isDestroyed }}</p>
                                                <span v-if="pool.errors!.length > 0" title="Pool has errors. Must Forcefully Import">
                                                    <ExclamationCircleIcon class="text-danger h-6" />
                                                </span>
                                                <!-- <p v-if="pool.errors!.length > 0" class="text-danger">
                                                    <li v-for="error in pool.errors!" :key="error">
                                                        {{ error }}
                                                    </li>
                                                </p> -->
                                            </label>
                                        </button>
                                    </li>
                                    <div v-else class="relative flex">
                                        <p
                                            class="absolute inset-0 grow text-center text-xl font-medium text-default p-10">
                                            No Destroyed Pools Found</p>
                                    </div>
                                </div>
                            </div>
                            <div v-else>
                                <LoadingSpinner :width="'w-10'" :height="'h-10'" :baseColor="'text-gray-200'"
                                    :fillColor="'fill-slate-500'" class="font-semibold text-lg my-0.5" />
                            </div>

                        </ul>
                    </div>

                    <!-- Switch for showing exported pools or showing deleted pools -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('show-destroyed-pools-switch')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Show Destroyed Pools</label>
                        <Switch v-model="showDeletedPools" :id="getIdKey('show-destroyed-pools-switch')"
                            :class="[showDeletedPools! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[showDeletedPools! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[showDeletedPools! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[showDeletedPools! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>

                    <!-- Disk Identifier -->
                    <div class="mt-2 col-span-2">
                        <label :for="getIdKey('disk-identifier')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Disk Identifier</label>
                        <select :id="getIdKey('disk-identifier')" v-model="importedPool.identifier" name=""
                            class="mt-1 block w-full input-textlike bg-default">
                            <option value="vdev_path">Device Alias</option>
                            <option value="sd_path">Block Device</option>
                            <option value="phy_path">Hardware Path</option>
                        </select>
                    </div>

                    <!-- Switch for renaming imported pool -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('rename-pool-switch')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Rename Pool</label>
                        <Switch v-model="importedPool.renamePool" :id="getIdKey('rename-pool-switch')"
                            :class="[importedPool.renamePool! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.renamePool! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.renamePool! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.renamePool! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>
                    <!-- If Switch is ON, show text input for new pool name -->
                    <div v-if="importedPool.renamePool" class="mt-2 col-span-2">
                        <label :for="getIdKey('new-pool-name')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">New Name</label>
                        <input type="text" v-model="importedPool.newPoolName" name="pool-name"
                            :id="getIdKey('new-pool-name')" class="mt-1 block w-full input-textlike bg-default"
                            placeholder="New Pool Name" />
                    </div>

                    <!-- Alt Root -->
                    <div class="mt-2 col-span-3">
                        <label :for="getIdKey('alt-root')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Alt Root</label>
                        <input type="text" v-model="importedPool.altRoot" name="pool-name" :id="getIdKey('alt-root')"
                            class="mt-1 block w-full input-textlike bg-default" placeholder="Alt Root" />
                    </div>

                    <!-- Switch for Read Only -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('read-only')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Read Only</label>
                        <Switch v-model="importedPool.readOnly" :id="getIdKey('read-only')"
                            :class="[importedPool.readOnly! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.readOnly! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.readOnly! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.readOnly! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>

                    <!-- Switch for Recovery Mode -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('recovery-mode')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Recovery Mode</label>
                        <Switch v-model="importedPool.recoveryMode" :id="getIdKey('recovery-mode')"
                            :class="[importedPool.recoveryMode! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.recoveryMode! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.recoveryMode! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.recoveryMode! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>

                    <!-- Switch for Ignore Missing Log Devices -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('ignore-missing-logs')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Ignore Missing Log
                            Devices</label>
                        <Switch v-model="importedPool.ignoreMissingLog" :id="getIdKey('ignore-missing-logs')"
                            :class="[importedPool.ignoreMissingLog! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.ignoreMissingLog! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.ignoreMissingLog! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.ignoreMissingLog! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>

                    <!-- Switch for Mount Filesystems (ON by default, if OFF then execute command) -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('mount-filesystems')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Mount File Systems</label>
                        <Switch v-model="importedPool.mountFileSystems" :id="getIdKey('mount-filesystems')"
                            :class="[importedPool.mountFileSystems! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.mountFileSystems! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.mountFileSystems! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.mountFileSystems! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-primary" fill="currentColor" viewBox="0 0 12 12">
                                        <path
                                            d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                                    </svg>
                                </span>
                            </span>
                        </Switch>
                    </div>

                    <!-- Switch for Force Import -->
                    <div class="mt-2 col-span-1">
                        <label :for="getIdKey('force-import')"
                            class="mt-1 bg-default block text-sm leading-6 text-default">Forcefully Import</label>
                        <Switch v-model="importedPool.forceImport" :id="getIdKey('force-import')"
                            :class="[importedPool.forceImport! ? 'bg-secondary' : 'bg-accent', 'mt-1 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-slate-600 focus:ring-offset-2']">
                            <span class="sr-only">Use setting</span>
                            <span
                                :class="[importedPool.forceImport! ? 'translate-x-5' : 'translate-x-0', 'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-default shadow ring-0 transition duration-200 ease-in-out']">
                                <span
                                    :class="[importedPool.forceImport! ? 'opacity-0 duration-100 ease-out' : 'opacity-100 duration-200 ease-in', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
                                    aria-hidden="true">
                                    <svg class="h-3 w-3 text-muted" fill="none" viewBox="0 0 12 12">
                                        <path d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2" stroke="currentColor"
                                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </span>
                                <span
                                    :class="[importedPool.forceImport! ? 'opacity-100 duration-200 ease-in' : 'opacity-0 duration-100 ease-out', 'absolute inset-0 flex h-full w-full items-center justify-center transition-opacity']"
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
            <div class="w-full grid grid-rows-2">
                <div class="w-full row-start-1">
                    <div class="mt-2">
                        <p class="text-danger" v-if="nameFeedback">{{ nameFeedback }}</p>
                    </div>
                </div>
                <div class="button-group-row w-full row-start-2 justify-between mt-2">
                    <button @click="showImportModal = false" :id="getIdKey('cancel-import')" name="cancel-import"
                        class="mt-1 btn btn-danger object-left justify-start h-fit">Cancel</button>
                    <button v-if="!importing" @click="importPoolBtn()" :id="getIdKey('import-pool-btn')"
                        name="import-pool-btn"
                        class="mt-1 btn btn-primary object-right justify-end h-fit">Import</button>
                    <button v-if="importing" disabled :id="getIdKey('import-pool-spinner')" type="button"
                        class="btn btn-danger object-right justify-end">
                        <svg aria-hidden="true" role="status"
                            class="inline w-4 h-4 mr-3 text-gray-200 animate-spin text-default" viewBox="0 0 100 101"
                            fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                fill="currentColor" />
                            <path
                                d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                fill="text-success" />
                        </svg>
                        Importing...
                    </button>
                </div>
            </div>
        </template>
    </OldModal>
</template>
<script setup lang="ts">
import { inject, ref, Ref, computed, watch } from 'vue';
import { Switch } from '@headlessui/vue';
import OldModal from '../common/OldModal.vue';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import { ExclamationCircleIcon } from '@heroicons/vue/24/outline';
import { loadImportablePools, loadImportableDestroyedPools } from '../../composables/loadImportables';
import { importPool } from '../../composables/pools';
import { VDevDisk, ZPool, ZFSFileSystemInfo } from '@45drives/houston-common-lib';
import { pushNotification, Notification } from '@45drives/houston-common-ui';
import { ImportablePoolData, PoolScanObjectGroup, PoolDiskStats, Activity, ImportedPool } from '../../types';
import { useRefreshAllData } from '../../composables/useRefreshAllData';

const showDeletedPools = ref(false);
const showImportModal = inject<Ref<boolean>>('show-import-modal')!;

const disks = inject<Ref<VDevDisk[]>>('disks')!;
const pools = inject<Ref<ZPool[]>>('pools')!;
const datasets = inject<Ref<ZFSFileSystemInfo[]>>('datasets')!;

const importablePools = inject<Ref<ImportablePoolData[]>>('importable-pools')!;
const allImportableDestroyedPools = inject<Ref<ImportablePoolData[]>>('importable-destroyed-pools')!;

const importableDestroyedPools = computed<ImportablePoolData[]>(() => {
    return allImportableDestroyedPools.value.filter((destroyedPool) => {
        return !importablePools.value.some((importablePool) => destroyedPool.guid === importablePool.guid);
    });
});

const importing = ref(false);
const loading = ref(true);

const nameFeedback = ref('');

const disksLoaded = inject<Ref<boolean>>('disks-loaded')!;
const poolsLoaded = inject<Ref<boolean>>('pools-loaded')!;
const fileSystemsLoaded = inject<Ref<boolean>>('datasets-loaded')!;
const scanObjectGroup = inject<Ref<PoolScanObjectGroup>>('scan-object-group')!;
const poolDiskStats = inject<Ref<PoolDiskStats>>('pool-disk-stats')!;

const scanActivities = inject<Ref<Map<string, Activity>>>('scan-activities')!;
const trimActivities = inject<Ref<Map<string, Activity>>>('trim-activities')!;

const poolSelectedClass = (poolGUID) => {
   return poolGUID === importedPool.value.poolGUID ? 'bg-green-300 dark:bg-green-700' : '';
}

function loadImports() {
    loading.value = true;
    importablePools.value = [];
    loadImportablePools(importablePools.value, disks, pools);
    loading.value = false;    
}

function loadDestroyedImports() {
    loading.value = true;
    allImportableDestroyedPools.value = [];
    loadImportableDestroyedPools(allImportableDestroyedPools.value, disks, pools);    
    loading.value = false;
}

loadImports();

watch(showDeletedPools, async (newValue, oldValue) => {
	if (showDeletedPools) {
        loadDestroyedImports();
    } else {
        loadImports();
    }
});

const importedPool = ref<ImportedPool>({
    name: '',
	poolGUID: '',
	altRoot: '',
	renamePool: false,
	newPoolName: '',
	identifier: 'vdev_path',
	forceImport: false,
	recoveryMode: false,
	ignoreMissingLog: false,
	mountFileSystems: true,
	readOnly: false,
    isDestroyed: false,
    errors: [],
});

function isPoolDestroyed() {
    return importableDestroyedPools.value.some(pool => pool.guid === importedPool.value.poolGUID);
}

function updateImportedPoolData(pool) {
    importedPool.value.name = pool.name;
    importedPool.value.errors! = pool.errors;
}

//method for validating pool name fits the criteria
const nameCheck = () => {
	let result = true;
	nameFeedback.value = '';
    // console.log('importedPool.newName:', importedPool.value.newPoolName!);
    if (importedPool.value.renamePool) {
        if (importedPool.value.newPoolName! == '') {
		    result = false;
            nameFeedback.value = 'Name cannot be empty.';
        } else if (importedPool.value.newPoolName!.match(/^[0-9]/) ) {
            result = false;
            nameFeedback.value = 'Name cannot begin with numbers.';
        } else if (importedPool.value.newPoolName!.match(/^[.]/ )) {
            result = false;
            nameFeedback.value = 'Name cannot begin with a period (.).';
        } else if (importedPool.value.newPoolName!.match(/^[_]/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with an underscore (_).';
        } else if (importedPool.value.newPoolName!.match(/^[-]/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with a hyphen (-).';
        } else if (importedPool.value.newPoolName!.match(/^[:]/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with a colon (:).';
        } else if (importedPool.value.newPoolName!.match(/^[ ]/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with whitespace.';
        } else if (importedPool.value.newPoolName!.match(/[ ]$/)) {
            result = false;
            nameFeedback.value = 'Name cannot end with whitespace.';
        } else if (importedPool.value.newPoolName!.match(/^c[0-9]|^log|^mirror|^raidz|^raidz1|^raidz2|^raidz3|^spare/)) {
            result = false;
            nameFeedback.value = 'Name cannot begin with a reserved name.';
        } else if (!importedPool.value.newPoolName!.match(/^[a-zA-Z0-9_.:-]*$/)) {
            result = false;
            nameFeedback.value = 'Name contains invalid characters.';
        } else if (importableNameExists()) {
            result = false;
            nameFeedback.value = 'A pool with that name already exists.';
        }
    }

    return result;
}

function importableNameExists() {
    return importablePools.value.some((pool) => {
        return importedPool.value.newPoolName! === pool.name;
    });
}

const { refreshAllData } = useRefreshAllData({
    poolData: pools,
    diskData: disks,
    filesystemData: datasets,
    disksLoaded,
    poolsLoaded,
    fileSystemsLoaded,
    scanObjectGroup,
    poolDiskStats,
    scanActivities,
    trimActivities
});


async function importPoolBtn() {
    if (nameCheck()) {
        if (isPoolDestroyed()) {
            importedPool.value.isDestroyed = true;
        }
        
        // console.log('importing pool:', importedPool.value);
        
        try {
            importing.value = true;

            const output: any = await importPool(importedPool.value);

            if (output == null || output.error) {
                const errorMessage = output?.error || 'Unknown error';
                pushNotification(new Notification('Import Failed', `Failed to Import Pool: ${errorMessage}`, 'error', 5000));

            } else {
                pushNotification(new Notification('Import Completed', `Imported Pool ${importedPool.value!.name!} from Pool ${importedPool.value!.name!}`, 'success', 5000));

                showImportModal.value = false;
            }
            importing.value = false;
            await refreshAllData();
        } catch (error) {
            pushNotification(new Notification('Import Failed', `Failed to Import Pool: ${error}.`, 'error', 5000));

            importing.value = false;
        }
    }
}

const getIdKey = (name: string) => `${name}`;
</script>