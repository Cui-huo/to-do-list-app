"""pytest fixtures — :memory: SQLite 隔离测试。"""

import pytest
import sqlite3


@pytest.fixture
def db_conn():
    """每次测试获取全新的内存 SQLite 连接。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()
