# TODO

Where the project stands and what is left.

## Status (2026-10-04)

The app is feature-complete for the first release on the `first-release` branch (not merged into
`main`). `make qa` passes with 484 tests.

## 1. Pullable image

Everything until there is a Docker image in a registry that the homelab can pull. In this order:
the merge cuts a release, so the image publishing must be in place before it.

Where things stand (checked 2026-10-04):

- The repo is public. Every push to `main` that passes QA cuts a release through cookie-pyrate
  v0.1.9. That already happened once: `v0.1.0` is the skeleton, and `origin/main` was bumped to
  `0.1.1-beta0`.
- `RELEASE_SSH_KEY` and its deploy key exist. `main` is protected by a ruleset: changes go through a
  PR, merge commits only, and the `qa / Run QA` check is required.
- The default workflow token is read-only, so any job that pushes to GHCR must ask for
  `packages: write` itself. No extra secret is needed, `GITHUB_TOKEN` can push to GHCR.
- cookie-pyrate's `reusable-release.yml` has no Docker step, and it declares no workflow-level
  outputs, so a job in this repo cannot read the released version or tag.

Steps:

- [ ] **Fix the Dockerfile.** The current one is the template's, unchanged:
      - `CMD ["nmtds"]` only prints help; it must be `["nmtds", "serve"]`.
      - Nothing excludes `data/` in `.dockerignore`, so `COPY . /app` bakes the local `nmtds.db` into
        the image. Add `data/` and `.coverage`.
      - Install `libpcap0.8` in the runtime stage (scapy compiles BPF filters through it).
      - Run as a non-root user. Docker's `cap_add` does not give a non-root process any effective
        capabilities on its own, so add file capabilities to the interpreter in the image
        (`setcap cap_net_raw,cap_net_admin+eip` on the real `python3.14` binary, via `libcap2-bin`).
        This is safe here because, unlike on a dev machine, nothing else shares that interpreter.
      - Defaults for the container: `NMTDS_HOST=0.0.0.0`, `NMTDS_DATA_DIR=/data`, `VOLUME /data`,
        `EXPOSE 8000`.
      - Check it locally with `make dockerimage` and a run with host networking.
- [ ] **Extend cookie-pyrate.** Add an optional `publish-docker-image` input (plus `docker-platforms`,
      default `linux/amd64`) to `reusable-release.yml`. It adds a job that runs after `release`, checks
      out the released commit, logs in to GHCR with `GITHUB_TOKEN`, and pushes
      `ghcr.io/<owner>/<repo>` tagged with the version and `latest`. Use `docker/metadata-action`
      so the image is labelled with its source repo. The template already ships a Dockerfile and
      `make dockerimage`, so this belongs in cookie-pyrate rather than here. Tag a new cookie-pyrate
      release (v0.1.10).
- [ ] **Use it here.** Move `qa.yml` and `release.yml` to the new cookie-pyrate tag (both the
      `uses: …@` ref and `cookie-pyrate-ref`), set `publish-docker-image: true`, and add
      `packages: write` to the release job's permissions.
- [ ] **Document running the container.** A compose example in `docs/public/` with
      `network_mode: host`, `cap_add: [NET_RAW, NET_ADMIN]`, the `/data` volume and the no-login
      warning. `capture-permissions.md` already has the capabilities part.
- [ ] **Merge `first-release` into `main`** through a PR:
      - The version line in `pyproject.toml` and `src/network_monitor_tds/__init__.py` conflicts with
        `main`'s bump to `0.1.1-beta0`. Nothing else conflicts.
      - Decide the version while resolving it: keeping `0.1.1-beta0` releases this as `v0.1.1`;
        setting `0.2.0-beta0` releases it as `v0.2.0`, which better marks the first usable release.
      - QA has never run on GitHub for this branch, so the PR's check may show CI-only problems.
      - Merging cuts the release and, after the steps above, publishes the first image.
- [ ] **Make the image pullable.** GHCR packages start private. Either make the package public in
      its GitHub settings, or give the homelab a token with `read:packages`. Check that the package
      is linked to this repo.

## 2. Homelab testing

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

## 3. Later releases

- "Forget device" action in the UI.
- Merge duplicate devices caused by randomized MACs (same hostname or DHCP fingerprint).
- New-device alerts (channel not decided; Telegram is a candidate).
- More discovery plugins: mDNS/Bonjour, SSDP/UPnP, ping sweep, opt-in nmap port scan.
