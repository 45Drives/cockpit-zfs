import { createApp} from 'vue';
import './assets/zfs.css';
import App from './App.vue';
import '@45drives/houston-common-css/src/index.css';
import "@45drives/houston-common-ui/style.css";
import { notificationStore } from './store/notification';

const app = createApp(App);

app.mount('#app');

