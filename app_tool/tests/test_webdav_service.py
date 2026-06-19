"""test_webdav_service.py — WebDAV 同步测试（§5.8 WebDAV 同步 P2）。R25"""

import json
import pytest


class TestWebDAVCredentials:
    """§5.8 校验: WebDAV 凭据已配置（url/user/pass 均非空）。"""

    def test_sync_without_credentials_fails(self, db_conn):
        """§5.8: 未配置凭据时同步返回 (False, 错误信息)。"""
        from app_tool.model.database import init_db
        from app_tool.controller.webdav_service import WebDAVService

        init_db(db_conn)
        svc = WebDAVService(db_conn)
        success, result = svc.sync()
        assert success is False
        assert "凭据" in result or "配置" in result

    def test_credentials_persist_and_retrieve(self, db_conn):
        """§5.8: 凭据持久化到 UserSettings，配置后可读取。R9"""
        from app_tool.model.database import init_db
        from app_tool.controller.webdav_service import WebDAVService

        init_db(db_conn)
        svc = WebDAVService(db_conn)
        svc.set_credentials(
            url="https://dav.example.com/notes",
            user="admin",
            password="secret123",
        )

        url, user, password = svc.get_credentials()
        assert url == "https://dav.example.com/notes"
        assert user == "admin"
        assert password == "secret123"

    def test_partial_credentials_fails(self, db_conn):
        """§5.8: url/user/pass 任一为空时同步失败。"""
        from app_tool.model.database import init_db
        from app_tool.controller.webdav_service import WebDAVService

        init_db(db_conn)
        svc = WebDAVService(db_conn)

        svc.set_credentials(url="", user="admin", password="secret123")
        success, result = svc.sync()
        assert success is False

        svc.set_credentials(url="https://dav.example.com", user="", password="secret123")
        success, result = svc.sync()
        assert success is False

        svc.set_credentials(url="https://dav.example.com", user="admin", password="")
        success, result = svc.sync()
        assert success is False

    def test_is_configured(self, db_conn):
        """§5.8: 凭据配置状态检测（UI 用于按钮置灰判断）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.webdav_service import WebDAVService

        init_db(db_conn)
        svc = WebDAVService(db_conn)
        assert svc.is_configured() is False

        svc.set_credentials(
            url="https://dav.example.com/notes",
            user="admin",
            password="secret123",
        )
        assert svc.is_configured() is True
