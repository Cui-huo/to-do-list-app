# P2：跨模块行为特征测试

> 锁住：标签删除联动、提醒无校验、搜索不过滤完成状态、FTS同步、跨主题守卫、Toast硬编码

---

## CT-P2-01：标签删除时从置顶列表移除

**来源**：`tag_service.py:delete()`

**现状行为**：
- `delete(name)` 删除标签后，自动检查 `get_pinned()` 列表
- 如果被删标签在置顶列表中，自动移除并保存

**测试场景**：
```python
def test_deleted_tag_removed_from_pinned_current_behavior():  # 现状
    """
    现状：delete() 自动从置顶列表中移除被删标签。
    """
    tag_svc = TagService(db_conn)

    tag_svc.create("工作")
    tag_svc.set_pinned(["工作"])
    assert "工作" in tag_svc.get_pinned()

    tag_svc.delete("工作")
    assert "工作" not in tag_svc.get_pinned()
```

---

## CT-P2-02：标签重命名时同步置顶列表

**来源**：`tag_service.py:update()`

**现状行为**：
- `update(old_name, new_name)` 在重命名成功后，检查置顶列表
- 如果 `old_name` 在置顶列表中，替换为 `new_name` 并保存

**测试场景**：
```python
def test_tag_rename_syncs_pinned_list_current_behavior():  # 现状
    """
    现状：update() 同步更新置顶列表中的标签名。
    """
    tag_svc = TagService(db_conn)

    tag_svc.create("工作")
    tag_svc.set_pinned(["工作"])

    tag_svc.update("工作", "上班")
    pinned = tag_svc.get_pinned()
    assert "工作" not in pinned
    assert "上班" in pinned
```

---

## CT-P2-03：提醒创建不校验时间

**来源**：`reminder_service.py:create()`

**现状行为**：
- `create()` 接受任意 `remind_at` 字符串，不做时间格式或范围校验
- 注释说"允许过去/未来任意时间（过去时间立即触发）"
- 只校验：便签是否存在、数量上限（MAX_REMINDERS_PER_NOTE=3）

**测试场景**：
```python
def test_reminder_accepts_past_time_current_behavior():  # 现状
    """
    现状：create() 接受过去时间，不做校验。
    """
    note_svc = NoteService(db_conn)
    rem_svc = ReminderService(db_conn)

    note = note_svc.create(title="测试", content="内容")
    reminder = rem_svc.create(note.id, "2020-01-01T00:00:00")
    assert reminder.id is not None


def test_reminder_accepts_future_time_current_behavior():  # 现状
    """
    现状：create() 接受未来时间，不做校验。
    """
    note_svc = NoteService(db_conn)
    rem_svc = ReminderService(db_conn)

    note = note_svc.create(title="测试", content="内容")
    reminder = rem_svc.create(note.id, "2099-12-31T23:59:59")
    assert reminder.id is not None


def test_reminder_accepts_arbitrary_string_current_behavior():  # 现状
    """
    现状：create() 接受任意字符串作为 remind_at，不做格式校验。
    """
    note_svc = NoteService(db_conn)
    rem_svc = ReminderService(db_conn)

    note = note_svc.create(title="测试", content="内容")
    reminder = rem_svc.create(note.id, "不是时间")
    assert reminder.id is not None
```

---

## CT-P2-04：搜索不过滤完成状态

**来源**：`search_service.py:search()`

**现状行为**：
- `search()` 的 WHERE 条件没有 `is_completed` 过滤
- 搜索结果是已完成 + 未完成便签的混合列表
- 排序始终按 `updated_at DESC`

**测试场景**：
```python
def test_search_returns_both_completed_and_incomplete_current_behavior():  # 现状
    """
    现状：search() 同时返回已完成和未完成便签。
    """
    note_svc = NoteService(db_conn)
    search_svc = SearchService(db_conn)

    n1 = note_svc.create(title="未完成", content="测试关键词")
    n2 = note_svc.create(title="已完成", content="测试关键词")
    note_svc.mark_complete(n2.id)

    results = search_svc.search(keyword="测试关键词")
    ids = [n.id for n in results]

    assert n1.id in ids
    assert n2.id in ids  # 现状：已完成的也在结果中
```

---

## CT-P2-05：FTS5 同步

**来源**：`note_service.py` + `database.py`

**现状行为**：
- `create()` → `fts_insert(conn, note_id, title, content)` + 单独 `commit()`
- `update()` → `fts_update(conn, note_id, new_title, new_content)`
- `delete()` → `fts_delete(conn, note_id)`
- FTS5 操作有独立的 `conn.commit()`（create 中有两次 commit）
- ASCII 搜索走 FTS5 MATCH，中文走 LIKE 兜底

**测试场景**：
```python
def test_fts_synced_on_create_current_behavior():  # 现状
    """
    现状：create() 后 FTS5 索引包含新便签内容。
    """
    note_svc = NoteService(db_conn)
    search_svc = SearchService(db_conn)

    note_svc.create(title="hello world", content="this is a test")

    results = search_svc.search(keyword="hello")
    assert len(results) == 1
    assert results[0].title == "hello world"


def test_fts_synced_on_update_current_behavior():  # 现状
    """
    现状：update() 后 FTS5 索引反映更新后的内容。
    """
    note_svc = NoteService(db_conn)
    search_svc = SearchService(db_conn)

    note = note_svc.create(title="old title", content="old content")
    note_svc.update(note.id, title="new title")

    results = search_svc.search(keyword="old")
    assert len(results) == 0

    results = search_svc.search(keyword="new")
    assert len(results) == 1


def test_fts_deleted_on_delete_current_behavior():  # 现状
    """
    现状：delete() 后 FTS5 索引移除对应记录。
    """
    note_svc = NoteService(db_conn)
    search_svc = SearchService(db_conn)

    note = note_svc.create(title="delete test", content="to be deleted")
    note_svc.delete(note.id)

    results = search_svc.search(keyword="delete")
    assert len(results) == 0


def test_chinese_falls_back_to_like_current_behavior():  # 现状
    """
    现状：中文关键词走 LIKE 兜底，不走 FTS5 MATCH。
    """
    note_svc = NoteService(db_conn)
    search_svc = SearchService(db_conn)

    note_svc.create(title="你好世界", content="中文测试")

    results = search_svc.search(keyword="中文")
    assert len(results) == 1
```

---

## CT-P2-06：跨主题样式编辑守卫

**来源**：`settings_screen.py:open_group1_dialog()` 等

**现状行为**：
- 在白天模式下点击"黑夜模式文字样式"的编辑按钮 → 弹出 Toast 拒绝 → 不打开弹窗
- 反之亦然
- `_on_save` 内还有第二层 `is_dark == current_dark` 检查

**测试场景**：
```python
# 需要完整 KivyMD App 环境
def test_cross_theme_editor_blocked_current_behavior():  # 现状
    """
    现状：在当前主题下编辑另一主题的样式时，被守卫拦截。
    - open_group1_dialog(theme="dark") 在 Light 模式下被拒
    - open_group1_dialog(theme="light") 在 Dark 模式下被拒
    - 守卫#1 在入口处返回，不打开弹窗
    - _on_save 中有守卫#2 做不同处理（但入口已挡，此路径在当前代码中不可达）
    """
    pass
```

---

## CT-P2-07：删除 Toast 文案硬编码

**来源**：`main_screen.py:_handle_delete()`

**现状行为**：
- 删除后 Toast 写死为 `"应用未关闭的12小时内，可以撤销最近1条删除"`
- 如果改了 `UNDO_TIMEOUT_SECONDS`（= 43200 秒），Toast 不会自动更新

**测试场景**：
```python
def test_delete_toast_text_is_hardcoded_current_behavior():  # 现状
    """
    现状：删除后 Toast 文案是硬编码字符串，
    不引用 UNDO_TIMEOUT_SECONDS 常量。
    """
    from app_tool.config import UNDO_TIMEOUT_SECONDS

    assert UNDO_TIMEOUT_SECONDS == 12 * 3600

    # 如果修改 UNDO_TIMEOUT_SECONDS 为 6 * 3600，
    # Toast 文案仍为 "应用未关闭的12小时内..."，不会变为 "6小时内"
    pass  # Toast 内容不可在无 UI 环境下验证
```
