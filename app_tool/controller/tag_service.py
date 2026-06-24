"""标签服务：CRUD + 置顶标签管理。全部 API 使用 tag_name（R1 ID 不可见）。"""

import json
import sqlite3
from datetime import datetime
from app_tool.model.models import Tag
from app_tool.config import MAX_PINNED_TAGS, MAX_TAG_NAME_LENGTH


class TagService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ── CRUD ──

    def create(self, name: str) -> Tag:
        name = name.strip()
        if not name:
            raise ValueError("标签名不能为空")
        if len(name) > MAX_TAG_NAME_LENGTH:
            raise ValueError(f"标签名不能超过 {MAX_TAG_NAME_LENGTH} 字符")
        try:
            cursor = self.conn.execute(
                "INSERT INTO Tag (name) VALUES (?)", (name,)
            )
            self.conn.commit()
            return Tag(id=cursor.lastrowid, name=name)
        except sqlite3.IntegrityError:
            raise ValueError(f"标签「{name}」已存在")

    def get_all(self) -> list[Tag]:
        rows = self.conn.execute("SELECT id, name FROM Tag ORDER BY id").fetchall()
        return [Tag(id=r["id"], name=r["name"]) for r in rows]

    def get_by_name(self, name: str) -> Tag | None:
        row = self.conn.execute(
            "SELECT id, name FROM Tag WHERE name=?", (name,)
        ).fetchone()
        if row is None:
            return None
        return Tag(id=row["id"], name=row["name"])

    def update(self, old_name: str, new_name: str) -> Tag:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("标签名不能为空")
        if len(new_name) > MAX_TAG_NAME_LENGTH:
            raise ValueError(f"标签名不能超过 {MAX_TAG_NAME_LENGTH} 字符")
        existing = self.get_by_name(old_name)
        if existing is None:
            raise ValueError(f"标签「{old_name}」不存在")
        try:
            self.conn.execute(
                "UPDATE Tag SET name=? WHERE name=?", (new_name, old_name)
            )
            self.conn.commit()
            # 同步更新置顶列表中的名称
            pinned = self.get_pinned()
            if old_name in pinned:
                pinned[pinned.index(old_name)] = new_name
                self._save_pinned(pinned)
            return Tag(id=existing.id, name=new_name)
        except sqlite3.IntegrityError:
            raise ValueError(f"标签「{new_name}」已存在")

    def delete(self, name: str) -> None:
        existing = self.get_by_name(name)
        if existing is None:
            raise ValueError(f"标签「{name}」不存在")
        self.conn.execute("DELETE FROM Tag WHERE name=?", (name,))
        # 从置顶列表中移除
        pinned = self.get_pinned()
        if name in pinned:
            pinned.remove(name)
            self._save_pinned(pinned)
        self.conn.commit()

    def batch_delete(self, names: list[str]) -> int:
        """批量删除标签，一条 SQL + 一次 commit。返回实际删除数量。"""
        if not names:
            return 0
        placeholders = ",".join("?" * len(names))
        cursor = self.conn.execute(
            f"DELETE FROM Tag WHERE name IN ({placeholders})",
            tuple(names),
        )
        deleted = cursor.rowcount
        # 从置顶列表中移除
        pinned = self.get_pinned()
        changed = False
        for name in names:
            if name in pinned:
                pinned.remove(name)
                changed = True
        if changed:
            self._save_pinned(pinned)
        self.conn.commit()
        return deleted

    # ── 置顶标签（存储 tag_name 列表，R1 合规）──

    def set_pinned(self, tag_names: list[str]) -> None:
        if len(tag_names) > MAX_PINNED_TAGS:
            raise ValueError(f"最多 {MAX_PINNED_TAGS} 个置顶标签")
        self._save_pinned(tag_names)

    def toggle_pinned(self, tag_name: str) -> list[str]:
        """切换标签置顶状态。已置顶→取消；未置顶→添加。超出上限时淘汰最早。"""
        pinned = self.get_pinned()
        if tag_name in pinned:
            pinned.remove(tag_name)
        else:
            if len(pinned) >= MAX_PINNED_TAGS:
                pinned.pop(0)  # 淘汰最早置顶
            pinned.append(tag_name)
        self._save_pinned(pinned)
        return pinned

    def get_pinned(self) -> list[str]:
        row = self.conn.execute(
            "SELECT value FROM UserSettings WHERE key='pinned_tags'"
        ).fetchone()
        if row is None:
            return []
        return json.loads(row["value"])

    def get_pinned_tags(self) -> list[Tag]:
        names = self.get_pinned()
        if not names:
            return []
        placeholders = ",".join("?" * len(names))
        rows = self.conn.execute(
            f"SELECT id, name FROM Tag WHERE name IN ({placeholders})",
            names,
        ).fetchall()
        # 保持置顶顺序
        tag_map = {r["name"]: Tag(id=r["id"], name=r["name"]) for r in rows}
        return [tag_map[n] for n in names if n in tag_map]

    # ── helpers ──

    def _save_pinned(self, tag_names: list[str]) -> None:
        value = json.dumps(tag_names)
        self.conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('pinned_tags', ?)",
            (value,),
        )
        self.conn.commit()
