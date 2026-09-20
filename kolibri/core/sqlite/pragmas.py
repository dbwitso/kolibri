CONNECTION_PRAGMAS = (
    "PRAGMA wal_autocheckpoint=500; "
    "PRAGMA legacy_alter_table = ON; "
    # NORMAL is safe (unlike OFF) under WAL: SQLite still syncs at every
    # checkpoint, it just skips the extra fsync after each transaction commit.
    "PRAGMA synchronous=NORMAL; "
    # Let SQLite retry internally on SQLITE_BUSY instead of failing
    # immediately when another connection briefly holds the write lock.
    "PRAGMA busy_timeout=10000; "
    # Negative value = size in KiB (~64MB) rather than a page count.
    "PRAGMA cache_size=-64000;"
)

START_PRAGMAS = "PRAGMA journal_mode=WAL;"
