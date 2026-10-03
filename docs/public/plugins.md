# Discovery plugins

Each plugin finds devices, or learns about them, in a different way. Switch them on and off and change their settings on the Settings page; changes apply immediately. Each plugin shows its status there: working (with the time of its last success), off, or the error that stops it.

There are three kinds:

- **Listens**: runs all the time and reacts to traffic.
- **Scheduled**: runs every so often.
- **Enrichment**: runs once for every new device.

| Plugin | Id | Kind | On by default | Needs capture permissions |
|---|---|---|---|---|
| ARP sweep | `arp-sweep` | Scheduled | yes | yes |
| ARP listener | `arp-listen` | Listens | yes | yes |
| DHCP sniffer | `dhcp-sniff` | Listens | yes | yes |
| MAC vendor lookup | `oui` | Enrichment | yes | no |
| Technitium DHCP leases | `technitium` | Scheduled | no | no |
| Demo network | `demo` | Scheduled | no | no |

## ARP sweep

Asks every address in the subnet who is there, and records the monitor's own machine too. This is what tells the monitor that quiet devices are still around.

| Setting | Default | Meaning |
|---|---|---|
| Interval | 5m | How often to sweep. |
| Timeout | 1m | Gives up on a sweep that takes longer. |
| Interface | automatic | Network interface. Empty means the one with the default route. |
| Subnet | automatic | Subnet to sweep, e.g. `192.168.1.0/24`. Empty means the interface's subnet. |
| Reply timeout | 3s | How long to wait for answers. |

Subnets larger than 1,024 addresses are refused, so a typo cannot start a scan of a `/16`.

## ARP listener

Watches ARP traffic to notice devices between sweeps. Each device is reported at most once per **Report every** (default 1m), so chatty devices do not flood the database.

## DHCP sniffer

Reads DHCP requests that devices broadcast when they join the network or renew their address. It learns the hostname the device asks for, its vendor class (such as `android-dhcp-14`) and its DHCP fingerprint. It only needs an **Interface** setting, empty by default.

## MAC vendor lookup

Looks up the manufacturer from the first half of the MAC address, using a copy of the IEEE registry that ships with the monitor; it never goes online. It runs for every new device and, when it starts, for every device already known. Devices with randomized MAC addresses are skipped.

## Technitium DHCP leases

Imports the hostnames from your Technitium DHCP server's leases, which are usually the best names available. See [Technitium DHCP integration](technitium.md).

## Demo network

Simulates a home network for trying the interface without capture permissions. Turn it off before monitoring a real network, or its devices will mix with yours.
