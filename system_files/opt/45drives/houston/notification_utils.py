import sqlite3
import json
import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import tempfile
import base64
import requests

LOG_FILE = "/var/log/msmtp_test.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Define SQLite Database Path
DB_PATH = "/var/lib/sqlite/45Drives/notifications.db"
MSMTP_CONFIG_PATH = "/etc/45drives/msmtp"
MSMTP_RECIPIENT_PATH = "/etc/45drives/msmtp_recipient"
MSMTP_PASSWORD_PATH = "/etc/45drives/msmtp_pass"
MSMTP_OAUTH_JSON_PATH = '/etc/45drives/msmtp_auth_token.json'
MSMTP_OAUTH_REFRESH_SCRIPT = "/etc/45drives/msmtp_oauth-email.py"
AUTH_SEND_EMAIL_URL = "https://email-auth.45d.io/auth/send-email"

def determine_severity(event, message):
    """Determine the severity of the notification based on event type."""
    health = message.get("health")
    state = message.get("state")
    errors = message.get("errors")
    if event == "storage_threshold":
        return "warning"  # ⚠️ Pool usage threshold crossed
        
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

        if message["event"] == "statechange":
            cursor.execute("""
                SELECT id, state, health FROM notifications
                WHERE event = ? AND timestamp = ? AND vdev = ?;
            """, (message["event"], message["timestamp"], message.get("vdev", None)))

            existing_event = cursor.fetchone()

            if existing_event:
                existing_id, existing_state, existing_health = existing_event

                # ✅ If state or health changed, update
                if existing_state != message.get("state") or existing_health != message.get("health"):
                    new_severity = determine_severity(message.get("event"), message)
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
                    message["id"] = existing_id
                    message["severity"] = new_severity
                    return message

                print(f"❌ Duplicate statechange detected, skipping insert: {message}")
                return None

        # ✅ Insert new notification for all other event types
        severity = determine_severity(message.get("event"), message)

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
            message.get("errors", 0)
        ))

        conn.commit()
        notification_id = cursor.lastrowid
        print(f"✅ [INSERT] New event stored: {message}")
        message["id"] = notification_id
        message["severity"] = severity
        return message

    except Exception as e:
        print(f"❌ [DB Insert Error] {e}")
        return None

    finally:
        conn.close()




# def sendTestEmail(config_json):
#     """
#     Sends a test email using msmtp. If OAuth config matches username, refresh token. 
#     If plain auth is detected, dynamically construct and use a temporary msmtp config.
#     """
#     try:
#         logging.info("📨 Preparing to send test email via msmtp...")
#         logging.getLogger().handlers[0].flush()

#         config = json.loads(config_json)

#         smtp_server = config.get("smtpServer", "").strip()
#         smtp_port = str(config.get("smtpPort", 587))
#         username = config.get("username", "").strip()
#         password = config.get("password", "").strip()
#         sender_email = config.get("email", "").strip()
#         recipient_email = config.get("recipientEmail", "").strip()
#         auth_method = config.get("authMethod", "plain").strip()
#         tls = "on" if config.get("tls", True) else "off"

#         if not recipient_email or "@" not in recipient_email:
#             logging.error("❌ Error: Invalid recipient email format.")
#             return "❌ Error: Invalid recipient email format."

#         # Check if using existing OAuth config
#         use_existing_config = False
#         if os.path.exists(MSMTP_CONFIG_PATH):
#             with open(MSMTP_CONFIG_PATH, "r") as f:
#                 current_config = f.read()
#             if "auth oauthbearer" in current_config:
#                 current_user_line = next((line for line in current_config.split('\n') if line.startswith("user ")), None)
#                 current_user = current_user_line.split(" ")[1] if current_user_line else ""
#                 if current_user == username:
#                     logging.info("🔄 Detected existing OAuth config with matching user. Refreshing token...")
#                     subprocess.run(["python3", MSMTP_OAUTH_REFRESH_SCRIPT], check=False)
#                     use_existing_config = True
#                 else:
#                     logging.info("ℹ️ OAuth config user does not match — using incoming config.")

#         # Construct the email content
#         email_content = f"Subject: Test Email from 45Drives\n\nThis is a test email."

#         if use_existing_config:
#             # Send using system-wide msmtp config
#             process = subprocess.run(
#                 ["msmtp", "-C", MSMTP_CONFIG_PATH, recipient_email],
#                 input=email_content,
#                 universal_newlines=True,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE
#             )
#         else:
#             # Dynamically create temporary msmtp config for plain-auth
#             with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
#                 tmp.write(f"""account default
# host {smtp_server}
# port {smtp_port}
# auth on
# user {username}
# password {password}
# from {sender_email}
# tls {tls}
# tls_starttls on
# logfile /var/log/msmtp.log
# """)
#                 tmp.flush()
#                 temp_config_path = tmp.name

#             process = subprocess.run(
#                 ["msmtp", "-C", temp_config_path, recipient_email],
#                 input=email_content,
#                 universal_newlines=True,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE
#             )

#             os.unlink(temp_config_path)  # Cleanup temp file

#         # Handle result
#         if process.returncode == 0:
#             success_msg = f"✅ Test email sent to {recipient_email} successfully!"
#             logging.info(success_msg)
#             return success_msg
#         else:
#             error_message = f"❌ Failed to send test email: {process.stderr.strip()}"
#             logging.error(error_message)
#             return error_message

#     except Exception as e:
#         error_message = f"❌ Error sending test email: {str(e)}"
#         logging.error(error_message)
#         return error_message
def sendTestEmailViaSMTP(config):
    """
    Sends a test email using msmtp (plain authentication).
    """
    try:
        smtp_server = config.get("smtpServer", "").strip()
        smtp_port = str(config.get("smtpPort", 587))
        username = config.get("username", "").strip()
        password = config.get("password", "").strip()
        sender_email = config.get("email", "").strip()
        recipient_email = config.get("recipientEmail", "").strip()
        tls = "on" if config.get("tls", True) else "off"

        if not recipient_email or "@" not in recipient_email:
            return "❌ Invalid recipient email."

        email_content = f"Subject: Test Email from 45Drives\n\nThis is a test email."

        # Check for existing msmtp OAuth config (optional legacy support)
        use_existing_config = False
        if os.path.exists(MSMTP_CONFIG_PATH):
            with open(MSMTP_CONFIG_PATH, "r") as f:
                current_config = f.read()
            if "auth oauthbearer" in current_config:
                current_user_line = next((line for line in current_config.split('\n') if line.startswith("user ")), None)
                current_user = current_user_line.split(" ")[1] if current_user_line else ""
                if current_user == username:
                    subprocess.run(["python3", MSMTP_OAUTH_REFRESH_SCRIPT], check=False)
                    use_existing_config = True

        # Use system config if available
        if use_existing_config:
            process = subprocess.run(
                ["msmtp", "-C", MSMTP_CONFIG_PATH, recipient_email],
                input=email_content,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Temporary config for plain SMTP
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                tmp.write(f"""account default
host {smtp_server}
port {smtp_port}
auth on
user {username}
password {password}
from {sender_email}
tls {tls}
tls_starttls on
logfile /var/log/msmtp.log
""")
                tmp.flush()
                temp_config_path = tmp.name

            process = subprocess.run(
                ["msmtp", "-C", temp_config_path, recipient_email],
                input=email_content,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            os.unlink(temp_config_path)

        if process.returncode == 0:
            return f"✅ Test email sent to {recipient_email} via SMTP!"
        else:
            return f"❌ SMTP error: {process.stderr.strip()}"

    except Exception as e:
        return f"❌ Exception in SMTP send: {str(e)}"

import base64
import requests
import email.message

# Paths to token info and refresh script

def sendTestEmailViaGmailApi(config):
    try:
        if not os.path.exists(MSMTP_OAUTH_JSON_PATH):
            return "❌ Gmail OAuth credentials file not found."

        # 🔄 Refresh access token
        logging.info("🔄 Refreshing Gmail token...")
        refresh = subprocess.run(
            ["python3", MSMTP_OAUTH_REFRESH_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        if refresh.returncode != 0:
            logging.error(f"❌ Refresh script failed: {refresh.stderr.strip()}")
            return f"❌ Token refresh failed: {refresh.stderr.strip()}"

        # ✅ Load refreshed token data
        with open(MSMTP_OAUTH_JSON_PATH) as f:
            oauth = json.load(f)

        access_token = oauth.get("access_token")
        sender_email = oauth.get("user_email")
        recipient_email = config.get("recipientEmail", "").strip()

        if not all([access_token, sender_email, recipient_email]):
            return "❌ Missing required fields: access token, sender, or recipient."

        # 🔁 Call your own API endpoint
        payload = {
            "accessToken": access_token,
            "from": sender_email,
            "to": recipient_email,
            "subject": "Test Email from 45Drives",
            "body": "This is a test email from the ZFS notification system."
        }

        logging.info(f"📡 Calling {AUTH_SEND_EMAIL_URL} to send email...")
        response = requests.post(
            AUTH_SEND_EMAIL_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"❌ Failed to send via API ({response.status_code}): {response.text.strip()}"

    except Exception as e:
        logging.error(f"❌ Exception in sendViaGmailApi: {str(e)}")
        return f"❌ Exception in sendViaGmailApi: {str(e)}"

def sendTestEmail(config_json):
    """
    Delegates to either Gmail API or msmtp based on auth method.
    """
    try:
        config = json.loads(config_json)
        auth_method = config.get("authMethod", "plain").strip().lower()

        if auth_method == "oauth2":
            return sendTestEmailViaGmailApi(config)
        else:
            return sendTestEmailViaSMTP(config)

    except Exception as e:
        error_message = f"❌ Error sending test email: {str(e)}"
        logging.error(error_message)
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


MSMTP_CONFIG_PATH = "/etc/45drives/msmtp"
MSMTP_PASSWORD_PATH = "/etc/45drives/msmtp_pass"
MSMTP_RECIPIENT_PATH = "/etc/45drives/msmtp_recipients"

def updateSMTPConfig(config_json):
    """
    Updates either msmtp (plain auth) or Gmail API (OAuth2) config depending on selected authMethod.
    """
    try:
        print("🔄 Updating email config...")

        config = json.loads(config_json)

        email = config.get("email", "")
        recipient_email = config.get("recieversEmail", "")
        auth_method = config.get("authMethod", "plain")
        tls = "on" if config.get("tls", True) else "off"

        # Store recipient email for both cases
        with open(MSMTP_RECIPIENT_PATH, "w") as f:
            f.write(recipient_email)
        os.chmod(MSMTP_RECIPIENT_PATH, 0o600)

        if auth_method == "oauth2":
            # Gmail API OAuth2 setup (NOT msmtp)
            user_email = config.get("username", "")
            access_token = config.get("oauthAccessToken", "")
            refresh_token = config.get("refreshToken", "")  # storing under 'password' for consistency
            expiry = config.get("tokenExpiry", "")

            oauth_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_email": user_email,
                "expiry": expiry
            }

            with open(MSMTP_OAUTH_JSON_PATH, "w") as f:
                json.dump(oauth_data, f, indent=4)
            os.chmod(MSMTP_OAUTH_JSON_PATH, 0o600)

            # Empty out msmtp config
            with open(MSMTP_CONFIG_PATH, "w") as f:
                f.write("")  # clear the file
            os.chmod(MSMTP_CONFIG_PATH, 0o600)

            print("✅ Gmail API config (OAuth2) saved and msmtp config cleared.")

        else:
            # Traditional SMTP config (msmtp)
            smtp_server = config.get("smtpServer", "smtp.gmail.com")
            smtp_port = config.get("smtpPort", 587)
            username = config.get("username", "")
            password = config.get("password", "")
            
            with open(MSMTP_OAUTH_JSON_PATH, "w") as f:
                f.write("")  # clear the file
                os.chmod(MSMTP_OAUTH_JSON_PATH, 0o600)

            # Save password securely
            with open(MSMTP_PASSWORD_PATH, "w") as f:
                f.write(password)
            os.chmod(MSMTP_PASSWORD_PATH, 0o600)

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

            with open(MSMTP_CONFIG_PATH, "w") as f:
                f.write(config_content)
            os.chmod(MSMTP_CONFIG_PATH, 0o600)

            print("✅ SMTP (msmtp) config updated successfully.")

        updateEmailSeverities(config_json)
        return "✅ Email configuration saved!"

    except Exception as e:
        error_message = f"❌ Error updating email config: {str(e)}"
        print(error_message)
        return error_message


def sendEmailNotification(subject, message, severity):
    if not should_send_email(severity):
        msg = f"⚠️ Email skipped: severity '{severity}' not enabled in smtp_settings."
        print(msg)
        logging.info(msg)
        return msg

    try:
        logging.info("📨 Preparing to send automated notification email...")

        # ✅ Check if msmtp config exists and is non-empty
        if not os.path.exists(MSMTP_CONFIG_PATH) or os.stat(MSMTP_CONFIG_PATH).st_size == 0:
            logging.warning("⚠️ msmtp config missing or empty, falling back to Gmail API.")
            use_gmail_api = True
            config_content = ""
        else:
            with open(MSMTP_CONFIG_PATH, "r") as f:
                config_content = f.read()
            use_gmail_api = "auth oauthbearer" in config_content

        if use_gmail_api:
            logging.info("🔄 Using Gmail API. Refreshing token...")
            refresh_process = subprocess.run(
                ["python3", MSMTP_OAUTH_REFRESH_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            logging.debug(f"[OAuth Refresh STDOUT]: {refresh_process.stdout.strip()}")
            logging.debug(f"[OAuth Refresh STDERR]: {refresh_process.stderr.strip()}")

            if refresh_process.returncode != 0:
                logging.warning(f"⚠️ Failed to refresh OAuth token.")
                return f"⚠️ Failed to refresh OAuth token."

            with open(MSMTP_OAUTH_JSON_PATH) as f:
                oauth_data = json.load(f)

            access_token = oauth_data.get("access_token")
            sender_email = oauth_data.get("user_email")

            with open(MSMTP_RECIPIENT_PATH, "r") as f:
                recipient_email = f.read().strip()

            if not all([access_token, sender_email, recipient_email]):
                return "❌ Missing required OAuth fields."

            payload = {
                "accessToken": access_token,
                "from": sender_email,
                "to": recipient_email,
                "subject": subject,
                "body": message
            }

            AUTH_SEND_EMAIL_URL = "https://email-auth.45d.io/auth/send-email"
            response = requests.post(
                AUTH_SEND_EMAIL_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logging.info("✅ Gmail API email sent successfully.")
                return response.text.strip()
            else:
                logging.error(f"❌ Gmail API error {response.status_code}: {response.text.strip()}")
                return f"❌ Gmail API error {response.status_code}: {response.text.strip()}"

        else:
            # ✅ Read recipient email
            with open(MSMTP_RECIPIENT_PATH, "r") as f:
                recipient_email = f.read().strip()

            # ✅ Construct email content
            email_content = f"""Subject: {subject}\n\n{message}"""

            # ✅ Send email using msmtp
            logging.info(f"📤 Sending email to {recipient_email} using msmtp...")
            process = subprocess.run(
                ["msmtp", "-C", MSMTP_CONFIG_PATH, recipient_email],
                input=email_content,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            logging.debug(f"[msmtp STDOUT]: {process.stdout.strip()}")
            logging.debug(f"[msmtp STDERR]: {process.stderr.strip()}")

            if process.returncode == 0:
                success_msg = f"✅ Notification sent to {recipient_email} successfully!"
                print(success_msg)
                logging.info(success_msg)
                return success_msg
            else:
                error_message = f"❌ Failed to send notification: {process.stderr.strip()}"
                print(error_message)
                logging.error(error_message)
                return error_message

    except Exception as e:
        error_message = f"❌ Error sending notification: {str(e)}"
        print(error_message)
        logging.exception(error_message)
        return error_message

def fetchMsmtpDetails():
    """Fetch the stored SMTP or Gmail OAuth configuration details."""
    try:
        smtp_details = {}

        if not os.path.exists(MSMTP_CONFIG_PATH) or os.stat(MSMTP_CONFIG_PATH).st_size == 0:
            # Fallback to Gmail OAuth mode
            if os.path.exists(MSMTP_OAUTH_JSON_PATH):
                with open(MSMTP_OAUTH_JSON_PATH, "r") as f:
                    oauth_data = json.load(f)
                smtp_details["authMethod"] = "oauth2"
                smtp_details["username"] = oauth_data.get("user_email", "")
                smtp_details["email"] = oauth_data.get("user_email", "")
                smtp_details["oauthAccessToken"] = oauth_data.get("access_token", "")
                smtp_details["password"] = oauth_data.get("refresh_token", "")
                smtp_details["tokenExpiry"] = oauth_data.get("expiry", "")
            else:
                return json.dumps({"error": "OAuth credentials not found."})
        else:
            # Traditional SMTP config (plain auth)
            with open(MSMTP_CONFIG_PATH, "r") as f:
                config_data = f.readlines()
            
            for line in config_data:
                if line.startswith("host"):
                    smtp_details["smtpServer"] = line.split(" ")[1].strip()
                elif line.startswith("port"):
                    smtp_details["smtpPort"] = line.split(" ")[1].strip()
                elif line.startswith("user"):
                    smtp_details["username"] = line.split(" ")[1].strip()
                elif line.startswith("from"):
                    smtp_details["email"] = line.split(" ")[1].strip()
                elif line.startswith("tls "):
                    smtp_details["tls"] = line.split(" ")[1].strip().lower() == "on"
                elif line.startswith("auth"):
                    smtp_details["authMethod"] = line.split(" ")[1].strip()

            # Default to "plain" if not explicitly defined
            if "authMethod" not in smtp_details:
                smtp_details["authMethod"] = "plain"

            with open(MSMTP_PASSWORD_PATH, "r") as f:
                smtp_details["password"] = f.read().strip()

        # Read recipient email (shared by both modes)
        if os.path.exists(MSMTP_RECIPIENT_PATH):
            with open(MSMTP_RECIPIENT_PATH, "r") as f:
                smtp_details["recieversEmail"] = f.read().strip()

        return json.dumps(smtp_details)

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch email config: {str(e)}"})

def updateWarningLevels(config_json):
    """Updates warning_levels table based on frontend config"""
    try:
        config = json.loads(config_json)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for event_type, severity in config.items():
            if severity not in ["info", "warning", "critical"]:
                continue  # skip invalid

            cursor.execute("""
                INSERT INTO warning_levels (event_type, severity)
                VALUES (?, ?)
                ON CONFLICT(event_type) DO UPDATE SET severity = excluded.severity
            """, (event_type, severity))

        conn.commit()
        conn.close()
        return "✅ Warning levels updated successfully."

    except Exception as e:
        return f"❌ Failed to update warning levels: {str(e)}"

def should_send_email(severity: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email_enabled, send_info, send_warning, send_critical
        FROM smtp_settings
        WHERE id = 1
    """)
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    email_enabled, send_info, send_warning, send_critical = result
    if not email_enabled:
        return False

    return (
        (severity == "info" and send_info) or
        (severity == "warning" and send_warning) or
        (severity == "critical" and send_critical)
    )

def updateEmailSeverities(json_string):
    try:
        data = json.loads(json_string)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        email_enabled = 1 if data.get("email_enabled") else 0
        send_info = 1 if data.get("send_info") else 0
        send_warning = 1 if data.get("send_warning") else 0
        send_critical = 1 if data.get("send_critical") else 0

        cursor.execute("""
            INSERT OR REPLACE INTO smtp_settings (id, email_enabled, send_info, send_warning, send_critical)
            VALUES (1, ?, ?, ?, ?)
        """, (
            email_enabled,
            send_info,
            send_warning,
            send_critical
        ))

        conn.commit()
        conn.close()
        return "✅ Email severity flags updated."

    except Exception as e:
        return f"❌ Failed to update email severity config: {str(e)}"

def should_send_email(severity: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email_enabled, send_info, send_warning, send_critical
        FROM smtp_settings
        WHERE id = 1
    """)
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    email_enabled, send_info, send_warning, send_critical = result
    if not email_enabled:
        return False

    return (
        (severity == "info" and send_info) or
        (severity == "warning" and send_warning) or
        (severity == "critical" and send_critical)
    )

if __name__ == "__main__":
    subject = "Manual Test from Terminal"
    message = "🚀 This is a manually triggered test email from the terminal."
    severity = "info"  # Can be "info", "warning", or "critical"
    
    print(sendEmailNotification(subject, message, severity))

def resetMsmtpData():
    """Reset the msmtp configuration files to empty or default state."""
    try:
        with open(MSMTP_OAUTH_JSON_PATH,"w") as auth_file:
            auth_file.write("")
        # Reset msmtprc
        with open(MSMTP_CONFIG_PATH, "w") as config_file:
            config_file.write("")

        # Clear password file
        with open(MSMTP_PASSWORD_PATH, "w") as pw_file:
            pw_file.write("")

        # Clear recipient file
        with open(MSMTP_RECIPIENT_PATH, "w") as recipient_file:
            recipient_file.write("")

        return json.dumps({"success": "SMTP config reset successfully."})

    except Exception as e:
        return json.dumps({"error": f"Failed to reset SMTP config: {str(e)}"})