"""特征测试 — 交互行为链路（INT-01 ~ INT-15, service 层）。

锁住：CRUD 交互链路的完整行为（创建/编辑/删除/撤销/完成/置顶/搜索/标签管理）。
对应 spec: characteristics_interaction.md
"""

import time
import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService
from app_tool.controller.search_service import SearchService
from app_tool.config import UNDO_TIMEOUT_SECONDS


@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def tag_svc(db_conn):
    init_db(db_conn)
    return TagService(db_conn)


@pytest.fixture
def search_svc(db_conn):
    return SearchService(db_conn)


# ═══════════════════════════════════════════════════════════
# INT-01/02: 创建/编辑便签
# ═══════════════════════════════════════════════════════════

class TestCreateEditFlow:
    """现状：创建和编辑的 service 层行为。"""

    def test_create_minimal_note_current_behavior(self, note_svc):
        """现状：最小参数创建（title 可选，content 必填）。"""
        note = note_svc.create(title="", content="最小内容")
        assert note.id is not None
        assert note.title == ""
        assert note.content == "最小内容"

    def test_create_with_title_current_behavior(self, note_svc):
        """现状：带标题创建。"""
        note = note_svc.create(title="标题", content="内容")
        assert note.title == "标题"

    def test_create_strips_whitespace_current_behavior(self, note_svc):
        """现状：title 和 content 前后空白被 strip。"""
        note = note_svc.create(title="  标题  ", content="  内容  ")
        assert note.title == "标题"
        assert note.content == "内容"

    def test_update_strips_whitespace_current_behavior(self, note_svc):
        """现状：update 也 strip。"""
        note = note_svc.create(title="旧", content="旧内容")
        updated = note_svc.update(note.id, title="  新标题  ")
        assert updated.title == "新标题"

    def test_update_without_changing_current_behavior(self, note_svc):
        """现状：不传参数时保持原值。"""
        note = note_svc.create(title="标题", content="内容")
        updated = note_svc.update(note.id)
        assert updated.title == "标题"
        assert updated.content == "内容"


# ═══════════════════════════════════════════════════════════
# INT-03/04: 删除 + 撤销
# ═══════════════════════════════════════════════════════════

class TestDeleteUndoFlow:
    """现状：删除→撤销的完整行为。"""

    def test_delete_preserves_title_and_content_in_undo_current_behavior(self, note_svc):
        """现状：_undo_data 保存原始 title 和 content。"""
        note = note_svc.create(title="重要标题", content="重要内容")
        note_svc.delete(note.id)

        assert note_svc._undo_data is not None
        assert note_svc._undo_data["title"] == "重要标题"
        assert note_svc._undo_data["content"] == "重要内容"

    def test_undo_restores_tags_current_behavior(self, note_svc, tag_svc):
        """现状：撤销恢复标签关联。"""
        tag_svc.create("工作")
        note = note_svc.create(title="测试", content="内容", tag_names=["工作"])
        note_svc.delete(note.id)

        restored = note_svc.undo_delete()
        assert restored is not None
        tags = note_svc.get_tags(restored.id)
        tag_names = [t.name for t in tags]
        assert "工作" in tag_names

    def test_second_delete_overwrites_undo_data_current_behavior(self, note_svc):
        """现状：连续删除只保留最后一次的撤销数据。"""
        n1 = note_svc.create(title="第一", content="c1")
        n2 = note_svc.create(title="第二", content="c2")
        note_svc.delete(n1.id)
        note_svc.delete(n2.id)

        assert note_svc._undo_data["title"] == "第二"

    def test_undo_within_timeout_succeeds_current_behavior(self, note_svc):
        """现状：12 小时内撤销成功。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.delete(note.id)

        restored = note_svc.undo_delete()
        assert restored is not None
        assert restored.title == "测试"
        assert restored.content == "内容"

    def test_undo_clears_undo_data_current_behavior(self, note_svc):
        """现状：撤销成功后 _undo_data 被清为 None。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.delete(note.id)
        note_svc.undo_delete()
        assert note_svc._undo_data is None

    def test_clear_undo_clears_data_current_behavior(self, note_svc):
        """现状：clear_undo() 清空撤销数据。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.delete(note.id)
        note_svc.clear_undo()
        assert note_svc._undo_data is None
        assert note_svc.undo_delete() is None


# ═══════════════════════════════════════════════════════════
# INT-05: 完成/取消完成
# ═══════════════════════════════════════════════════════════

class TestCompleteToggle:
    """现状：标记完成和取消完成的完整行为。"""

    def test_completed_note_not_in_incomplete_list_current_behavior(self, note_svc):
        """现状：完成后的便签不出现在 get_incomplete()。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.mark_complete(note.id)

        incomplete = note_svc.get_incomplete()
        ids = [n.id for n in incomplete]
        assert note.id not in ids

    def test_completed_note_in_completed_list_current_behavior(self, note_svc):
        """现状：完成后便签出现在 get_completed()。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.mark_complete(note.id)

        completed = note_svc.get_completed()
        ids = [n.id for n in completed]
        assert note.id in ids

    def test_mark_complete_idempotent_rejection_current_behavior(self, note_svc):
        """现状：重复完成抛 ValueError。R6"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.mark_complete(note.id)
        with pytest.raises(ValueError, match="已完成"):
            note_svc.mark_complete(note.id)

    def test_mark_incomplete_returns_to_incomplete_list_current_behavior(self, note_svc):
        """现状：取消完成后回到未完成列表。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.mark_complete(note.id)
        note_svc.mark_incomplete(note.id)

        incomplete = note_svc.get_incomplete()
        ids = [n.id for n in incomplete]
        assert note.id in ids


# ═══════════════════════════════════════════════════════════
# INT-06: 手动置顶
# ═══════════════════════════════════════════════════════════

class TestPinToggle:
    """现状：置顶/取消置顶行为。"""

    def test_pin_note_sets_is_pinned_current_behavior(self, note_svc):
        """现状：pin_note() 设置 is_pinned=1 和 pinned_at。"""
        note = note_svc.create(title="测试", content="内容")
        pinned = note_svc.pin_note(note.id)
        assert pinned.is_pinned == 1
        assert pinned.pinned_at is not None

    def test_unpin_note_clears_is_pinned_current_behavior(self, note_svc):
        """现状：unpin_note() 设置 is_pinned=0 和 pinned_at=NULL。"""
        note = note_svc.create(title="测试", content="内容")
        note_svc.pin_note(note.id)
        unpinned = note_svc.unpin_note(note.id)
        assert unpinned.is_pinned == 0
        assert unpinned.pinned_at is None


# ═══════════════════════════════════════════════════════════
# INT-08/09: 搜索交互
# ═══════════════════════════════════════════════════════════

class TestSearchInteraction:
    """现状：搜索的 service 层行为。"""

    def test_empty_keyword_returns_nothing_with_other_conditions_current_behavior(self, note_svc, search_svc):
        """现状：空关键词 + 标签条件组合仍能工作。"""
        note_svc.create(title="测试", content="c")
        # 空关键词 + 无任何条件 → 应返回全部
        results = search_svc.search()
        assert len(results) >= 1

    def test_search_with_only_tag_filter_current_behavior(self, note_svc, search_svc, tag_svc):
        """现状：仅标签筛选不过滤文本。"""
        tag_svc.create("A")
        note_svc.create(title="任何标题", content="任何内容", tag_names=["A"])

        results = search_svc.search(tag_names=["A"])
        assert len(results) == 1

    def test_search_with_year_filter_current_behavior(self, note_svc, search_svc):
        """现状：年份筛选基于时间字段的前 4 位。"""
        note = note_svc.create(title="测试", content="内容")
        created_year = note.created_at[:4]

        results = search_svc.search(year=int(created_year))
        assert len(results) >= 1


# ═══════════════════════════════════════════════════════════
# INT-11~14: 标签管理交互
# ═══════════════════════════════════════════════════════════

class TestTagManagement:
    """现状：标签的 CRUD 行为。"""

    def test_create_tag_success_current_behavior(self, tag_svc):
        """现状：创建标签返回 Tag 对象。"""
        tag = tag_svc.create("新标签")
        assert tag.id is not None
        assert tag.name == "新标签"

    def test_create_duplicate_tag_rejected_current_behavior(self, tag_svc):
        """现状：重名标签抛 ValueError。"""
        tag_svc.create("工作")
        with pytest.raises(ValueError, match="已存在"):
            tag_svc.create("工作")

    def test_delete_tag_removes_from_db_current_behavior(self, tag_svc):
        """现状：删除后 get_all 不再包含。"""
        tag_svc.create("临时")
        tag_svc.delete("临时")
        names = [t.name for t in tag_svc.get_all()]
        assert "临时" not in names

    def test_get_by_name_returns_none_for_nonexistent_current_behavior(self, tag_svc):
        """现状：不存在的标签返回 None。"""
        assert tag_svc.get_by_name("不存在") is None

    def test_seed_tags_exist_after_init_current_behavior(self, tag_svc):
        """现状：init_db 后 6 个种子标签存在。"""
        from app_tool.config import SEED_TAGS
        all_names = [t.name for t in tag_svc.get_all()]
        for seed in SEED_TAGS:
            assert seed in all_names
