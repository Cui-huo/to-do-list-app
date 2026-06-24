"""特征测试 — 持久化格式（P1）。

锁住：username 纯文本、样式 JSON、模版种子、completed_at NULL。
对应 spec: p1_persistence.md CT-P1-01 ~ CT-P1-05
"""

import json
import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService


@pytest.fixture
def svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


class TestUsernamePlainText:
    """现状：username 以纯文本存储，不经 json。CT-P1-01"""

    def test_username_stored_as_plain_text_current_behavior(self, db_conn):
        """现状：username 的 value 是纯文本字符串 '李四'，不是 '"李四"'。"""
        init_db(db_conn)
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('username', ?)",
            ("李四",),
        )
        db_conn.commit()

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='username'"
        ).fetchone()
        assert row["value"] == "李四"

        # 验证不是合法 JSON
        with pytest.raises((json.JSONDecodeError, TypeError)):
            json.loads(row["value"])

    def test_username_not_json_encapsulated_current_behavior(self, db_conn):
        """现状：username 存储与 sort_preference 格式不同。
        sort_preference 是 '"updated_at"'（JSON 字符串），username 是 '张三'（纯文本）。
        """
        init_db(db_conn)
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('username', ?)",
            ("张三",),
        )
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('sort_preference', ?)",
            (json.dumps("updated_at"),),
        )
        db_conn.commit()

        u = db_conn.execute("SELECT value FROM UserSettings WHERE key='username'").fetchone()
        s = db_conn.execute("SELECT value FROM UserSettings WHERE key='sort_preference'").fetchone()
        assert u["value"] == "张三"
        assert s["value"] == '"updated_at"'


class TestTextStyleJson:
    """现状：文字样式以 JSON 字典存储。CT-P1-02"""

    def test_style_stored_as_json_dict_current_behavior(self, db_conn):
        """现状：style key 的 value 是 JSON 对象。"""
        init_db(db_conn)
        style = {
            "color": [1, 0.85, 0.4, 1],
            "font_size": "20sp",
            "font": "AlimamaDongFangDaKai",
            "bold": False,
        }
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
            ("username_style", json.dumps(style)),
        )
        db_conn.commit()

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='username_style'"
        ).fetchone()
        loaded = json.loads(row["value"])
        assert loaded["color"] == [1, 0.85, 0.4, 1]
        assert loaded["font_size"] == "20sp"
        assert loaded["font"] == "AlimamaDongFangDaKai"
        assert loaded["bold"] is False

    def test_style_with_null_color_current_behavior(self, db_conn):
        """现状：color 可以为 null。"""
        init_db(db_conn)
        style = {"color": None, "font_size": "16sp", "font": "", "bold": True}
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
            ("test_style", json.dumps(style)),
        )
        db_conn.commit()

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='test_style'"
        ).fetchone()
        loaded = json.loads(row["value"])
        assert loaded["color"] is None


class TestTemplatePersistence:
    """现状：模版以 JSON 数组存储，首次自动写入种子。CT-P1-03"""

    def test_template_seed_data_structure_current_behavior(self):
        """现状：_BUILTIN_TEMPLATES 含 2 套模版。"""
        from app_tool.ui.main_screen import _BUILTIN_TEMPLATES
        assert len(_BUILTIN_TEMPLATES) == 2
        assert _BUILTIN_TEMPLATES[0]["name"] == "默认风格"
        assert _BUILTIN_TEMPLATES[0]["builtin"] is True
        assert _BUILTIN_TEMPLATES[1]["name"] == "个人审美"
        assert "light" in _BUILTIN_TEMPLATES[0]
        assert "dark" in _BUILTIN_TEMPLATES[0]

    def test_templates_stored_as_json_array_current_behavior(self, db_conn):
        """现状：text_templates 的 value 是 JSON 数组。"""
        init_db(db_conn)
        from app_tool.ui.main_screen import _BUILTIN_TEMPLATES
        templates = list(_BUILTIN_TEMPLATES)
        db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('text_templates', ?)",
            (json.dumps(templates),),
        )
        db_conn.commit()

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='text_templates'"
        ).fetchone()
        loaded = json.loads(row["value"])
        assert isinstance(loaded, list)
        assert len(loaded) == 2


class TestMarkIncompleteClearsCompletedAt:
    """现状：mark_incomplete 将 completed_at 设为 NULL。CT-P1-05"""

    def test_mark_incomplete_clears_completed_at_current_behavior(self, svc):
        """现状：取消完成后 completed_at 为 None。"""
        note = svc.create(title="测试", content="内容")
        svc.mark_complete(note.id)

        completed = svc.get_by_id(note.id)
        assert completed.is_completed == 1
        assert completed.completed_at is not None

        svc.mark_incomplete(note.id)
        incomplete = svc.get_by_id(note.id)
        assert incomplete.is_completed == 0
        assert incomplete.completed_at is None

    def test_mark_complete_sets_completed_at_current_behavior(self, svc):
        """现状：完成时 completed_at 设为当前时间。"""
        note = svc.create(title="测试", content="内容")
        svc.mark_complete(note.id)

        completed = svc.get_by_id(note.id)
        assert completed.is_completed == 1
        assert completed.completed_at is not None
        assert completed.completed_at != ""
