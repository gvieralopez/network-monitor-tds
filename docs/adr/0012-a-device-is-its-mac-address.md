# A device is its MAC address, for now

Devices are keyed by MAC address. Phones, tablets and laptops randomize their MAC per network, so one physical device can appear as several; the randomized ones are recognized (the locally administered bit) and shown as "Private MAC", but they are not merged yet. Merging by hostname or DHCP fingerprint is planned (see the roadmap in the README), and changing the identity key later will need a data migration, which is why this is recorded.
