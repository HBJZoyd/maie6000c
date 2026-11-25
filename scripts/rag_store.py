"""Durable completed-result replay. A crash before commit can still repeat inference."""

import json
import sqlite3
import time
from pathlib import Path


class ResultStore:
    def __init__(self, path, ttl=86400, max_results=1000):
        self.path, self.ttl, self.max_results = Path(path), ttl, max_results
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS results "
                       "(key TEXT PRIMARY KEY, created REAL NOT NULL, payload TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def get(self, key):
        with self.connect() as db:
            row = db.execute("SELECT created, payload FROM results WHERE key=?", (key,)).fetchone()
        return json.loads(row[1]) if row and time.time() - row[0] < self.ttl else None

    def put(self, key, payload):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO results VALUES (?, ?, ?)",
                       (key, time.time(), json.dumps(payload, ensure_ascii=False)))
            db.execute("DELETE FROM results WHERE created < ?", (time.time() - self.ttl,))
            db.execute("DELETE FROM results WHERE key NOT IN "
                       "(SELECT key FROM results ORDER BY created DESC LIMIT ?)",
                       (self.max_results,))
