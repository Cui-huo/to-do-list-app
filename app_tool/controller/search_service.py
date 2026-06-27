"""搜索筛选服务：关键词 + 标签 + 时间 组合 AND 查询。"""

import sqlite3
from app_tool.model.models import Note
from app_tool.controller.note_service import NoteService
from app_tool.model.database import has_fts5


def _is_ascii(s: str) -> bool:
    return all(ord(c) < 128 for c in s)


class SearchService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def search(
        self,
        keyword: str | None = None,
        tag_names: list[str] | None = None,
        year: int | None = None,
        month: int | None = None,
        week: int | None = None,
        time_type: str | None = None,
    ) -> list[Note]:
        conditions: list[str] = []
        params: list = []

        # 关键词
        if keyword and keyword.strip():
            kw = keyword.strip()
            if has_fts5() and _is_ascii(kw):
                conditions.append(
                    "n.id IN (SELECT rowid FROM notes_fts WHERE notes_fts MATCH ?)"
                )
                params.append(kw)
            else:
                conditions.append("(n.title LIKE ? OR n.content LIKE ?)")
                params.extend([f"%{kw}%", f"%{kw}%"])

        # 标签（AND：便签必须含所有指定标签）
        if tag_names:
            placeholders = ",".join("?" * len(tag_names))
            conditions.append(
                f"n.id IN ("
                f"  SELECT nt.note_id FROM NoteTag nt "
                f"  INNER JOIN Tag t ON nt.tag_id = t.id "
                f"  WHERE t.name IN ({placeholders}) "
                f"  GROUP BY nt.note_id HAVING COUNT(DISTINCT t.name) = ?"
                f")"
            )
            params.extend(tag_names)
            params.append(len(tag_names))

        # 时间
        tf = time_type if time_type else "创建时间"
        time_field = "n.created_at" if tf == "创建时间" else "n.completed_at"
        if year is not None:
            conditions.append(
                f"CAST(substr({time_field}, 1, 4) AS INTEGER) = ?"
            )
            params.append(year)
        if month is not None:
            conditions.append(
                f"CAST(substr({time_field}, 6, 2) AS INTEGER) = ?"
            )
            params.append(month)
        if week is not None:
            start_day = (week - 1) * 7 + 1
            end_day = week * 7
            conditions.append(
                f"CAST(substr({time_field}, 9, 2) AS INTEGER) BETWEEN ? AND ?"
            )
            params.extend([start_day, end_day])

        # spec §5.4: 搜索始终同时返回已完成和未完成便签
        where_clause = "WHERE 1=1"
        if conditions:
            where_clause += " AND " + " AND ".join(conditions)

        sql = (
            "SELECT DISTINCT n.* FROM Note n "
            + where_clause
            + " ORDER BY n.updated_at DESC"
        )

        rows = self.conn.execute(sql, params).fetchall()
        return [NoteService._row_to_note(r) for r in rows]  # type: ignore[return-value]
