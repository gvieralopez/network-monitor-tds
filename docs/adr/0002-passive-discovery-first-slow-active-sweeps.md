# Passive discovery first, slow active sweeps

New devices are found by listening (DHCP and ARP broadcasts arrive within a second of a device joining), so active ARP sweeps only answer "is it still there?" and run every 5 minutes by default instead of every few seconds. Frequent sweeps are cheap on the server but wake sleeping phones and IoT radios and add noise; the cost of slow sweeps is that a device is marked offline minutes after it leaves, which is acceptable for a home network.

## Consequences

- Offline detection time is the presence threshold (10 minutes by default, 15 for phones and tablets), not the sweep interval. See [ADR-0011](0011-presence-thresholds-are-durations.md).
- The planned refinement is targeted sweeps (only devices not heard from recently) with an occasional full-subnet sweep; see `TODO.md`.
