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

Split into stories, done one at a time in this order. Each story ends with `make qa` passing.

| # | Story | Size | Depends on |
|---|---|---|---|
| 1 | Housekeeping | S | none |
| 2 | Settings tabs and plugin grouping | M | none |
| 3 | Shared packet capture | L | 1 |
| 4 | Targeted ARP sweeps | M | 2, 3 |
| 5 | Data retention | M | 2 |
| 6 | JSON API (optional) | S–M | none |

### Story 1: Housekeeping

- [x] **`pytest-timeout`.** Add it as a dev dependency with a suite-wide timeout. A single hung
      async test currently blocks `make qa` with no output. Goes first because Story 3 changes
      async capture code.
- [x] **Check the NetAlertX link in the footer** (`github.com/jokob-sk/NetAlertX` may have moved to
      https://github.com/netalertx/NetAlertX).
- [ ] **Delete `web/api/v1`** if Story 6 is dropped. Still an empty package from the skeleton.

### Story 2: Settings tabs and plugin grouping

- [x] **Rework settings.** The settings view is cluttered. Add internal tabs (General, Plugins,
      maybe Presence) and group plugins by type (discovery, enrichment, integration). Done before
      Stories 4 and 5 so their new settings land straight in the new layout.

### Story 3: Shared packet capture

- [x] **One shared packet capture.** The ARP listener and DHCP sniffer each open their own raw
      socket. Replace with one capture per interface that fans packets out to listeners, building
      on `plugins/builtin/capture/`. Pure refactor: no behaviour change, must survive live plugin
      reload.

### Story 4: Targeted ARP sweeps

- [x] **Targeted ARP sweeps.** Sweep only devices not heard from recently every few minutes, and
      the full subnet less often. Today every sweep covers the full subnet. Both intervals become
      plugin settings in the Plugins tab. Done after Story 3 so a regression points at one change.

### Story 5: Data retention

- [x] **Data retention.** Presence intervals and events grow forever. Add a retention setting
      (e.g. 90 days, General tab) and a daily prune job through `application/scheduling.py`.
      Decision: retention prunes only presence intervals and events. Facts and detections stay;
      removing a device is the manual "forget device" action (backlog), so a returning device is
      never mistaken for a new one.

### Story 6: JSON API (optional)

- [ ] **Fill `web/api/v1`** if a JSON API is wanted (alerts, Home Assistant): endpoints for known
      devices and currently connected ones. Otherwise Story 1 deletes the package.

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

- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- IPv6 neighbour discovery.
- "Forget device" action in the UI.

## Open questions

- **Access control:** LAN-only without login, or behind a reverse proxy with authentication?
- **Alert channel:** where should "new device" notifications go?
- **License:** `pyproject.toml` says MIT; confirm before making the repository public.
