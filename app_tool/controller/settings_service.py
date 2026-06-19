"""用户设置服务：夜间模式 / 排序偏好 等。§5.6"""

import json
import sqlite3


class SettingsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ── 夜间模式 ──

    def set_dark_mode(self, theme: str) -> tuple[bool, str]:
        """§5.6: 设置夜间模式，持久化到 UserSettings。

        Returns:
            (True, theme) — 当前主题字符串
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('dark_mode', ?)",
            (json.dumps(theme),),
        )
        self.conn.commit()
        return True, theme

    def get_dark_mode(self) -> tuple[bool, str]:
        """§5.6: 获取当前主题，默认 Light。

        Returns:
            (True, 'Light' | 'Dark')
        """
        row = self.conn.execute(
            "SELECT value FROM UserSettings WHERE key='dark_mode'"
        ).fetchone()
        if row is None:
            return True, "Light"
        return True, json.loads(row["value"])
