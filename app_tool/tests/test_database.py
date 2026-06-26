"""test_database.py — 数据库建表/FTS5/索引/种子数据/CRUD 测试。"""

import pytest
import sqlite3


class TestCreateTables:
    def test_note_table_exists(self, db_conn):
        """Note 表应被创建且包含所有字段。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute("PRAGMA table_info(Note)")
        columns = {row["name"] for row in cursor.fetchall()}
        expected = {"id", "title", "content", "created_at", "updated_at",
                    "completed_at", "is_completed"}
        assert expected.issubset(columns)

    def test_tag_table_exists(self, db_conn):
        """Tag 表应被创建。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute("PRAGMA table_info(Tag)")
        columns = {row["name"] for row in cursor.fetchall()}
        assert {"id", "name"}.issubset(columns)

    def test_note_tag_table_exists(self, db_conn):
        """NoteTag 关联表应被创建。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute("PRAGMA table_info(NoteTag)")
        columns = {row["name"] for row in cursor.fetchall()}
        assert {"note_id", "tag_id"}.issubset(columns)

    def test_reminder_table_exists(self, db_conn):
        """Reminder 表应被创建。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute("PRAGMA table_info(Reminder)")
        columns = {row["name"] for row in cursor.fetchall()}
        assert {"id", "note_id", "remind_at", "is_triggered"}.issubset(columns)

    def test_user_settings_table_exists(self, db_conn):
        """UserSettings 表应被创建。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute("PRAGMA table_info(UserSettings)")
        columns = {row["name"] for row in cursor.fetchall()}
        assert {"key", "value"}.issubset(columns)


class TestFTS5:
    def test_fts5_virtual_table_exists(self, db_conn):
        """FTS5 虚拟表应被创建。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes_fts'"
        )
        assert cursor.fetchone() is not None

    def test_fts5_search_returns_results(self, db_conn):
        """FTS5 应能搜索到手动插入的内容。"""
        from app_tool.model.database import init_db, fts_insert

        init_db(db_conn)
        db_conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("hello world", "some test content", "2026-06-14T10:00:00", "2026-06-14T10:00:00"),
        )
        fts_insert(db_conn, 1, "hello world", "some test content")
        db_conn.commit()
        row = db_conn.execute(
            "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ?", ("hello",)
        ).fetchone()
        assert row is not None

    def test_like_search_chinese(self, db_conn):
        """中文关键词应通过 LIKE 模糊匹配命中。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        db_conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("测试标题", "这是测试内容", "2026-06-14T10:00:00", "2026-06-14T10:00:00"),
        )
        db_conn.commit()
        row = db_conn.execute(
            "SELECT id FROM Note WHERE title LIKE ? OR content LIKE ?",
            ("%测试%", "%测试%"),
        ).fetchone()
        assert row is not None


class TestIndexes:
    def test_indexes_exist(self, db_conn):
        """所有必要索引应存在。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        names = {row["name"] for row in cursor.fetchall()}
        expected = {
            "idx_note_created_at", "idx_note_updated_at",
            "idx_note_completed_at", "idx_note_is_completed",
            "idx_reminder_remind_at",
        }
        assert expected.issubset(names)


class TestSeedTags:
    def test_seed_tags_inserted(self, db_conn):
        """首次初始化后应有 6 个种子标签。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        tags = db_conn.execute("SELECT name FROM Tag ORDER BY id").fetchall()
        names = [t["name"] for t in tags]
        assert len(names) == 6
        assert "紧急重要" in names
        assert "紧急" in names
        assert "重要不紧急" in names
        assert "P1" in names
        assert "P2" in names
        assert "P3" in names

    def test_seed_tags_idempotent(self, db_conn):
        """重复初始化不产生重复标签。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        init_db(db_conn)
        count = db_conn.execute("SELECT COUNT(*) FROM Tag").fetchone()[0]
        assert count == 6


class TestCRUD:
    def test_insert_and_select_note(self, db_conn):
        """插入便签应能正确读取。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        db_conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("标题", "内容", "2026-06-14T10:00:00", "2026-06-14T10:00:00"),
        )
        db_conn.commit()
        row = db_conn.execute("SELECT * FROM Note WHERE id=1").fetchone()
        assert row["title"] == "标题"
        assert row["content"] == "内容"
        assert row["is_completed"] == 0

    def test_update_note(self, db_conn):
        """更新便签 title 应生效。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        db_conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("旧标题", "", "2026-06-14T10:00:00", "2026-06-14T10:00:00"),
        )
        db_conn.execute("UPDATE Note SET title=?, updated_at=? WHERE id=1",
                        ("新标题", "2026-06-14T12:00:00"))
        db_conn.commit()
        row = db_conn.execute("SELECT title, updated_at FROM Note WHERE id=1").fetchone()
        assert row["title"] == "新标题"
        assert row["updated_at"] == "2026-06-14T12:00:00"

    def test_delete_note(self, db_conn):
        """删除便签应从数据库中消失。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        db_conn.execute(
            "INSERT INTO Note (title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            ("标题", "", "2026-06-14T10:00:00", "2026-06-14T10:00:00"),
        )
        db_conn.execute("DELETE FROM Note WHERE id=1")
        db_conn.commit()
        row = db_conn.execute("SELECT * FROM Note WHERE id=1").fetchone()
        assert row is None

    def test_tag_unique_constraint(self, db_conn):
        """同名标签插入应抛出 IntegrityError。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute("INSERT INTO Tag (name) VALUES (?)", ("紧急重要",))
            db_conn.execute("INSERT INTO Tag (name) VALUES (?)", ("紧急重要",))

    def test_reminder_note_id_foreign_key(self, db_conn):
        """提醒插入不存在的 note_id 应失败。"""
        from app_tool.model.database import init_db

        init_db(db_conn)
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO Reminder (note_id, remind_at) VALUES (?, ?)",
                (999, "2026-06-15T09:00:00"),
            )
