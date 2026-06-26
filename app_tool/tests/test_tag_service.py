"""test_tag_service.py — 标签 CRUD + 置顶管理测试。"""

import pytest
import sqlite3


class TestTagCRUD:
    def test_create_tag(self, db_conn):
        """创建标签应返回新标签对象。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        tag = svc.create("自定义标签")
        assert tag.name == "自定义标签"
        assert tag.id is not None

    def test_create_duplicate_name_raises(self, db_conn):
        """创建重名标签应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.create("唯一标签")
        with pytest.raises(ValueError):
            svc.create("唯一标签")

    def test_create_empty_name_raises(self, db_conn):
        """空标签名应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.create("")
        with pytest.raises(ValueError):
            svc.create("   ")

    def test_create_name_too_long_raises(self, db_conn):
        """标签名超过 10 字符应拒绝。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.create("a" * 11)

    def test_get_all(self, db_conn):
        """获取所有标签（含种子标签）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        tags = svc.get_all()
        names = {t.name for t in tags}
        assert len(tags) == 6
        assert "紧急重要" in names

    def test_get_by_name(self, db_conn):
        """按名称获取标签（R1：使用可读名称，不暴露 ID）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        tag = svc.get_by_name("紧急重要")
        assert tag is not None
        assert tag.name == "紧急重要"

    def test_update_tag(self, db_conn):
        """更新标签名（R1：使用可读名称定位）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        tag = svc.update("紧急重要", "新的标签名")
        assert tag.name == "新的标签名"
        updated = svc.get_by_name("新的标签名")
        assert updated is not None

    def test_update_to_duplicate_name_raises(self, db_conn):
        """更新为已存在的标签名应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.update("紧急重要", "P1")

    def test_update_nonexistent_raises(self, db_conn):
        """更新不存在的标签应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.update("不存在的标签", "新名")

    def test_delete_tag(self, db_conn):
        """删除标签应移除记录（R1：使用可读名称）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.delete("紧急重要")
        assert svc.get_by_name("紧急重要") is None

    def test_delete_nonexistent_raises(self, db_conn):
        """删除不存在的标签应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.delete("不存在的标签")


class TestPinnedTags:
    def test_set_pinned_tags(self, db_conn):
        """设置置顶标签名称列表（R1：使用可读名称）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急", "重要不紧急"])
        pinned = svc.get_pinned()
        assert pinned == ["紧急重要", "紧急", "重要不紧急"]

    def test_pinned_tags_max_limit(self, db_conn):
        """超过最大置顶数应抛出 ValueError。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        with pytest.raises(ValueError):
            svc.set_pinned(["紧急重要", "紧急", "重要不紧急", "P1"])

    def test_get_pinned_empty_default(self, db_conn):
        """无设置时获取置顶应为空列表。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        pinned = svc.get_pinned()
        assert pinned == []

    def test_pinned_tags_persisted(self, db_conn):
        """置顶标签应在 UserSettings 中持久化。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急", "P1"])
        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='pinned_tags'"
        ).fetchone()
        assert row is not None

    def test_get_pinned_tags_as_objects(self, db_conn):
        """获取置顶标签对象列表（R1：按置顶顺序返回 Tag 对象）。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急"])
        tags = svc.get_pinned_tags()
        assert len(tags) == 2
        assert tags[0].name == "紧急重要"

    def test_toggle_pinned_add(self, db_conn):
        """toggle_pinned：未置顶标签变为置顶。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        result = svc.toggle_pinned("紧急重要")
        assert "紧急重要" in result
        assert len(result) == 1

    def test_toggle_pinned_remove(self, db_conn):
        """toggle_pinned：已置顶标签取消置顶。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急"])
        result = svc.toggle_pinned("紧急重要")
        assert "紧急重要" not in result
        assert result == ["紧急"]

    def test_toggle_pinned_auto_evict_earliest(self, db_conn):
        """超出置顶上限时自动淘汰最早置顶的标签。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急", "重要不紧急"])
        # 最早是"紧急重要"，添加"P1"应淘汰"紧急重要"
        result = svc.toggle_pinned("P1")
        assert result == ["紧急", "重要不紧急", "P1"]

    def test_update_tag_syncs_pinned_list(self, db_conn):
        """更新标签名时同步更新置顶列表中的名称。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急"])
        svc.update("紧急重要", "改名后标签")

        pinned = svc.get_pinned()
        assert pinned == ["改名后标签", "紧急"]

    def test_delete_tag_removes_from_pinned(self, db_conn):
        """删除标签时从置顶列表中自动移除。"""
        from app_tool.model.database import init_db
        from app_tool.controller.tag_service import TagService

        init_db(db_conn)
        svc = TagService(db_conn)
        svc.set_pinned(["紧急重要", "紧急", "P1"])
        svc.delete("紧急重要")

        pinned = svc.get_pinned()
        assert pinned == ["紧急", "P1"]
