# Getting started

Network Monitor TDS watches your home network and shows every device it finds: whether it is online, what it is, who made it, and when it comes and goes. It does not replace your router, DHCP server or DNS server; it only listens and asks.

## Requirements

- Linux, with Python 3.14 and [uv](https://docs.astral.sh/uv/).
- libpcap (installed on most desktops; `apt install libpcap0.8` on Debian).
- Root, or the `CAP_NET_RAW` and `CAP_NET_ADMIN` capabilities, for the plugins that capture packets. See [Packet capture permissions](capture-permissions.md).

## Install

To run the published image instead of installing from source, see [Running in Docker](docker.md).

```bash
git clone https://github.com/gvieralopez/network-monitor-tds.git
cd network-monitor-tds
uv sync
```

## Try it with the demo network

The demo plugin simulates a home network with about twenty devices and daily routines. It needs no special permissions, so it is the quickest way to see the interface.

```bash
uv run nmtds plugins enable demo
uv run nmtds serve
```

Open <http://127.0.0.1:8000>. Two of the demo devices join a few minutes after start, so you can watch new devices arrive.

## Monitor your real network

Turn the demo off and run the monitor with capture permissions:

```bash
uv run nmtds plugins disable demo
sudo --preserve-env=NMTDS_DATA_DIR .venv/bin/nmtds serve
```

Within a few seconds the ARP sweep fills the page with the devices on your subnet. Names improve over the following minutes as devices renew their DHCP leases. If you run Technitium, connect it for better names: see [Technitium DHCP integration](technitium.md).

By default the web interface only listens on `127.0.0.1`. To reach it from other machines, set `NMTDS_HOST=0.0.0.0` (see [Configuration](configuration.md)). There is no login yet, so only do this on a network you trust.
