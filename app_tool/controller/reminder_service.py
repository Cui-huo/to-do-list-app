"""提醒服务：CRUD + 触发管理。P0 Desktop 版（threading.Timer）。"""

import sqlite3
from datetime import datetime
from app_tool.model.models import Reminder
from app_tool.config import MAX_REMINDERS_PER_NOTE


class ReminderService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, note_id: int, remind_at: str) -> Reminder:
        # 校验便签存在
        note = self.conn.execute(
            "SELECT id FROM Note WHERE id=?", (note_id,)
        ).fetchone()
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")

        # spec §5.7: 允许过去/未来任意时间（过去时间立即触发）

        # 校验数量上限
        count = self.conn.execute(
            "SELECT COUNT(*) FROM Reminder WHERE note_id=?", (note_id,)
        ).fetchone()[0]
        if count >= MAX_REMINDERS_PER_NOTE:
            raise ValueError(f"每条便签最多 {MAX_REMINDERS_PER_NOTE} 个提醒")

        cursor = self.conn.execute(
            "INSERT INTO Reminder (note_id, remind_at) VALUES (?, ?)",
            (note_id, remind_at),
        )
        self.conn.commit()
        return Reminder(
            id=cursor.lastrowid,
            note_id=note_id,
            remind_at=remind_at,
            is_triggered=0,
        )

    def delete(self, reminder_id: int) -> None:
        existing = self.get_by_id(reminder_id)
        if existing is None:
            raise ValueError(f"提醒 ID={reminder_id} 不存在")
        self.conn.execute("DELETE FROM Reminder WHERE id=?", (reminder_id,))
        self.conn.commit()

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        return self._row_to_reminder(
            self.conn.execute(
                "SELECT * FROM Reminder WHERE id=?", (reminder_id,)
            ).fetchone()
        )

    def get_for_note(self, note_id: int) -> list[Reminder]:
        rows = self.conn.execute(
            "SELECT * FROM Reminder WHERE note_id=? ORDER BY remind_at",
            (note_id,),
        ).fetchall()
        return [self._row_to_reminder(r) for r in rows]  # type: ignore[return-value]

    def trigger(self, reminder_id: int) -> None:
        self.conn.execute(
            "UPDATE Reminder SET is_triggered=1 WHERE id=?", (reminder_id,)
        )
        self.conn.commit()

    def get_pending(self) -> list[Reminder]:
        rows = self.conn.execute(
            "SELECT * FROM Reminder WHERE is_triggered=0 ORDER BY remind_at"
        ).fetchall()
        return [self._row_to_reminder(r) for r in rows]  # type: ignore[return-value]

    @staticmethod
    def _row_to_reminder(row: sqlite3.Row | None) -> Reminder | None:
        if row is None:
            return None
        return Reminder(
            id=row["id"],
            note_id=row["note_id"],
            remind_at=row["remind_at"],
            is_triggered=row["is_triggered"],
        )
