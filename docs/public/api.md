# JSON API

A small read-only API for scripts and home automation, such as Home Assistant's REST sensors. Like the web interface, it has no login: keep it on your LAN or behind a reverse proxy.

| Endpoint | Returns |
|---|---|
| `GET /api/v1/devices` | Every known device. |
| `GET /api/v1/devices/online` | Only the devices that are online right now. |

Both return a JSON list sorted by MAC address. Each device looks like this:

```json
{
  "mac": "24:0a:c4:9f:31:5e",
  "ip": "192.168.1.143",
  "name": "esp-31f5e",
  "category": "iot",
  "vendor": "Espressif Inc.",
  "online": true,
  "new": false,
  "first_seen": "2026-10-03T12:00:00Z",
  "last_seen": "2026-10-04T08:15:02Z"
}
```

- `name` and `category` are the ones the web interface shows: your labels if you set them, otherwise what the monitor worked out. See [How devices are named and categorized](device-identity.md).
- `ip` is the last address the device was seen with, or `null` if none is known yet.
- `vendor` is `null` until the MAC vendor lookup has run.
- `new` is `true` until you mark the device as known.
- Times are UTC.

For example, to count the devices online:

```sh
curl -s http://monitor.lan:8000/api/v1/devices/online | jq length
```

The machine-readable schema is at `/openapi.json`.
