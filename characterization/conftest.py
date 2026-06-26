"""特征测试 fixtures — 独立 conftest，提供 :memory: DB + KivyMD 环境。"""

import os
import sys
import pytest
import sqlite3

# 确保项目根在 Python 路径中
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── Kivy headless 配置（必须在任何 kivy 导入之前设置） ──
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

from kivy.config import Config
Config.set("graphics", "position", "custom")
Config.set("graphics", "left", 0)
Config.set("graphics", "top", 0)
Config.set("graphics", "width", 360)
Config.set("graphics", "height", 640)
Config.set("kivy", "log_level", "error")


@pytest.fixture
def db_conn():
    """每次测试获取全新的 :memory: SQLite 连接。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def kivy_app():
    """会话级：启动最小 KivyMD App 实例。"""
    from kivymd.app import MDApp
    from kivy.app import App
    from kivy.uix.widget import Widget

    class _TestApp(MDApp):
        def build(self):
            return Widget()

    app = _TestApp()
    from kivy.base import EventLoop
    EventLoop.ensure_window()
    app.theme_cls.primary_palette = "Indigo"
    app.theme_cls.theme_style = "Light"
    app.db_conn = None
    app.note_service = None
    app.tag_service = None
    app.search_service = None
    if App.get_running_app() is None:
        App._running_app = app
    yield app
    App._running_app = None


@pytest.fixture
def kivy_app_instance(kivy_app):
    """每个测试获取已初始化的 KivyMD App 实例（db_conn 重置为 None）。"""
    from kivy.app import App
    if App.get_running_app() is None:
        App._running_app = kivy_app
    kivy_app.db_conn = None
    return kivy_app
