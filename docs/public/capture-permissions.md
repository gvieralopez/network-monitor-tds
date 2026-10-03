# Packet capture permissions

The ARP sweep, ARP listener and DHCP sniffer read and send raw network packets. Linux only allows that with the `CAP_NET_RAW` and `CAP_NET_ADMIN` capabilities. Without them, those plugins show this error on the Settings page and retry in the background:

> Capturing packets needs the CAP_NET_RAW and CAP_NET_ADMIN capabilities

The rest of the monitor keeps working: the web interface, the MAC vendor lookup and Technitium do not need them.

## Running locally

The simplest way is to run the server as root, keeping your data folder setting:

```bash
sudo --preserve-env=NMTDS_DATA_DIR,NMTDS_PORT .venv/bin/nmtds serve
```

Granting the capabilities to the Python interpreter (`setcap`) also works, but the interpreter uv uses is shared by every project that uses that Python version, so prefer `sudo` or a container.

## In a container

Run the container with host networking and only these two capabilities, rather than privileged:

```yaml
network_mode: host
cap_add:
  - NET_RAW
  - NET_ADMIN
```
