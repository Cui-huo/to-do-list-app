"""特征测试 — SearchService + FTS5 同步（P2）。

锁住：搜索不过滤完成状态、FTS5 同步、中文 LIKE 兜底。
对应 spec: p2_crosscutting.md CT-P2-04, CT-P2-05
"""

import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.search_service import SearchService


@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def search_svc(db_conn):
    return SearchService(db_conn)


class TestSearchNoCompletionFilter:
    """现状：search() 不过滤 is_completed。CT-P2-04"""

    def test_search_returns_both_completed_and_incomplete_current_behavior(self, note_svc, search_svc):
        """现状：搜索结果同时包含已完成和未完成便签。"""
        n1 = note_svc.create(title="未完成", content="关键词")
        n2 = note_svc.create(title="已完成", content="关键词")
        note_svc.mark_complete(n2.id)

        results = search_svc.search(keyword="关键词")
        ids = [n.id for n in results]
        assert n1.id in ids
        assert n2.id in ids  # 现状：已完成也在结果中

    def test_search_sorted_by_updated_at_desc_current_behavior(self, note_svc, search_svc):
        """现状：搜索结果按 updated_at DESC 排序。"""
        import time
        n1 = note_svc.create(title="先", content="关键词")
        time.sleep(0.001)
        n2 = note_svc.create(title="后", content="关键词")

        results = search_svc.search(keyword="关键词")
        assert results[0].id == n2.id


class TestFtsSync:
    """现状：CRUD 操作同步 FTS5 索引。CT-P2-05"""

    def test_fts_synced_on_create_current_behavior(self, note_svc, search_svc):
        """现状：create() 后 ASCII 关键词可通过 FTS5 MATCH 搜到。"""
        note_svc.create(title="hello world", content="test content")
        results = search_svc.search(keyword="hello")
        assert len(results) == 1
        assert results[0].title == "hello world"

    def test_fts_synced_on_update_current_behavior(self, note_svc, search_svc):
        """现状：update() 后旧关键词搜不到，新关键词搜得到。"""
        note = note_svc.create(title="old title", content="old content")
        note_svc.update(note.id, title="new title", content="new content")

        results = search_svc.search(keyword="old")
        assert len(results) == 0

        results = search_svc.search(keyword="new")
        assert len(results) == 1

    def test_fts_deleted_on_delete_current_behavior(self, note_svc, search_svc):
        """现状：delete() 后 FTS5 索引移除。"""
        note = note_svc.create(title="delete me", content="to be deleted")
        note_svc.delete(note.id)

        results = search_svc.search(keyword="delete")
        assert len(results) == 0

    def test_fts_title_search_current_behavior(self, note_svc, search_svc):
        """现状：FTS5 同时搜索 title 和 content。"""
        note_svc.create(title="abc title", content="xyz content")
        assert len(search_svc.search(keyword="abc")) == 1
        assert len(search_svc.search(keyword="xyz")) == 1


class TestChineseSearch:
    """现状：中文关键词走 LIKE 兜底。"""

    def test_chinese_falls_back_to_like_current_behavior(self, note_svc, search_svc):
        """现状：中文关键词通过 LIKE '%keyword%' 搜索。"""
        note_svc.create(title="你好世界", content="中文测试内容")
        results = search_svc.search(keyword="中文")
        assert len(results) == 1
        assert results[0].title == "你好世界"

    def test_chinese_title_search_current_behavior(self, note_svc, search_svc):
        """现状：中文搜索匹配标题。"""
        note_svc.create(title="工作笔记", content="内容")
        results = search_svc.search(keyword="工作")
        assert len(results) == 1

    def test_chinese_content_search_current_behavior(self, note_svc, search_svc):
        """现状：中文搜索匹配内容。"""
        note_svc.create(title="标题", content="这是一段中文内容")
        results = search_svc.search(keyword="中文")
        assert len(results) == 1


class TestTagFilterSearch:
    """现状：标签筛选使用 AND 逻辑。"""

    def test_tag_filter_and_logic_current_behavior(self, note_svc, search_svc, db_conn):
        """现状：多标签筛选要求便签同时包含所有指定标签。"""
        from app_tool.controller.tag_service import TagService
        tag_svc = TagService(db_conn)
        tag_svc.create("A")
        tag_svc.create("B")

        n1 = note_svc.create(title="有AB", content="c", tag_names=["A", "B"])
        n2 = note_svc.create(title="仅A", content="c", tag_names=["A"])

        results = search_svc.search(tag_names=["A", "B"])
        ids = [n.id for n in results]
        assert n1.id in ids
        assert n2.id not in ids  # 只有 A 没有 B，不应出现


class TestTimeTypeSearch:
    """现状：时间类型切换 '创建时间' / '完成时间'。"""

    def test_time_type_defaults_to_created_at_current_behavior(self, note_svc, search_svc):
        """现状：不指定 time_type 时默认用 '创建时间'。"""
        from datetime import datetime
        note = note_svc.create(title="今年的", content="c")
        current_year = datetime.now().year
        results = search_svc.search(year=current_year)
        assert len(results) == 1
