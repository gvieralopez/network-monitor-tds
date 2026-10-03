# Command line

Everything is under one command, `nmtds`. It uses the same environment variables as the server (see [Configuration](configuration.md)), so set `NMTDS_DATA_DIR` the same way for both.

| Command | What it does |
|---|---|
| `nmtds serve` | Runs the monitor and the web interface. Stop it with Ctrl+C. |
| `nmtds version` | Shows the installed version. |
| `nmtds db upgrade` | Migrates the database to the latest schema. `serve` does this by itself. |
| `nmtds db current` | Shows the database's schema version without changing anything. |
| `nmtds plugins list` | Lists installed plugins and whether each is on. |
| `nmtds plugins enable <id>` | Turns a plugin on. |
| `nmtds plugins disable <id>` | Turns a plugin off. |
| `nmtds plugins show <id>` | Shows a plugin's settings. Secrets are masked. |
| `nmtds plugins set <id> key=value …` | Changes plugin settings, checking them first. |

Durations on the command line use seconds or ISO 8601, for example `interval=600` or `interval=PT10M`. (The Settings page also accepts `10m`, `30s` or `1h30m`.)

Changes made with the command line are stored straight away, but a running `nmtds serve` only picks them up after a restart. Changes made on the Settings page apply immediately.
