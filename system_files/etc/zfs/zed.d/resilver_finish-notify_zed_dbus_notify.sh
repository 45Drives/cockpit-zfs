#!/bin/bash

# Path to the D-Bus client script
DBUS_CLIENT="/opt/45drives/houston/houston-notify"
DEBUG_LOG="/tmp/zed_resilver_debug.log"

# Extract ZFS event details
EVENT_CLASS="resilver_finish"
EVENT_POOL="${ZEVENT_POOL:-Unknown}"
EVENT_STATE="${ZEVENT_POOL_HEALTH:-Unknown}"  # Pool-wide health
EVENT_ERRORS="${ZEVENT_ERRORS:-0}"
EVENT_REPAIRED="${ZEVENT_REPAIRED:-0}"
EVENT_POOL_GUID="${ZEVENT_POOL_GUID:-Unknown}"
EVENT_DURATION="${ZEVENT_DURATION:-Unknown}"  # Resilver duration (if available)
EVENT_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')  # Use current time

# Determine resilver status message
if [[ "$EVENT_ERRORS" -gt 0 ]]; then
  IMPACT_MESSAGE="The ZFS resilver process has completed, but errors were detected. Some data may be corrupted or unrecoverable."
  RECOMMENDATION="Investigate the affected disks and consider replacing any failing devices. If corruption is detected, restore from backups if necessary."
  URGENCY="WARNING"
else
  IMPACT_MESSAGE="The ZFS resilver process has completed successfully with no detected errors."
  RECOMMENDATION="No immediate action is required. Regular resilvers help maintain data redundancy and system stability."
  URGENCY="SUCCESS"
fi


# Construct Subject & User-Friendly Email Message
EMAIL_SUBJECT="ZFS Resilver Completed: Pool $EVENT_POOL - $URGENCY"

EMAIL_MESSAGE=$(cat <<EOF
====================================================
ZFS RESILVER COMPLETION REPORT - POOL: $EVENT_POOL
====================================================

$IMPACT_MESSAGE

----------------------------------------------------
Resilver Details
----------------------------------------------------
- Pool Name: $EVENT_POOL
- Pool GUID: $EVENT_POOL_GUID
- Pool State: $EVENT_STATE
- Errors Found: $EVENT_ERRORS
- Errors Repaired: $EVENT_REPAIRED
- Resilver Duration: $EVENT_DURATION
- Timestamp: $EVENT_TIMESTAMP

----------------------------------------------------
Recommended Actions
----------------------------------------------------
1. Check the detailed resilver report using:

   zpool status $EVENT_POOL

2. If errors were found:
   - Identify which disks encountered errors.
   - Consider replacing degraded or failing drives.
   - Verify data integrity using backups if necessary.

3. If all is well:
   - No immediate action is needed.
   - Continue monitoring system health for future issues.

For further details, refer to system logs or ZFS documentation.
EOF
)

# Construct JSON message for forwarding to Houston UI
FORWARD_MESSAGE=$(jq -n \
  --arg timestamp "$EVENT_TIMESTAMP" \
  --arg event "$EVENT_CLASS" \
  --arg pool "$EVENT_POOL" \
  --arg state "$EVENT_STATE" \
  --arg pool_guid "$EVENT_POOL_GUID" \
  --argjson errors "$EVENT_ERRORS" \
  --argjson repaired "$EVENT_REPAIRED" \
  --arg duration "$EVENT_DURATION" \
  --arg subject "$EMAIL_SUBJECT" \
  --arg email_message "$EMAIL_MESSAGE" \
  '{timestamp: $timestamp, event: $event, pool: $pool, state: $state, pool_guid: $pool_guid, errors: $errors, repaired: $repaired, duration: $duration,subject: $subject, email_message: $email_message}')

# Logging event details for debugging
{
  echo "==== DEBUG START ===="
  echo "DEBUG: Timestamp = $EVENT_TIMESTAMP"
  echo "DEBUG: Event Class = $EVENT_CLASS"
  echo "DEBUG: Pool = $EVENT_POOL"
  echo "DEBUG: State = $EVENT_STATE"
  echo "DEBUG: Pool GUID = $EVENT_POOL_GUID"
  echo "DEBUG: Errors Found = $EVENT_ERRORS"
  echo "DEBUG: Errors Repaired = $EVENT_REPAIRED"
  echo "DEBUG: Resilver Duration = $EVENT_DURATION"
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
  echo "[SUCCESS] Resilver event successfully forwarded to Houston UI" >> "$DEBUG_LOG"
else
  echo "[ERROR] Failed to forward resilver event to Houston UI" >> "$DEBUG_LOG"
fi


exit 0
