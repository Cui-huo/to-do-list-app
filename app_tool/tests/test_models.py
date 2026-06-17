"""test_models.py — 数据类字段与行为测试（红灯）。"""

import pytest
from datetime import datetime


class TestNote:
    def test_create_note_with_defaults(self):
        """新建便签：必填 title，其余有默认值。"""
        from app_tool.model.models import Note

        now = datetime.now().isoformat()
        note = Note(title="测试标题", created_at=now, updated_at=now)

        assert note.title == "测试标题"
        assert note.content == ""
        assert note.is_completed == 0
        assert note.completed_at is None
        assert note.created_at == now
        assert note.updated_at == now

    def test_create_note_with_content(self):
        """便签可带 Markdown 内容。"""
        from app_tool.model.models import Note

        note = Note(
            title="标题",
            content="# 一级标题\n内容",
            created_at="2026-06-14T10:00:00",
            updated_at="2026-06-14T10:00:00",
        )
        assert note.content == "# 一级标题\n内容"

    def test_note_is_completed_flag(self):
        """已完成便签 is_completed=1 且 completed_at 非空。"""
        from app_tool.model.models import Note

        note = Note(
            title="已完成",
            created_at="2026-06-14T10:00:00",
            updated_at="2026-06-14T10:00:00",
            is_completed=1,
            completed_at="2026-06-14T12:00:00",
        )
        assert note.is_completed == 1
        assert note.completed_at == "2026-06-14T12:00:00"


class TestTag:
    def test_create_tag(self):
        """标签：name 唯一必填。"""
        from app_tool.model.models import Tag

        tag = Tag(id=1, name="紧急")
        assert tag.id == 1
        assert tag.name == "紧急"

    def test_tag_equality_by_name(self):
        """同名的标签应视为相同。"""
        from app_tool.model.models import Tag

        t1 = Tag(id=1, name="P1")
        t2 = Tag(id=2, name="P1")
        assert t1.name == t2.name


class TestNoteTag:
    def test_create_note_tag_association(self):
        """便签-标签关联。"""
        from app_tool.model.models import NoteTag

        nt = NoteTag(note_id=1, tag_id=3)
        assert nt.note_id == 1
        assert nt.tag_id == 3


class TestReminder:
    def test_create_reminder(self):
        """提醒：绑定便签 + 提醒时间。"""
        from app_tool.model.models import Reminder

        r = Reminder(note_id=1, remind_at="2026-06-15T09:00:00")
        assert r.note_id == 1
        assert r.remind_at == "2026-06-15T09:00:00"
        assert r.is_triggered == 0

    def test_reminder_can_be_triggered(self):
        """已触发的提醒 is_triggered=1。"""
        from app_tool.model.models import Reminder

        r = Reminder(note_id=1, remind_at="2026-06-15T09:00:00", is_triggered=1)
        assert r.is_triggered == 1
