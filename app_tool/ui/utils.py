"""Shared UI utilities and mixins for the note-taking app."""

import json

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar


class ToastMixin:
    """Mixin that provides _toast() for any MDScreen subclass."""

    def _toast(self, text: str):
        MDSnackbar(
            MDLabel(text=text, font_style="Body2"),
            duration=2,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ).open()


class ServiceMixin:
    """Mixin that provides _app accessor for any MDScreen subclass."""

    @property
    def _app(self):
        return MDApp.get_running_app()


def load_setting(key: str):
    """从 UserSettings 读取 JSON 值，无记录返回 None。"""
    app = MDApp.get_running_app()
    if app and app.db_conn:
        row = app.db_conn.execute(
            "SELECT value FROM UserSettings WHERE key=?", (key,)
        ).fetchone()
        if row:
            try:
                return json.loads(row["value"])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
    return None


def save_setting(key: str, value):
    """写入 JSON 值到 UserSettings（INSERT OR REPLACE）。"""
    app = MDApp.get_running_app()
    if app and app.db_conn:
        app.db_conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        app.db_conn.commit()
