"""数据导出服务：JSON / TEXT 格式。§5.5"""

import json
import logging
import sqlite3
from app_tool.controller.note_service import NoteService

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def export(self, format: str, output_path: str | None = None) -> tuple[bool, str]:
        """§5.5: 导出全部便签为 JSON 或 TEXT。

        Returns:
            (True, 文件路径或内容字符串) | (False, 错误信息)
        """
        format = format.strip().lower()
        if format not in ("json", "text"):
            return False, "格式必须为 'json' 或 'text'"

        rows = self.conn.execute("SELECT * FROM Note ORDER BY created_at").fetchall()
        notes = [NoteService._row_to_note(r) for r in rows]

        results = []
        for note in notes:
            assert note is not None
            tag_rows = self.conn.execute(
                "SELECT t.name FROM Tag t "
                "INNER JOIN NoteTag nt ON t.id = nt.tag_id "
                "WHERE nt.note_id=? ORDER BY t.id",
                (note.id,),
            ).fetchall()
            tag_names = [r["name"] for r in tag_rows]
            results.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "completed_at": note.completed_at,
                "is_completed": note.is_completed,
                "tags": tag_names,
            })

        if format == "json":
            content = json.dumps(results, ensure_ascii=False, indent=2)
        else:
            if not results:
                content = ""
            else:
                blocks = []
                for r in results:
                    tags_str = ", ".join(r["tags"]) if r["tags"] else ""
                    block = f"【{r['title']}】\n{r['content']}\n标签: {tags_str}\n---"
                    blocks.append(block)
                content = "\n\n".join(blocks)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("数据导出: format=%s, path=%s, count=%d", format, output_path, len(results))
            return True, output_path

        logger.info("数据导出: format=%s, count=%d", format, len(results))
        return True, content
