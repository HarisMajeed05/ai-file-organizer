"""Small SQLite store for duplicate detection and unique file names."""
import sqlite3
from .config import DATA_DIR

_conn = sqlite3.connect(DATA_DIR / "state.db", check_same_thread=False)
_conn.execute(
    "CREATE TABLE IF NOT EXISTS files (sha TEXT PRIMARY KEY, category TEXT, name TEXT)"
)
_conn.commit()


def find_duplicate(sha):
    row = _conn.execute("SELECT category, name FROM files WHERE sha=?", (sha,)).fetchone()
    return row


def unique_name(category, name):
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    candidate, n = name, 1
    while _conn.execute(
        "SELECT 1 FROM files WHERE category=? AND name=?", (category, candidate)
    ).fetchone():
        n += 1
        candidate = f"{stem}_{n}.{ext}" if ext else f"{stem}_{n}"
    return candidate


def register(sha, category, name):
    _conn.execute("INSERT OR REPLACE INTO files VALUES (?,?,?)", (sha, category, name))
    _conn.commit()
