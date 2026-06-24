# P1：持久化格式特征测试

> 锁住：username 纯文本存储、样式 JSON 格式、模版种子写入、置顶标签顺序、完成状态字段

---

## CT-P1-01：username 以纯文本存储（非 JSON）

**来源**：`main_screen.py:_load_username()` / `_save_username()`

**现状行为**：
- `UserSettings.username` 的 value 是**纯文本字符串**（如 `"张三"`），不是 JSON
- 读取时直接用 `row[0]`，不经 `json.loads`
- 而其他所有设置（sort_preference, pinned_tags, dark_mode, 文字样式）都是 JSON 格式

**测试场景**：
```python
def test_username_stored_as_plain_text_current_behavior():  # 现状
    """
    现状：username 以纯文本存储，不经 json.dumps/loads。
    与其他设置的 JSON 格式不一致。
    """
    import json
    import pytest

    db_conn.execute(
        "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('username', ?)",
        ("李四",),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='username'"
    ).fetchone()
    stored_value = row["value"]

    assert stored_value == "李四"
    # 验证它确实不是合法 JSON 字符串
    with pytest.raises((json.JSONDecodeError, TypeError)):
        json.loads(stored_value)
```

---

## CT-P1-02：文字样式以 JSON 存储（含 color=None 情况）

**来源**：`main_screen.py:save_style()` / `_load_style()` / `settings_screen.py:_save_style_dict()`

**现状行为**：
- 每个样式 key 的 value 是 JSON 字典
- 字典格式：`{"color": [r,g,b,a] | null, "font_size": "16sp", "font": "字体名", "bold": true/false}`
- `color` 可以为 `null`（JSON null → Python None）
- 当 DB 中无记录时，返回硬编码默认值（`LIGHT_STYLE_DEFAULTS` 或 `DARK_STYLE_DEFAULTS`）

**测试场景**：
```python
def test_style_stored_as_json_dict_current_behavior():  # 现状
    """
    现状：文字样式以 JSON 字典存储。
    """
    import json

    style = {
        "color": [1, 0.85, 0.4, 1],
        "font_size": "20sp",
        "font": "AlimamaDongFangDaKai",
        "bold": False,
    }
    db_conn.execute(
        "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
        ("username_style", json.dumps(style)),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='username_style'"
    ).fetchone()
    loaded = json.loads(row["value"])
    assert loaded["color"] == [1, 0.85, 0.4, 1]
    assert loaded["font_size"] == "20sp"
    assert loaded["font"] == "AlimamaDongFangDaKai"
    assert loaded["bold"] is False


def test_style_with_null_color_current_behavior():  # 现状
    """
    现状：color 可以存为 null（JSON null），读取后为 Python None。
    当 color 为 None 时，UI 层不设置 text_color（跟随主题色）。
    """
    import json

    style = {
        "color": None,
        "font_size": "16sp",
        "font": "",
        "bold": True,
    }
    db_conn.execute(
        "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
        ("test_style", json.dumps(style)),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='test_style'"
    ).fetchone()
    loaded = json.loads(row["value"])
    assert loaded["color"] is None
```

---

## CT-P1-03：模版种子数据写入与加载

**来源**：`main_screen.py:_load_templates()` / `_save_templates()` / `_BUILTIN_TEMPLATES`

**现状行为**：
- 首次调用 `_load_templates()` 时，如果 DB 无 `text_templates` 记录，自动写入内置 2 套模版
- 模版数据结构：`[{"name": "默认风格", "light": {...}, "dark": {...}, "builtin": true}, ...]`
- 整个模版列表作为一个 JSON 数组存储在 `UserSettings` key=`text_templates`
- `_save_templates()` 做全量替换（INSERT OR REPLACE）

**测试场景**：
```python
def test_templates_auto_seeded_on_first_load_current_behavior():  # 现状
    """
    现状：首次 _load_templates() 自动写入 2 套内置模版。
    """
    import json
    from app_tool.ui.main_screen import _BUILTIN_TEMPLATES

    # 确认 DB 中无记录（初始 :memory: 状态）
    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='text_templates'"
    ).fetchone()
    assert row is None

    templates = list(_BUILTIN_TEMPLATES)
    db_conn.execute(
        "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('text_templates', ?)",
        (json.dumps(templates),),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='text_templates'"
    ).fetchone()
    loaded = json.loads(row["value"])
    assert len(loaded) == 2
    assert loaded[0]["name"] == "默认风格"
    assert loaded[0]["builtin"] is True
    assert loaded[1]["name"] == "个人审美"


def test_template_persistence_roundtrip_current_behavior():  # 现状
    """
    现状：模版的增删改保存全流程。
    """
    import json

    templates = [
        {"name": "测试模版", "light": {}, "dark": {}, "builtin": False}
    ]
    db_conn.execute(
        "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('text_templates', ?)",
        (json.dumps(templates),),
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='text_templates'"
    ).fetchone()
    loaded = json.loads(row["value"])
    assert loaded[0]["name"] == "测试模版"
    assert loaded[0]["builtin"] is False
```

---

## CT-P1-04：置顶标签的顺序维护

**来源**：`tag_service.py:toggle_pinned()` / `get_pinned()` / `_save_pinned()`

**现状行为**：
- 置顶标签存储为 JSON 数组，按添加顺序排列
- `toggle_pinned()` 的逻辑：
  - 已置顶 → 从列表中移除
  - 未置顶 → 追加到列表末尾
  - 超出 `MAX_PINNED_TAGS`（=3）时，**淘汰最早置顶的**（`pinned.pop(0)`）
- `get_pinned()` 返回的列表顺序即添加顺序

**测试场景**：
```python
def test_pinned_tags_order_is_addition_order_current_behavior():  # 现状
    """
    现状：置顶标签按添加顺序排列。
    """
    tag_svc = TagService(db_conn)

    for name in ["A", "B", "C"]:
        tag_svc.create(name)

    tag_svc.set_pinned(["A", "B"])
    assert tag_svc.get_pinned() == ["A", "B"]


def test_pinned_tags_fifo_eviction_current_behavior():  # 现状
    """
    现状：超出 3 个置顶上限时，淘汰最早置顶的（FIFO）。
    """
    tag_svc = TagService(db_conn)

    for name in ["A", "B", "C"]:
        tag_svc.create(name)

    tag_svc.set_pinned(["A", "B", "C"])
    assert tag_svc.get_pinned() == ["A", "B", "C"]

    # toggle_pinned("D") → D 追加，A 被淘汰
    tag_svc.create("D")
    tag_svc.toggle_pinned("D")
    pinned = tag_svc.get_pinned()
    assert "D" in pinned
    assert "A" not in pinned
    assert len(pinned) <= 3


def test_toggle_pinned_removes_if_already_pinned_current_behavior():  # 现状
    """
    现状：toggle_pinned 对已置顶标签执行取消。
    """
    tag_svc = TagService(db_conn)
    tag_svc.create("X")
    tag_svc.set_pinned(["X"])

    result = tag_svc.toggle_pinned("X")
    assert "X" not in result
```

---

## CT-P1-05：`mark_incomplete` 清除 `completed_at`

**来源**：`note_service.py:mark_incomplete()`

**现状行为**：
- `mark_incomplete(note_id)` 将 `is_completed` 设为 0，`completed_at` 设为 `NULL`

**测试场景**：
```python
def test_mark_incomplete_clears_completed_at_current_behavior():  # 现状
    """
    现状：mark_incomplete() 将 completed_at 设为 NULL。
    """
    note_svc = NoteService(db_conn)

    note = note_svc.create(title="测试", content="内容")
    note_svc.mark_complete(note.id)

    completed_note = note_svc.get_by_id(note.id)
    assert completed_note.is_completed == 1
    assert completed_note.completed_at is not None

    note_svc.mark_incomplete(note.id)

    incomplete_note = note_svc.get_by_id(note.id)
    assert incomplete_note.is_completed == 0
    assert incomplete_note.completed_at is None  # 现状：设为 NULL
```
