<template>
	<div class="bg-default mr-[2rem]">
		<div>
			<div class="border-b border-default">					
						<Menu>
							<!-- Menu Button (Bell Icon & Badge) -->
							<MenuButton  @click="menuOpen = !menuOpen" class="relative rounded-full p-1 bg-default text-default hover:text-gray-600">
								<span class="sr-only">Open notifications</span>
								
								<!-- Bell Icon (Fixed Positioning) -->
								<div class="relative">
								<BellIcon class="w-8 h-8 text-white-700" aria-hidden="true" />
								
								<!-- Notification Badge -->
								<span v-if="notificationStore.notificationsCount>0" class="absolute -top-2 -right-2 max-h-[80vh] overflow-y-auto flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-600 text-white text-xs font-bold px-1">
									{{notificationStore.notificationsCount }}
								</span>
								</div>
							</MenuButton>

							<!-- Dropdown Menu Items -->
							<MenuItems v-bind="emailSetUpModal ? { static: true } : {}" @click.stop class="absolute right-0 overflow-y-scroll z-10 w-[30rem] max-h-[40rem] origin-top-right rounded-md bg-default shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
								<div class="flex items-center justify-between text-xl p-4 border-b border-gray-300">
									<p>Notifications</p>
									<div class="relative inline-block">
										<!-- Dropdown Trigger: Cog Icon -->
										<button @click="toggleDropdown" class="focus:outline-none">
											<Cog6ToothIcon class="w-[2rem] h-[2rem] text-gray-300 hover:text-white transition duration-200" />
										</button>

										<!-- Dropdown Menu -->
										<transition name="fade">
											<div v-if="showDropdown" class="absolute right-0 mt-1 w-56 bg-gray-800 rounded-lg shadow-lg z-50 border border-gray-700">
												<button
												@click="openEmailSettings"
												class="block px-4 py-2 text-base text-left text-white hover:bg-gray-700 w-full transition duration-800"
												>
												Email Notifications
												</button>
											</div>
										</transition>
									</div>	
									<EmailSetupModal v-if="emailSetUpModal" @close="emailSetUpModal = false" />
							
								</div>


								<!-- Notification Items -->
								 <div class="overflow-y-auto max-h-[30rem] px-4 py-4 space-y-4" ref="scrollContainer" >								
								<!--  Pool Degraded (Unrecoverable Error) -->
								 <MenuItem as="div" v-for="notification in notificationStore.notifications" :key="notification.id" v-slot="{ active }"> 
									<div class="flex items-start gap-3" v-if="notification.event === 'scrub_finish'">
										<!-- Icon Based on Scrub Status -->
										<div>
											<CheckCircleIcon 
												v-if="notification.errors == '0' || notification.errors === null" 
												class="icon-success size-icon-lg text-green-500" 
												aria-hidden="true" 
												/>
												<ExclamationCircleIcon 
												v-else 
												class="icon-warning size-icon-lg text-yellow-500" 
												aria-hidden="true" 
												/>
										</div>

										<!-- Notification Content -->
										<div class="w-full">
											<p class="text-xl font-semibold" 
											:class="{
												'text-green-500': notification.errors == '0' || notification.errors ===null,
												'text-yellow-500': notification.errors !== null && notification.errors != '0'
											}"
											>
											Scrub Finished - {{ notification.pool }}
											</p>
											<p class="pl-4 text-sm text-white-400">
											- Scrubbing of pool <strong>{{ notification.pool }}</strong> finished at <strong>{{ notification.timestamp }}</strong>
											</p>

											<!-- Show Errors if Found -->
											<p class="pl-4 text-sm" v-if="notification.errors && notification.errors !== '0' && notification.errors !== 'null'">
												<strong>Errors Detected:</strong> <span class="text-yellow-500">{{ notification.errors }}</span>
											</p>

										</div>

										<!-- Close Button -->
										<div>
											<XMarkIcon 
											class="size-icon text-white-500 cursor-pointer hover:text-red-500" 
											aria-hidden="true" 
											@click.stop="handleDismiss(notification.id)" 
											/> 
										</div>
									</div>

									<div class="flex items-start gap-3" v-if="notification.event === 'storage_threshold'">
										<!-- Icon Based on Scrub Status -->
										<div>

											<ExclamationCircleIcon 
												class="icon-warning size-icon-lg text-yellow-500" 
												aria-hidden="true" 
											/>
										</div>

										<!-- Notification Content -->
										<div class="w-full">
											<p class="text-xl font-semibold text-yellow-500">
											Storage Warning - {{ notification.pool }}
											</p>
											<p class="pl-4 text-sm text-white-400">
												- Pool <strong>{{ notification.pool }}</strong> is more than 80% full (triggered at {{ notification.timestamp }})		
											</p>
										</div>

										<!-- Close Button -->
										<div>
											<XMarkIcon 
											class="size-icon text-white-500 cursor-pointer hover:text-red-500" 
											aria-hidden="true" 
											@click.stop="handleDismiss(notification.id)" 
											/> 
										</div>
									</div>

									<!-- Snapshot Creation -->
									<div class="flex items-start gap-3" v-if="notification.event === 'snapshot_created'">
									<!-- Icon -->
										<div>
											<CheckCircleIcon class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
										</div>

										<!-- Message Content -->
										<div class="w-full">
											<p class="text-xl font-semibold text-green-500">
											Snapshot Created - <span class="text-lg">{{ notification.snapShot }}</span>
											</p>

											<p class="pl-4 text-sm text-white-500">
											 - A new snapshot <strong>{{ notification.snapShot }}</strong> has been successfully created
											for the filesystem <strong>{{ notification.fileSystem }}</strong>.
											<br />
											<br />
											<strong>Timestamp:</strong> {{ notification.timestamp }}
											</p>
										</div>
										<!-- Dismiss Icon -->
										<div>
											<XMarkIcon
											class="size-icon text-white-500 cursor-pointer hover:text-red-500"
											aria-hidden="true"
											@click.stop="handleDismiss(notification.id)"
											/>
										</div>
									</div>

										<!-- Snapshot Failed -->
									<!-- Snapshot Creation Failed -->
									<div class="flex items-start gap-3" v-if="notification.event === 'snapshot_failed'">
									<!-- Icon -->
										<div>
											<XCircleIcon class="icon-error size-icon-lg text-red-500" aria-hidden="true" />
										</div>

									<!-- Message Content -->
										<div class="w-full">
											<p class="text-xl font-semibold text-red-500">
											Snapshot Creation Failed - {{ notification.snapShot || 'Unknown Snapshot' }}
											</p>

											<p class="pl-4 text-sm text-white-500">
											 Failed to create snapshot on <strong>{{ notification.fileSystem || 'unknown filesystem' }}</strong>.
											<br />
											 <strong>Error:</strong> {{ notification.error  || 'Unknown error' }}
											<br />
											<strong>Timestamp:</strong> {{ notification.timestamp }}
											</p>
										</div>

									<!-- Dismiss Icon -->
										<div>
											<XMarkIcon
											class="size-icon text-white-500 cursor-pointer hover:text-red-500"
											aria-hidden="true"
											@click.stop="handleDismiss(notification.id)"
											/>
										</div>
									</div>
									
									<!-- ZFS Replication Success -->
									<div class="flex items-start gap-3" v-if="notification.event === 'zfs_replication_success'">
										<!-- Icon -->
										<div>
											<CheckCircleIcon class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
										</div>
										<div class="w-[85%]">
											<p class="text-xl font-semibold text-green-500">
											ZFS Replication Completed - <span class="text-lg">{{ notification.snapShot || 'Snapshot Unknown' }}</span>
											</p>

											<p class="pl-4 text-sm text-white-500">
											- Snapshot <strong>{{ notification.snapShot }}</strong> was successfully replicated
											from <strong>{{ notification.fileSystem || 'source unknown' }}</strong>.
											<br />
											<strong>Destination:</strong> {{ notification.replicationDestination || 'N/A' }}
											<br />
											 <strong>Timestamp:</strong> {{ notification.timestamp }}
											</p>
										</div>

											<!-- Dismiss Icon -->
										<div>
											<XMarkIcon
											class="size-icon text-white-500 cursor-pointer hover:text-red-500"
											aria-hidden="true"
											@click.stop="handleDismiss(notification.id)"
											/>
										</div>
									</div>
									<!-- ZFS Replication Failed -->
										<div class="flex items-start gap-3" v-if="notification.event === 'zfs_replication_failed'">
										<!-- Icon -->
										<div>
											<XCircleIcon class="icon-error size-icon-lg text-red-500" aria-hidden="true" />
										</div>

										<!-- Message Content -->
										<div class="w-[85%]">
											<p class="text-xl font-semibold text-red-500">
											ZFS Replication Failed - <span class="text-lg">{{ notification.snapShot || 'Snapshot Unknown' }}</span>
											</p>

											<p class="pl-4 text-sm text-white-500">
											- Replication failed for snapshot <strong>{{ notification.snapShot || 'unknown' }}</strong>
											from <strong>{{ notification.fileSystem || 'unknown filesystem' }}</strong>.
											<br />
											 <strong>Error:</strong> {{ notification.errors ||  'Unknown error' }}
											<br />
											 <strong>Timestamp:</strong> {{ notification.timestamp }}
											</p>
										</div>

										<!-- Dismiss Icon -->
										<div>
											<XMarkIcon
											class="size-icon text-white-500 cursor-pointer hover:text-red-500"
											aria-hidden="true"
											@click.stop="handleDismiss(notification.id)"
											/>
										</div>
										</div>


										<!-- Vdev Attatch -->
									<div class="flex items-start gap-3" v-if="notification.event === 'vdev_attach'" >
											<div >
												<CheckCircleIcon class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
											</div>
											<div class="w-full">
											<p class="text-xl font-semibold text-green-500">VDev Added - {{ notification.pool }}</p>
											<p class="pl-4 text-sm">
												Status: <strong :class="{
												'text-green-500': notification.state === 'ONLINE',
												'text-yellow-500': notification.state === 'DEGRADED',
												'text-red-500': notification.state === 'FAULTED'
											}">{{ notification.state }}</strong>
											</p>
											<p class="pl-4 text-sm text-white-500">- A new virtual device <strong>{{ notification.vdev }}</strong> has been successfully added to the pool {{ notification.pool }}
												<br> <strong>timestamp:</strong> {{ notification.timestamp }}
											</p>
											</div>
											<div>
												<XMarkIcon class="size-icon text-white-500 cursor-pointer hover:text-red-500" aria-hidden="true"@click.stop="handleDismiss(notification.id)"  /> 
											</div>
										</div>
										<div class="flex items-start gap-3" v-if="notification.event === 'resilver_finish'" >
											<div >
												<CheckCircleIcon class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
											</div>
											<div class="w-full">
											<p class="text-xl font-semibold text-green-500">Resilver Finished - {{ notification.pool }}</p>
											<p class="pl-4 text-sm text-white-500">Resilvering completed successfully for the pool <strong>{{ notification.pool }}</strong>
												<br> <strong>timestamp: </strong> {{ notification.timestamp }}
											</p>
											</div>
											<div>
												<XMarkIcon class="size-icon text-white-500 cursor-pointer hover:text-red-500" aria-hidden="true" @click.stop="handleDismiss(notification.id)"  /> 
											</div>
										</div>
										<div class="flex items-start gap-3" v-if="notification.event === 'vdev_clear'" >
											<div >
												<CheckCircleIcon class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
											</div>
											<div class="w-full">
												<p class="text-xl font-semibold text-green-500">VDEV Cleared - {{ notification.pool }}</p>
												<p class="pl-4 text-sm">
													Virtual device <strong>{{ notification.vdev }}</strong> was cleared in pool <strong>{{ notification.pool }}</strong>.
												</p>

												<!-- Status -->
												<p class="pl-4 text-sm" >
													Status: <span :class="{
													'text-green-500': notification.state === 'ONLINE',
													'text-yellow-500': notification.state === 'DEGRADED',
													'text-red-500': notification.state === 'FAULTED' || notification.state === 'UNAVAIL'
													}">{{ notification.state }}</span>
												</p>

												<!-- GUID, Error, Timestamp Section -->
												<div class=" text-sm text-white-500 pl-4">
													<p v-if="notification.guid">
													 GUID: <strong>{{ notification.guid }}</strong>
													</p>
													<p v-if="notification.error && notification.error !== 'None' && notification.error !== 'null' ">
													 Error:<strong> {{ notification.error }}</strong>
													</p>
													<p><strong>Timestamp: </strong> {{ notification.timestamp }}</p>
												</div>
												</div>
											<div>
												<XMarkIcon class="size-icon text-white-500 cursor-pointer hover:text-red-500" aria-hidden="true" @click.stop="handleDismiss(notification.id)"  /> 
											</div>
										</div>
										<div class="flex items-start gap-3" v-if="notification.event === 'pool_import'" >
											  <!-- Icon Based on Pool Health -->
											<div>
												<CheckCircleIcon v-if="notification.health === 'ACTIVE'" class="icon-success size-icon-lg text-green-500" aria-hidden="true" />
												<ExclamationCircleIcon v-else-if="notification.health != 'ACTIVE'" class="icon-warning size-icon-lg text-red-500" aria-hidden="true" />
											</div>
												<!-- Event Details -->
												<div class="w-full">
													<p class="text-xl font-semibold"  :class="{
														'text-green-500': notification.health === 'ACTIVE',
														'text-red-500': notification.health != 'ACTIVE'
													}">ZFS Pool Imported - {{ notification.pool }}</p>
													<p class="pl-4 text-sm text-white-500">
													 Pool <strong>{{ notification.pool }}</strong> has been successfully imported.
													<br> 
													<strong>Status: </strong>  
													<span :class="{
														'text-green-500': notification.health === 'ACTIVE',
														'text-yellow-500': notification.health === 'DEGRADED',
														'text-red-500': notification.health != 'ACTIVE'
													}">
														{{ notification.health }}
												</span>
													<br><strong> Timestamp: </strong> {{ notification.timestamp }}
													</p>
												</div>
											<div>
												<XMarkIcon class="size-icon text-white-500 cursor-pointer hover:text-red-500" aria-hidden="true" @click.stop="handleDismiss(notification.id)"  /> 
											</div>
										</div>
										<div class="flex items-start gap-3" v-if="notification.event === 'statechange'">
										<!-- Icon Based on Scrub Status -->
										<!-- Status Icon -->
										<div>
										<CheckCircleIcon v-if="notification.state === 'ONLINE'" class="text-green-500 size-icon-lg" />
										<ExclamationCircleIcon v-else class="text-red-500 size-icon-lg" />
										</div>

										<!-- Notification Content -->
										<div class="w-full">
										<p class="text-xl font-semibold" :class="{
											'text-green-500': notification.state === 'ONLINE',
											'text-red-600': notification.state === 'FAULTED' ||  notification.state === 'REMOVED' ||notification.state === 'DEGRADED' || notification.state === 'OFFLINE',
										}">
											{{ notification.event.replace("_", " ").toUpperCase() }} - {{ notification.pool }}
										</p>
										<p class="text-sm pl-4 text-white-600">
											<strong>Pool:</strong> {{ notification.pool ?? "N/A" }}  
											<br><strong>VDEV:</strong> {{ notification.vdev ?? "Unknown" }}  
											<br><strong>Status: </strong>  
											<span :class="{
											'text-green-500': notification.state === 'ONLINE',
											'text-red-500': notification.state === 'FAULTED' || notification.state === 'REMOVED' || notification.state === 'DEGRADED' || notification.state === 'OFFLINE',
											}">
											{{ notification.state }}
											</span>
										</p>

										<!-- Timestamp -->
										<p class="text-sm pl-4 text-white-500">
											 <strong>Timestamp:</strong> {{ notification.timestamp }}
										</p>
										</div>
										<!-- Close Button -->
										<div>
											<XMarkIcon 
											class="size-icon text-white-500 cursor-pointer hover:text-red-500" 
											aria-hidden="true" 
											@click.stop="handleDismiss(notification.id)"
											/> 
										</div>
									</div>
								</MenuItem>
								<div ref="loadMoreTrigger" class="h-6 w-full bg-transparent"></div>
							 </div> 

								<!-- Dismiss Button
								<div class="text-md p-4 flex justify-center border-t border-gray-300">
								<button   @click="dismissAllNotifications()" class=" hover:underline">Dismiss all Notifications</button>
								</div> -->

								<div class="text-md p-4 border-t border-gray-300">
									<button @click="dismissAllNotifications()" class="hover:underline w-full text-center">
									Dismiss all Notifications
									</button>
  								</div>
							
							</MenuItems>
						</Menu>


			</div>
		</div>
	
	</div>
</template>
<style>
/* CSS to disable page scrolling */
.no-scroll {
  overflow: hidden;
  height: 100vh;
}
</style>
<script setup lang="ts">

import { BellIcon, Cog6ToothIcon, CheckCircleIcon,ExclamationCircleIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import {Menu,MenuButton, MenuItem, MenuItems } from '@headlessui/vue';
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { notificationStore } from "../../store/notification";
import EmailSetupModal from './EmailSetupModal.vue';

// Reactive state to track menu visibility
const menuOpen = ref(false);
const showDropdown = ref(false);
const emailSetUpModal = ref(false);
const loadMoreTrigger = ref(null)

// Watch for menu state changes and control page scrolling
watch(menuOpen, (isOpen) => {
  if (isOpen) {
	document.body.classList.add("no-scroll"); // 🚀 Disable scrolling
  } else {
	document.body.classList.remove("no-scroll"); // Enable scrolling
  }
});
// Ensure scrolling is enabled if the component unmounts
async function handleDismiss(notificationId) {
  await notificationStore.markNotificationAsRead(notificationId);
 notificationStore.removeNotification(notificationId);
}
async function dismissAllNotifications() {
  await notificationStore.clearAllNotifications();
 notificationStore.removeAllNotifications();
}


const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};
const openEmailSettings = () => {
	// console.log("Opening Email Settings...");
	emailSetUpModal.value = true;
	showDropdown.value = false; // Close dropdown when opening modal
};

const offset = ref(0)
const limit = 50
const loading = ref(false)
const scrollContainer = ref<HTMLElement | null>(null)

async function loadMoreNotifications() {
  if (loading.value) return
  loading.value = true
  const count = await notificationStore.fetchMissedNotifications(limit, offset.value)
  if (count > 0) offset.value += limit
  loading.value = false
}

let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        loadMoreNotifications()
      }
    },
    {
      root: scrollContainer.value, // 👈 observe within the scrollable container
      threshold: 1.0
    }
  )

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value)
  }
})

onBeforeUnmount(() => {
  if (observer && loadMoreTrigger.value) {
    observer.unobserve(loadMoreTrigger.value)
  }
})

watch(menuOpen, async (isOpen) => {
  if (isOpen) {
    await nextTick()

    if (observer && loadMoreTrigger.value) {
      observer.disconnect() // clear any existing observer
    }

    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMoreNotifications()
        }
      },
      {
        root: scrollContainer.value,
        threshold: 1.0
      }
    )

    if (loadMoreTrigger.value) {
      observer.observe(loadMoreTrigger.value)
    }
  } else {
    if (observer && loadMoreTrigger.value) {
      observer.unobserve(loadMoreTrigger.value)
    }
  }
})

</script>