"""特征测试 — ReminderService 行为（P2）。

锁住：提醒创建不校验时间格式/范围。
对应 spec: p2_crosscutting.md CT-P2-03
"""

import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.reminder_service import ReminderService
from app_tool.config import MAX_REMINDERS_PER_NOTE


@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def rem_svc(db_conn):
    return ReminderService(db_conn)


class TestReminderNoTimeValidation:
    """现状：create() 接受任意 remind_at 字符串。CT-P2-03"""

    def test_reminder_accepts_past_time_current_behavior(self, note_svc, rem_svc):
        """现状：过去时间不报错。"""
        note = note_svc.create(title="测试", content="内容")
        reminder = rem_svc.create(note.id, "2020-01-01T00:00:00")
        assert reminder.id is not None
        assert reminder.remind_at == "2020-01-01T00:00:00"

    def test_reminder_accepts_future_time_current_behavior(self, note_svc, rem_svc):
        """现状：未来时间不报错。"""
        note = note_svc.create(title="测试", content="内容")
        reminder = rem_svc.create(note.id, "2099-12-31T23:59:59")
        assert reminder.id is not None

    def test_reminder_accepts_arbitrary_string_current_behavior(self, note_svc, rem_svc):
        """现状：非时间格式字符串不报错。"""
        note = note_svc.create(title="测试", content="内容")
        reminder = rem_svc.create(note.id, "根本不是时间格式")
        assert reminder.id is not None
        assert reminder.remind_at == "根本不是时间格式"

    def test_reminder_accepts_empty_string_current_behavior(self, note_svc, rem_svc):
        """现状：空字符串不报错。"""
        note = note_svc.create(title="测试", content="内容")
        reminder = rem_svc.create(note.id, "")
        assert reminder.id is not None
        assert reminder.remind_at == ""


class TestReminderLimits:
    """现状：数量上限和便签存在校验。"""

    def test_reminder_limit_per_note_current_behavior(self, note_svc, rem_svc):
        """现状：超过 MAX_REMINDERS_PER_NOTE 个提醒时报错。"""
        note = note_svc.create(title="测试", content="内容")
        for i in range(MAX_REMINDERS_PER_NOTE):
            rem_svc.create(note.id, f"2026-06-{i+1:02d}T12:00:00")

        with pytest.raises(ValueError, match="最多"):
            rem_svc.create(note.id, "2026-06-30T12:00:00")

    def test_reminder_requires_existing_note_current_behavior(self, note_svc, rem_svc):
        """现状：不存在的便签 ID 报错。"""
        with pytest.raises(ValueError, match="不存在"):
            rem_svc.create(99999, "2026-06-24T12:00:00")


class TestReminderCRUD:
    """现状：提醒的增删查行为。"""

    def test_get_pending_returns_untriggered_current_behavior(self, note_svc, rem_svc):
        """现状：get_pending() 只返回 is_triggered=0 的提醒。"""
        note = note_svc.create(title="测试", content="内容")
        r1 = rem_svc.create(note.id, "2026-01-01T00:00:00")
        r2 = rem_svc.create(note.id, "2026-06-01T00:00:00")
        rem_svc.trigger(r1.id)

        pending = rem_svc.get_pending()
        pending_ids = [r.id for r in pending]
        assert r1.id not in pending_ids  # 已触发
        assert r2.id in pending_ids       # 未触发

    def test_trigger_sets_is_triggered_current_behavior(self, note_svc, rem_svc):
        """现状：trigger() 将 is_triggered 设为 1。"""
        note = note_svc.create(title="测试", content="内容")
        r = rem_svc.create(note.id, "2026-06-24T12:00:00")
        assert r.is_triggered == 0

        rem_svc.trigger(r.id)
        updated = rem_svc.get_by_id(r.id)
        assert updated.is_triggered == 1
