# Data, upgrades and backups

All data lives in one SQLite database, `nmtds.db`, in the data folder (`NMTDS_DATA_DIR`, `./data` by default): devices, what each plugin learned about them, online history, events, plugin settings including the Technitium token, and presence thresholds.

## How long history is kept

Online history and events are deleted once they are older than **Keep history for** under **Settings → General** (90 days by default, at least 14 so the device panel's two-week history is always complete). The monitor checks once when it starts and then once a day.

Devices themselves, their names, labels and what plugins learned about them are never deleted automatically, however long a device has been gone. A device that comes back after months is recognised as the same device, not reported as new.

## Upgrading

When a new version needs a new database layout, `nmtds serve` upgrades the database by itself when it starts. Before changing anything it copies the database to `nmtds.db.bak-<old version>` in the same folder.

If you go back to an older version of the monitor after an upgrade, it refuses to start rather than damage a database it does not understand. Either run the newer version again, or restore the matching backup:

```bash
cp data/nmtds.db.bak-0001 data/nmtds.db
```

`nmtds db current` shows which version a database is at.

## Backing up

Copy the whole data folder while the monitor is stopped, or use SQLite's own backup, which is safe while it runs:

```bash
sqlite3 data/nmtds.db ".backup 'nmtds-backup.db'"
```

Backups contain the Technitium token if you configured one.
