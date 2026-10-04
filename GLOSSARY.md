# Network Monitor TDS

Watches a home network to keep a catalogue of its devices, whether each is present, and what each one is.

## Devices

**Device**:
Something on the network, identified by its MAC address.
_Avoid_: Host, client, node

**Randomized MAC**:
A made-up MAC address a device uses instead of its real one, recognisable by the locally administered bit; its vendor cannot be looked up.
_Avoid_: Private address, fake MAC

**Label**:
A name, category or drawing the user chose for a device; always wins over what was detected.
_Avoid_: Alias, override, custom name

**Detected name**:
The best name found without the user's help, from lease hostnames, DHCP hostnames, mDNS, UPnP or the vendor.
_Avoid_: Hostname (one of its sources, not the same thing)

**Category**:
The kind of device: network, server, computer, phone, tablet, wearable, media, gaming, smart home, camera, printer or unknown.
_Avoid_: Type, class

**Vendor**:
The manufacturer of a device's network interface, looked up from the first half of its MAC address.
_Avoid_: Brand, manufacturer, OUI (the prefix it is looked up from)

**New device**:
A device the user has not reviewed yet; it stops being new when marked as known or labelled.
_Avoid_: Unknown device (that is the *unknown* category)

## Discovery

**Plugin**:
One way of finding or learning about devices; it reports observations and nothing else.
_Avoid_: Scanner, module, integration

**Observation**:
One report from a plugin about one device at one moment, carrying named fields.
_Avoid_: Scan result, record

**Sighting**:
An observation proving the device was on the network at that moment.

**Enrichment**:
An observation adding information about a device without proving it is present.

**Fact**:
The latest known value of one field for a device, with the plugin that reported it and when.
_Avoid_: Attribute, property

**Detection**:
The first and last time a given plugin reported a given device; what "Discovered by" shows.

**Sweep**:
An active round of ARP requests to every address in the subnet.
_Avoid_: Scan

**Lease**:
An address assignment held by the DHCP server, read from Technitium.

## Presence

**Presence**:
Whether a device is online or offline, since when, and when it was last seen.
_Avoid_: Status (used for plugins), state

**Presence interval**:
A span of time during which a device was online; the history behind the strips and the heatmap.
_Avoid_: Session, online period

**Offline threshold**:
How long a device may go unseen before it is offline; longer for phones and tablets.
_Avoid_: Timeout, grace period

**Event**:
A notable change: a device discovered, coming online or going offline.
