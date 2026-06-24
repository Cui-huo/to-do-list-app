"""特征测试 — SettingsService 夜间模式持久化（P2）。

锁住：夜间模式持久化、默认 Light、R26 统一返回结构。
对应 spec: p2_crosscutting.md + characteristics_dark_mode.md DM-01
"""

import json
import pytest

from app_tool.model.database import init_db
from app_tool.controller.settings_service import SettingsService


@pytest.fixture
def svc(db_conn):
    init_db(db_conn)
    return SettingsService(db_conn)


class TestDarkModePersistence:
    """现状：夜间模式持久化到 UserSettings。DM-01, DM-05"""

    def test_default_dark_mode_is_light_current_behavior(self, svc):
        """现状：DB 无记录时默认返回 'Light'。"""
        success, theme = svc.get_dark_mode()
        assert success is True
        assert theme == "Light"

    def test_set_dark_mode_persists_current_behavior(self, svc):
        """现状：set_dark_mode 后 get_dark_mode 返回新值。"""
        svc.set_dark_mode("Dark")
        success, theme = svc.get_dark_mode()
        assert success is True
        assert theme == "Dark"

    def test_dark_mode_stored_as_json_string_current_behavior(self, svc, db_conn):
        """现状：value 是 JSON 字符串。"""
        svc.set_dark_mode("Dark")
        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='dark_mode'"
        ).fetchone()
        assert json.loads(row["value"]) == "Dark"

    def test_dark_mode_toggle_roundtrip_current_behavior(self, svc):
        """现状：Light→Dark→Light 切换完整。"""
        svc.set_dark_mode("Dark")
        assert svc.get_dark_mode() == (True, "Dark")
        svc.set_dark_mode("Light")
        assert svc.get_dark_mode() == (True, "Light")


class TestSettingsReturnPattern:
    """现状：SettingsService 使用 (bool, str) 元组。R26"""

    def test_set_dark_mode_returns_tuple_current_behavior(self, svc):
        """现状：返回 (True, theme)。"""
        result = svc.set_dark_mode("Dark")
        assert result == (True, "Dark")

    def test_get_dark_mode_returns_tuple_current_behavior(self, svc):
        """现状：返回 (True, theme)。"""
        result = svc.get_dark_mode()
        assert isinstance(result, tuple)
        assert result[0] is True
