<template>
	<div class="min-h-screen h-full w-full min-w-fit flex flex-col bg-default overflow-auto">
		<HoustonAppContainer moduleName="ZFS" :appVersion="version" :notificationComponent="NotificationBell" >
		<Navigation :navigationItems="navigation" :currentNavigationItem="currentNavigationItem" :navigationCallback="navigationCallback" :show="show"/>
			<ZFS :tag="navTag"/>
			
		</HoustonAppContainer>
	</div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
// import "@45drives/houston-common-ui/style.css";
import "@45drives/houston-common-ui/style.css";
import '@45drives/houston-common-css/src/index.css';
import { HoustonAppContainer } from "@45drives/houston-common-ui";
import Navigation from "./components/common/Navigation.vue";
import ZFS from './views/ZFS.vue';
import { NavigationItem, NavigationCallback } from './types';
import { notificationStore } from './store/notification';
import NotificationBell from './components/notification/Notification.vue';

const show = ref(true);
const navTag = ref('dashboard');
const version = __APP_VERSION__;


const currentNavigationItem = computed<NavigationItem | undefined>(() => navigation.find(item => item.current));
onMounted(async () => {
  await Promise.all([
    notificationStore.countMissedNotifications(),

    notificationStore.fetchMissedNotifications(50, 0)
  ]);
});
//navigation for tabs
const navigationCallback: NavigationCallback = (item: NavigationItem) => {
	navTag.value = item.tag;
};


//tabs for navigation
const navigation = reactive<NavigationItem[]>([
	{ name: 'Dashboard', tag: 'dashboard', current: computed(() => navTag.value == 'dashboard') as unknown as boolean, show: true, },
	{ name: 'Pools', tag: 'pools', current: computed(() => navTag.value == 'pools') as unknown as boolean, show: true, },
	{ name: 'File Systems', tag: 'filesystems', current: computed(() => navTag.value == 'filesystems') as unknown as boolean, show: true, },
].filter(item => item.show));

// function setUpMessageHandler(handler: (message:string) => void) {
//     const client = cockpit.dbus("org._45drives.Houston");
//     const houston = client.proxy("org._45drives.Houston", "/org/_45drives/Houston");
//     houston.addEventListener("Message", (event_, message: string) => handler(message));
// }

// setUpMessageHandler((message) => {
//     console.log("message from dbus",message)
// })

</script>

	