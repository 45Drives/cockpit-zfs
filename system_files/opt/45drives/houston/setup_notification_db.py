import sqlite3
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

DB_PATH = "/var/lib/sqlite/45Drives/notifications.db"

# Notification Schema
class Notification(BaseModel):
    id: Optional[int] = None
    timestamp: str
    event: str
    pool: Optional[str] = None
    vdev: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    scrub_details: Optional[str] = None
    errors: Optional[str] = None
    repaired: Optional[str] = None
    received: int = 0  # 0 = unread, 1 = read
    health: Optional[str] = None
    severity: Optional[str] = "info"

# 🟢 Create SQLite Table If Not ExistsERROR: Could not find a version that satisfies the requirement sqlite3 (from versions: none)
def setup_database():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)  # ✅ Prevents FileExistsError
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event TEXT NOT NULL,
        pool TEXT,
        vdev TEXT,
        state TEXT,
        error TEXT,
        description TEXT,
        health TEXT,
        guid TEXT,
        scrub_details TEXT,
        errors TEXT,
        repaired TEXT,
        severity TEXT DEFAULT 'info' CHECK(severity IN ('info', 'warning', 'error')),
        received INTEGER DEFAULT 0  -- 0 = Not sent to UI, 1 = Sent
    )
    """)
    
    conn.commit()
    conn.close()

setup_database()