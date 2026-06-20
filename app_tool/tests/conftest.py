"""pytest fixtures — :memory: SQLite 隔离测试 + KivyMD UI 测试环境。"""

import os
import pytest
import sqlite3

# ── Kivy headless 配置（必须在任何 kivy 导入之前设置） ──
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

# 阻止 Kivy 配置文件干扰测试
_KIVY_CONFIG_OVERWRITTEN = False
if not _KIVY_CONFIG_OVERWRITTEN:
    _KIVY_CONFIG_OVERWRITTEN = True
    from kivy.config import Config
    Config.set("graphics", "position", "custom")
    Config.set("graphics", "left", 0)
    Config.set("graphics", "top", 0)
    Config.set("graphics", "width", 360)
    Config.set("graphics", "height", 640)
    Config.set("kivy", "log_level", "error")


@pytest.fixture
def db_conn():
    """每次测试获取全新的内存 SQLite 连接。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


# ── KivyMD UI 测试 fixture ──

@pytest.fixture(scope="session")
def kivy_app():
    """会话级：启动最小 KivyMD App 实例，供 UI widget 测试使用。"""
    from kivymd.app import MDApp
    from kivy.app import App
    from kivy.uix.widget import Widget

    class _TestApp(MDApp):
        def build(self):
            return Widget()

    app = _TestApp()
    # 手动初始化 EventLoop（不调用 app.run()）
    from kivy.base import EventLoop
    EventLoop.ensure_window()
    app.theme_cls.primary_palette = "Indigo"
    app.theme_cls.theme_style = "Light"
    # 设置 Mock 属性，防止 UI 代码访问未定义的服务时崩溃
    app.db_conn = None
    app.note_service = None
    app.tag_service = None
    app.search_service = None
    # 关键：设置 App._running_app 使 KivyMD 的
    # "App object must be initialized" 检查通过
    if App.get_running_app() is None:
        App._running_app = app
    yield app
    App._running_app = None


@pytest.fixture
def kivy_app_instance(kivy_app):
    """每个测试获取已初始化的 KivyMD App 实例（确保 _running_app 未丢失）。"""
    from kivy.app import App
    if App.get_running_app() is None:
        App._running_app = kivy_app
    return kivy_app
