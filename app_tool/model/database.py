"""数据库初始化：建表 / FTS5虚拟表 / 索引 / 种子标签。"""

import sqlite3
import sys
from app_tool.config import SEED_TAGS

# FTS5 可用性标记：Android SQLite 可能未编译 FTS5 扩展
_has_fts5: bool = True

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
    FTS5 不可用时静默降级，搜索回退到 LIKE。
    """
    global _has_fts5
    conn.execute(PRAGMA_FK)
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError as e:
        if "no such module: fts5" in str(e):
            _has_fts5 = False
            # 去除 FTS5 建表语句后重新执行
            schema_no_fts = _strip_fts5_from_schema(SCHEMA)
            conn.executescript(schema_no_fts)
        else:
            raise
    _seed_tags(conn)
    conn.commit()


def _seed_tags(conn: sqlite3.Connection) -> None:
    """写入种子标签（如果不存在）。"""
    for name in SEED_TAGS:
        conn.execute(
            "INSERT OR IGNORE INTO Tag (name) VALUES (?)", (name,)
        )


def _strip_fts5_from_schema(schema: str) -> str:
    """移除 FTS5 虚拟表建表语句，用于不支持 FTS5 的环境。"""
    lines = schema.split("\n")
    result: list[str] = []
    skip_until_semicolon = False
    for line in lines:
        if "CREATE VIRTUAL TABLE" in line and "fts5" in line:
            skip_until_semicolon = True
            continue
        if skip_until_semicolon:
            if ";" in line:
                skip_until_semicolon = False
            continue
        result.append(line)
    return "\n".join(result)


def has_fts5() -> bool:
    """返回当前环境是否支持 FTS5。"""
    return _has_fts5


def fts_insert(conn: sqlite3.Connection, rowid: int, title: str, content: str) -> None:
    """向 FTS5 索引插入一条记录（FTS5 不可用时静默跳过）。"""
    if not _has_fts5:
        return
    conn.execute(
        "INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)",
        (rowid, title, content),
    )


def fts_update(conn: sqlite3.Connection, rowid: int, title: str, content: str) -> None:
    """更新 FTS5 索引中的一条记录（FTS5 不可用时静默跳过）。"""
    if not _has_fts5:
        return
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (rowid,))
    conn.execute(
        "INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)",
        (rowid, title, content),
    )


def fts_delete(conn: sqlite3.Connection, rowid: int) -> None:
    """从 FTS5 索引删除一条记录（FTS5 不可用时静默跳过）。"""
    if not _has_fts5:
        return
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (rowid,))
