# TODO

Where the project stands and what is left.

## Status (2026-10-04)

The app is feature-complete and released as a docker image tagged 0.2.0.


## Homelab testing

Everything done on the real network once the image exists.

- [ ] **Homelab stack.** New stack in the homelab repo following its own rules (compose template,
      app data under the home directory, Technitium token through SOPS, backups). Pin the image tag.
- [ ] **Verify Technitium against the real server.** The endpoint (`/api/dhcp/leases/list`), the
      token query parameter and the response shape come from Technitium's docs, not from a live
      call.
- [ ] **Run next to NetAlertX** for about a week, compare, then retire NetAlertX.
- [ ] **Tune device classification with real devices.** `domain/devices/classification.py` was
      written from guesses; adjust with what the week next to NetAlertX shows (misnamed devices,
      wrong categories).
- [ ] **Resource check on the server.** Target under ~100 MB RAM and near-zero idle CPU on the
      4-core Celeron. Measure with real traffic for a day.

## Later releases

- "Forget device" action in the UI.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- Custom thumbnails for devices
- Dark mode / Light mode should be configurable in settings
- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
