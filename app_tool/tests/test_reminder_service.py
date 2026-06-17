"""test_reminder_service.py — 提醒 CRUD 测试（红灯）。"""

import pytest
from datetime import datetime, timedelta


class TestReminderCRUD:
    def test_create_reminder(self, db_conn):
        """创建提醒应返回 Reminder 对象。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="提醒测试", content="内容")
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = svc.create(note_id=note.id, remind_at=future)

        assert reminder.id is not None
        assert reminder.note_id == note.id
        assert reminder.remind_at == future
        assert reminder.is_triggered == 0

    def test_create_past_time_raises(self, db_conn):
        """提醒时间在过去应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="测试", content="内容")
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        with pytest.raises(ValueError):
            svc.create(note_id=note.id, remind_at=past)

    def test_create_nonexistent_note_raises(self, db_conn):
        """为不存在的便签创建提醒应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        svc = ReminderService(db_conn)

        future = (datetime.now() + timedelta(hours=1)).isoformat()
        with pytest.raises(ValueError):
            svc.create(note_id=999, remind_at=future)

    def test_max_three_reminders_per_note(self, db_conn):
        """每条便签最多 3 个提醒，超过抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="提醒上限", content="内容")
        for i in range(3):
            future = (datetime.now() + timedelta(hours=i + 1)).isoformat()
            svc.create(note_id=note.id, remind_at=future)

        future = (datetime.now() + timedelta(hours=4)).isoformat()
        with pytest.raises(ValueError):
            svc.create(note_id=note.id, remind_at=future)

    def test_delete_reminder(self, db_conn):
        """删除提醒应从数据库移除。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="删除提醒", content="内容")
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = svc.create(note_id=note.id, remind_at=future)
        svc.delete(reminder.id)

        assert svc.get_by_id(reminder.id) is None

    def test_delete_nonexistent_reminder_raises(self, db_conn):
        """删除不存在的提醒应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        svc = ReminderService(db_conn)
        with pytest.raises(ValueError):
            svc.delete(999)

    def test_get_reminders_for_note(self, db_conn):
        """获取某便签的所有提醒。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="多提醒", content="内容")
        t1 = (datetime.now() + timedelta(hours=1)).isoformat()
        t2 = (datetime.now() + timedelta(hours=2)).isoformat()

        svc.create(note_id=note.id, remind_at=t1)
        svc.create(note_id=note.id, remind_at=t2)

        reminders = svc.get_for_note(note.id)
        assert len(reminders) == 2

    def test_cascade_delete_on_note_delete(self, db_conn):
        """删除便签应级联删除其提醒。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="级联测试", content="内容")
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = svc.create(note_id=note.id, remind_at=future)

        note_svc.delete(note.id)
        assert svc.get_by_id(reminder.id) is None


class TestReminderTrigger:
    def test_trigger_reminder(self, db_conn):
        """触发提醒设置 is_triggered=1。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="触发测试", content="内容")
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        reminder = svc.create(note_id=note.id, remind_at=future)

        svc.trigger(reminder.id)
        updated = svc.get_by_id(reminder.id)
        assert updated is not None
        assert updated.is_triggered == 1

    def test_get_pending_reminders(self, db_conn):
        """获取未触发的提醒列表。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.reminder_service import ReminderService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = ReminderService(db_conn)

        note = note_svc.create(title="待触发", content="内容")
        t1 = (datetime.now() + timedelta(hours=1)).isoformat()
        t2 = (datetime.now() + timedelta(hours=2)).isoformat()

        r1 = svc.create(note_id=note.id, remind_at=t1)
        r2 = svc.create(note_id=note.id, remind_at=t2)
        svc.trigger(r1.id)

        pending = svc.get_pending()
        assert len(pending) == 1
        assert pending[0].id == r2.id
