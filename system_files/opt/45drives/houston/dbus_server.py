import dbus
import dbus.service
import dbus.mainloop.glib
import sqlite3
import gi
import json
from gi.repository import GLib

from notification_utils import (
    determine_severity,
    store_notification,
    get_missed_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    updateSMTPConfig,
    sendTestEmail,
    sendEmailNotification,
    fetchMsmtpDetails,
    updateWarningLevels,
    resetMsmtpData,
    fetchWarningLevels,
    getNotificationCount,
    getHighestMissedSeverity
)

# Initialize DBus
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class DBusService(dbus.service.Object):
    """D-Bus Service to handle incoming messages and forward valid ones to the UI."""

    def __init__(self, bus_name):
        bus_path = "/org/_45drives/Houston"
        dbus.service.Object.__init__(self, bus_name, bus_path)

    @dbus.service.signal("org._45drives.Houston", signature="s")
    def Message(self, message):
        """Signal an event has occurred and notify the UI."""
        print(f"[D-Bus Signal Sent] {message}")

    @dbus.service.method("org._45drives.Houston", in_signature="s")
    def ForwardMessage(self, message):
        """Process message: Save to DB first, then send to UI only if stored or updated."""
        print(f"[Forwarding message] {message}")
        try:
            parsed_message = json.loads(message)  
            updated_message = store_notification(parsed_message)  # Save/update in DB

            if updated_message:
                
                print(f"[FORWARD] Sending to UI: {updated_message}")  
                self.Message(json.dumps(updated_message))  # Forward message with correct ID
                subject = parsed_message.get("subject") or f"ZFS Event: {parsed_message.get('event')}"
                body = parsed_message.get("email_message") or json.dumps(updated_message, indent=2)
                severity = updated_message.get("severity", "info")
                # print(f"[FORWARD] SENDING TO  EMAIL: {updated_message}")  

                sendEmailNotification(subject, body, severity)
            else:
                print("Duplicate event detected, not forwarding to UI.")

        except json.JSONDecodeError:
            print("Error: Invalid JSON format received")
    @dbus.service.method("org._45drives.Houston", in_signature="ii", out_signature="s")
    def GetMissedNotifications(self,limit,offset):
        """D-Bus method to retrieve missed notifications in JSON format."""
        return get_missed_notifications(limit,offset)
    @dbus.service.method("org._45drives.Houston", in_signature="i", out_signature="s")
    def MarkNotificationAsRead(self, notification_id):
        return mark_notification_as_read(notification_id)
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def MarkAllNotificationsAsRead(self):
        return mark_all_notifications_as_read()
    @dbus.service.method("org._45drives.Houston", in_signature="s", out_signature="s")
    def UpdateSMTPConfig(self, config_json):
        return updateSMTPConfig(config_json)
    @dbus.service.method("org._45drives.Houston", in_signature="s", out_signature="s")
    def SendTestEmail(self, config_json):    
        result = sendTestEmail(config_json)  # returns a dict like { success, message }
        return json.dumps(result)  
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def FetchMsmtpDetails(self):    
        return fetchMsmtpDetails()
    @dbus.service.method("org._45drives.Houston", in_signature="s", out_signature="s")
    def UpdateWarningLevels(self, config_json):
        return updateWarningLevels(config_json)
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def resetMsmtpData(self):
        return resetMsmtpData()
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def fetchWarningLevels(self):
        return fetchWarningLevels()
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="i")
    def GetNotificationCount(self):
        return getNotificationCount()
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def GetHighestMissedSeverity(self):
        return getHighestMissedSeverity()




# Setup D-Bus
bus = dbus.SystemBus()
bus_name = dbus.service.BusName("org._45drives.Houston", bus)
service = DBusService(bus_name)

# Start Main Loop
loop = GLib.MainLoop()
loop.run()