"""特征测试 — 夜间模式切换行为（DM-01 ~ DM-05）。

锁住：主题持久化、启动恢复、默认 Light。
对应 spec: characteristics_dark_mode.md
"""

import json
import pytest

from app_tool.model.database import init_db
from app_tool.controller.settings_service import SettingsService


@pytest.fixture
def svc(db_conn):
    init_db(db_conn)
    return SettingsService(db_conn)


class TestThemePersistence:
    """现状：主题持久化到 UserSettings.dark_mode。DM-01, DM-04, DM-05"""

    def test_default_theme_is_light_current_behavior(self, svc):
        """现状：数据库无记录时默认为 Light。DM-05"""
        success, theme = svc.get_dark_mode()
        assert theme == "Light"

    def test_theme_survives_roundtrip_current_behavior(self, svc):
        """现状：Light↔Dark 切换后持久化值正确。DM-01"""
        svc.set_dark_mode("Dark")
        assert svc.get_dark_mode() == (True, "Dark")

        svc.set_dark_mode("Light")
        assert svc.get_dark_mode() == (True, "Light")

    def test_theme_stored_as_json_value_current_behavior(self, svc, db_conn):
        """现状：dark_mode 的 value 是 JSON 字符串。"""
        svc.set_dark_mode("Dark")
        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='dark_mode'"
        ).fetchone()
        assert json.loads(row["value"]) == "Dark"


class TestThemeReturnPattern:
    """现状：SettingsService 使用 (bool, str) 元组返回。DM-01"""

    def test_set_returns_tuple_current_behavior(self, svc):
        """现状：set_dark_mode 返回 (True, 'Dark')。"""
        result = svc.set_dark_mode("Dark")
        assert isinstance(result, tuple)
        assert result[0] is True
        assert result[1] == "Dark"

    def test_get_returns_tuple_current_behavior(self, svc):
        """现状：get_dark_mode 返回 (True, theme)。"""
        result = svc.get_dark_mode()
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestThemeNoEffectOnOtherSettings:
    """现状：dark_mode 设置不影响其他 UserSettings key。DM-04"""

    def test_dark_mode_independent_from_sort_preference_current_behavior(self, svc, db_conn):
        """现状：设置 dark_mode 不影响 sort_preference。"""
        svc.set_dark_mode("Dark")

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='sort_preference'"
        ).fetchone()
        # sort_preference 在无记录时应为 None
        assert row is None  # 现状：设置 dark_mode 不会新增 sort_preference 记录
