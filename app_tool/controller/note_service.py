"""便签服务：CRUD + 置顶 + 拖拽排序 + 撤销 + 标签关联 + FTS5 同步。"""

import json
import sqlite3
from datetime import datetime
from app_tool.model.models import Note, Tag
from app_tool.model.database import fts_insert, fts_update, fts_delete
from app_tool.config import UNDO_TIMEOUT_SECONDS, MAX_TITLE_LENGTH, MAX_CONTENT_LENGTH, MAX_TAGS_PER_NOTE


class NoteWithTags:
    """带标签的便签投影。"""

    def __init__(self, note: Note, tags: list[Tag]):
        self.id = note.id
        self.title = note.title
        self.content = note.content
        self.created_at = note.created_at
        self.updated_at = note.updated_at
        self.completed_at = note.completed_at
        self.is_completed = note.is_completed
        self.is_pinned = note.is_pinned
        self.pinned_at = note.pinned_at
        self.position = note.position
        self.tags = tags


class NoteService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._undo_data: dict | None = None  # {title, content, tag_names, deleted_at}

    # ── CRUD ──

    def create(self, title: str = "", content: str = "", tag_names: list[str] | None = None) -> Note:
        title = title.strip()
        content = content.strip()
        if not content:
            raise ValueError("内容不能为空")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValueError(f"内容不能超过 {MAX_CONTENT_LENGTH} 字符")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValueError(f"标题不能超过 {MAX_TITLE_LENGTH} 字符")
        now = datetime.now().isoformat()
        cursor = self.conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (title, content, now, now),
        )
        note_id = cursor.lastrowid
        self.conn.commit()
        fts_insert(self.conn, note_id, title, content)
        self.conn.commit()
        # spec §5.1: 创建时关联标签，不存在的标签自动跳过
        if tag_names:
            for name in tag_names:
                try:
                    self.add_tag(note_id, name)
                except ValueError as e:
                    if "不存在" not in str(e):
                        raise
        return Note(
            id=note_id, title=title, content=content,
            created_at=now, updated_at=now,
        )

    def get_by_id(self, note_id: int) -> Note | None:
        return self._row_to_note(
            self.conn.execute("SELECT * FROM Note WHERE id=?", (note_id,)).fetchone()
        )

    def update(self, note_id: int, title: str | None = None, content: str | None = None,
               tag_names: list[str] | None = None) -> Note:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        new_title = title.strip() if title is not None else note.title
        new_content = content.strip() if content is not None else note.content
        if not new_content:
            raise ValueError("内容不能为空")
        if len(new_content) > MAX_CONTENT_LENGTH:
            raise ValueError(f"内容不能超过 {MAX_CONTENT_LENGTH} 字符")
        if len(new_title) > MAX_TITLE_LENGTH:
            raise ValueError(f"标题不能超过 {MAX_TITLE_LENGTH} 字符")
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE Note SET title=?, content=?, updated_at=? WHERE id=?",
            (new_title, new_content, now, note_id),
        )
        fts_update(self.conn, note_id, new_title, new_content)
        # spec §5.1: 标签变更时同步更新 NoteTag 关联（仅增/删）
        if tag_names is not None:
            current_names = {t.name for t in self.get_tags(note_id)}
            new_names = set(tag_names)
            # 先移除不再需要的标签（释放配额）
            for name in current_names - new_names:
                self.remove_tag(note_id, name)
            # 再添加新标签（不存在的自动跳过）
            for name in new_names - current_names:
                try:
                    self.add_tag(note_id, name)
                except ValueError as e:
                    if "不存在" not in str(e):
                        raise
        self.conn.commit()
        updated = self.get_by_id(note_id)
        assert updated is not None
        return updated

    def delete(self, note_id: int) -> None:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        # 暂存撤销数据（覆盖上次）
        tag_names = [t.name for t in self.get_tags(note_id)]
        self._undo_data = {
            "title": note.title,
            "content": note.content,
            "tag_names": tag_names,
            "deleted_at": datetime.now(),
        }
        fts_delete(self.conn, note_id)
        self.conn.execute("DELETE FROM Note WHERE id=?", (note_id,))
        self.conn.commit()

    def undo_delete(self) -> Note | None:
        """撤销最后一次删除。返回新便签或 None（无可撤销数据/超时）。"""
        if self._undo_data is None:
            return None
        elapsed = (datetime.now() - self._undo_data["deleted_at"]).total_seconds()
        if elapsed > UNDO_TIMEOUT_SECONDS:
            self._undo_data = None
            return None
        data = self._undo_data
        self._undo_data = None
        note = self.create(
            title=data["title"],
            content=data["content"],
        )
        for tag_name in data["tag_names"]:
            self.add_tag(note.id, tag_name)
        return note

    def get_undo_info(self) -> dict | None:
        """获取当前可撤销数据（供 UI 判断是否显示 UndoBar）。"""
        if self._undo_data is None:
            return None
        elapsed = (datetime.now() - self._undo_data["deleted_at"]).total_seconds()
        if elapsed > UNDO_TIMEOUT_SECONDS:
            self._undo_data = None
            return None
        return self._undo_data

    def clear_undo(self) -> None:
        self._undo_data = None

    # ── 完成状态 ──

    def mark_complete(self, note_id: int) -> Note:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        if note.is_completed:
            raise ValueError("该便签已完成")
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE Note SET is_completed=1, completed_at=?, position=0 WHERE id=?",
            (now, note_id),
        )
        self.conn.commit()
        updated = self.get_by_id(note_id)
        assert updated is not None
        return updated

    def mark_incomplete(self, note_id: int) -> Note:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        if not note.is_completed:
            raise ValueError("该便签未完成")
        self.conn.execute(
            "UPDATE Note SET is_completed=0, completed_at=NULL WHERE id=?",
            (note_id,),
        )
        self.conn.commit()
        updated = self.get_by_id(note_id)
        assert updated is not None
        return updated

    # ── 手动置顶 ──

    def pin_note(self, note_id: int) -> Note:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        if note.is_pinned:
            raise ValueError("该便签已置顶")
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE Note SET is_pinned=1, pinned_at=? WHERE id=?", (now, note_id)
        )
        self.conn.commit()
        updated = self.get_by_id(note_id)
        assert updated is not None
        return updated

    def unpin_note(self, note_id: int) -> Note:
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"便签 ID={note_id} 不存在")
        if not note.is_pinned:
            raise ValueError("该便签未置顶")
        self.conn.execute(
            "UPDATE Note SET is_pinned=0, pinned_at=NULL WHERE id=?", (note_id,)
        )
        self.conn.commit()
        updated = self.get_by_id(note_id)
        assert updated is not None
        return updated

    # ── 排序查询 ──

    def _get_sort_preference(self) -> str:
        row = self.conn.execute(
            "SELECT value FROM UserSettings WHERE key='sort_preference'"
        ).fetchone()
        if row is None:
            return "updated_at"
        return json.loads(row["value"])

    def set_sort_preference(self, pref: str) -> None:
        if pref not in ("updated_at", "created_at"):
            raise ValueError("排序偏好必须为 'updated_at' 或 'created_at'")
        self.conn.execute(
            "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('sort_preference', ?)",
            (json.dumps(pref),),
        )
        self.conn.commit()

    def get_incomplete(self) -> list[Note]:
        """未完成便签：手动置顶 → 标签置顶 → 时间偏好。"""
        from app_tool.controller.tag_service import TagService
        tag_svc = TagService(self.conn)
        pinned_tag_names = tag_svc.get_pinned()
        sort_pref = self._get_sort_preference()
        time_col = "n.updated_at" if sort_pref == "updated_at" else "n.created_at"

        if pinned_tag_names:
            placeholders = ",".join("?" * len(pinned_tag_names))
            sql = (
                "SELECT DISTINCT n.* FROM Note n "
                "LEFT JOIN NoteTag nt ON n.id = nt.note_id "
                "LEFT JOIN Tag t ON nt.tag_id = t.id "
                "WHERE n.is_completed = 0 "
                "ORDER BY "
                "  CASE WHEN n.is_pinned = 1 THEN 0 ELSE 1 END, "
                f"  CASE WHEN t.name IN ({placeholders}) THEN 0 ELSE 1 END, "
                f"  {time_col} DESC"
            )
            rows = self.conn.execute(sql, pinned_tag_names).fetchall()
        else:
            time_col_no_alias = "updated_at" if sort_pref == "updated_at" else "created_at"
            sql = (
                "SELECT * FROM Note WHERE is_completed = 0 "
                "ORDER BY "
                "  CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END, "
                f"  {time_col_no_alias} DESC"
            )
            rows = self.conn.execute(sql).fetchall()
        return [self._row_to_note(r) for r in rows]  # type: ignore[return-value]

    def get_completed(self) -> list[Note]:
        """已完成便签：手动置顶 → completed_at。"""
        rows = self.conn.execute(
            "SELECT * FROM Note WHERE is_completed = 1 "
            "ORDER BY "
            "  CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END, "
            "  completed_at DESC"
        ).fetchall()
        return [self._row_to_note(r) for r in rows]  # type: ignore[return-value]

    # ── 标签关联（R1：API 使用 tag_name）──

    def add_tag(self, note_id: int, tag_name: str) -> None:
        tag = self.conn.execute(
            "SELECT id FROM Tag WHERE name=?", (tag_name,)
        ).fetchone()
        if tag is None:
            raise ValueError(f"标签「{tag_name}」不存在")
        # spec §3.1: 每个便签最多 3 个标签
        existing_count = self.conn.execute(
            "SELECT COUNT(*) FROM NoteTag WHERE note_id=?", (note_id,)
        ).fetchone()[0]
        if existing_count >= MAX_TAGS_PER_NOTE:
            raise ValueError(f"每个便签最多 {MAX_TAGS_PER_NOTE} 个标签")
        try:
            self.conn.execute(
                "INSERT INTO NoteTag (note_id, tag_id) VALUES (?, ?)",
                (note_id, tag["id"]),
            )
        except sqlite3.IntegrityError:
            pass  # 已存在，静默忽略（R6 在 UI 层用 Toast 处理）
        self.conn.commit()

    def remove_tag(self, note_id: int, tag_name: str) -> None:
        tag = self.conn.execute(
            "SELECT id FROM Tag WHERE name=?", (tag_name,)
        ).fetchone()
        if tag is None:
            return
        self.conn.execute(
            "DELETE FROM NoteTag WHERE note_id=? AND tag_id=?", (note_id, tag["id"])
        )
        self.conn.commit()

    def get_tags(self, note_id: int) -> list[Tag]:
        rows = self.conn.execute(
            "SELECT t.id, t.name FROM Tag t "
            "INNER JOIN NoteTag nt ON t.id = nt.tag_id "
            "WHERE nt.note_id=? ORDER BY t.id",
            (note_id,),
        ).fetchall()
        return [Tag(id=r["id"], name=r["name"]) for r in rows]

    def get_with_tags(self, note_id: int) -> NoteWithTags | None:
        note = self.get_by_id(note_id)
        if note is None:
            return None
        tags = self.get_tags(note_id)
        return NoteWithTags(note, tags)

    # ── helpers ──

    @staticmethod
    def _row_to_note(row: sqlite3.Row | None) -> Note | None:
        if row is None:
            return None
        return Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            is_completed=row["is_completed"],
            position=row["position"] if "position" in row.keys() else 0.0,
            is_pinned=row["is_pinned"] if "is_pinned" in row.keys() else 0,
            pinned_at=row["pinned_at"] if "pinned_at" in row.keys() else None,
        )
