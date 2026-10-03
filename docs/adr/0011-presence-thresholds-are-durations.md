# Presence thresholds are durations, and offline time is the last sighting

A device goes offline when nothing has seen it for a configurable duration (10 minutes, 15 for phones and tablets, which sleep their Wi-Fi), and the offline moment recorded is its last sighting, not the moment the check ran. The first design counted missed ARP sweeps, but that tied presence to one plugin's interval and was harder to explain on a settings page; the settings page now only warns when a threshold is shorter than two sweeps.

## Consequences

- A late sighting older than the recorded offline time cannot bring a device back online.
- Presence checks read the policy from the database each time, so changes apply without a restart.
