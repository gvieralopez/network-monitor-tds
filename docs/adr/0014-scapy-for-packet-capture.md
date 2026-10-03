# Scapy for packet capture and ARP sweeps

ARP sweeps, the ARP listener and the DHCP sniffer use scapy, with parsing kept in pure functions that tests feed hand-built packets. Raw `AF_PACKET` sockets with our own ARP and DHCP parsing would be lighter and fully under our control, and remain an option behind the same `capture()` interface, but scapy was quicker to get right and was verified to work on Python 3.14.

## Consequences

- Capturing needs `CAP_NET_RAW` and `CAP_NET_ADMIN` (root locally, capabilities in the container).
- scapy compiles BPF filters through libpcap, so the container image needs `libpcap`.
- scapy prints whatever a sniffer callback returns, so callbacks must return `None` (a test enforces this).
