"""test_search_service.py — 搜索筛选测试。"""

import pytest
from datetime import datetime


class TestKeywordSearch:
    def test_search_by_ascii_keyword(self, db_conn):
        """ASCII 关键词走 FTS5 命中。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="hello world", content="some test content")
        note_svc.create(title="other", content="nothing matches")

        results = svc.search(keyword="hello")
        assert len(results) == 1
        assert results[0].title == "hello world"

    def test_search_by_chinese_keyword(self, db_conn):
        """中文关键词走 LIKE 兜底。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="测试便签", content="内容标书")
        note_svc.create(title="其他", content="不相关")

        results = svc.search(keyword="标书")
        assert len(results) == 1
        assert results[0].title == "测试便签"

    def test_search_keyword_no_match(self, db_conn):
        """无匹配时返回空列表。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="测试", content="内容")

        results = svc.search(keyword="不存在的关键词")
        assert results == []


class TestTagFilter:
    def test_search_by_tag_names(self, db_conn):
        """按标签名筛选（R1：使用标签名）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note1 = note_svc.create(title="紧急任务", content="重要")
        note2 = note_svc.create(title="普通任务", content="一般")
        note_svc.add_tag(note1.id, "紧急重要")
        note_svc.add_tag(note2.id, "P1")

        results = svc.search(tag_names=["紧急重要"])
        assert len(results) == 1
        assert results[0].title == "紧急任务"

    def test_search_by_multiple_tags(self, db_conn):
        """多标签筛选 AND 逻辑（便签必须同时含所有指定标签）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note1 = note_svc.create(title="双标签", content="两个都有")
        note2 = note_svc.create(title="单标签", content="只有一个")
        note_svc.add_tag(note1.id, "紧急重要")
        note_svc.add_tag(note1.id, "紧急")
        note_svc.add_tag(note2.id, "紧急重要")

        results = svc.search(tag_names=["紧急重要", "紧急"])
        assert len(results) == 1
        assert results[0].title == "双标签"


class TestTimeFilter:
    def test_search_by_year_only(self, db_conn):
        """按年份筛选。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="今年便签", content="内容A")
        note_svc.create(title="旧便签", content="内容B")

        # 手动修改旧便签时间为 2020 年
        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2020-01-01T00:00:00", "旧便签"),
        )
        db_conn.commit()

        results = svc.search(year=2020, time_type="创建时间")
        assert len(results) == 1
        assert results[0].title == "旧便签"

    def test_search_by_year_and_month(self, db_conn):
        """按年月筛选。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="6月便签", content="A")
        note_svc.create(title="7月便签", content="B")

        # 手动修改时间
        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2026-06-15T10:00:00", "6月便签"),
        )
        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2026-07-15T10:00:00", "7月便签"),
        )
        db_conn.commit()

        results = svc.search(year=2026, month=6, time_type="创建时间")
        assert len(results) == 1
        assert results[0].title == "6月便签"

    def test_search_by_week(self, db_conn):
        """按周筛选（月内第 N 周）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="第1周", content="A")
        note_svc.create(title="第3周", content="B")

        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2026-06-03T10:00:00", "第1周"),  # 日期 3 = 第1周
        )
        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2026-06-18T10:00:00", "第3周"),  # 日期 18 = 第3周
        )
        db_conn.commit()

        results = svc.search(year=2026, month=6, week=1, time_type="创建时间")
        assert len(results) == 1
        assert results[0].title == "第1周"

    def test_time_type_defaults_to_created_at(self, db_conn):
        """不传 time_type 时默认按创建时间筛选。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="旧便签", content="A")
        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2020-01-01T00:00:00", "旧便签"),
        )
        db_conn.commit()

        results = svc.search(year=2020)
        assert len(results) == 1


class TestCombinedSearch:
    def test_keyword_and_tag_combined(self, db_conn):
        """关键词 + 标签组合 AND 查询。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note1 = note_svc.create(title="紧急会议", content="讨论项目")
        note2 = note_svc.create(title="紧急任务", content="日常")
        note3 = note_svc.create(title="普通会议", content="讨论")
        note_svc.add_tag(note1.id, "紧急重要")
        note_svc.add_tag(note2.id, "紧急重要")
        note_svc.add_tag(note3.id, "P1")

        # 关键词"会议" + 标签"紧急重要" → 只命中 note1
        results = svc.search(keyword="会议", tag_names=["紧急重要"])
        assert len(results) == 1
        assert results[0].title == "紧急会议"

    def test_keyword_and_time_combined(self, db_conn):
        """关键词 + 时间组合 AND 查询。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="2025年", content="旧报告")
        note_svc.create(title="2026年", content="新报告")

        db_conn.execute(
            "UPDATE Note SET created_at=? WHERE title=?",
            ("2025-03-01T00:00:00", "2025年"),
        )
        db_conn.commit()

        results = svc.search(keyword="报告", year=2025, time_type="创建时间")
        assert len(results) == 1
        assert results[0].title == "2025年"

    def test_all_empty_params_returns_all_notes(self, db_conn):
        """spec §5.4: 搜索始终同时返回已完成和未完成便签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="A", content="a")
        note_svc.create(title="B", content="b")
        # 创建并标记完成
        n3 = note_svc.create(title="C", content="c")
        note_svc.mark_complete(n3.id)

        results = svc.search()
        assert len(results) == 3
        titles = {r.title for r in results}
        assert titles == {"A", "B", "C"}

    def test_keyword_search_includes_completed(self, db_conn):
        """spec §5.4: 关键词搜索同时返回已完成便签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.search_service import SearchService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        svc = SearchService(db_conn)

        note_svc.create(title="pending task", content="todo")
        n2 = note_svc.create(title="completed task", content="done")
        note_svc.mark_complete(n2.id)

        results = svc.search(keyword="task")
        assert len(results) == 2
        titles = {r.title for r in results}
        assert titles == {"pending task", "completed task"}
