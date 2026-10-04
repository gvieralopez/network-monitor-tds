# Using the web interface

![Devices page](../images/devices.png)

## The devices page

The top of the page shows how many devices are online now, with buttons for devices waiting for review and devices that are offline. The chart shows how many devices were seen in each of the last 24 hours; hover it to read a value.

Each device is a card with:

- artwork in its category's colour, generated from its MAC address, so every device looks different and keeps the same look;
- online or "last seen" status, a **NEW** tag if you have not reviewed it yet, and its IP address;
- name, category and vendor ("Private MAC" when the device hides its real address);
- a strip with one block per hour of the last 24 hours, filled when the device was online.

Offline devices are shown in grey.

## Finding devices

- **Search** matches names, IP addresses, MAC addresses, vendors and categories.
- **All / Online / Offline** filters by status.
- The **chips** below filter by category, or show only new devices.
- **Group** arranges devices in rows by category, status or vendor, or in one grid with "None". Devices waiting for review also get their own "New on your network" row.
- **Sort** orders by new-then-online, name, IP address or last seen.

The page address changes with your filters, so a filtered view can be bookmarked. The page updates by itself when devices come, go or appear for the first time, and shows a short notification. The dot next to "Live" in the header shows whether live updates are connected.

## The device panel

![Device panel](../images/device-panel.png)

Click a card to open its panel:

- **Presence, last 14 days**: one row per day, one square per hour, today at the top. Hours before the device was first seen show as "no data".
- **Discovered by**: the plugin that found the device first, and every plugin that has reported it since. Hover a plugin to see what it learned.
- **Details**: IP and MAC address, vendor, the detected name and where it came from, and the detected type.
- **Your labels**: your own name, category and icon. Leave a field on automatic to keep using what was detected. Saving also marks the device as known.

Press **Mark as known** to remove the NEW tag without changing anything else.

## Settings

The Settings page has two tabs. **General** holds the presence thresholds and how long history is kept. **Plugins** lists every plugin, grouped by how it works (listening, running on a schedule, enriching devices), with a switch, its current status and its settings. Changes apply immediately. See [Discovery plugins](plugins.md) and [How online and offline work](presence.md).
