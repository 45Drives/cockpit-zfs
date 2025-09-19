import sqlite3
from pathlib import Path

DB_PATH = "/var/lib/sqlite/45drives/notifications.db"
EXPECTED_COLUMNS = {
    "id", "timestamp", "event", "pool", "vdev", "state", "health", "guid",
    "severity", "received", "fileSystem", "snapShot", "replicationDestination"
}

def setup_database():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if notifications table exists
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'
    """)
    table_exists = cursor.fetchone() is not None

    def get_existing_columns():
        cursor.execute("PRAGMA table_info(notifications)")
        return {row[1] for row in cursor.fetchall()}

    if table_exists:
        existing_columns = get_existing_columns()
        if existing_columns != EXPECTED_COLUMNS:
            print("Schema mismatch detected. Rebuilding 'notifications' table...")

            cursor.execute("ALTER TABLE notifications RENAME TO notifications_old")

            cursor.execute("""
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event TEXT NOT NULL,
                pool TEXT,
                vdev TEXT,
                state TEXT,
                health TEXT,
                guid TEXT,
                errors TEXT,
                severity TEXT DEFAULT 'info' CHECK(severity IN ('info', 'warning', 'error')),
                received INTEGER DEFAULT 0,
                fileSystem TEXT,
                snapShot TEXT,
                replicationDestination TEXT
            )
            """)

            shared_columns = existing_columns & EXPECTED_COLUMNS
            cols_str = ", ".join(shared_columns)
            cursor.execute(f"""
                INSERT INTO notifications ({cols_str})
                SELECT {cols_str} FROM notifications_old
            """)

            cursor.execute("DROP TABLE notifications_old")
        else:
            print("'notifications' table is up to date.")
    else:
        print("Creating new 'notifications' table")
        cursor.execute("""
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event TEXT NOT NULL,
            pool TEXT,
            vdev TEXT,
            state TEXT,
            health TEXT,
            guid TEXT,
            errors TEXT,
            severity TEXT DEFAULT 'info' CHECK(severity IN ('info', 'warning', 'error')),
            received INTEGER DEFAULT 0,
            fileSystem TEXT,
            snapShot TEXT,
            replicationDestination TEXT
        )
        """)

    # Create warning_levels table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warning_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL UNIQUE,
        severity TEXT NOT NULL CHECK(severity IN ('info', 'warning', 'critical'))
    )
    """)

    defaults = {
        "scrubFinish": "info",
        "vdevCleared": "info",
        "resilverFinish": "info",
        "clearPoolErrors": "info",
        "snapshotCreation": "info",
        "snapshotFailure": "warning",
        "stateChange": "critical",
        "storageThreshold": "warning",
        "poolImport": "info",
        "replicationTaskFailure": "warning"
    }

    for event_type, severity in defaults.items():
        cursor.execute("""
            INSERT OR IGNORE INTO warning_levels (event_type, severity)
            VALUES (?, ?)
        """, (event_type, severity))

    # Create smtp_settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smtp_settings (
        id INTEGER PRIMARY KEY,
        send_info INTEGER DEFAULT 0,
        send_warning INTEGER DEFAULT 1,
        send_critical INTEGER DEFAULT 1
    )
    """)
    cursor.execute("""
    INSERT OR IGNORE INTO smtp_settings (id, send_info, send_warning, send_critical)
    VALUES (1, 0, 1, 1)
    """)

    # Create index on 'received' column for fast unread count queries
    print("Ensuring index on 'received' column...")
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_notifications_received
    ON notifications (received)
    """)

    conn.commit()
    conn.close()

# Run the setup
setup_database()
