# Running in Docker

Every release publishes an image to `ghcr.io/gvieralopez/network-monitor-tds`, tagged with its version (for example `0.2.0`) and `latest`. Pin a version tag so upgrades happen when you choose.

## Compose

```yaml
services:
  network-monitor:
    image: ghcr.io/gvieralopez/network-monitor-tds:<version>
    restart: unless-stopped
    network_mode: host
    cap_add:
      - NET_RAW
      - NET_ADMIN
    volumes:
      - nmtds-data:/data

volumes:
  nmtds-data:
```

Start it with `docker compose up -d` and open `http://<host>:8000`.

- **Host networking** is required. The ARP and DHCP plugins have to see your LAN; on Docker's default bridge network they would only see the container's own virtual network.
- **Both capabilities** are required, not just for the capture plugins: the image grants them to its Python interpreter, and Linux refuses to start that interpreter in a container that lacks them. Without them the container stops immediately with `operation not permitted`. Do not use `privileged: true`; these two are all it needs. See [Packet capture permissions](capture-permissions.md).
- **Data** lives in `/data`: the database and the backups taken before upgrades. Keep it on a volume.

## Settings in the image

The image sets `NMTDS_HOST=0.0.0.0` and `NMTDS_DATA_DIR=/data`, and listens on port `8000`. Change the port with `NMTDS_PORT` under `environment:`. The other variables are in [Configuration](configuration.md).

There is no login, and with host networking the web interface is reachable from your whole LAN. If you don't trust everyone on it, set `NMTDS_HOST=127.0.0.1` and put a reverse proxy with authentication on the same host in front of it.

## Keeping the data in a host folder

The monitor runs as user `nmtds` (uid 10001). To use a folder on the host instead of a named volume, either make the folder writable by uid 10001, or run the container as the folder's owner:

```yaml
    user: "1000:1000"
    volumes:
      - /home/me/apps/network-monitor:/data
```

Packet capture keeps working under any user, because the capabilities belong to the interpreter, not to the user.

## Upgrading

Change the tag, then `docker compose pull && docker compose up -d`. The monitor upgrades its database by itself on start, after copying it to `/data/nmtds.db.bak-<old version>`. See [Data, upgrades and backups](data-and-upgrades.md).
