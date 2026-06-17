"""便签应用主入口：MDApp + DB 初始化 + 服务注入 + ScreenManager。"""

import os
import sys
import sqlite3

from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService
from app_tool.controller.search_service import SearchService
from app_tool.controller.reminder_service import ReminderService
from app_tool.config import DB_FILENAME

# 注册中文字体，解决 KivyMD 默认 Roboto 字体无法渲染中文的问题
_FONT_CANDIDATES = [
    "C:\\Windows\\Fonts\\msyh.ttc",       # 微软雅黑 (Windows)
    "C:\\Windows\\Fonts\\msyhbd.ttc",     # 微软雅黑 粗体
    "C:\\Windows\\Fonts\\simsun.ttc",     # 宋体
    "/System/Library/Fonts/PingFang.ttc", # 苹方 (macOS)
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Android/Linux
]
_FONT_PATH = None
for _fp in _FONT_CANDIDATES:
    if os.path.isfile(_fp):
        _FONT_PATH = _fp
        break

if _FONT_PATH:
    # 替换所有 Roboto 字重变体为同一中文字体
    for _font_name in ("Roboto", "RobotoLight", "RobotoMedium", "RobotoThin", "RobotoBlack"):
        LabelBase.register(name=_font_name, fn_regular=_FONT_PATH)
else:
    print("[WARN] 未找到中文字体文件，中文可能无法正常显示", file=sys.stderr)


class NotesApp(MDApp):
    """便签应用主类。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_path: str = ""
        self.db_conn: sqlite3.Connection | None = None
        self.note_service: NoteService | None = None
        self.tag_service: TagService | None = None
        self.search_service: SearchService | None = None
        self.reminder_service: ReminderService | None = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = "Light"
        Window.size = (420, 740)

        # 数据库初始化
        self.db_path = os.path.join(self.user_data_dir, DB_FILENAME)
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row
        self.db_conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.db_conn)

        # 服务初始化
        self.note_service = NoteService(self.db_conn)
        self.tag_service = TagService(self.db_conn)
        self.search_service = SearchService(self.db_conn)
        self.reminder_service = ReminderService(self.db_conn)

        # ScreenManager
        sm = MDScreenManager()

        # 延迟导入，避免循环依赖
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui.tag_manager import TagManagerScreen
        from app_tool.ui.settings_screen import SettingsScreen

        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(TagManagerScreen(name="tags"))
        sm.add_widget(SettingsScreen(name="settings"))

        return sm

    def on_stop(self):
        if self.db_conn:
            self.db_conn.close()
