# How devices are named and categorized

A device is identified by its MAC address. Everything else is worked out from what the discovery plugins report.

## Names

The name shown is the first available of:

1. the name you gave it;
2. the hostname from a DHCP lease (Technitium);
3. the hostname the device sent in its own DHCP request;
4. its mDNS (Bonjour) name;
5. its UPnP friendly name;
6. "*Vendor* device", from the manufacturer of its network card;
7. its MAC address.

Local suffixes such as `.local`, `.lan` and `.home.arpa` are removed, and placeholder names like `localhost` or `*` are skipped. The device panel shows the detected name and where it came from, even after you rename the device.

## Categories

Categories are network, server, computer, phone, tablet, media, smart home, camera, printer and unknown. The category is guessed from, in order: hostnames (`iPhone`, `ThinkPad`, `shellyplug`, `DiskStation` …), mDNS services (`_googlecast`, `_ipp` …), the DHCP vendor class (`android-dhcp`, `MSFT`), and the manufacturer. Anything the rules do not recognise is "unknown". Choosing a category yourself always wins.

## Randomized MAC addresses

Most phones, tablets and laptops use a different, made-up MAC address on each network. These are recognised and shown with the vendor "Private MAC". The manufacturer cannot be looked up for them, and one physical device can appear twice if it changes its address. Merging such duplicates is planned.

## New devices

A device is **new** until you review it: either press **Mark as known** in its panel or save labels for it. New devices are listed first and get their own row on the devices page.
