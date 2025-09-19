#!/bin/bash

# Path to the D-Bus client script
DBUS_CLIENT="/opt/45drives/houston/houston-notify"
DEBUG_LOG="/tmp/zed_vdev_attach_debug.log"

# Log that the script was triggered
echo "[INFO] VDEV attach event detected at $(date)" >> "$DEBUG_LOG"

# Extract event details
EVENT_CLASS="vdev_attach"
EVENT_POOL="${ZEVENT_POOL:-Unknown}"
EVENT_VDEV="${ZEVENT_VDEV_PATH:-Unknown}"
EVENT_VDEV_GUID="${ZEVENT_VDEV_GUID:-Unknown}"
EVENT_POOL_GUID="${ZEVENT_POOL_GUID:-Unknown}"
EVENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')  # Capture timestamp
EVENT_HOST=$(hostname)

# Ensure EVENT_POOL is set (required for valid notifications)
if [[ "$EVENT_POOL" == "Unknown" ]]; then
    echo "[ERROR] Missing EVENT_POOL - Notification aborted" >> "$DEBUG_LOG"
    exit 1
fi

# Generate an appropriate message
IMPACT_MESSAGE="A new device has been successfully attached to the ZFS pool '$EVENT_POOL'. This may have been done to expand storage capacity or improve redundancy."
RECOMMENDATION="Verify the new device is functioning correctly and update any documentation if necessary."



# Construct Subject & User-Friendly Email Message
EMAIL_SUBJECT="ZFS Alert: New Device Attached to Pool '$EVENT_POOL'"

EMAIL_MESSAGE=$(cat <<EOF
====================================================
ZFS VDEV ATTACH REPORT - POOL: $EVENT_POOL
====================================================

$IMPACT_MESSAGE

----------------------------------------------------
Device Details
----------------------------------------------------
- Pool Name: $EVENT_POOL
- Newly Attached Device: $EVENT_VDEV
- Device GUID: $EVENT_VDEV_GUID
- Pool GUID: $EVENT_POOL_GUID
- Timestamp: $EVENT_TIMESTAMP
- Host: $EVENT_HOST

----------------------------------------------------
Recommended Actions
----------------------------------------------------
1. Verify the new device is functioning properly:

   zpool status $EVENT_POOL

2. If redundancy was improved, ensure the mirror or RAID configuration is correct.

3. If this was an expansion:
   - Check if the added storage space is now available.
   - Run `zpool list` to confirm the updated pool size.

For further details, refer to system logs or ZFS documentation.
EOF
)

# Construct JSON message for forwarding to Houston UI
FORWARD_MESSAGE=$(jq -n \
  --arg timestamp "$EVENT_TIMESTAMP" \
  --arg event "$EVENT_CLASS" \
  --arg pool "$EVENT_POOL" \
  --arg vdev "$EVENT_VDEV" \
  --arg vdev_guid "$EVENT_VDEV_GUID" \
  --arg pool_guid "$EVENT_POOL_GUID" \
  --arg subject "$EMAIL_SUBJECT" \
  --arg email_message "$EMAIL_MESSAGE" \
  '{timestamp: $timestamp, event: $event, pool: $pool, vdev: $vdev, vdev_guid: $vdev_guid, pool_guid: $pool_guid,subject: $subject, email_message: $email_message}')

# Logging event details for debugging
{
  echo "==== DEBUG START ===="
  echo "DEBUG: Timestamp = $EVENT_TIMESTAMP"
  echo "DEBUG: Event Class = $EVENT_CLASS"
  echo "DEBUG: Pool = $EVENT_POOL"
  echo "DEBUG: VDEV = $EVENT_VDEV"
  echo "DEBUG: VDEV GUID = $EVENT_VDEV_GUID"
  echo "DEBUG: Pool GUID = $EVENT_POOL_GUID"
  echo "DEBUG: FORWARD_MESSAGE = $FORWARD_MESSAGE"
  echo "DEBUG: EMAIL_SUBJECT = $EMAIL_SUBJECT"
  echo "DEBUG: EMAIL_MESSAGE = $EMAIL_MESSAGE"
  echo "==== DEBUG END ===="
} >> "$DEBUG_LOG"

# Send event notification to Houston UI
python3 "$DBUS_CLIENT" "$FORWARD_MESSAGE" >> "$DEBUG_LOG" 2>&1
FORWARD_STATUS=$?


# Log final result
if [ "$FORWARD_STATUS" -eq 0 ]; then
  echo "[SUCCESS] VDEV attach event successfully forwarded to Houston UI" >> "$DEBUG_LOG"
else
  echo "[ERROR] Failed to forward VDEV attach event to Houston UI" >> "$DEBUG_LOG"
fi


exit 0
