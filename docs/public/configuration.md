# Configuration

Only what is needed to start the monitor is configured with environment variables. Everything else (plugins, their settings, presence thresholds) is changed on the Settings page and stored in the database.

| Variable | Default | Meaning |
|---|---|---|
| `NMTDS_DATA_DIR` | `data` | Folder for the database and its backups. Created if missing. |
| `NMTDS_HOST` | `127.0.0.1` | Address the web interface listens on. Use `0.0.0.0` to reach it from other machines. |
| `NMTDS_PORT` | `8000` | Port of the web interface. |
| `NMTDS_OBSERVATION_QUEUE_SIZE` | `1000` | How many observations can wait to be stored. Rarely needs changing. |
| `NMTDS_EVENT_QUEUE_SIZE` | `100` | How many live updates can wait per open browser tab. Rarely needs changing. |

`.env.example` lists them all. `make run` starts the server with the variables from `.env`.

There is no login. Keep `NMTDS_HOST` on `127.0.0.1`, or put the monitor behind a reverse proxy with authentication, unless you trust everyone on the network.
