import os
import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    chat_id     INTEGER NOT NULL,
                    query       TEXT    NOT NULL,
                    areas       TEXT    NOT NULL DEFAULT '1,2',
                    period      INTEGER NOT NULL DEFAULT 3,
                    level_filter TEXT   DEFAULT '',
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sent_vacancies (
                    chat_id INTEGER NOT NULL,
                    url     TEXT    NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, url)
                );
            """)

    def add_subscription(self, user_id: int, chat_id: int, query: str,
                         areas: str, period: int, level_filter: str) -> int | None:
        with self._conn() as conn:
            try:
                cur = conn.execute(
                    """INSERT INTO subscriptions (user_id, chat_id, query, areas, period, level_filter)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, chat_id, query, areas, period, level_filter),
                )
                return cur.lastrowid
            except sqlite3.IntegrityError:
                return None

    def remove_subscription(self, sub_id: int, user_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
                (sub_id, user_id),
            )
            return cur.rowcount > 0

    def get_subscriptions(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, user_id, chat_id, query, areas, period, level_filter, created_at
                   FROM subscriptions ORDER BY id"""
            ).fetchall()
            return [
                {
                    "id": r[0], "user_id": r[1], "chat_id": r[2],
                    "query": r[3], "areas": r[4], "period": r[5],
                    "level_filter": r[6], "created_at": r[7],
                }
                for r in rows
            ]

    def get_user_subscriptions(self, user_id: int) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, user_id, chat_id, query, areas, period, level_filter, created_at
                   FROM subscriptions WHERE user_id = ? ORDER BY id""",
                (user_id,),
            ).fetchall()
            return [
                {
                    "id": r[0], "user_id": r[1], "chat_id": r[2],
                    "query": r[3], "areas": r[4], "period": r[5],
                    "level_filter": r[6], "created_at": r[7],
                }
                for r in rows
            ]

    def is_sent(self, chat_id: int, url: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM sent_vacancies WHERE chat_id = ? AND url = ?",
                (chat_id, url),
            ).fetchone()
            return row is not None

    def mark_sent(self, chat_id: int, url: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sent_vacancies (chat_id, url) VALUES (?, ?)",
                (chat_id, url),
            )

    def cleanup(self, days: int = 90):
        with self._conn() as conn:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            conn.execute(
                "DELETE FROM sent_vacancies WHERE sent_at < ?",
                (cutoff,),
            )
