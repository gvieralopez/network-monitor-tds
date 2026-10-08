# Using the web interface

![Devices page](../images/devices.png)

## The devices page

The top of the page shows how many devices are online now, with buttons for devices waiting for review and devices that are offline. The chart shows how many devices were seen in each of the last 24 hours; hover it to read a value.

Each device is a card with:

- a drawing of the kind of device it is, on artwork in its category's colour generated from its MAC address, so every device looks different and keeps the same look;
- online or "last seen" status, a **NEW** tag if you have not reviewed it yet, and its IP address;
- name, category and vendor ("Private MAC" when the device hides its real address);
- a strip with one block per hour of the last 24 hours, filled when the device was online.

Offline devices are shown in grey.

## Finding devices

- **Search** matches names, IP addresses, MAC addresses, vendors and categories.
- **Filters** opens a panel to filter by status (All, Online or Offline), by category, or to show only new devices. Each category shows how many devices it has. The button shows how many filters are on, and each one appears as a chip under the search: press its ✕ to remove it, or **Clear all** to remove them all. Click anywhere else or press Escape to close the panel.
- The button next to it shows the current sort and opens a panel to change the grouping and sorting:
  - **Group by** shows every device in one grid with "None", the default, or arranges them in rows by category or vendor. Each device appears once; new devices carry a NEW badge.
  - **Sort by** orders by last seen (the default), name, IP address or first seen. The button next to it reverses the order; each sort starts the natural way round, for example most recent first for last seen and A to Z for name. Online devices count as seen now, so they come first, alphabetically. Devices with no IP address always come last when sorting by IP.
- The **new to review** and **offline** pills under the device count are shortcuts to those two filters.

The page address changes with your filters, so a filtered view can be bookmarked. The page updates by itself when devices come, go or appear for the first time, and shows a short notification. The dot next to "Live" in the header shows whether live updates are connected.

## The device panel

![Device panel](../images/device-panel.png)

Click a card to open its panel. It has two tabs.

**Overview** shows what is known about the device:

- **Presence, last 14 days**: one row per day, one square per hour, today at the top. Hours before the device was first seen show as "no data".
- **Details**: IP and MAC address, vendor, category, the detected name and where it came from, and the detected type.
- **Discovered by**: the plugin that found the device first, and every plugin that has reported it since. Hover a plugin to see what it learned.

Press **Mark as known** to remove the NEW tag without changing anything else.

**Manage** holds your own name and category for the device, and changes save as you make them. The category decides which group the card is shown in and its colour; changing it also switches the drawing to the first one recommended for that category. To pick another drawing, press the pencil next to the drawing on the banner: the panel turns over to show every drawing, with those of the chosen category recommended first. You can pick any drawing; search by name to find one, for example "console" for the several shapes and colours of consoles. The name is saved when you leave the field or close the panel; leave it empty to use the detected name. Press **Reset to detected** to go back to the detected name, category and drawing. Saving also marks the device as known.

![Drawing picker](../images/device-drawings.png)

Press **Forget device** at the bottom of the Manage tab to delete a device you no longer own, together with its labels, details and history. This cannot be undone. If the device is still on the network, it shows up again as a new device the next time it is seen.

Press Escape, the close button or anywhere outside the panel to close it.

## Settings

The Settings page has three tabs.

- **General** holds how long history is kept and how long a device can stay silent before it is marked offline. These apply to the whole monitor.
- **Appearance** is saved in each browser only. *Style* sets the theme (Auto, Light or Dark) and the card style (Artwork, with each device on a pattern in its category's colour, or Studio, on a plain backdrop). *Presentation* sets how the devices page is grouped and sorted when you open it; you can still change both on the page, and a link that includes them opens exactly that view.
- **Sources** lists every plugin, the parts of the monitor that find devices or learn about them, grouped by what it is for (passive and active device finders, third-party integrations, metadata providers, developer tools), with a switch, its current status and its settings. Changes apply immediately. See [Discovery plugins](plugins.md) and [How online and offline work](presence.md).
