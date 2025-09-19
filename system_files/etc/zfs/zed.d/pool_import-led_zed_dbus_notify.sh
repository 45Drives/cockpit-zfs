#!/bin/bash

# Path to the D-Bus client script
DBUS_CLIENT="/opt/45drives/houston/houston-notify"
DEBUG_LOG="/tmp/zed_pool_import_debug.log"

# Log that the script was triggered
echo "[INFO] Pool import event detected at $(date)" >> "$DEBUG_LOG"

# Extract event details
EVENT_CLASS="pool_import"
EVENT_POOL="${ZEVENT_POOL:-Unknown}"
EVENT_POOL_GUID="${ZEVENT_POOL_GUID:-Unknown}"
EVENT_HEALTH="${ZEVENT_POOL_STATE_STR:-Unknown}"  # Health of the pool
EVENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')  # Capture timestamp
EVENT_HOST=$(hostname)

# Ensure EVENT_POOL is set (required for valid notifications)
if [[ "$EVENT_POOL" == "Unknown" ]]; then
    echo "[ERROR] Missing EVENT_POOL - Notification aborted" >> "$DEBUG_LOG"
    exit 1
fi

# Generate an appropriate message based on the health status
if [[ "$EVENT_HEALTH" == "ONLINE" ]]; then
  IMPACT_MESSAGE="The ZFS pool '$EVENT_POOL' has been successfully imported and is in a healthy state."
  RECOMMENDATION="No immediate action is required. However, it's good practice to check the pool's status and ensure all expected datasets are present."
  URGENCY="SUCCESS"
elif [[ "$EVENT_HEALTH" == "DEGRADED" ]]; then
  IMPACT_MESSAGE="The ZFS pool '$EVENT_POOL' has been imported but is in a DEGRADED state. One or more devices may be missing or damaged."
  RECOMMENDATION="Check the pool status immediately to identify any failed or degraded devices."
  URGENCY="WARNING"
else
  IMPACT_MESSAGE="The ZFS pool '$EVENT_POOL' has been imported but is in an UNKNOWN state."
  RECOMMENDATION="Manually verify the pool health using 'zpool status' to check for any potential issues."
  URGENCY="NOTICE"
fi


# Construct Subject & User-Friendly Email Message
EMAIL_SUBJECT="ZFS Alert: Pool '$EVENT_POOL' Imported - $URGENCY"

EMAIL_MESSAGE=$(cat <<EOF
====================================================
ZFS POOL IMPORT REPORT - POOL: $EVENT_POOL
====================================================

$IMPACT_MESSAGE

----------------------------------------------------
Pool Details
----------------------------------------------------
- Pool Name: $EVENT_POOL
- Pool GUID: $EVENT_POOL_GUID
- Pool Health: $EVENT_HEALTH
- Timestamp: $EVENT_TIMESTAMP
- Host: $EVENT_HOST

----------------------------------------------------
Recommended Actions
----------------------------------------------------
1. Check the current pool status using:

   zpool status $EVENT_POOL

2. If the pool is DEGRADED:
   - Identify missing or faulty devices.
   - Consider replacing or reattaching missing drives.
   - Monitor system logs for additional details.

3. If the pool is healthy:
   - No immediate action is required.
   - Perform a routine check to verify datasets.

For further details, refer to system logs or ZFS documentation.
EOF
)

# Construct JSON message for forwarding to Houston UI
FORWARD_MESSAGE=$(jq -n \
  --arg timestamp "$EVENT_TIMESTAMP" \
  --arg event "$EVENT_CLASS" \
  --arg pool "$EVENT_POOL" \
  --arg health "$EVENT_HEALTH" \
  --arg pool_guid "$EVENT_POOL_GUID" \
  --arg subject "$EMAIL_SUBJECT" \
  --arg email_message "$EMAIL_MESSAGE" \
  '{timestamp: $timestamp, event: $event, pool: $pool, health: $health, pool_guid: $pool_guid, subject: $subject, email_message: $email_message}')
  
# Logging event details for debugging
{
  echo "==== DEBUG START ===="
  echo "DEBUG: Timestamp = $EVENT_TIMESTAMP"
  echo "DEBUG: Event Class = $EVENT_CLASS"
  echo "DEBUG: Pool = $EVENT_POOL"
  echo "DEBUG: Pool GUID = $EVENT_POOL_GUID"
  echo "DEBUG: Health = $EVENT_HEALTH"
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
  echo "[SUCCESS] Pool import event successfully forwarded to Houston UI" >> "$DEBUG_LOG"
else
  echo "[ERROR] Failed to forward pool import event to Houston UI" >> "$DEBUG_LOG"
fi

exit 0
