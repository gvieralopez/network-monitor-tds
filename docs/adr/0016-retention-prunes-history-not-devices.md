# Retention prunes history, not devices

Presence intervals and events are deleted once they are older than a retention period set on the Settings page (90 days by default), by a daily job in the monitor. Devices, facts and detections are never deleted automatically. Removing a device is a separate, manual "forget device" action.

Pruning devices that have been gone a long time would keep the database smaller, but a returning device would then be reported as new, which is exactly the alert the monitor exists to raise. A home network has at most a few hundred devices, so keeping them all costs little; intervals and events are what grow without bound.

## Consequences

- Retention is at least 14 days, the length of the device panel's history, so the panel never shows a gap. A test keeps the two in step.
- Open presence intervals are never pruned, whatever their start date.
- Retention is a whole number of days, not a duration like the presence thresholds, because durations are entered in hours at most.
