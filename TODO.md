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

## Phase 7: Hardening

- [ ] **Data retention.** Presence intervals and events grow forever. Add a retention setting
      (e.g. 90 days) and a daily prune. Decide whether facts and detections of devices not seen
      for a long time should also go, or whether "forget device" is a separate, manual action.
- [ ] **One shared packet capture.** The ARP listener and DHCP sniffer each open their own raw
      socket. Replace with one capture per interface that fans packets out to listeners.
- [ ] **Targeted ARP sweeps.** The original plan: sweep only devices not heard from recently every
      few minutes, and the full subnet less often. Today every sweep covers the full subnet.
- [ ] **Resource check on the server.** Target under ~100 MB RAM and near-zero idle CPU on the
      4-core Celeron. Measure with real traffic for a day.
- [ ] **`pytest-timeout`.** Add it as a dev dependency with a suite-wide timeout. A single hung
      async test currently blocks `make qa` with no output.
- [ ] **Tune device classification with real devices.** `domain/devices/classification.py` was
      written from guesses; adjust with what the real network shows (misnamed devices, wrong
      categories).
- [ ] **Verify Technitium against the real server.** The endpoint (`/api/dhcp/leases/list`), the
      token query parameter and the response shape come from Technitium's docs, not from a live
      call.
- [ ] **Check dark mode.** All screenshots so far were light mode.
- [ ] **Check the NetAlertX link in the footer** (`github.com/jokob-sk/NetAlertX` may have moved).
- [ ] **CLI changes vs a running server.** `nmtds plugins set/enable` write the database but cannot
      reload a running `serve`. Either document it (current message says "restart") or add a small
      local admin endpoint the CLI can call.
- [ ] **Remove or fill `web/api/v1`.** Still an empty package from the skeleton. Fill it if a JSON
      API is wanted (alerts, Home Assistant), otherwise delete it.

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

## Backlog (after the first release)

- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- IPv6 neighbour discovery.
- "Forget device" action in the UI.

## Open questions

- **Access control:** LAN-only without login, or behind a reverse proxy with authentication?
- **Alert channel:** where should "new device" notifications go?
- **License:** `pyproject.toml` says MIT; confirm before making the repository public.
