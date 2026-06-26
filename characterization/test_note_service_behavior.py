"""特征测试 — NoteService 核心行为（P0）。

锁住：撤销副作用、标签静默跳过、排序SQL双分支、排序偏好持久化。
对应 spec: p0_core_services.md
"""

import time
import json
from datetime import datetime, timedelta

import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService


@pytest.fixture
def svc(db_conn):
    """每个测试获得独立的 NoteService（:memory: DB）。"""
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def tag_svc(db_conn):
    init_db(db_conn)
    return TagService(db_conn)


# ═══════════════════════════════════════════════════════════
# CT-P0-01: get_undo_info() 副作用
# ═══════════════════════════════════════════════════════════

class TestUndoInfoSideEffect:
    """现状：get_undo_info() 是有副作用的 getter。"""

    def test_get_undo_info_clears_expired_data_current_behavior(self, svc):
        """现状：get_undo_info() 在超时后自动将 _undo_data 置为 None。"""
        note = svc.create(title="测试", content="内容")
        svc.delete(note.id)

        # 手动将 deleted_at 设为 13 小时前以模拟超时
        svc._undo_data["deleted_at"] = datetime.now() - timedelta(hours=13)

        # 第一次调用 → 超时，自动清除
        info = svc.get_undo_info()
        assert info is None

        # 第二次调用 → 已被清除
        assert svc.get_undo_info() is None

        # undo_delete() 也返回 None
        assert svc.undo_delete() is None

    def test_get_undo_info_modifies_internal_state_current_behavior(self, svc):
        """现状：调用 get_undo_info() 后 _undo_data 可能被清空。"""
        note = svc.create(title="测试", content="内容")
        svc.delete(note.id)

        # 设置超时
        svc._undo_data["deleted_at"] = datetime.now() - timedelta(hours=13)

        assert svc._undo_data is not None
        svc.get_undo_info()
        # 现状：_undo_data 已被清空
        assert svc._undo_data is None

    def test_get_undo_info_within_timeout_returns_data_current_behavior(self, svc):
        """现状：未超时时 get_undo_info() 返回数据且不清除。"""
        note = svc.create(title="测试", content="内容")
        svc.delete(note.id)

        info = svc.get_undo_info()
        assert info is not None
        assert info["title"] == "测试"
        assert info["content"] == "内容"

        # 数据未被清除
        assert svc._undo_data is not None


# ═══════════════════════════════════════════════════════════
# CT-P0-02: create() 标签静默跳过
# ═══════════════════════════════════════════════════════════

class TestCreateTagSkip:
    """现状：create() 对不存在的标签静默跳过，依据异常消息字符串 '不存在'。"""

    def test_create_silently_skips_nonexistent_tags_current_behavior(self, svc):
        """现状：传入不存在的标签名，便签仍创建成功，无标签关联。"""
        note = svc.create(
            title="测试",
            content="内容",
            tag_names=["完全不存在的标签名"]
        )
        assert note.id is not None
        tags = svc.get_tags(note.id)
        assert len(tags) == 0

    def test_create_tag_skip_depends_on_error_message_string_current_behavior(self, svc):
        """
        现状：跳过逻辑依赖 ValueError 消息包含 '不存在'。
        如果 add_tag 的消息改为 '标签 X 未找到'，此逻辑会失效。
        """
        note = svc.create(
            title="测试2",
            content="内容2",
            tag_names=["不存在的标签"]
        )
        assert note.id is not None
        # 便签成功创建证明 '不存在' 匹配生效


# ═══════════════════════════════════════════════════════════
# CT-P0-03: update() 标签静默跳过
# ═══════════════════════════════════════════════════════════

class TestUpdateTagSkip:
    """现状：update() 与 create() 使用相同的静默跳过逻辑。"""

    def test_update_silently_skips_nonexistent_tags_current_behavior(self, svc):
        """现状：更新时传入不存在的标签，静默跳过。"""
        note = svc.create(title="测试", content="内容")
        updated = svc.update(note.id, tag_names=["不存在的标签"])
        assert updated is not None
        tags = svc.get_tags(note.id)
        assert len(tags) == 0

    def test_update_keeps_existing_tags_when_new_ones_fail_current_behavior(self, svc, tag_svc):
        """现状：update 时既有合法标签又有不存在标签，合法标签正常关联。"""
        tag_svc.create("工作")
        note = svc.create(title="测试", content="内容", tag_names=["工作"])

        svc.update(note.id, tag_names=["工作", "不存在的标签"])
        tags = svc.get_tags(note.id)
        tag_names = [t.name for t in tags]
        assert "工作" in tag_names


# ═══════════════════════════════════════════════════════════
# CT-P0-04: get_incomplete() 有置顶标签时
# ═══════════════════════════════════════════════════════════

class TestGetIncompleteWithPinnedTags:
    """现状：有置顶标签时使用 LEFT JOIN + DISTINCT 路径。"""

    def test_tag_pinned_note_before_unpinned_note_current_behavior(self, svc, tag_svc):
        """现状：含置顶标签的便签排在不含置顶标签之前。"""
        tag_svc.create("置顶")
        tag_svc.set_pinned(["置顶"])

        n1 = svc.create(title="含置顶标签", content="c1", tag_names=["置顶"])
        time.sleep(0.001)
        n2 = svc.create(title="无置顶标签", content="c2")

        notes = svc.get_incomplete()
        assert notes[0].id == n1.id
        assert notes[1].id == n2.id

    def test_manual_pin_overrides_tag_pin_current_behavior(self, svc, tag_svc):
        """现状：手动置顶优先于标签置顶。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = svc.create(title="含置顶标签", content="c1", tag_names=["工作"])
        time.sleep(0.001)
        n2 = svc.create(title="手动置顶", content="c2")
        svc.pin_note(n2.id)

        notes = svc.get_incomplete()
        assert notes[0].id == n2.id  # 手动置顶
        assert notes[1].id == n1.id

    def test_multiple_pinned_tags_order_current_behavior(self, svc, tag_svc):
        """现状：多个便签含同一置顶标签时，按时间偏好排序。"""
        tag_svc.create("A")
        tag_svc.set_pinned(["A"])

        n1 = svc.create(title="较早", content="c1", tag_names=["A"])
        time.sleep(0.001)
        n2 = svc.create(title="较新", content="c2", tag_names=["A"])

        notes = svc.get_incomplete()
        # 默认按 updated_at DESC，较新排前
        assert notes[0].id == n2.id


# ═══════════════════════════════════════════════════════════
# CT-P0-05: get_incomplete() 无置顶标签时
# ═══════════════════════════════════════════════════════════

class TestGetIncompleteWithoutPinnedTags:
    """现状：无置顶标签时使用简单 SELECT *（无 JOIN，无 n. 前缀）。"""

    def test_sort_by_updated_at_desc_default_current_behavior(self, svc):
        """现状：默认按 updated_at DESC 排序。"""
        n1 = svc.create(title="较早", content="c1")
        time.sleep(0.001)
        n2 = svc.create(title="较新", content="c2")

        notes = svc.get_incomplete()
        assert notes[0].id == n2.id
        assert notes[1].id == n1.id

    def test_manual_pin_priority_without_pinned_tags_current_behavior(self, svc):
        """现状：无置顶标签时，手动置顶仍优先。"""
        n1 = svc.create(title="普通", content="c1")
        time.sleep(0.001)
        n2 = svc.create(title="置顶", content="c2")
        svc.pin_note(n2.id)

        notes = svc.get_incomplete()
        assert notes[0].id == n2.id
        assert notes[1].id == n1.id


# ═══════════════════════════════════════════════════════════
# CT-P0-06: 排序偏好持久化
# ═══════════════════════════════════════════════════════════

class TestSortPreference:
    """现状：排序偏好以 JSON 字符串存储，默认 updated_at。"""

    def test_default_sort_preference_is_updated_at_current_behavior(self, svc):
        """现状：首次使用时默认返回 'updated_at'。"""
        pref = svc._get_sort_preference()
        assert pref == "updated_at"

    def test_sort_preference_stored_as_json_string_current_behavior(self, svc, db_conn):
        """现状：value 是 json.dumps("updated_at") → '"updated_at"'（带引号的 JSON 字符串）。"""
        svc.set_sort_preference("created_at")
        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='sort_preference'"
        ).fetchone()
        assert row["value"] == '"created_at"'
        assert json.loads(row["value"]) == "created_at"

    def test_set_sort_preference_rejects_invalid_current_behavior(self, svc):
        """现状：只接受 'updated_at' 或 'created_at'，否则抛 ValueError。"""
        with pytest.raises(ValueError, match="必须为"):
            svc.set_sort_preference("invalid")

    def test_sort_preference_affects_get_incomplete_order_current_behavior(self, svc):
        """现状：切换到 created_at 后按创建时间排序。"""
        n1 = svc.create(title="先创建", content="c1")
        time.sleep(0.001)
        n2 = svc.create(title="后创建", content="c2")

        svc.set_sort_preference("created_at")
        notes = svc.get_incomplete()
        # created_at DESC → 后创建的排前
        assert notes[0].id == n2.id


# ═══════════════════════════════════════════════════════════
# 补充：R26 统一返回结构 — 现状不统一
# ═══════════════════════════════════════════════════════════

class TestReturnPatterns:
    """现状：NoteService 使用 raise ValueError 而非返回 (bool, str)。"""

    def test_create_raises_on_empty_content_current_behavior(self, svc):
        """现状：空内容抛 ValueError。"""
        with pytest.raises(ValueError, match="内容不能为空"):
            svc.create(title="test", content="")

    def test_create_returns_note_on_success_current_behavior(self, svc):
        """现状：成功时返回 Note 对象（非元组）。"""
        note = svc.create(title="test", content="content")
        assert note.id is not None
        assert note.title == "test"

    def test_pin_raises_when_already_pinned_current_behavior(self, svc):
        """现状：重复置顶抛 ValueError。"""
        note = svc.create(title="test", content="content")
        svc.pin_note(note.id)
        with pytest.raises(ValueError, match="已置顶"):
            svc.pin_note(note.id)

    def test_unpin_raises_when_not_pinned_current_behavior(self, svc):
        """现状：取消未置顶便签抛 ValueError。"""
        note = svc.create(title="test", content="content")
        with pytest.raises(ValueError, match="未置顶"):
            svc.unpin_note(note.id)

    def test_mark_complete_raises_when_already_completed_current_behavior(self, svc):
        """现状：重复完成抛 ValueError。"""
        note = svc.create(title="test", content="content")
        svc.mark_complete(note.id)
        with pytest.raises(ValueError, match="已完成"):
            svc.mark_complete(note.id)

    def test_mark_incomplete_raises_when_not_completed_current_behavior(self, svc):
        """现状：取消未完成的便签抛 ValueError。"""
        note = svc.create(title="test", content="content")
        with pytest.raises(ValueError, match="未完成"):
            svc.mark_incomplete(note.id)


# ═══════════════════════════════════════════════════════════
# 补充：S-03 异常消息做控制流
# ═══════════════════════════════════════════════════════════

class TestExceptionMessageControlFlow:
    """现状：create/update 中异常消息字符串决定分支。S-03"""

    def test_valueerror_with_bu_cun_zai_is_silenced_current_behavior(self, svc):
        """
        现状：包含 '不存在' 的 ValueError 被静默吞掉。
        如果 add_tag 抛出 '标签「X」不存在' → 被捕获跳过。
        如果 add_tag 抛出 '每个便签最多 3 个标签' → 向上传播。
        """
        # 创建不存在的标签 → 静默跳过
        note = svc.create(title="test", content="c", tag_names=["nonexistent"])
        assert note.id is not None
