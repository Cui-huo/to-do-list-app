"""test_settings_service.py — 夜间模式 + 用户设置测试（§5.6 夜间模式 P1）。R25"""

import pytest


class TestDarkMode:
    """§5.6: 夜间模式 — 全局主题即时切换 + 持久化到 UserSettings(key='dark_mode')。"""

    def test_set_dark_mode(self, db_conn):
        """§5.6: 设置夜间模式返回 (True, theme)，持久化到 DB。R9"""
        from app_tool.model.database import init_db
        from app_tool.controller.settings_service import SettingsService

        init_db(db_conn)
        svc = SettingsService(db_conn)
        success, result = svc.set_dark_mode("Dark")
        assert success is True
        assert result == "Dark"

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='dark_mode'"
        ).fetchone()
        assert row is not None
        assert '"Dark"' in row["value"] or row["value"] == "Dark"

    def test_get_dark_mode_default_light(self, db_conn):
        """§5.6: 未设置时返回 (True, 'Light')。"""
        from app_tool.model.database import init_db
        from app_tool.controller.settings_service import SettingsService

        init_db(db_conn)
        svc = SettingsService(db_conn)
        success, result = svc.get_dark_mode()
        assert success is True
        assert result == "Light"

    def test_dark_mode_roundtrip(self, db_conn):
        """§5.6: 设置后读取应一致。R9 持久化"""
        from app_tool.model.database import init_db
        from app_tool.controller.settings_service import SettingsService

        init_db(db_conn)
        svc = SettingsService(db_conn)
        success, result = svc.set_dark_mode("Dark")
        assert success is True
        assert result == "Dark"

        success, result = svc.get_dark_mode()
        assert success is True
        assert result == "Dark"

        success, result = svc.set_dark_mode("Light")
        assert success is True
        assert result == "Light"

        success, result = svc.get_dark_mode()
        assert success is True
        assert result == "Light"
