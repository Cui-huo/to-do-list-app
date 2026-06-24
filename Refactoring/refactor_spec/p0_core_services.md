# P0：NoteService 核心行为特征测试

> 锁住：撤销副作用、标签静默跳过、排序 SQL 双分支、排序偏好持久化

---

## CT-P0-01：`get_undo_info()` 的副作用 — 超时自动清除

**来源**：`note_service.py:get_undo_info()`

**现状行为**：
- 调用 `get_undo_info()` 时，如果 `_undo_data` 存在但已超时（`> UNDO_TIMEOUT_SECONDS`），会**自动将 `_undo_data` 置为 `None`** 并返回 `None`
- 这是一个有副作用的 getter，不是纯查询

**测试场景**：
```python
def test_get_undo_info_clears_expired_data_current_behavior():  # 现状
    """
    现状：get_undo_info() 在超时后自动清除 _undo_data。
    这是一个有副作用的 getter。
    """
    svc = NoteService(db_conn)

    note = svc.create(title="测试", content="内容")
    svc.delete(note.id)

    # 手动将 deleted_at 设置为 13 小时前
    svc._undo_data["deleted_at"] = datetime.now() - timedelta(hours=13)

    # 第一次调用 → 超时，自动清除
    info = svc.get_undo_info()
    assert info is None

    # 第二次调用 → 已被清除
    info2 = svc.get_undo_info()
    assert info2 is None

    # undo_delete() 也返回 None
    result = svc.undo_delete()
    assert result is None
```

**锁定要点**：
- `get_undo_info()` 修改了 `self._undo_data`
- 超时清除发生在 getter 中，不是独立定时器

---

## CT-P0-02：`create()` 对不存在的标签静默跳过

**来源**：`note_service.py:create()` L45-L48

**现状行为**：
- `create()` 在关联标签时，对不存在的标签**不报错、不提示，静默跳过**
- 判断依据是 `ValueError` 异常消息中是否包含 `"不存在"` 字符串
- 其他类型的 `ValueError`（如"每个便签最多 N 个标签"）会**向上传播**

**测试场景**：
```python
def test_create_silently_skips_nonexistent_tags_current_behavior():  # 现状
    """
    现状：create() 在标签不存在时静默跳过。
    判断依据是异常消息字符串 "不存在"。
    """
    svc = NoteService(db_conn)

    note = svc.create(
        title="测试",
        content="内容",
        tag_names=["不存在的标签", "另一个不存在的"]
    )
    assert note.id is not None

    # 便签创建成功，但没有关联任何标签
    tags = svc.get_tags(note.id)
    assert len(tags) == 0


def test_create_reraises_non_skip_valueerror_current_behavior():  # 现状
    """
    现状：create() 中非"不存在"的 ValueError 会向上传播。
    例如：标签数量超限的异常消息不含"不存在"，应 reraise。
    """
    # 需构造超限场景：创建 4 个标签、给一个便签关联满 3 个后
    # 通过 create() 传入第 4 个标签名触发 add_tag 上限异常
    # 验证异常不被吞掉
    pass
```

**锁定要点**：
- `"不存在" not in str(e)` 字符串匹配是控制流的一部分
- 修改 `ValueError` 消息文案会破坏此逻辑

---

## CT-P0-03：`update()` 对不存在的标签静默跳过

**来源**：`note_service.py:update()` L76-L84

**现状行为**：
- 与 `create()` 相同：`update()` 中的标签同步逻辑也对不存在的标签静默跳过
- 使用相同的 `"不存在" not in str(e)` 字符串匹配

**测试场景**：
```python
def test_update_silently_skips_nonexistent_tags_current_behavior():  # 现状
    """
    现状：update() 在 tag_names 变更时，
    对不存在的标签静默跳过。
    """
    svc = NoteService(db_conn)
    note = svc.create(title="测试", content="内容")

    updated = svc.update(note.id, tag_names=["不存在的标签"])
    assert updated is not None

    tags = svc.get_tags(note.id)
    assert len(tags) == 0
```

---

## CT-P0-04：`get_incomplete()` 有置顶标签时的排序 SQL

**来源**：`note_service.py:get_incomplete()` L148-L167

**现状行为**：
- 当存在置顶标签时，SQL 使用 `SELECT DISTINCT n.* FROM Note n LEFT JOIN NoteTag nt ON n.id = nt.note_id LEFT JOIN Tag t ON nt.tag_id = t.id`
- 排序：手动置顶 → 标签置顶（`CASE WHEN t.name IN (...)`）→ 时间偏好（`n.updated_at` DESC 或 `n.created_at` DESC）
- 列引用使用 `n.` 前缀

**测试场景**：
```python
def test_get_incomplete_sort_with_pinned_tags_current_behavior():  # 现状
    """
    现状：有置顶标签时使用 LEFT JOIN + DISTINCT 的 SQL 路径。
    """
    import time
    tag_svc = TagService(db_conn)
    note_svc = NoteService(db_conn)

    tag1 = tag_svc.create("置顶标签")
    tag2 = tag_svc.create("普通标签")
    tag_svc.set_pinned(["置顶标签"])

    n1 = note_svc.create(title="含置顶标签", content="内容1", tag_names=["置顶标签"])
    time.sleep(0.001)
    n2 = note_svc.create(title="无置顶标签", content="内容2")

    notes = note_svc.get_incomplete()
    assert notes[0].id == n1.id
    assert notes[1].id == n2.id


def test_get_incomplete_manual_pin_overrides_tag_pin_current_behavior():  # 现状
    """
    现状：手动置顶优先于标签置顶。
    """
    tag_svc = TagService(db_conn)
    note_svc = NoteService(db_conn)

    tag = tag_svc.create("工作")
    tag_svc.set_pinned(["工作"])

    n1 = note_svc.create(title="含置顶标签", content="内容1", tag_names=["工作"])
    time.sleep(0.001)
    n2 = note_svc.create(title="手动置顶", content="内容2")
    note_svc.pin_note(n2.id)

    notes = note_svc.get_incomplete()
    assert notes[0].id == n2.id
    assert notes[1].id == n1.id
```

---

## CT-P0-05：`get_incomplete()` 无置顶标签时的排序 SQL

**来源**：`note_service.py:get_incomplete()` L158-L167

**现状行为**：
- 无置顶标签时，SQL 使用 `SELECT * FROM Note WHERE is_completed = 0 ORDER BY CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END, {time_col} DESC`
- 列引用**没有** `n.` 前缀（是 `updated_at` 而不是 `n.updated_at`）
- 没有 JOIN，没有 DISTINCT

**测试场景**：
```python
def test_get_incomplete_sort_without_pinned_tags_current_behavior():  # 现状
    """
    现状：无置顶标签时使用简单 SELECT * 路径（无 JOIN）。
    """
    import time
    note_svc = NoteService(db_conn)

    n1 = note_svc.create(title="较早", content="内容1")
    time.sleep(0.001)
    n2 = note_svc.create(title="较新", content="内容2")

    notes = note_svc.get_incomplete()
    assert notes[0].id == n2.id
    assert notes[1].id == n1.id
```

---

## CT-P0-06：排序偏好持久化

**来源**：`note_service.py:_get_sort_preference()` / `set_sort_preference()`

**现状行为**：
- 排序偏好存储在 `UserSettings` 表，key=`sort_preference`
- value 是 **JSON 字符串**（如 `"\"updated_at\""`，带引号）
- 默认值为 `"updated_at"`
- `_get_sort_preference()` 虽以下划线开头但被外部直接调用

**测试场景**：
```python
def test_sort_preference_default_is_updated_at_current_behavior():  # 现状
    """
    现状：首次使用时排序偏好默认为 updated_at。
    """
    note_svc = NoteService(db_conn)
    pref = note_svc._get_sort_preference()
    assert pref == "updated_at"


def test_sort_preference_stored_as_json_string_current_behavior():  # 现状
    """
    现状：排序偏好以 JSON 字符串存储（带引号）。
    """
    import json
    note_svc = NoteService(db_conn)
    note_svc.set_sort_preference("created_at")

    row = db_conn.execute(
        "SELECT value FROM UserSettings WHERE key='sort_preference'"
    ).fetchone()
    stored_value = row["value"]
    assert stored_value == '"created_at"'  # 带引号的 JSON 字符串
    assert json.loads(stored_value) == "created_at"


def test_sort_preference_rejects_invalid_value_current_behavior():  # 现状
    """
    现状：set_sort_preference() 只接受 'updated_at' 或 'created_at'，否则抛 ValueError。
    """
    note_svc = NoteService(db_conn)
    import pytest
    with pytest.raises(ValueError, match="必须为"):
        note_svc.set_sort_preference("invalid")
```
