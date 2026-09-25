import sqlite3
from pathlib import Path


DB_PATH = Path("chat_bot.db")


class Database:
    """SQLite 数据库。"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_guid TEXT PRIMARY KEY,
                    message_content TEXT NOT NULL,
                    place INTEGER NOT NULL,
                    insert_time TEXT NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    replied INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def message_exists(self, message_guid: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT 1
                FROM messages
                WHERE message_guid = ?
                LIMIT 1
                """,
                (message_guid,),
            )

            return cursor.fetchone() is not None

    def save_message(self, message: dict):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO messages (
                    message_guid,
                    message_content,
                    place,
                    insert_time,
                    processed,
                    replied
                )
                VALUES (?, ?, ?, ?, 0, 0)
                """,
                (
                    message["messageGuid"],
                    message["messageContent"],
                    int(message["place"]),
                    message["insertTime"],
                ),
            )
            conn.commit()

    def mark_processed(self, message_guid: str):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE messages
                SET processed = 1
                WHERE message_guid = ?
                """,
                (message_guid,),
            )
            conn.commit()

    def mark_replied(self, message_guid: str):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE messages
                SET replied = 1
                WHERE message_guid = ?
                """,
                (message_guid,),
            )
            conn.commit()
    def get_recent_messages(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """获取最近的聊天记录。"""

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT
                    message_guid,
                    message_content,
                    place,
                    insert_time
                FROM messages
                ORDER BY insert_time DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [dict(row) for row in reversed(rows)]
