import dbus
import dbus.service
import dbus.mainloop.glib
import sqlite3
import gi
import json
import os
from datetime import datetime
import subprocess
import logging


gi.require_version("GLib", "2.0")
from gi.repository import GLib

LOG_FILE = "/var/log/msmtp_test.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Initialize DBus
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# Define SQLite Database Path
DB_PATH = "/var/lib/sqlite/45Drives/notifications.db"
MSMTP_CONFIG_PATH = "/etc/45drives/msmtp"
MSMTP_RECIPIENT_PATH = "/etc/45drives/msmtp_recipient"
MSMTP_PASSWORD_PATH = "/etc/45drives/msmtp_pass"

def determine_severity(event, message):
    """Determine the severity of the notification based on event type."""
    health = message.get("health")
    state = message.get("state")
    errors = message.get("errors")

    if event in ["pool_fail", "pool_faulted"] or health == "FAULTED":
        return "error"  # ❌ Critical failure

    if event in ["scrub_finish", "scrub_warning"] and errors and errors.lower() != "no":
        return "warning"  # ⚠️ Scrub completed with errors

    if event in ["pool_import", "pool_degraded"] and health == "DEGRADED":
        return "warning"  # ⚠️ Pool degraded
        
    if event == "statechange" and (state == "FAULTED" or state == "DEGRADED"):
        return "error"  

    return "info"  # ℹ️ Default for general notifications
def store_notification(message):
    """Stores notifications in SQLite DB, updates statechange events if necessary, and returns the message with ID."""
    print(f"[DEBUG] Attempting to store: {message}")  

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"[DEBUG] Checking if {message.get('event')} already exists")

        # ✅ Check if a similar event exists (for statechange updates)
        cursor.execute("""
            SELECT id, state, health FROM notifications
            WHERE event = ? AND timestamp = ? AND vdev = ?;
        """, (message["event"], message["timestamp"], message.get("vdev", None)))

        existing_event = cursor.fetchone()

        if existing_event:
            existing_id, existing_state, existing_health = existing_event

            # ✅ If it's a statechange event and the state or health has changed, update it
            if message["event"] == "statechange" and (existing_state != message.get("state") or existing_health != message.get("health")):
                new_severity = determine_severity(message.get("event"), message)  # ✅ Recalculate severity
                
                cursor.execute("""
                    UPDATE notifications
                    SET state = ?, severity = ?, health = ?
                    WHERE id = ?;
                """, (
                    message.get("state"),
                    new_severity,
                    message.get("health", None),
                    existing_id
                ))
                conn.commit()
                print(f"✅ [UPDATE] Statechange event updated: {message}")  

                # ✅ Include `id` and `severity` in the returned message
                message["id"] = existing_id
                message["severity"] = new_severity
                return message  

            print(f"❌ Duplicate detected, skipping insert: {message}")
            return None  

        # ✅ Insert new notification if no matching event found
        severity = determine_severity(message.get("event"), message)  # ✅ Get severity for new events

        cursor.execute("""
            INSERT INTO notifications (timestamp, event, pool, vdev, state, severity, health, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            message.get("timestamp"),
            message.get("event"),
            message.get("pool"),
            message.get("vdev", None),
            message.get("state", None),
            severity,
            message.get("health", None),
            message.get("errors", 0)  # ✅ Added errors field with a default of 0
        ))

        conn.commit()
        notification_id = cursor.lastrowid  # ✅ Get the new row ID
        print(f"✅ [INSERT] New event stored: {message}")  

        # ✅ Include `id` and `severity` in the returned message
        message["id"] = notification_id
        message["severity"] = severity
        return message  

    except Exception as e:
        print(f"❌ [DB Insert Error] {e}")
        return None  

    finally:
        conn.close()  



# Configure logging
LOG_FILE = "/var/log/msmtp_test.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def sendTestEmail(config_json):
    """
    Sends a test email using msmtp without requiring /etc/msmtprc.
    Logs all activities to /var/log/msmtp_test.log.
    """
    try:
        logging.info("📨 Sending test email via msmtp...")
        logging.getLogger().handlers[0].flush()  # ✅ Force log to write immediately

        # ✅ Parse SMTP details from UI
        config = json.loads(config_json)

        smtp_server = config.get("smtpServer", "").strip()
        smtp_port = str(config.get("smtpPort", 587))
        username = config.get("username", "").strip()
        password = config.get("password", "").strip()
        sender_email = config.get("email", "").strip()
        recipient_email = config.get("recipientEmail", "").strip()

        # ✅ Debugging: Show recipient email before sending
        logging.info(f"📨 Debug: Recipient Email -> {repr(recipient_email)}")
        logging.getLogger().handlers[0].flush()  # ✅ Flush logs

        # ✅ Ensure recipient email is valid
        if not recipient_email or "@" not in recipient_email:
            logging.error("❌ Error: Invalid recipient email format.")
            logging.getLogger().handlers[0].flush()
            return "❌ Error: Invalid recipient email format."

        logging.info(f"📨 Sending test email to: {recipient_email}")
        logging.getLogger().handlers[0].flush()

        # ✅ Construct Email Content
        email_content = f"Subject: Test Email from 45Drives\n\nThis is a test email."
        
        # ✅ Proper `msmtp` Command
        msmtp_command = f"echo -e '{email_content}' | msmtp --host={smtp_server} --port={smtp_port} --auth=on --user={username} --passwordeval='echo {password}' --from={sender_email} --tls --tls-starttls {recipient_email}"

        # ✅ Execute the command
        process = subprocess.run(
            msmtp_command,
            shell=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # ✅ Check if the email was sent successfully
        if process.returncode == 0:
            success_msg = f"✅ Test email sent to {recipient_email} successfully!"
            logging.info(success_msg)
            logging.getLogger().handlers[0].flush()
            return success_msg
        else:
            error_message = f"❌ Failed to send test email: {process.stderr.strip()}"
            logging.error(error_message)
            logging.getLogger().handlers[0].flush()
            return error_message

    except Exception as e:
        error_message = f"❌ Error sending test email: {str(e)}"
        logging.error(error_message)
        logging.getLogger().handlers[0].flush()
        return error_message
def get_missed_notifications():
    """Fetch missed notifications (received = 0), mark them as received, and return as JSON."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("[DEBUG] Executing SQL Query to fetch missed notifications")
        cursor.execute("""
            SELECT id, timestamp, event, pool, vdev, state, error, description, scrub_details, 
                   errors, repaired, received, health, severity
            FROM notifications WHERE received = 0
        """)
        
        rows = cursor.fetchall()
        print(f"[DEBUG] Raw Rows from DB: {rows}")

        # Convert rows into a structured list
        notifications = [
            {
                "id": row[0], "timestamp": row[1], "event": row[2], "pool": row[3],
                "vdev": row[4], "state": row[5], "error": row[6], "description": row[7],
                "scrub_details": row[8], "errors": row[9], "repaired": row[10],
                "received": row[11], "health": row[12], "severity": row[13]
            }
            for row in rows
        ]

        conn.commit()

        print(f"[DEBUG] Missed Notifications Processed: {notifications}")

        return json.dumps(notifications)  # ✅ Return JSON for easy integration with D-Bus

    except Exception as e:
        print(f"❌ [DB Error] Failed to fetch missed notifications: {e}")
        return json.dumps([])  # Return an empty list on failure

    finally:
        conn.close()  # ✅ Always close the database connection
def mark_notification_as_read(notification_id):
    """Mark a specific notification as read by setting received = 1"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Update notification to mark as read
        cursor.execute("UPDATE notifications SET received = 1 WHERE id = ?", (notification_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return "❌ Notification not found"

        conn.close()
        return f"✅ Notification {notification_id} marked as read"

    except Exception as e:
        return f"❌ DB Error: {str(e)}"
def mark_all_notifications_as_read():
    """Mark all unread notifications as read via D-Bus."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if any notifications are unread
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE received = 0")
        unread_count = cursor.fetchone()[0]

        if unread_count == 0:
            conn.close()
            return "No unread notifications to mark as read."

        # Update only if there are unread notifications
        cursor.execute("UPDATE notifications SET received = 1 WHERE received = 0")
        conn.commit()
        conn.close()

        return f"✅ Marked {unread_count} notifications as read"  # ✅ Ensure string return type

    except Exception as e:
        return f"❌ DB Error: {str(e)}"  # ✅ Return error as a string
import subprocess
import json

def updateSMTPConfig(config_json):
    """
    Updates the SMTP configuration in /etc/45drives/msmtp and stores recipient email.
    """
    try:
        print("🔄 Updating SMTP config...")  # Debugging log

        config = json.loads(config_json)

        email = config.get("email", "")
        smtp_server = config.get("smtpServer", "")
        smtp_port = config.get("smtpPort", 587)
        username = config.get("username", "")
        password = config.get("password", "")
        recipient_email = config.get("recieversEmail", "")  # ✅ Store recipient permanently
        tls = "on" if config.get("tls", True) else "off"

        # ✅ Save password securely in a separate file
        with open(MSMTP_PASSWORD_PATH, "w") as f:
            f.write(password)
        os.chmod(MSMTP_PASSWORD_PATH, 0o600)  # Secure permissions

        # ✅ Store SMTP config in msmtp file
        config_content = f"""account default
host {smtp_server}
port {smtp_port}
auth on
user {username}
passwordeval cat {MSMTP_PASSWORD_PATH}
from {email}
tls {tls}
tls_starttls on
"""

        # ✅ Store recipient email in a separate file
        with open(MSMTP_RECIPIENT_PATH, "w") as f:
            f.write(recipient_email)
        os.chmod(MSMTP_RECIPIENT_PATH, 0o600)  # Secure permissions

        # ✅ Write SMTP config
        with open(MSMTP_CONFIG_PATH, "w") as f:
            f.write(config_content)
        os.chmod(MSMTP_CONFIG_PATH, 0o600)  # Secure permissions

        print("✅ SMTP configuration updated successfully!")
        return "✅ SMTP configuration updated successfully!"

    except Exception as e:
        return f"❌ Error updating SMTP: {str(e)}"
def sendEmailNotification(subject, message):
    """
    Sends an automated notification email using msmtp with the correct config file.
    """
    try:
        print("📨 Sending automated notification email...")  # Debugging log

        # ✅ Read recipient email from the saved file
        with open(MSMTP_RECIPIENT_PATH, "r") as f:
            recipient_email = f.read().strip()

        # ✅ Construct the email content
        email_content = f"""Subject: {subject}\n\n{message}"""

        # ✅ Explicitly specify the `msmtp` config file location
        process = subprocess.run(
            ["msmtp", "-C", "/etc/45drives/msmtp", recipient_email],
            input=email_content,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # ✅ Check if the email was sent successfully
        if process.returncode == 0:
            print(f"✅ Notification sent to {recipient_email} successfully!")
            return f"✅ Notification sent to {recipient_email} successfully!"
        else:
            error_message = f"❌ Failed to send notification: {process.stderr.strip()}"
            print(error_message)
            return error_message

    except Exception as e:
        error_message = f"❌ Error sending notification: {str(e)}"
        print(error_message)
        return error_message
def fetchMsmtpDetails():
    """Fetch the stored SMTP configuration details from /etc/45drives/msmtp"""
    try:

        # Read SMTP config
        with open(MSMTP_CONFIG_PATH, "r") as f:
            config_data = f.readlines()
        
        # Extract relevant values
        smtp_details = {}
        for line in config_data:
            if line.startswith("host"):
                smtp_details["smtpServer"] = line.split(" ")[1].strip()
            elif line.startswith("port"):
                smtp_details["smtpPort"] = line.split(" ")[1].strip()
            elif line.startswith("user"):
                smtp_details["username"] = line.split(" ")[1].strip()
            elif line.startswith("from"):
                smtp_details["email"] = line.split(" ")[1].strip()
            elif line.startswith("tls "):  # ✅ Extract TLS value
                smtp_details["tls"] = line.split(" ")[1].strip().lower() == "on"
        
        # Read password securely
        with open(MSMTP_PASSWORD_PATH, "r") as f:
            smtp_details["password"] = f.read().strip()

        # Read recipient email
        with open(MSMTP_RECIPIENT_PATH, "r") as f:
            smtp_details["recieversEmail"] = f.read().strip()

        return json.dumps(smtp_details)  # Convert to JSON string

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch SMTP details: {str(e)}"})



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
            updated_message = store_notification(parsed_message)  # ✅ Save/update in DB

            if updated_message:
                print(f"✅ [FORWARD] Sending to UI: {updated_message}")  
                self.Message(json.dumps(updated_message))  # ✅ Forward message with correct ID
            else:
                print("❌ Duplicate event detected, not forwarding to UI.")

        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON format received")
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def GetMissedNotifications(self):
        """D-Bus method to retrieve missed notifications in JSON format."""
        return get_missed_notifications()
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
        return sendTestEmail(config_json)
    @dbus.service.method("org._45drives.Houston", in_signature="ss", out_signature="s")
    def sendEmailNotification(self, subject, message):    
        return sendEmailNotification(subject, message)
    @dbus.service.method("org._45drives.Houston", in_signature="", out_signature="s")
    def FetchMsmtpDetails(self):    
        return fetchMsmtpDetails()


        
    

# Setup D-Bus
bus = dbus.SystemBus()
bus_name = dbus.service.BusName("org._45drives.Houston", bus)
service = DBusService(bus_name)

# Start Main Loop
loop = GLib.MainLoop()
loop.run()
