"""数据库初始化：建表 / FTS5虚拟表 / 索引 / 种子标签。"""

import sqlite3
from app_tool.config import SEED_TAGS

PRAGMA_FK = "PRAGMA foreign_keys = ON;"

SCHEMA = """
CREATE TABLE IF NOT EXISTS Note (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL DEFAULT '',
    content       TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    completed_at  TEXT,
    is_completed  INTEGER DEFAULT 0,
    position      REAL DEFAULT 0,
    is_pinned     INTEGER DEFAULT 0,
    pinned_at     TEXT
);

CREATE TABLE IF NOT EXISTS Tag (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS NoteTag (
    note_id INTEGER NOT NULL REFERENCES Note(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES Tag(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

CREATE TABLE IF NOT EXISTS Reminder (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id      INTEGER NOT NULL REFERENCES Note(id) ON DELETE CASCADE,
    remind_at    TEXT NOT NULL,
    is_triggered INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS UserSettings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- 独立 FTS5 全文索引（服务层手动同步，默认分词器处理 ASCII，中文走 LIKE 兜底）
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title,
    content
);

CREATE INDEX IF NOT EXISTS idx_note_created_at   ON Note(created_at);
CREATE INDEX IF NOT EXISTS idx_note_updated_at   ON Note(updated_at);
CREATE INDEX IF NOT EXISTS idx_note_completed_at ON Note(completed_at);
CREATE INDEX IF NOT EXISTS idx_note_is_completed ON Note(is_completed);
CREATE INDEX IF NOT EXISTS idx_reminder_remind_at ON Reminder(remind_at);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """执行建表 DDL、FTS5、索引，并写入种子标签。
    幂等：多次调用不会重复建表或重复插入种子标签。
    """
    conn.execute(PRAGMA_FK)
    conn.executescript(SCHEMA)
    _seed_tags(conn)
    conn.commit()


def _seed_tags(conn: sqlite3.Connection) -> None:
    """写入种子标签（如果不存在）。"""
    for name in SEED_TAGS:
        conn.execute(
            "INSERT OR IGNORE INTO Tag (name) VALUES (?)", (name,)
        )


def fts_insert(conn: sqlite3.Connection, rowid: int, title: str, content: str) -> None:
    """向 FTS5 索引插入一条记录。"""
    conn.execute(
        "INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)",
        (rowid, title, content),
    )


def fts_update(conn: sqlite3.Connection, rowid: int, title: str, content: str) -> None:
    """更新 FTS5 索引中的一条记录（删旧 + 插新）。"""
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (rowid,))
    conn.execute(
        "INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)",
        (rowid, title, content),
    )


def fts_delete(conn: sqlite3.Connection, rowid: int) -> None:
    """从 FTS5 索引删除一条记录。"""
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (rowid,))
