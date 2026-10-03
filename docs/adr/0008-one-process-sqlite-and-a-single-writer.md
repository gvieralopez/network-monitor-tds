# One process, SQLite, and a single writer

Everything (plugins, ingestion, presence checks and the web server) runs as asyncio tasks in one process, against one SQLite file in WAL mode. Plugins never write: they put observations on a bounded queue that a single ingestion task drains, so SQLite never sees competing writers and a burst of packets cannot block a listener. A separate database server or a multi-process layout would add operational weight to a homelab service whose whole data set is a few dozen devices.
