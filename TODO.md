# TODO

Where the project stands and what is left, in the order we planned to do it.

## Status (2026-10-04)

Phases 0 to 6 are done on the `first-release` branch (local, not merged into `main`). `make qa`
passes with 428 tests.

| Phase | What | State |
|---|---|---|
| 0 | Skeleton, dependencies, Alembic | done |
| 1 | Domain model | done |
| 2 | Storage, migrations, repositories | done |
| 3 | Plugin SDK and host, ingestion, CLI, demo plugin | done |
| 4 | Web UI (devices catalogue, device panel, live updates) | done |
| 5 | Real plugins: ARP sweep, ARP listener, DHCP sniffer, MAC vendor lookup, Technitium | done |
| 6 | Settings page, live plugin reload, presence thresholds | done |
| 7 | Hardening | **next** |
| 8 | Packaging and deployment | last |


## Phase 8: Packaging and deployment (last)

- [ ] **Dockerfile.** Python 3.14 slim plus **libpcap** (scapy compiles BPF filters through it).
      Run as a non-root user with `CAP_NET_RAW` and `CAP_NET_ADMIN`.
- [ ] **Container settings.** `network_mode: host`, `NMTDS_HOST=0.0.0.0`, `NMTDS_DATA_DIR` on a
      volume.
- [ ] **Release pipeline.** Build and publish the image to GHCR from the cookie-pyrate release
      workflow; pin the tag in the homelab stack.
- [ ] **Homelab stack.** New stack in the homelab repo following its own rules (compose template,
      app data under the home directory, Technitium token through SOPS, backups).
- [ ] **Run next to NetAlertX** for about a week, compare, then retire NetAlertX.
- [ ] **Tune device classification with real devices.** Moved from Phase 7: needs real data.
      `domain/devices/classification.py` was written from guesses; adjust with what the week next
      to NetAlertX shows (misnamed devices, wrong categories).
- [ ] **Resource check on the server.** Target under ~100 MB RAM and near-zero idle CPU on the
      4-core Celeron. Measure with real traffic for a day.
- [ ] **Verify Technitium against the real server.** The endpoint (`/api/dhcp/leases/list`), the
      token query parameter and the response shape come from Technitium's docs, not from a live
      call.

## Backlog (after the first release)

- "Forget device" action in the UI.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
