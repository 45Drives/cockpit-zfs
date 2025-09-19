import { reactive } from "vue";
import { Notification } from "../types";

// Define the reactive notification store
export const notificationStore = reactive<{
  notifications: Notification[];
  addNotification: (message: string) => void;
  removeNotification: (id: number) => void;
  removeAllNotifications: () => void;
  fetchMissedNotifications: (limit, offset) => Promise<void>;
  markNotificationAsRead: (id: number) => Promise<void>;
  clearAllNotifications: () => Promise<void>;
  countMissedNotifications: () => void;
  notificationsCount: number
}>({
  notifications: [],
  notificationsCount: 0,

  // Add notification to the list
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
      // console.log("message id recieved in adddnotification: ", parsedMessage.id)
  
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
        // console.log("Fetching missed notifications via D-Bus...");

        const dbus = cockpit.dbus("org._45drives.Houston");

        // Call GetMissedNotifications with correct object path & interface
        const response = await dbus.call(
          "/org/_45drives/Houston",       
          "org._45drives.Houston",       
          "GetMissedNotifications",      
          [limit, offset]                
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
    }
},


  async markNotificationAsRead(notificationId: number) {
    try {
        // console.log(`Marking notification ${notificationId} as read via D-Bus...`);

        const dbus = cockpit.dbus("org._45drives.Houston");

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
        // console.log("Marking all notifications as read via D-Bus...");

        const dbus = cockpit.dbus("org._45drives.Houston");

        // Call the new D-Bus method
        const response = await dbus.call(
            "/org/_45drives/Houston",  // Object path
            "org._45drives.Houston",   // Interface
            "MarkAllNotificationsAsRead"  // Method name
        );

        // console.log(`D-Bus Response: ${response}`);

        // Clear UI notifications
        notificationStore.notifications = [];

        sideBarNotification();
    } catch (error) {
        console.error("Error clearing notifications via D-Bus:", error);
    }
  },

  async countMissedNotifications(){
    const dbus = cockpit.dbus("org._45drives.Houston");
    const result = await dbus.call(
      "/org/_45drives/Houston",
      "org._45drives.Houston",
      "GetNotificationCount"
    );
    const count = result[0]; // Extract the count
    this.notificationsCount = count;
    // console.log("Total missed notifications:", count);

    return parseInt(result); // result is returned as a string
  }


  
  
});

async function sideBarNotification(): Promise<void> {
  const count: number = notificationStore.notificationsCount;

  const dbus = cockpit.dbus("org._45drives.Houston");

  try {
    const [highestSeverity] = await dbus.call(
      "/org/_45drives/Houston",
      "org._45drives.Houston",
      "GetHighestMissedSeverity"
    );

    const severityType = count > 0 ? highestSeverity : null;
    // console.log("severityType:", severityType);

    (cockpit.transport as any).control("notify", {
      page_status: {
        type: severityType,
        title: cockpit.gettext(`${count} Notifications available`)
      }
    });
  } catch (error) {
    console.error("Failed to fetch highest severity:", error);
  }
}