# Plugin settings live in the database and are edited through generated forms

Environment variables only cover what is needed to start (data folder, host, port); everything a user tunes at runtime (which plugins run, their intervals and credentials, presence thresholds) lives in SQLite and is edited on the Settings page or with `nmtds plugins set`. Each plugin declares a frozen pydantic settings model, and the page builds its form from that model, so a new plugin gets a settings UI without template work, and saving restarts only that plugin.

## Consequences

- Secrets such as the Technitium token are stored in plain text in the database, and therefore in its backups. Fields declared with `repr=False` are treated as secrets: masked in the CLI, never pre-filled in forms, kept when a form leaves them blank.
- The CLI writes to the database but cannot reload a running server.
