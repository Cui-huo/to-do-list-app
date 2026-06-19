"""test_export_service.py — 数据导出测试（§5.5 数据导出 P1）。R25"""

import json
import tempfile
import os
import pytest


class TestExportJSON:
    """§5.5: JSON 导出 — 含所有便签完整数据（id/title/content/tags/时间戳等）。"""

    def test_export_json_with_notes(self, db_conn):
        """§5.5: JSON 导出含所有便签及标签，返回 (True, 文件路径)。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.export_service import ExportService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        note_svc.create(title="任务A", content="内容A", tag_names=["紧急重要", "P1"])
        note_svc.create(title="任务B", content="内容B")

        svc = ExportService(db_conn)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            success, result = svc.export(format="json", output_path=path)
            assert success is True
            assert result == path
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0]["title"] == "任务A"
            assert data[0]["content"] == "内容A"
            assert "tags" in data[0]
            assert set(data[0]["tags"]) == {"紧急重要", "P1"}
            assert data[1]["title"] == "任务B"
            assert data[1]["tags"] == []
        finally:
            os.unlink(path)

    def test_export_json_empty_db(self, db_conn):
        """§5.5: 空数据库导出空数组 []，不报错。"""
        from app_tool.model.database import init_db
        from app_tool.controller.export_service import ExportService

        init_db(db_conn)
        svc = ExportService(db_conn)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            success, result = svc.export(format="json", output_path=path)
            assert success is True
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data == []
        finally:
            os.unlink(path)


class TestExportTEXT:
    """§5.5: TEXT 导出 — 每便签按「标题」\n内容\n标签:...\n--- 格式分段。"""

    def test_export_text_with_notes(self, db_conn):
        """§5.5: TEXT 导出每便签一段。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.export_service import ExportService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        note_svc.create(title="任务A", content="内容A", tag_names=["P1"])

        svc = ExportService(db_conn)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name
        try:
            success, result = svc.export(format="text", output_path=path)
            assert success is True
            with open(path, encoding="utf-8") as f:
                text = f.read()
            assert "【任务A】" in text
            assert "内容A" in text
            assert "标签: P1" in text
            assert "---" in text
        finally:
            os.unlink(path)

    def test_export_text_empty_db(self, db_conn):
        """§5.5: 空数据库导出空文本，不报错。"""
        from app_tool.model.database import init_db
        from app_tool.controller.export_service import ExportService

        init_db(db_conn)
        svc = ExportService(db_conn)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name
        try:
            success, result = svc.export(format="text", output_path=path)
            assert success is True
            with open(path, encoding="utf-8") as f:
                text = f.read()
            assert text == ""
        finally:
            os.unlink(path)


class TestExportValidation:
    """§5.5 校验: format 必须为 'json' 或 'text'。"""

    def test_export_invalid_format(self, db_conn):
        """§5.5: 非法 format 返回 (False, 错误信息)。"""
        from app_tool.model.database import init_db
        from app_tool.controller.export_service import ExportService

        init_db(db_conn)
        svc = ExportService(db_conn)
        success, result = svc.export(format="xml")
        assert success is False
        assert "格式" in result
        assert "json" in result.lower() or "text" in result.lower()
