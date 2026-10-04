# TODO

Where the project stands and what is left.

## Status (2026-10-04)

The app is feature-complete and released as a docker image tagged 0.2.0.


## Homelab testing

Everything yet to be done

- [ ] **Release 0.2.1** (branch `fix/graceful-shutdown`), then bump the homelab stack to its tag
      and digest in a commit of its own, and update the memory comment in its compose file.
      - Graceful shutdown, found during the backup test: `docker stop` waited 10 s and killed the
        app (exit 137) every time, because `serve` kept waiting for its background loops after
        uvicorn stopped. Fixed: 0.3 s, exit 0, and SQLite folds its WAL into the database on exit.
      - Memory: the image migrates in a short-lived `nmtds db upgrade`, then `exec`s
        `python -m network_monitor_tds.server`, which never loads alembic or the CLI; the MAC vendor
        table is kept as raw bytes instead of a dict. About 130 → 109 MiB; replacing scapy
        (another ~40 MiB) is not planned.
- [ ] **Run next to NetAlertX** for about a week, compare, then retire NetAlertX.
- [ ] **Tune device classification with real devices.** `domain/devices/classification.py` was
      written from guesses; adjust with what the week next to NetAlertX shows (misnamed devices,
      wrong categories). First day: the router (FRITZ!), the server (GIGA-BYTE), the desktop and
      both Macs are `unknown`; names keep Technitium's `.gao.it` domain suffix.

## Later releases

- "Forget device" action in the UI.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- Custom thumbnails for devices
- Dark mode / Light mode should be configurable in settings
- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
- Security audit
