# How online and offline work

A device is **online** from the moment any plugin sees it on the network: it answers an ARP sweep, sends an ARP packet, or asks for a DHCP lease. Information that does not prove the device is there right now, such as a vendor lookup or a lease in Technitium, never makes a device online.

A device goes **offline** when nothing has seen it for a while. By default that is **10 minutes**, and **15 minutes** for phones, tablets and wearables, which turn off their Wi-Fi to save battery. The time recorded as "offline since" is the last moment it was seen, not the moment the monitor noticed.

Change both thresholds under **Settings → General**. They apply immediately. If a threshold is shorter than two ARP sweep intervals, the page warns you: quiet devices that only answer sweeps would flicker between online and offline.

The 24-hour strips, the 14-day heatmap and the "online X% of the last 7 days" figure are all built from these online periods.
