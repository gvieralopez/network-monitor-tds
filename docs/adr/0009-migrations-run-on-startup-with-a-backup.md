# Migrations run on startup, with a backup, and never import application code

`nmtds serve` upgrades the database to the latest Alembic revision before anything else starts, after copying the file to `nmtds.db.bak-<revision>` with SQLite's backup API, and refuses to start if the database is at a revision the code does not know (an image was rolled back). Migrations ship inside the package and are configured in code, because `alembic.ini` at the repository root is not part of the installed package.

## Consequences

- An `env.py` hook renders custom column types (`UTCDateTime`, `MacAddressType` …) as the SQL type they store, so later changes to application types cannot break old migrations.
- Batch mode and a constraint naming convention are on from the first migration, because SQLite can only alter most columns by rebuilding the table.
- A test compares the migrated schema with the models, playing the role of `alembic check`.
