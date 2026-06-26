"""特征测试 — TagService 置顶标签行为（P1）。

锁住：置顶标签顺序、FIFO 淘汰、删除/重命名联动。
对应 spec: p1_persistence.md CT-P1-04, p2_crosscutting.md CT-P2-01, CT-P2-02
"""

import json
import pytest

from app_tool.model.database import init_db
from app_tool.controller.tag_service import TagService
from app_tool.config import MAX_PINNED_TAGS


@pytest.fixture
def svc(db_conn):
    init_db(db_conn)
    return TagService(db_conn)


class TestPinnedTagsOrder:
    """现状：置顶标签按添加顺序排列。CT-P1-04"""

    def test_pinned_order_is_addition_order_current_behavior(self, svc):
        """现状：set_pinned 保持传入顺序。"""
        for name in ["C", "A", "B"]:
            svc.create(name)
        svc.set_pinned(["C", "A"])
        assert svc.get_pinned() == ["C", "A"]

    def test_toggle_pinned_appends_to_end_current_behavior(self, svc):
        """现状：toggle_pinned 将新标签追加到列表末尾。"""
        svc.create("A")
        svc.create("B")
        svc.set_pinned(["A"])
        svc.toggle_pinned("B")
        assert svc.get_pinned() == ["A", "B"]

    def test_toggle_pinned_removes_if_already_pinned_current_behavior(self, svc):
        """现状：已置顶标签 toggle 后取消。"""
        svc.create("X")
        svc.set_pinned(["X"])
        result = svc.toggle_pinned("X")
        assert "X" not in result


class TestPinnedTagsEviction:
    """现状：超出上限时 FIFO 淘汰最早置顶的。"""

    def test_fifo_eviction_when_over_limit_current_behavior(self, svc):
        """现状：第 4 个标签置顶时，最早置顶的被淘汰。"""
        for name in ["A", "B", "C", "D"]:
            svc.create(name)

        svc.set_pinned(["A", "B", "C"])
        assert svc.get_pinned() == ["A", "B", "C"]

        svc.toggle_pinned("D")
        pinned = svc.get_pinned()
        assert len(pinned) == MAX_PINNED_TAGS
        assert "D" in pinned
        assert "A" not in pinned  # A 最早，被淘汰

    def test_set_pinned_rejects_over_limit_current_behavior(self, svc):
        """现状：set_pinned 超过 3 个直接抛 ValueError。"""
        for name in ["A", "B", "C", "D"]:
            svc.create(name)
        with pytest.raises(ValueError, match="最多"):
            svc.set_pinned(["A", "B", "C", "D"])


class TestPinnedStorage:
    """现状：置顶标签以 JSON 数组存储在 UserSettings。"""

    def test_pinned_stored_as_json_array_current_behavior(self, svc, db_conn):
        """现状：value 是 json 数组字符串，如 '["A","B"]'。"""
        svc.create("A")
        svc.set_pinned(["A"])
        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='pinned_tags'"
        ).fetchone()
        loaded = json.loads(row["value"])
        assert loaded == ["A"]
        assert isinstance(loaded, list)


class TestDeleteRemovesFromPinned:
    """现状：删除标签自动从置顶列表移除。CT-P2-01"""

    def test_delete_removes_from_pinned_current_behavior(self, svc):
        """现状：delete() 后置顶列表不再包含该标签。"""
        svc.create("工作")
        svc.set_pinned(["工作"])
        assert "工作" in svc.get_pinned()

        svc.delete("工作")
        assert "工作" not in svc.get_pinned()

    def test_delete_unpinned_tag_no_effect_on_pinned_current_behavior(self, svc):
        """现状：删除未置顶标签不影响置顶列表。"""
        svc.create("A")
        svc.create("B")
        svc.set_pinned(["A"])
        svc.delete("B")
        assert svc.get_pinned() == ["A"]


class TestRenameSyncsPinned:
    """现状：重命名标签同步更新置顶列表。CT-P2-02"""

    def test_rename_syncs_pinned_list_current_behavior(self, svc):
        """现状：update(old, new) 将置顶列表中的旧名替换为新名。"""
        svc.create("工作")
        svc.set_pinned(["工作"])
        svc.update("工作", "上班")
        pinned = svc.get_pinned()
        assert "工作" not in pinned
        assert "上班" in pinned

    def test_rename_unpinned_tag_no_effect_on_pinned_current_behavior(self, svc):
        """现状：重命名未置顶标签不影响置顶列表。"""
        svc.create("A")
        svc.create("B")
        svc.set_pinned(["A"])
        svc.update("B", "BB")
        assert svc.get_pinned() == ["A"]
