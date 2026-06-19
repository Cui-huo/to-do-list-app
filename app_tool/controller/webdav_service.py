"""WebDAV 同步服务（P2）— 桩实现。§5.8"""

import json
import sqlite3


class WebDAVService:
    """WebDAV 同步：凭据管理 + 上传/下载。"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ── 凭据管理 ──

    def set_credentials(self, url: str, user: str, password: str) -> tuple[bool, str]:
        """§5.8: 持久化 WebDAV 凭据到 UserSettings。"""
        creds = json.dumps({"url": url, "user": user, "password": password})
        self.conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('webdav_credentials', ?)",
            (creds,),
        )
        self.conn.commit()
        return True, "凭据已保存"

    def get_credentials(self) -> tuple[str, str, str]:
        """§5.8: 读取 WebDAV 凭据。"""
        row = self.conn.execute(
            "SELECT value FROM UserSettings WHERE key='webdav_credentials'"
        ).fetchone()
        if row is None:
            return "", "", ""
        creds = json.loads(row["value"])
        return creds.get("url", ""), creds.get("user", ""), creds.get("password", "")

    def is_configured(self) -> bool:
        """§5.8: 凭据是否已配置（url/user/pass 均非空）。"""
        url, user, password = self.get_credentials()
        return bool(url and user and password)

    # ── 同步 ──

    def sync(self) -> tuple[bool, str]:
        """§5.8: 执行同步（上传本地 + 下载远程覆盖本地）。P2 完整实现在后续阶段。"""
        if not self.is_configured():
            return False, "WebDAV 凭据未配置，请在设置中填写服务器地址、用户名和密码"
        # P2 完整实现：上传 db → 下载远程 db 覆盖本地
        return False, "WebDAV 同步功能尚未实现（P2 阶段）"
