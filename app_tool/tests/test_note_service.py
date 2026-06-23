"""test_note_service.py — 便签 CRUD + 排序 + 标签关联测试（红灯）。"""

import time

import pytest
from datetime import datetime


class TestNoteCRUD:
    def test_create_note(self, db_conn):
        """创建便签应返回 Note 对象，且同步 FTS5。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="测试便签", content="# 内容")

        assert note.id is not None
        assert note.title == "测试便签"
        assert note.content == "# 内容"
        assert note.is_completed == 0
        assert note.completed_at is None

        # FTS5 同步验证
        row = db_conn.execute(
            "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ?", ("测试便签",)
        ).fetchone()
        # FTS5 默认分词器对中文不工作，验证 LIKE 可查
        row_like = db_conn.execute(
            "SELECT id FROM Note WHERE title LIKE ?", ("%测试便签%",)
        ).fetchone()
        assert row_like is not None

    def test_create_note_empty_content_raises(self, db_conn):
        """空内容应拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        with pytest.raises(ValueError):
            svc.create(title="", content="")

    def test_create_note_empty_title_allowed(self, db_conn):
        """空标题允许（title 0–50 字符，可为空）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="", content="只有内容")
        assert note.title == ""
        assert note.content == "只有内容"
        assert note.id is not None

    def test_get_note_by_id(self, db_conn):
        """按 ID 获取便签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        created = svc.create(title="获取测试", content="内容")
        fetched = svc.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == "获取测试"

    def test_update_note(self, db_conn):
        """更新便签 title/content/updated_at，同步 FTS5。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="旧标题", content="旧内容")
        time.sleep(0.001)
        updated = svc.update(note.id, title="新标题", content="新内容")

        assert updated.title == "新标题"
        assert updated.content == "新内容"
        assert updated.updated_at != note.updated_at

        # FTS5 旧数据应不存在，新数据应可查
        old_fts = db_conn.execute(
            "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ?", ("旧标题",)
        ).fetchone()
        # 英文词应命中 FTS5
        new_note = svc.create(title="hello update world", content="fts test")
        fts_row = db_conn.execute(
            "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ?", ("hello",)
        ).fetchone()
        assert fts_row is not None

    def test_delete_note(self, db_conn):
        """删除便签应级联删除 NoteTag、Reminder 和 FTS5。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="待删除", content="内容")
        svc.delete(note.id)

        assert svc.get_by_id(note.id) is None

    def test_delete_nonexistent_raises(self, db_conn):
        """删除不存在的便签应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        with pytest.raises(ValueError):
            svc.delete(999)

    def test_create_note_content_too_long_raises(self, db_conn):
        """内容超过 5000 字符应拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        long_content = "a" * 5001
        with pytest.raises(ValueError):
            svc.create(title="超长", content=long_content)

    def test_create_note_title_too_long_raises(self, db_conn):
        """标题超过 50 字符应拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        long_title = "a" * 51
        with pytest.raises(ValueError):
            svc.create(title=long_title, content="正常内容")


class TestCompleteToggle:
    def test_mark_complete(self, db_conn):
        """标记完成设置 completed_at 和 is_completed=1。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="完成测试", content="内容")
        completed = svc.mark_complete(note.id)

        assert completed.is_completed == 1
        assert completed.completed_at is not None

    def test_mark_complete_resets_position(self, db_conn):
        """标记完成时 position 归零。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="排序后完成", content="内容")
        svc.set_position(note.id, 5.0)
        completed = svc.mark_complete(note.id)

        assert completed.is_completed == 1
        assert completed.position == 0.0

    def test_mark_incomplete(self, db_conn):
        """取消完成清除 completed_at，is_completed=0。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="取消测试", content="内容")
        svc.mark_complete(note.id)
        incomplete = svc.mark_incomplete(note.id)

        assert incomplete.is_completed == 0
        assert incomplete.completed_at is None

    def test_mark_complete_already_completed_raises(self, db_conn):
        """spec §5.1 标记完成: 已完成的便签再次标记应拒绝（R6 幂等）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="已完成", content="内容")
        svc.mark_complete(note.id)

        with pytest.raises(ValueError, match="已完成"):
            svc.mark_complete(note.id)

    def test_mark_incomplete_already_incomplete_raises(self, db_conn):
        """spec §5.1 取消完成: 未完成的便签再次取消应拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="未完成", content="内容")

        with pytest.raises(ValueError, match="未完成"):
            svc.mark_incomplete(note.id)


class TestSorting:
    def test_get_incomplete_sorted_by_updated_at(self, db_conn):
        """未完成便签按 updated_at 降序排列。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        n1 = svc.create(title="第一", content="内容1")
        time.sleep(0.001)
        n2 = svc.create(title="第二", content="内容2")
        # 第二应该排在前面
        notes = svc.get_incomplete()
        assert notes[0].title == "第二"
        assert notes[1].title == "第一"

    def test_get_completed_sorted_by_completed_at(self, db_conn):
        """已完成便签按 completed_at 降序排列。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        n1 = svc.create(title="先完成", content="内容1")
        n2 = svc.create(title="后完成", content="内容2")
        svc.mark_complete(n1.id)
        import time
        time.sleep(0.01)
        svc.mark_complete(n2.id)

        notes = svc.get_completed()
        assert notes[0].title == "后完成"
        assert notes[1].title == "先完成"

    def test_pinned_tags_priority(self, db_conn):
        """含置顶标签的便签排在未完成区最前面。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        tag_svc = TagService(db_conn)

        # 创建标签并设为置顶（R1：使用标签名）
        tag = tag_svc.create("置顶测试标签")
        tag_svc.set_pinned([tag.name])

        normal = note_svc.create(title="普通便签", content="普通内容")
        pinned = note_svc.create(title="置顶便签", content="置顶内容")
        note_svc.add_tag(pinned.id, tag.name)

        notes = note_svc.get_incomplete()
        assert notes[0].title == "置顶便签"
        assert notes[1].title == "普通便签"

    def test_manual_pin_priority_over_tag_pin(self, db_conn):
        """手动置顶便签排在标签置顶便签前面。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        tag_svc = TagService(db_conn)

        tag = tag_svc.create("排序标签")
        tag_svc.set_pinned([tag.name])

        tag_pinned = note_svc.create(title="标签置顶", content="内容")
        note_svc.add_tag(tag_pinned.id, tag.name)

        manual_pinned = note_svc.create(title="手动置顶", content="内容")
        note_svc.pin_note(manual_pinned.id)

        normal = note_svc.create(title="普通", content="内容")

        notes = note_svc.get_incomplete()
        assert notes[0].title == "手动置顶"
        assert notes[1].title == "标签置顶"
        assert notes[2].title == "普通"

    def test_position_sorting_within_pinned_group(self, db_conn):
        """置顶区内按 position DESC 排序。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        n1 = svc.create(title="A", content="a")
        n2 = svc.create(title="B", content="b")

        svc.pin_note(n1.id)
        svc.pin_note(n2.id)

        # B 手动排序靠前
        svc.set_position(n2.id, 10.0)
        svc.set_position(n1.id, 5.0)

        notes = svc.get_incomplete()
        assert notes[0].title == "B"
        assert notes[1].title == "A"

    def test_completed_sorted_by_pin_priority(self, db_conn):
        """已完成便签：手动置顶排在前。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        n1 = svc.create(title="已完成后完成", content="a")
        n2 = svc.create(title="已完成先完成", content="b")

        svc.pin_note(n2.id)
        import time
        time.sleep(0.01)
        svc.mark_complete(n1.id)
        time.sleep(0.01)
        svc.mark_complete(n2.id)

        notes = svc.get_completed()
        # 手动置顶的排前面，即使 completed_at 更晚
        assert notes[0].title == "已完成先完成"
        assert notes[1].title == "已完成后完成"


class TestUndoDelete:
    def test_undo_delete_restores_note(self, db_conn):
        """撤销删除恢复便签内容及标签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="待撤销", content="撤销内容")
        svc.add_tag(note.id, "紧急重要")
        svc.delete(note.id)

        restored = svc.undo_delete()
        assert restored is not None
        assert restored.title == "待撤销"
        assert restored.content == "撤销内容"
        tags = svc.get_tags(restored.id)
        assert len(tags) == 1
        assert tags[0].name == "紧急重要"

    def test_undo_info_empty_initially(self, db_conn):
        """初始无撤销数据。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        assert svc.get_undo_info() is None
        assert svc.undo_delete() is None

    def test_undo_delete_only_one_level(self, db_conn):
        """仅保留最后一次删除的撤销。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)

        n1 = svc.create(title="第一", content="第一内容")
        n2 = svc.create(title="第二", content="第二内容")
        svc.delete(n1.id)
        svc.delete(n2.id)

        restored = svc.undo_delete()
        assert restored.title == "第二"
        assert restored.content == "第二内容"

    def test_undo_timeout_returns_none(self, db_conn, monkeypatch):
        """超时后撤销返回 None。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        import app_tool.controller.note_service as ns_module

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="超时测试", content="内容")
        svc.delete(note.id)

        # 模拟超时：修改 note_service 模块中已导入的常量为 -1
        monkeypatch.setattr(ns_module, "UNDO_TIMEOUT_SECONDS", -1)

        assert svc.undo_delete() is None
        assert svc.get_undo_info() is None

    def test_clear_undo(self, db_conn):
        """手动清除撤销数据。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="清除测试", content="内容")
        svc.delete(note.id)
        svc.clear_undo()

        assert svc.undo_delete() is None


class TestPinNote:
    def test_pin_note(self, db_conn):
        """手动置顶便签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="待置顶", content="内容")
        pinned = svc.pin_note(note.id)

        assert pinned.is_pinned == 1
        assert pinned.pinned_at is not None

    def test_unpin_note(self, db_conn):
        """取消手动置顶。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="待取消", content="内容")
        svc.pin_note(note.id)
        unpinned = svc.unpin_note(note.id)

        assert unpinned.is_pinned == 0
        assert unpinned.pinned_at is None

    def test_pin_already_pinned_raises(self, db_conn):
        """已置顶便签再次置顶抛出 ValueError（R6 幂等拒绝）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="已置顶", content="内容")
        svc.pin_note(note.id)
        with pytest.raises(ValueError):
            svc.pin_note(note.id)

    def test_unpin_not_pinned_raises(self, db_conn):
        """未置顶便签取消置顶抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="未置顶", content="内容")
        with pytest.raises(ValueError):
            svc.unpin_note(note.id)


class TestSortPreference:
    def test_set_and_get_sort_preference(self, db_conn):
        """设置排序偏好影响 get_incomplete 排序。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)

        # 默认 updated_at DESC → 后创建的在前
        svc.set_sort_preference("created_at")
        n1 = svc.create(title="先创建", content="a")
        import time
        time.sleep(0.01)
        n2 = svc.create(title="后创建", content="b")

        # created_at DESC → 后创建的在前
        notes = svc.get_incomplete()
        assert notes[0].title == "后创建"
        assert notes[1].title == "先创建"

    def test_sort_preference_default_is_updated_at(self, db_conn):
        """无设置时默认按 updated_at 降序。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        n1 = svc.create(title="先创建", content="a")
        import time
        time.sleep(0.01)
        n2 = svc.create(title="后创建", content="b")

        notes = svc.get_incomplete()
        assert notes[0].title == "后创建"
        assert notes[1].title == "先创建"


class TestNoteTags:
    def test_add_tag_to_note(self, db_conn):
        """为便签添加标签（R1：使用标签名）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        note_svc = NoteService(db_conn)
        tag_svc = TagService(db_conn)

        note = note_svc.create(title="标签测试", content="内容")
        tag = tag_svc.get_by_name("紧急重要")
        note_svc.add_tag(note.id, tag.name)

        tags = note_svc.get_tags(note.id)
        assert len(tags) == 1
        assert tags[0].name == "紧急重要"

    def test_duplicate_add_tag_is_idempotent(self, db_conn):
        """重复添加相同标签静默忽略（R6 幂等拒绝）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="重复标签测试", content="内容")
        svc.add_tag(note.id, "紧急重要")
        svc.add_tag(note.id, "紧急重要")  # 不应抛出异常

        tags = svc.get_tags(note.id)
        assert len(tags) == 1

    def test_add_nonexistent_tag_raises(self, db_conn):
        """添加不存在的标签抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="不存在标签", content="内容")
        with pytest.raises(ValueError):
            svc.add_tag(note.id, "不存在的标签")

    def test_remove_tag_from_note(self, db_conn):
        """从便签移除标签（R1：使用标签名）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="移除标签测试", content="内容")
        svc.add_tag(note.id, "紧急重要")
        svc.remove_tag(note.id, "紧急重要")

        tags = svc.get_tags(note.id)
        assert len(tags) == 0

    def test_remove_nonexistent_tag_silent(self, db_conn):
        """移除不存在的标签静默返回（无异常）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="移除不存在", content="内容")
        # 不应抛出异常
        svc.remove_tag(note.id, "不存在的标签")

    def test_get_note_with_tags(self, db_conn):
        """获取便签及其标签（R1：使用标签名）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="带标签便签", content="内容")
        svc.add_tag(note.id, "紧急重要")
        svc.add_tag(note.id, "紧急")

        full_note = svc.get_with_tags(note.id)
        assert full_note is not None
        assert len(full_note.tags) == 2
        assert full_note.tags[0].name == "紧急重要"

    def test_add_tag_exceeds_max_limit_raises(self, db_conn):
        """spec §3.1: 每个便签最多 3 个标签，超出时后端提交校验拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="标签上限", content="内容")
        svc.add_tag(note.id, "紧急重要")
        svc.add_tag(note.id, "紧急")
        svc.add_tag(note.id, "重要不紧急")

        with pytest.raises(ValueError, match="最多 3 个标签"):
            svc.add_tag(note.id, "P1")

    def test_create_note_with_tag_names(self, db_conn):
        """spec §5.1 新增: create() 接受 tag_names 参数并写入 NoteTag 关联。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="带标签创建", content="内容", tag_names=["紧急重要", "紧急"])

        assert note.id is not None
        assert note.content == "内容"
        tags = svc.get_tags(note.id)
        assert len(tags) == 2
        assert {t.name for t in tags} == {"紧急重要", "紧急"}

    def test_create_note_skips_nonexistent_tags(self, db_conn):
        """spec §5.1 新增: create 遇到不存在的标签时自动跳过。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="跳过不存在标签", content="内容",
                          tag_names=["紧急重要", "不存在的标签"])

        assert note.id is not None
        tags = svc.get_tags(note.id)
        assert len(tags) == 1
        assert tags[0].name == "紧急重要"

    def test_update_note_set_tag_names(self, db_conn):
        """spec §5.1 编辑: update() 接受 tag_names 替换全部标签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="标签替换", content="内容", tag_names=["紧急重要", "紧急"])
        # 替换为不同的标签集
        updated = svc.update(note.id, tag_names=["重要不紧急", "P1"])

        assert updated.id == note.id
        tags = svc.get_tags(note.id)
        assert len(tags) == 2
        assert {t.name for t in tags} == {"重要不紧急", "P1"}

    def test_update_note_clear_tags(self, db_conn):
        """spec §5.1 编辑: tag_names=[] 清空所有标签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="清空标签", content="内容", tag_names=["紧急重要", "紧急"])
        svc.update(note.id, tag_names=[])

        tags = svc.get_tags(note.id)
        assert len(tags) == 0

    def test_update_note_skip_nonexistent_tags(self, db_conn):
        """spec §5.1 编辑: update 不存在的标签自动跳过。"""
        from app_tool.model.database import init_db
        from app_tool.controller.note_service import NoteService

        init_db(db_conn)
        svc = NoteService(db_conn)
        note = svc.create(title="跳过不存在", content="内容", tag_names=["紧急重要"])
        svc.update(note.id, tag_names=["紧急", "不存在的标签"])

        tags = svc.get_tags(note.id)
        assert len(tags) == 1
        assert tags[0].name == "紧急"
