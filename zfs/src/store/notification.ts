import { reactive } from "vue";
import { Notification } from "../types";

// Shared D-Bus singleton — reused across all store methods to avoid leaking connections
let _dbus: ReturnType<typeof cockpit.dbus> | null = null;
function getHoustonDbus() {
  if (!_dbus) {
    const dbus = cockpit.dbus("org._45drives.Houston", { bus: "system" });
    dbus.addEventListener("close", () => {
      if (_dbus === dbus) {
        _dbus = null;
      }
    });
    _dbus = dbus;
  }
  return _dbus;
}

// Event types that belong to the ZFS module
const ZFS_EVENTS = [
  "scrub_finish",
  "storage_threshold",
  "snapshot_created",
  "snapshot_failed",
  "zfs_replication_success",
  "zfs_replication_failed",
  "vdev_attach",
  "resilver_finish",
  "vdev_clear",
  "pool_import",
  "statechange",
  "data",
];

const ZFS_EVENTS_JSON = JSON.stringify(ZFS_EVENTS);

function isZfsEvent(event: string | undefined): boolean {
  return !!event && ZFS_EVENTS.includes(event);
}

// Define the reactive notification store
export const notificationStore = reactive<{
  notifications: Notification[];
  addNotification: (message: string) => void;
  removeNotification: (id: number) => void;
  removeAllNotifications: () => void;
  fetchMissedNotifications: (limit: number, offset: number) => Promise<number>;
  markNotificationAsRead: (id: number) => Promise<void>;
  clearAllNotifications: () => Promise<void>;
  countMissedNotifications: () => void;
  notificationsCount: number
}>({
  notifications: [],
  notificationsCount: 0,

  // Add notification to the list (only ZFS-related events)
  addNotification(message: string) {
    try {
      const parsedMessage = JSON.parse(message) as {
        id: number;
        timestamp: string;
        event: string;
        pool?: string;
        vdev?: string;
        state?: string;
        health?: string;
        errors?: string;
        severity?: string;
        fileSystem?: string;
        snapShot?: string;
        replicationDestination?: string
      };

      // Ignore events that don't belong to the ZFS module
      if (!isZfsEvent(parsedMessage.event)) return;
  
      // Find existing notification by ID
      const existingNotification = notificationStore.notifications.find(
        (notif) => notif.id === parsedMessage.id
      );
  
      if (existingNotification) {
        // If ID exists, update only the state field
        existingNotification.state = parsedMessage.state;
        // console.log(`Updated state of notification ID ${parsedMessage.id}`);
      } else {
        // If ID does not exist, add new notification
        notificationStore.notifications.unshift({
          id: parsedMessage.id,
          timestamp: parsedMessage.timestamp,
          event: parsedMessage.event,
          pool: parsedMessage.pool,
          text: `Event: ${parsedMessage.event}, Pool: ${parsedMessage.pool ?? "N/A"}`,
          state: parsedMessage.state,
          vdev: parsedMessage.vdev,
          health: parsedMessage.health,
          errors: parsedMessage.errors,
          severity: parsedMessage.severity,
          fileSystem: parsedMessage.fileSystem,
          snapShot: parsedMessage.snapShot,
          replicationDestination: parsedMessage.replicationDestination
        });
        this.notificationsCount +=1
  
        // console.log(`Added new notification severity ${parsedMessage.severity}`);
      }
  
      // Trigger sidebar notification
      sideBarNotification();
    } catch (error) {
      console.error("Invalid JSON format received:", message);
    }
  },


  // Remove notification by ID
  removeNotification(id: number) {
    // console.log("remove Notivficatio id :", id )
    notificationStore.notifications = notificationStore.notifications.filter(
      (n) => n.id !== id
    );
    sideBarNotification();

    
  },
    // Remove notification by ID
  removeAllNotifications() {
    notificationStore.notifications = []
    this.notificationsCount = 0;
    sideBarNotification();

  },

  async fetchMissedNotifications(limit = 50, offset = 0) {
    try {
        const dbus = getHoustonDbus();

        const response = await dbus.call(
          "/org/_45drives/Houston",
          "org._45drives.Houston",
          "GetMissedNotificationsByEvents",
          [ZFS_EVENTS_JSON, limit, offset]
        );
        if (!response) throw new Error("No response received from Houston D-Bus.");

        //console.log("📥 Raw response from D-Bus:", response);

        // Parse response JSON
        const missedNotifications = JSON.parse(response);

        // Add notifications to store
        missedNotifications.forEach((notification) => {
          const exists = notificationStore.notifications.some(
            (n) => n.id === notification.id
          );
        
          if (!exists) {
            notificationStore.notifications.push(notification);
          }
        });
        

        // Update UI with new notifications
        sideBarNotification();

    return missedNotifications.length; 

        //console.log("Missed notifications fetched successfully.");
    } catch (error) {
        console.error("Error fetching missed notifications via D-Bus:", error);
        return 0;
    }
},


  async markNotificationAsRead(notificationId: number) {
    try {
        // console.log(`Marking notification ${notificationId} as read via D-Bus...`);

        const dbus = getHoustonDbus();

        // Call the D-Bus method instead of FastAPI
        const response = await dbus.call(
            "/org/_45drives/Houston",  // Object path
            "org._45drives.Houston",   // Interface
            "MarkNotificationAsRead",  // Method name
            [notificationId]           // Argument (notification ID)
        );

        // console.log(`D-Bus Response: ${response}`);

        // Remove from UI after marking as read
        notificationStore.notifications = notificationStore.notifications.filter(
            (n) => n.id !== notificationId
        );

        this.notificationsCount -= 1;
        sideBarNotification();

    } catch (error) {
        console.error("Error marking notification as read via D-Bus:", error);
    }
},

  async clearAllNotifications() {
    try {
        const dbus = getHoustonDbus();

        // Mark only ZFS-scoped notifications as read (not global)
        await dbus.call(
            "/org/_45drives/Houston",
            "org._45drives.Houston",
            "MarkAllNotificationsByEventsAsRead",
            [ZFS_EVENTS_JSON]
        );

        // Clear UI notifications
        notificationStore.notifications = [];
        this.notificationsCount = 0;

        sideBarNotification();
    } catch (error) {
        console.error("Error clearing notifications via D-Bus:", error);
    }
  },

  async countMissedNotifications(){
    const dbus = getHoustonDbus();
    const result = await dbus.call(
      "/org/_45drives/Houston",
      "org._45drives.Houston",
      "GetNotificationCountByEvents",
      [ZFS_EVENTS_JSON]
    );
    const count = result[0];
    this.notificationsCount = count;

    return parseInt(result);
  }


  
  
});

async function sideBarNotification(): Promise<void> {
  const count: number = notificationStore.notificationsCount;

  const dbus = getHoustonDbus();

  try {
    if (count > 0) {
      const [highestSeverity] = await dbus.call(
        "/org/_45drives/Houston",
        "org._45drives.Houston",
        "GetHighestMissedSeverityByEvents",
        [ZFS_EVENTS_JSON]
      );

      (cockpit.transport as any).control("notify", {
        page_status: {
          type: highestSeverity,
          title: cockpit.gettext(`${count} Notifications available`)
        }
      });
    } else {
      (cockpit.transport as any).control("notify", {
        page_status: null
      });
    }
  } catch (error) {
    console.error("Failed to fetch highest severity:", error);
  }
}