#!/bin/bash

# Path to the D-Bus client script
DBUS_CLIENT="/opt/45drives/houston/houston-notify"
DEBUG_LOG="/tmp/zed_vdev_clear_debug.log"

# Log that the script was triggered
echo "[INFO] VDEV clear event detected at $(date)" >> "$DEBUG_LOG"

# Extract event details
EVENT_CLASS="vdev_clear"
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
IMPACT_MESSAGE="A device in the ZFS pool '$EVENT_POOL' has been manually cleared. This may indicate previous errors were acknowledged, or a device issue has been resolved."
RECOMMENDATION="Monitor the device health closely to ensure no further errors occur."


# Construct Subject & User-Friendly Email Message
EMAIL_SUBJECT="ZFS Alert: Device Cleared in Pool '$EVENT_POOL'"

EMAIL_MESSAGE=$(cat <<EOF
====================================================
ZFS DEVICE CLEAR REPORT - POOL: $EVENT_POOL
====================================================

$IMPACT_MESSAGE

----------------------------------------------------
Device Details
----------------------------------------------------
- Pool Name: $EVENT_POOL
- Cleared Device: $EVENT_VDEV
- Device GUID: $EVENT_VDEV_GUID
- Pool GUID: $EVENT_POOL_GUID
- Timestamp: $EVENT_TIMESTAMP
- Host: $EVENT_HOST

----------------------------------------------------
Recommended Actions
----------------------------------------------------
1. Check the current pool status using:

   zpool status $EVENT_POOL

2. Monitor the cleared device for potential recurring errors:

   zpool events -v $EVENT_POOL

3. If issues persist:
   - Consider replacing the device if errors reappear.
   - Run a scrub to verify data integrity.

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
  echo "[SUCCESS] VDEV clear event successfully forwarded to Houston UI" >> "$DEBUG_LOG"
else
  echo "[ERROR] Failed to forward VDEV clear event to Houston UI" >> "$DEBUG_LOG"
fi



exit 0
