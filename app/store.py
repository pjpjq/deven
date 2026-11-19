"""Single-instance SQLite storage for user preferences and Telegram file IDs."""
import sqlite3
from pathlib import Path

MODELS = {"flare": "gpt-image-2.6-flare", "sunburst": "gpt-image-2.6-sunburst"}
MAX_REFS = 4


class Store:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    model TEXT NOT NULL DEFAULT 'flare',
                    last_image TEXT
                );
                CREATE TABLE IF NOT EXISTS refs (
                    user_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    PRIMARY KEY (user_id, position)
                );
            """)

    def _db(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def get_model(self, user_id: int) -> str:
        with self._db() as conn:
            row = conn.execute("SELECT model FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else "flare"

    def set_model(self, user_id: int, model: str):
        if model not in MODELS:
            raise ValueError("Unsupported model")
        with self._db() as conn:
            conn.execute(
                "INSERT INTO users(user_id, model) VALUES (?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET model=excluded.model",
                (user_id, model),
            )

    def add_ref(self, user_id: int, file_id: str, filename: str):
        with self._db() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(position), 0) FROM refs WHERE user_id=?", (user_id,)
            ).fetchone()
            index = row[0] + 1
            conn.execute(
                "INSERT INTO refs(user_id, position, file_id, filename) VALUES (?,?,?,?)",
                (user_id, index, file_id, filename),
            )
            # Keep most recent reference images.
            conn.execute(
                "DELETE FROM refs WHERE user_id=? AND position NOT IN "
                "(SELECT position FROM refs WHERE user_id=? ORDER BY position DESC LIMIT ?)",
                (user_id, user_id, MAX_REFS),
            )

    def get_refs(self, user_id: int) -> list[tuple[str, str]]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT file_id, filename FROM refs WHERE user_id=? ORDER BY position",
                (user_id,),
            ).fetchall()
        return [(str(fid), str(name)) for fid, name in rows]

    def clear_refs(self, user_id: int):
        with self._db() as conn:
            conn.execute("DELETE FROM refs WHERE user_id=?", (user_id,))

    def get_last_image(self, user_id: int) -> str | None:
        with self._db() as conn:
            row = conn.execute("SELECT last_image FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else None

    def set_last_image(self, user_id: int, file_id: str):
        with self._db() as conn:
            conn.execute(
                "INSERT INTO users(user_id, last_image) VALUES (?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET last_image=excluded.last_image",
                (user_id, file_id),
            )
