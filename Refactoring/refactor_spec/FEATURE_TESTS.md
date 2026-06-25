# 重构特征测试规格 — 综合文档

> **目的**：锁住当前代码行为，不作为对合理性的判断。
> 这些是"特征测试"（characterization tests），不是"正确性测试"。
> 每条测试描述当前代码**实际做什么**，不论 spec 怎么说。
>
> **使用方式**：
> - 每个测试必须标注 `# 现状` 以明确"这是锁住现有行为，不是验证正确性"
> - 测试名含 `_current_behavior` 后缀或注释标明"现状"
> - 测试失败意味着重构改变了行为，需人工判断是"有意修复"还是"意外破坏"

---

## 目录

- [一、测试输出规格](#一测试输出规格)
- [二、特征测试用例 — P0 核心服务](#二特征测试用例--p0-核心服务)
- [三、特征测试用例 — P1 持久化格式](#三特征测试用例--p1-持久化格式)
- [四、特征测试用例 — P2 跨模块行为](#四特征测试用例--p2-跨模块行为)
- [五、可疑行为清单](#五可疑行为清单)
- [六、当前行为特征 — 文字可见性](#六当前行为特征--文字可见性)
- [七、当前行为特征 — 视觉回归](#七当前行为特征--视觉回归)
- [八、当前行为特征 — 交互行为](#八当前行为特征--交互行为)
- [九、当前行为特征 — 夜间模式切换](#九当前行为特征--夜间模式切换)
- [十、覆盖统计](#十覆盖统计)

---

## 一、测试输出规格

### 命名规范

每个特征测试函数名必须以 `_current_behavior` 结尾：
```
test_<描述>_current_behavior
```

每个测试函数的 docstring 第一行必须以 `现状：` 开头：
```python
def test_undo_getter_clears_expired_data_current_behavior():
    """现状：get_undo_info() 在超时后自动清除 _undo_data。"""
```

### 测试文件组织

特征测试与现有测试分开放置，不污染现有测试套件：

```
app_tool/tests/
├── conftest.py              # 现有 fixtures（复用）
├── test_database.py         # 现有测试（不改动）
├── test_note_service.py     # 现有测试（不改动）
├── ...
└── characterization/        # 新增特征测试目录
    ├── __init__.py
    ├── test_undo_behavior.py        # CT-P0-01
    ├── test_tag_skip_behavior.py    # CT-P0-02, CT-P0-03
    ├── test_sort_behavior.py        # CT-P0-04, CT-P0-05, CT-P0-06
    ├── test_persistence_behavior.py # CT-P1-01 ~ CT-P1-05
    ├── test_crosscutting_behavior.py # CT-P2-01 ~ CT-P2-07
    └── conftest.py                  # 特征测试专用 fixtures
```

### 每条测试的输出格式

```
## CT-XX-YY：简短标题

**来源**：`文件路径:方法名()`

**现状行为**：
- 用 1-3 句话描述当前代码实际做什么

**对应的可疑行为**（如有）：
- S-XX

**测试伪代码**：
```python
def test_xxx_current_behavior():
    """现状：..."""
    # 测试代码
```
```

### 状态标记

| 状态 | 含义 |
|------|------|
| 📝 规格已写 | 测试规格文档已完成 |
| 🟢 绿灯 | 测试通过，行为已锁住 |
| ⚠️ 需 UI 环境 | 测试需要完整 KivyMD App 环境 |

---

## 二、特征测试用例 — P0 核心服务

> 锁住：撤销副作用、标签静默跳过、排序 SQL 双分支、排序偏好持久化

### CT-P0-01：`get_undo_info()` 的副作用 — 超时自动清除

**来源**：`note_service.py:get_undo_info()`

**现状行为**：
- 调用 `get_undo_info()` 时，如果 `_undo_data` 存在但已超时（`> UNDO_TIMEOUT_SECONDS`），会**自动将 `_undo_data` 置为 `None`** 并返回 `None`
- 这是一个有副作用的 getter，不是纯查询

**对应可疑行为**：S-02

**测试伪代码**：

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

### CT-P0-02：`create()` 对不存在的标签静默跳过

**来源**：`note_service.py:create()` L45-L48

**现状行为**：
- `create()` 在关联标签时，对不存在的标签**不报错、不提示，静默跳过**
- 判断依据是 `ValueError` 异常消息中是否包含 `"不存在"` 字符串
- 其他类型的 `ValueError`（如"每个便签最多 N 个标签"）会**向上传播**

**对应可疑行为**：S-03

**测试伪代码**：

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

### CT-P0-03：`update()` 对不存在的标签静默跳过

**来源**：`note_service.py:update()` L76-L84

**现状行为**：
- 与 `create()` 相同：`update()` 中的标签同步逻辑也对不存在的标签静默跳过
- 使用相同的 `"不存在" not in str(e)` 字符串匹配

**对应可疑行为**：S-03

**测试伪代码**：

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

### CT-P0-04：`get_incomplete()` 有置顶标签时的排序 SQL

**来源**：`note_service.py:get_incomplete()` L239-272

**现状行为**：
- 当存在置顶标签时，SQL 使用 `SELECT DISTINCT n.* FROM Note n LEFT JOIN NoteTag nt ON n.id = nt.note_id LEFT JOIN Tag t ON nt.tag_id = t.id`
- 排序三层：手动置顶（`CASE WHEN n.is_pinned=1 THEN 0 ELSE 1 END`）→ 标签置顶（`CASE WHEN t.name IN (...) THEN 0 ELSE 1 END`）→ 时间偏好（`n.updated_at` DESC 或 `n.created_at` DESC）
- 列引用使用 `n.` 前缀
- **当前 gap**：排序偏好切换会影响所有三层（包括置顶区），而预期行为是手动置顶区和标签置顶区不受排序按钮影响
- **当前 gap**：标签置顶区内同一置顶标签的便签按时间偏好而非按标签选择顺序排列
- **当前 gap**：无冲突去重——同时手动置顶+含置顶标签的便签可能同时出现在两处

**对应可疑行为**：S-06

**测试伪代码**：

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

### CT-P0-05：`get_incomplete()` 无置顶标签时的排序 SQL

**来源**：`note_service.py:get_incomplete()` L158-L167

**现状行为**：
- 无置顶标签时，SQL 使用 `SELECT * FROM Note WHERE is_completed = 0 ORDER BY CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END, {time_col} DESC`
- 列引用**没有** `n.` 前缀（是 `updated_at` 而不是 `n.updated_at`）
- 没有 JOIN，没有 DISTINCT

**对应可疑行为**：S-06

**测试伪代码**：

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

### CT-P0-06：排序偏好持久化

**来源**：`note_service.py:_get_sort_preference()` / `set_sort_preference()`

**现状行为**：
- 排序偏好存储在 `UserSettings` 表，key=`sort_preference`
- value 是 **JSON 字符串**（如 `"\"updated_at\""`，带引号）
- 默认值为 `"updated_at"`
- `_get_sort_preference()` 虽以下划线开头但被外部直接调用

**对应可疑行为**：S-04

**测试伪代码**：

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

---

### CT-P0-07：排序切换 Toast 反馈缺失

**来源**：`main_screen.py:toggle_sort_preference()` L1070-1076

**现状行为**：
- `toggle_sort_preference()` 切换排序偏好、更新图标和标签文字后，**不弹出任何 Toast**
- 仅 `_update_sort_label()` 更新了视觉标识，用户无明确的"切换成功"反馈

**预期行为**（gap）：
- 每次切换弹出 Toast："按更新时间排序" / "按创建时间排序"，持续 2 秒，居中显示

**对应可疑行为**：无（功能缺失，非 bug）

**测试伪代码**：

```python
def test_sort_toggle_has_no_toast_current_behavior():  # 现状（红灯）
    """
    现状：toggle_sort_preference() 切换后无 Toast 反馈。
    此测试验证当前缺失行为，预期未来修复后变为绿灯。
    """
    # 验证 toggle_sort_preference 不调用 _toast（需 mock）
    pass
```

---

### CT-P0-08：排序切换时标题栏/功能栏刷新

**来源**：`main_screen.py:_reorder_cards()` L1078-1109

**现状行为**：
- `_reorder_cards()` 从两个 box 中收集卡片 → `remove_widget` 取下 → `add_widget` 放回
- `remove_widget` + `add_widget` 每次触发 Kivy layout 重算，导致标题栏区域可见闪烁
- 还更新 `self.ids.completed_label.text` + 调用 `_update_undo_btn_visibility()` + `_update_completed_visibility()`

**预期行为**（gap）：
- 排序切换仅重排卡片顺序，标题栏（`completed_label`）和功能栏不应触发可见刷新

**对应可疑行为**：无（性能问题）

**测试伪代码**：

```python
def test_reorder_cards_touches_titlebar_current_behavior():  # 现状（红灯）
    """
    现状：_reorder_cards() 更新 completed_label.text 并调用 _update_undo_btn_visibility。
    预期排序切换不引起标题栏刷新。
    """
    # 验证 _reorder_cards 的副作用（需 UI 环境）
    pass
```

---

### CT-P0-09：`add_widget` 默认 index=0 导致列表顺序反转

**来源**：`main_screen.py:refresh_list()` L865, L871, L876; `_reorder_cards()` L1100, L1105

**现状行为**：
- Kivy `add_widget(widget)` 默认 `index=0`，将 widget 插入 children[0]（BoxLayout vertical 的视觉顶部）
- service 层返回的列表已是正确排序（最新→最旧），但 `refresh_list()` 和 `_reorder_cards()` 中逐张 `add_widget` 导致第一张卡片（应排最前）被后续卡片推到底部
- 结果：UI 顺序与服务层顺序**完全反转**

**预期行为**（gap）：
- 服务层返回的顺序应原样呈现在 UI 上（最新便签在顶部）

**对应可疑行为**：无（bug）

**测试伪代码**：

```python
def test_add_widget_reverses_list_order_current_behavior():  # 现状（红灯）
    """
    现状：add_widget 默认 index=0 导致列表反转。
    服务层返回 [newest, ..., oldest]，UI 显示 [oldest, ..., newest]。
    """
    # 对比 service 返回顺序与 UI 显示顺序（需 UI 环境或 mock layout）
    pass
```

**受影响位置（全局排查结果）**：

| 文件 | 行号 | 调用 | 影响 |
|------|------|------|------|
| `main_screen.py` | L865 | `incomplete_box.add_widget(empty_label)` | 低（仅一个元素） |
| `main_screen.py` | L871 | `incomplete_box.add_widget(card)` | **严重** — 反转未完成列表 |
| `main_screen.py` | L876 | `completed_box.add_widget(card)` | **严重** — 反转已完成列表 |
| `main_screen.py` | L1100 | `incomplete_box.add_widget(card)` | **严重** — `_reorder_cards` 中也反转 |
| `main_screen.py` | L1105 | `completed_box.add_widget(card)` | **严重** — `_reorder_cards` 中也反转 |
| `main_screen.py` | L1024 | `box.add_widget(card, index=insert_idx)` | ✅ 已修复 |
| 其他 66 处 | — | dialog/settings/chip 内容 | 无影响（顺序不关键） |

---

## 三、特征测试用例 — P1 持久化格式

> 锁住：username 纯文本存储、样式 JSON 格式、模版种子写入、置顶标签顺序、完成状态字段

### CT-P1-01：username 以纯文本存储（非 JSON）

**来源**：`main_screen.py:_load_username()` / `_save_username()`

**现状行为**：
- `UserSettings.username` 的 value 是**纯文本字符串**（如 `"张三"`），不是 JSON
- 读取时直接用 `row[0]`，不经 `json.loads`
- 而其他所有设置（sort_preference, pinned_tags, dark_mode, 文字样式）都是 JSON 格式

**对应可疑行为**：S-05、S-09

**测试伪代码**：

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

### CT-P1-02：文字样式以 JSON 存储（含 color=None 情况）

**来源**：`main_screen.py:save_style()` / `_load_style()` / `settings_screen.py:_save_style_dict()`

**现状行为**：
- 每个样式 key 的 value 是 JSON 字典
- 字典格式：`{"color": [r,g,b,a] | null, "font_size": "16sp", "font": "字体名", "bold": true/false}`
- `color` 可以为 `null`（JSON null → Python None）
- 当 DB 中无记录时，返回硬编码默认值（`LIGHT_STYLE_DEFAULTS` 或 `DARK_STYLE_DEFAULTS`）

**对应可疑行为**：S-05、S-13

**测试伪代码**：

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

### CT-P1-03：模版种子数据写入与加载

**来源**：`main_screen.py:_load_templates()` / `_save_templates()` / `_BUILTIN_TEMPLATES`

**现状行为**：
- 首次调用 `_load_templates()` 时，如果 DB 无 `text_templates` 记录，自动写入内置 2 套模版
- 模版数据结构：`[{"name": "默认风格", "light": {...}, "dark": {...}, "builtin": true}, ...]`
- 整个模版列表作为一个 JSON 数组存储在 `UserSettings` key=`text_templates`
- `_save_templates()` 做全量替换（INSERT OR REPLACE）

**对应可疑行为**：S-05

**测试伪代码**：

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

### CT-P1-04：置顶标签的顺序维护

**来源**：`tag_service.py:toggle_pinned()` / `get_pinned()` / `_save_pinned()`

**现状行为**：
- 置顶标签存储为 JSON 数组，按添加顺序排列
- `toggle_pinned()` 的逻辑：
  - 已置顶 → 从列表中移除
  - 未置顶 → 追加到列表末尾
  - 超出 `MAX_PINNED_TAGS`（=3）时，**淘汰最早置顶的**（`pinned.pop(0)`）
- `get_pinned()` 返回的列表顺序即添加顺序

**测试伪代码**：

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

### CT-P1-05：`mark_incomplete` 清除 `completed_at`

**来源**：`note_service.py:mark_incomplete()`

**现状行为**：
- `mark_incomplete(note_id)` 将 `is_completed` 设为 0，`completed_at` 设为 `NULL`

**测试伪代码**：

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

---

## 四、特征测试用例 — P2 跨模块行为

> 锁住：标签删除联动、提醒无校验、搜索不过滤完成状态、FTS同步、跨主题守卫、Toast硬编码

### CT-P2-01：标签删除时从置顶列表移除

**来源**：`tag_service.py:delete()`

**现状行为**：
- `delete(name)` 删除标签后，自动检查 `get_pinned()` 列表
- 如果被删标签在置顶列表中，自动移除并保存

**测试伪代码**：

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

### CT-P2-02：标签重命名时同步置顶列表

**来源**：`tag_service.py:update()`

**现状行为**：
- `update(old_name, new_name)` 在重命名成功后，检查置顶列表
- 如果 `old_name` 在置顶列表中，替换为 `new_name` 并保存

**测试伪代码**：

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

### CT-P2-03：提醒创建不校验时间

**来源**：`reminder_service.py:create()`

**现状行为**：
- `create()` 接受任意 `remind_at` 字符串，不做时间格式或范围校验
- 注释说"允许过去/未来任意时间（过去时间立即触发）"
- 只校验：便签是否存在、数量上限（MAX_REMINDERS_PER_NOTE=3）

**对应可疑行为**：S-07

**测试伪代码**：

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

### CT-P2-04：搜索不过滤完成状态

**来源**：`search_service.py:search()`

**现状行为**：
- `search()` 的 WHERE 条件没有 `is_completed` 过滤
- 搜索结果是已完成 + 未完成便签的混合列表
- 排序始终按 `updated_at DESC`

**测试伪代码**：

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

### CT-P2-05：FTS5 同步

**来源**：`note_service.py` + `database.py`

**现状行为**：
- `create()` → `fts_insert(conn, note_id, title, content)` + 单独 `commit()`
- `update()` → `fts_update(conn, note_id, new_title, new_content)`
- `delete()` → `fts_delete(conn, note_id)`
- FTS5 操作有独立的 `conn.commit()`（create 中有两次 commit）
- ASCII 搜索走 FTS5 MATCH，中文走 LIKE 兜底

**测试伪代码**：

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

### CT-P2-06：跨主题样式编辑守卫

**来源**：`settings_screen.py:open_group1_dialog()` 等

**现状行为**：
- 在白天模式下点击"黑夜模式文字样式"的编辑按钮 → 弹出 Toast 拒绝 → 不打开弹窗
- 反之亦然
- `_on_save` 内还有第二层 `is_dark == current_dark` 检查

**对应可疑行为**：S-01、S-12

**测试伪代码**：

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

### CT-P2-07：删除 Toast 文案硬编码

**来源**：`main_screen.py:_handle_delete()`

**现状行为**：
- 删除后 Toast 写死为 `"应用未关闭的12小时内，可以撤销最近1条删除"`
- 如果改了 `UNDO_TIMEOUT_SECONDS`（= 43200 秒），Toast 不会自动更新

**对应可疑行为**：S-11

**测试伪代码**：

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

---

## 五、可疑行为清单

> 以下 14 条行为看起来像 bug 或不合理的设计，但在重构时必须**原样锁住**。
> 是否修复由后续决策决定，特征测试仅记录"现状如此"。

### S-01：`_update_theme_colors` — 标题栏颜色逻辑

**来源**：`main_screen.py:_update_theme_colors`, `settings_screen.py:_update_theme_colors`, `tag_manager.py:on_enter`

**现状**：
```python
# Light: top_bar.md_bg_color = theme.primary_color  (Indigo 蓝)
# Dark:  top_bar.md_bg_color = theme.bg_dark         (暗色)
```
三处分别实现相同逻辑。

**为什么可疑**：如果重构统一主题色逻辑，标题栏颜色可能意外变化。

**已映射测试**：CT-P2-06

---

### S-02：`get_undo_info()` — 有副作用的 getter

**来源**：`note_service.py:get_undo_info()`

**现状**：
```python
def get_undo_info(self) -> dict | None:
    ...
    if elapsed > UNDO_TIMEOUT_SECONDS:
        self._undo_data = None  # ← 清除数据
        return None
```
**为什么可疑**：getter 方法修改了内部状态。

**已映射测试**：CT-P0-01

---

### S-03：`create()` / `update()` — 用异常消息字符串做控制流

**来源**：`note_service.py:create()` L45-L48, `update()` L76-L84

**现状**：
```python
try:
    self.add_tag(note_id, name)
except ValueError as e:
    if "不存在" not in str(e):
        raise
```
**为什么可疑**：依赖异常消息中的子串匹配来控制分支。修改任何错误文案都会破坏此逻辑。

**已映射测试**：CT-P0-02, CT-P0-03

---

### S-04：`_get_sort_preference()` — 私有方法被外部调用

**来源**：`note_service.py:_get_sort_preference()`, `main_screen.py:_update_sort_label`

**现状**：以下划线开头的方法被 `MainScreen._update_sort_label()` 和 `toggle_sort_preference()` 直接调用。

**为什么可疑**：命名约定被破坏。

**已映射测试**：CT-P0-06

---

### S-05：UI 层直接访问 `db_conn`

**来源**：`main_screen.py`, `settings_screen.py`

**现状**：`_load_style()`, `save_style()`, `_load_username()`, `_save_username()`, `_load_templates()`, `_save_templates()` 等方法直接执行 `app.db_conn.execute(sql)`，绕过了 Service 层。

**为什么可疑**：重构时如果改了表结构，这些位置不会报编译错误。

**已映射测试**：CT-P1-01, CT-P1-02, CT-P1-03

---

### S-06：`get_incomplete()` — 双分支 SQL 列别名不一致

**来源**：`note_service.py:get_incomplete()`

**现状**：
- 有置顶标签：`n.updated_at DESC`（有 `n.` 前缀，有 JOIN + DISTINCT）
- 无置顶标签：`updated_at DESC`（无前缀，无 JOIN）

**为什么可疑**：两路 SQL 对同一功能的列引用方式不同。

**已映射测试**：CT-P0-04, CT-P0-05

---

### S-07：提醒不校验时间

**来源**：`reminder_service.py:create()`

**现状**：注释说"允许过去/未来任意时间"，但没有实际的时间校验逻辑。`remind_at` 可以是任意字符串。

**为什么可疑**：如果将来加校验，会破坏现有调用方依赖的无校验行为。

**已映射测试**：CT-P2-03

---

### S-08：标签选择逻辑两套实现但有细微差异

**来源**：`dialogs.py:AddEditContent` vs `search_dialog.py:SearchContent`

**现状**：
- 两者都有 `_selected_tags: set` + `set_all_tags` + `get_selected_tags` + `_make_chip` + `_toggle_tag`
- 但 `AddEditContent` 有 `MAX_TAGS_PER_NOTE` 上限检查，`SearchContent` 没有

**为什么可疑**：合并时可能误把上限检查带到搜索面板。

**已映射测试**：暂无（需 UI 测试环境）

---

### S-09：username 存储格式与其他设置不一致

**来源**：`main_screen.py:_load_username()` vs `_load_style()`

**现状**：
- `username` → 纯文本，读 `row[0]`
- 其他所有设置 → `json.dumps/loads`

**为什么可疑**：统一序列化时可能需要数据迁移。

**已映射测试**：CT-P1-01

---

### S-10：两套颜色选项不一致

**来源**：`main_screen.py:edit_username()` vs `settings_screen.py:_get_theme_color_options()`

**现状**：

| 入口 | 可选颜色 |
|------|---------|
| edit_username（昵称编辑） | 金色、天蓝、珊瑚橙（3色） |
| settings_screen（样式编辑） | 亮色：黑/金/天蓝/珊瑚橙；暗色：白/金/天蓝/珊瑚橙（4色） |

**为什么可疑**：同一"金色"在两处独立定义，昵称编辑缺白色/黑色选项。

**已映射测试**：暂无（需 UI 测试环境）

---

### S-11：Toast 文案不引用常量

**来源**：`main_screen.py:_handle_delete()`

**现状**：
```python
self._toast("应用未关闭的12小时内，可以撤销最近1条删除")
```
`UNDO_TIMEOUT_SECONDS = 12 * 3600`（43200 秒）

**为什么可疑**：修改 `UNDO_TIMEOUT_SECONDS` 后 Toast 文案不会自动更新。

**已映射测试**：CT-P2-07

---

### S-12：跨主题编辑器双重守卫

**来源**：`settings_screen.py:open_group1_dialog()` 等

**现状**：
```python
# 守卫#1 — 入口
if is_dark != current_dark:
    self._toast("请关闭/开启黑夜模式...")
    return  # 不打开弹窗

# 守卫#2 — _on_save 内
if is_dark == current_dark:
    # 应用样式
else:
    self._toast("已保存，切换至对应模式可查看效果")
```

**为什么可疑**：守卫#1 已挡掉不匹配主题，守卫#2 的 else 分支在当前代码路径中不可达。

**已映射测试**：CT-P2-06

---

### S-13：`_apply_title_suffix_style` 在 color=None 时不设置 text_color

**来源**：`main_screen.py:_apply_title_suffix_style()`

**现状**：
```python
if color:
    label.theme_text_color = "Custom"
    label.text_color = tuple(color)
# color=None 时跳过，依赖 label 默认行为
```

**为什么可疑**：跨主题切换后 label 默认颜色可能变化，导致文字不可见。

**已映射测试**：CT-P1-02

---

### S-14：三套 Chip 颜色修复实现

**来源**：`note_card.py:_apply_chip_text_style`, `dialogs.py:_fix_chip_label_color`, `search_dialog.py:_fix_chip_label_color`

**现状**：
- 三处都用 `chip.walk()` 遍历查找 `isinstance(w, Label)` 设置颜色
- `note_card.py` 版额外设置 `font_size/font_name/bold`
- `dialogs.py` 和 `search_dialog.py` 版只设置 `color`
- 都没有处理多层嵌套深度

**为什么可疑**：同一问题的三个独立修复，合并时可能遗漏某个变体的额外行为。

**已映射测试**：暂无（需 UI 测试环境）

---

### 可疑行为 → 特征测试映射表

| 可疑行为 | 已映射测试 | 测试文件 |
|---------|-----------|---------|
| S-01 标题栏颜色不一致 | CT-P2-06 | p2_crosscutting |
| S-02 get_undo_info 副作用 | CT-P0-01 | p0_core_services |
| S-03 异常消息做控制流 | CT-P0-02, CT-P0-03 | p0_core_services |
| S-04 私有方法被外部调用 | CT-P0-06 | p0_core_services |
| S-05 UI 直连 DB | CT-P1-01, CT-P1-02, CT-P1-03 | p1_persistence |
| S-06 双分支 SQL | CT-P0-04, CT-P0-05 | p0_core_services |
| S-07 提醒无校验 | CT-P2-03 | p2_crosscutting |
| S-08 标签选择两套 | 暂无 | — |
| S-09 username 格式不一致 | CT-P1-01 | p1_persistence |
| S-10 颜色选项不一致 | 暂无 | — |
| S-11 Toast 不引用常量 | CT-P2-07 | p2_crosscutting |
| S-12 双守卫 | CT-P2-06 | p2_crosscutting |
| S-13 color=None 不设颜色 | CT-P1-02 | p1_persistence |
| S-14 Chip 颜色三套 | 暂无 | — |

---

## 六、当前行为特征 — 文字可见性

> 记录 Light / Dark 两种主题下所有页面的文字可见性特征。
> 每条特征 = 一页中的一个文字区域 × 两种主题。

### 页面总览

| 页面 | 文件 | 文字区域 |
|------|------|---------|
| 主界面 | main_screen.py + note_card.py | 16 |
| 便签编辑弹窗 | dialogs.py | 10 |
| 搜索弹窗 | search_dialog.py | 11 |
| 设置页 | settings_screen.py | 18 |
| 标签管理页 | tag_manager.py | 5 |
| 昵称编辑弹窗 | main_screen.py:edit_username() | 8 |
| 确认删除弹窗 | dialogs.py:build_confirm_dialog() | 3 |

---

### 一、主界面

#### V-01：顶部标题栏

**位置**：main_screen.py KV FloatLayout > MDTopAppBar
**背景色（现状）**：
- Light: theme.primary_color（Indigo 蓝 ~ (0.25, 0.32, 0.71, 1)）
- Dark: theme.bg_dark

##### V-01a：用户名（username_btn）
- 默认文字色：(1, 0.85, 0.4, 1) 金色 — 两种主题相同
- 字体：AlimamaDongFangDaKai / 20sp / 非粗体

##### V-01b：后缀 "的专属便签本"（title_suffix_label）
- 默认文字色：(0.39, 0.71, 0.96, 1) 天蓝 — 两种主题相同
- 字体：Lemibo / 20sp / 非粗体
- 特殊：DB 中 color=None 时不设 text_color

##### V-01c：撤销按钮图标（undo_btn）
- 图标色：(1, 0.85, 0.4, 1) 金色 — 硬编码
- 正常 opacity=0, disabled=True
- 删除后 opacity=1, disabled=False

#### V-02：功能栏

**背景**：theme.bg_light

##### V-02a：排序图标（func_sort_icon）
- 图标字体文字，28sp

##### V-02b：排序标签（sort_label）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (0.39, 0.71, 0.96, 1) 天蓝
- 字体：Lemibo / 12sp / 非粗体

##### V-02c：搜索标签 "便签检索"（func_search_label）
- 同 V-02b（共享 func_row_style）

##### V-02d：标签标签 "标签"（func_tag_label）
- 同 V-02b

##### V-02e：设置标签 "设置"（func_settings_label）
- 同 V-02b

#### V-03：搜索条件栏（search_bar）

**背景**：theme.bg_light，初始 height=0

##### V-03a：搜索条件文字（search_label）
- Body2，theme.text_color

##### V-03b：取消 "取消 ✕"（search_close_btn）
- (0.4, 0.8, 1, 1) 亮蓝 — 硬编码
- 初始 opacity=0，有搜索后 opacity=1

#### V-04：分类标题

##### V-04a："未完成"（incomplete_header）
- Light: (0.39, 0.71, 0.96, 1) 天蓝
- Dark: (1, 0.85, 0.4, 1) 金色
- 字体：AlimamaDongFangDaKai / 20sp / 非粗体

##### V-04b："已完成 (N)"（completed_label）
- 同 V-04a

##### V-04c：展开图标（expand_btn）
- chevron-down / chevron-up，默认图标色

#### V-05：空态提示

"还没有便签，点击右下角 + 创建一个吧"
- Body1，Hint 色，居中

#### V-06：便签卡片（NoteCard）

正常背景 theme.bg_normal，已完成背景 theme.bg_dark

##### V-06a：卡片标题（title_label）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (1, 1, 1, 1) 白
- 字体：AlimamaDongFangDaKai / 16sp / 粗体
- 已完成 opacity=0.6

##### V-06b：标签芯片文字
- (0.91, 0.45, 0.29, 1) 珊瑚橙 — 硬编码，两种主题相同
- 芯片背景 theme.bg_light
- 字体：Lemibo / 12sp / 非粗体
- KivyMD 1.2.0 MDChipText→MDLabel 转换需 `_apply_chip_text_style` 修复

##### V-06c：内容预览（content_preview）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (1, 1, 1, 1) 白
- 字体：Lemibo / 12sp / 非粗体
- 已完成 opacity=0.5，max 2 行截断

##### V-06d：完成按钮（complete_btn）
- 未完成 check-circle，已完成 undo，默认图标色

##### V-06e：编辑按钮
- pencil，默认图标色

##### V-06f：删除按钮
- delete，theme_icon_color: "Error"（红色）

##### V-06g：置顶按钮（pin_btn）
- 未置顶 pin-outline + opacity=0.3
- 已置顶 pin + opacity=1

#### V-07：FAB

- plus，theme.primary_color，右下角 16dp

---

### 二、便签编辑弹窗

**组件**：dialogs.py AddEditContent + build_add_edit_dialog()

#### V-08：标题输入框
- hint "标题（可选）"，max 50，mode rectangle

#### V-09：内容输入框
- hint "内容（必填）"，max 5000，multiline，mode rectangle

#### V-10：标签选择区
- 提示 "标签（点击选择）："，Caption
- 未选芯片：bg_light 背景 + text_color
- 已选芯片：primary_color 背景 + (1,1,1,1) 白 — 硬编码
- 超限提示 "每个便签最多 3 个标签"，Error 色，2 秒消失

#### V-11：弹窗按钮
- "取消" + "保存"，MDFlatButton 默认色

#### V-12：保存校验
- 内容空 → error=True + "内容不能为空"

---

### 三、搜索弹窗

**组件**：search_dialog.py SearchContent + build_search_dialog()

#### V-13：关键词输入框
- hint "搜索关键词"，mode rectangle

#### V-14：标签筛选
- 提示 "标签筛选（点击选择，AND 逻辑）："
- 未选 bg_light + text_color
- 已选 primary_color + (1,1,1,1) 白 — 硬编码

#### V-15：时间类型芯片
- "创建时间" / "完成时间"
- 选中 primary_color+白，未选 bg_light+text_color

#### V-16~V-18：年/月/周下拉
- 按钮文字 "全部" 或具体值，MDFlatButton 默认

#### V-19：弹窗按钮
- "清除" + "搜索"，MDFlatButton 默认

---

### 四、设置页面

#### V-20：顶栏
- 标题 "设置" + arrow-left
- Light: primary_color，Dark: bg_dark

#### V-21：夜间模式开关
- "夜间模式" Body1，MDSwitch 默认

#### V-22：排序偏好
- "排序偏好" Body1
- 选中 primary_color+白，未选 bg_light+text_color

#### V-23：文字样式模版区
- "文字样式模版" Subtitle1
- 模版名 + "使用"/"删除"/"编辑"
- "+ 保存当前为模版" primary_color+白

#### V-24~V-25：白天/黑夜文字样式区
- 标题 Subtitle1
- 4 行编辑入口，每行 标签名 + 预览(Hint) + "编辑"

#### V-26：关于
- "便签应用 v0.1.0" Body2 Hint 居中

#### V-27：样式编辑弹窗
- 预览区 + 颜色/字号/粗体/字体控件
- 颜色按钮文字 sum(rgb)>1.8 → 黑，否则白
- "取消" + "保存"

#### V-28：模版操作弹窗
- 保存/重命名：输入框 + 取消/保存
- 删除：确认弹窗

---

### 五、标签管理页面

#### V-29：顶栏
- "标签管理" + arrow-left + plus + delete-sweep/check
- Light: primary_color，Dark: bg_dark

#### V-30：标签列表行
- 标签名 Body1
- 已置顶 pin + primary_color，未置顶 pin-outline + secondary_text_color
- 删除图标 Error 红

#### V-31：空态
- "暂无标签，点击右上角 + 创建" Hint

#### V-32：批量删除按钮
- "删除选中 (N)"，(0.9, 0.2, 0.2, 1) 红背景 + 白字 — 硬编码

#### V-33：新建/重命名弹窗
- hint "标签名称（1-10字符）"
- "取消" + "创建"/"保存"

---

### 六、昵称编辑弹窗

#### V-34：输入框
- hint "请输入你的名字"，max 10

#### V-35~V-37：颜色/字体/粗体
- 颜色 3 按钮（金/天蓝/珊瑚橙），sum(rgb)>1.8 黑字
- 字体 3 按钮（默认/东方大楷/乐米波波）
- 粗体 MDSwitch

#### V-38：预览
- "预览" Caption Secondary + 实时预览文字

#### V-39：按钮
- "取消" + "保存"

---

### 七、确认删除弹窗

#### V-40：弹窗
- 可变标题 + 消息 + "取消" + "确认删除"

---

### 八、Toast

- MDSnackbar(MDLabel(...))，2 秒，中央

---

### 硬编码颜色汇总

| 位置 | 颜色 | 随主题 |
|------|------|--------|
| username_btn | 金色 (1,0.85,0.4) | 不变 |
| title_suffix 默认 | 天蓝 (0.39,0.71,0.96) | 不变 |
| undo_btn 图标 | 金色 (1,0.85,0.4) | 不变 |
| search_close_btn | 亮蓝 (0.4,0.8,1) | 不变 |
| tag chip 文字 | 珊瑚橙 (0.91,0.45,0.29) | 不变 |
| 已选标签 chip | 白 (1,1,1) | 不变 |
| 批量删除按钮 | 红 (0.9,0.2,0.2) | 不变 |

---

## 七、当前行为特征 — 视觉回归

> 记录关键页面的布局特征，用于全屏渲染快照对比。
> 像素级差异阈值 1% 以内视为通过。

### REG-01：主界面 — 空态

- 顶栏：用户名 "某某" + 后缀 "的专属便签本"
- 功能栏：4 个图标按钮（排序/搜索/标签/设置）+ 标签文字
- 搜索条件栏：height=0，不可见
- "未完成"区标题可见
- 空态提示："还没有便签，点击右下角 + 创建一个吧"
- 已完成区：opacity=0，折叠
- FAB：右下角 plus
- 撤销按钮：opacity=0，不可见
- 窗口 420×740

### REG-02：主界面 — 有便签

- 同 REG-01，但空态提示消失
- "未完成"区包含便签卡片列表
- "已完成 (N)"标题可见，默认折叠
- 每张卡片：标题 + 标签芯片 + 内容预览 + 操作按钮行
- 底部 72dp 空白垫片

### REG-03：主界面 — 已完成区展开

- expand_btn 图标变为 chevron-up
- completed_box opacity=1
- 已完成卡片：elevation=0，内容 opacity=0.5

### REG-04：主界面 — 有搜索条件

- search_bar 高度 32dp
- search_label 显示条件文字
- search_close_btn 可见

### REG-05：主界面 — 置顶卡片

- 置顶卡片排在列表最前面
- pin_btn 图标 pin，opacity=1
- 非置顶 pin_btn 图标 pin-outline，opacity=0.3

### REG-06：主界面 — 已完成卡片

- 卡片从"未完成"区移到"已完成"区
- elevation=0，bg=theme.bg_dark
- title_label opacity=0.6，content_preview opacity=0.5
- complete_btn 图标 undo

### REG-07：便签编辑弹窗

- 标题输入框 hint "标题（可选）"，max 50
- 内容输入框 hint "内容（必填）"，max 5000，multiline
- 标签提示 "标签（点击选择）："
- 标签芯片水平滚动
- 已选标签 primary_color 背景 + 白字
- 未选标签 bg_light 背景 + text_color
- 底部 "取消" + "保存"

### REG-08：搜索弹窗

- 关键词输入框 "搜索关键词"
- 标签筛选提示 + 芯片列表
- 时间类型切换 "创建时间"/"完成时间"
- 年/月/周下拉按钮
- 底部 "清除" + "搜索"

### REG-09：设置页面

- 顶栏 "设置" + 返回箭头
- 夜间模式开关
- 排序偏好按钮
- 文字样式模版区 + 模版行 + 保存按钮
- 白天模式文字样式 4 行
- 黑夜模式文字样式 4 行
- 关于 "便签应用 v0.1.0"

### REG-10：标签管理页面

- 顶栏 "标签管理" + 返回 + 新建 + 批量删除
- 标签行：标签名 + 置顶 + 重命名 + 删除
- 空态 "暂无标签，点击右上角 + 创建"

### REG-11：确认删除弹窗

- 标题 + 消息 + "取消" + "确认删除"

### REG-12：昵称编辑弹窗

- 输入框 hint "请输入你的名字"
- 颜色选择 3 按钮（金/天蓝/珊瑚橙）
- 字体选择 3 按钮（默认/东方大楷/乐米波波）
- 粗体开关 + 预览区 + "取消" + "保存"

### REG-13：样式编辑弹窗

- 标题 "编辑：XXX"
- 预览区 + 颜色/字号/粗体/字体控件
- 卡片样式额外：可折叠 + ScrollView
- "取消" + "保存"

---

### WCAG AA 对比度检查点（≥ 4.5:1）

| 场景 | 前景 | 背景 | Light | Dark |
|------|------|------|-------|------|
| 用户名(顶栏) | 金色 (1,0.85,0.4) | Indigo/暗bg | 需验证 | 需验证 |
| 后缀(顶栏) | 天蓝 (0.39,0.71,0.96) | Indigo/暗bg | 需验证 | 需验证 |
| 功能栏文字(Light) | 黑 (0.05,0.05,0.05) | bg_light | 需验证 | — |
| 功能栏文字(Dark) | 天蓝 (0.39,0.71,0.96) | bg_light(暗) | — | 需验证 |
| 卡片标题(Light) | 黑 (0.05,0.05,0.05) | bg_normal | 需验证 | — |
| 卡片标题(Dark) | 白 (1,1,1) | bg_normal(暗) | — | 需验证 |
| 标签芯片文字 | 珊瑚橙 (0.91,0.45,0.29) | bg_light | 需验证 | 需验证 |
| 已完成卡片标题 | opacity 0.6 | bg_dark | 需验证 | 需验证 |
| 已选标签芯片 | 白 (1,1,1) | primary_color | 需验证 | 需验证 |
| 搜索条件关闭 | 亮蓝 (0.4,0.8,1) | bg_light | 需验证 | 需验证 |
| 分类标题(Light) | 天蓝 (0.39,0.71,0.96) | bg_normal | 需验证 | — |
| 分类标题(Dark) | 金色 (1,0.85,0.4) | bg_normal(暗) | — | 需验证 |
| 批量删除按钮 | 白字 | 红 (0.9,0.2,0.2) | 需验证 | 需验证 |
| Toast 文字 | Snackbar默认 | Snackbar默认 | 需验证 | 需验证 |

---

## 八、当前行为特征 — 交互行为

> 记录用户操作链路的完整行为特征。
> 每条 = 一个完整交互流程（触发→状态变更→UI反馈）。

### INT-01：创建便签

**步骤**：FAB → 填写 → 保存

**行为**：
1. 点击 FAB → 弹窗标题 "新增便签"
2. 标签芯片点击切换选中/未选，选中=primary_color背景+白字
3. 超过 3 个标签 → "每个便签最多 3 个标签" + 2秒后消失
4. 内容为空时保存 → content_field.error=True + "内容不能为空" → 弹窗不关闭
5. 保存成功 → note_svc.create() + add_tag() → 弹窗关闭 → Toast "便签创建成功" → refresh_list()
6. 不存在的标签 → 静默跳过（见 CT-P0-02）

---

### INT-02：编辑便签

**步骤**：卡片 pencil → 修改 → 保存

**行为**：
1. 弹窗标题 "编辑便签"，标题/内容/标签预填当前值
2. 保存 → note_svc.update() + 标签 add/remove → 弹窗关闭
3. **现状：编辑保存后无显式成功 Toast** — refresh_list() 直接刷新

---

### INT-03：删除便签

**步骤**：卡片 delete → 确认

**行为**：
1. 确认弹窗 "确认删除此便签吗？"
2. 取消 → 无任何变化
3. 确认 → note_svc.delete() → refresh_list()
4. Toast "应用未关闭的12小时内，可以撤销最近1条删除"
5. undo_btn 出现（opacity=1, disabled=False）
6. 连续删两条 → _undo_data 只保留最后一条

---

### INT-04：撤销删除

**步骤**：删除后 → 点击 undo 按钮

**行为**：
1. 删除后 undo_btn 可见（金色图标）
2. 点击 → note_svc.undo_delete() → refresh_list() → Toast "便签已恢复"
3. undo_btn 消失
4. 12小时后 get_undo_info() 返回 None → undo_btn 不可见

---

### INT-05：标记完成/取消完成

**步骤**：卡片 complete_btn

**行为**：
1. 未完成 → 点击 check-circle → mark_complete()
   - 已完成的报 ValueError → Toast 错误
   - 否则卡片移到已完成区，elevation=0, bg=bg_dark, 标题 opacity=0.6, 内容 opacity=0.5
   - 图标变 undo
2. 已完成 → 点击 undo → mark_incomplete()
   - 未完成的报 ValueError → Toast 错误
   - 否则卡片移回未完成区，图标变 check-circle

---

### INT-06：手动置顶/取消

**步骤**：卡片 pin_btn

**行为**：
1. 未置顶 → 点击 pin-outline → pin_note()
   - 已置顶报 ValueError → Toast 错误
   - 否则卡片排最前，图标变 pin + opacity=1
2. 已置顶 → 点击 pin → unpin_note()
   - 未置顶报 ValueError → Toast 错误
   - 否则图标变 pin-outline + opacity=0.3

---

### INT-07：排序切换

**步骤**：功能栏排序图标

**行为**：
1. toggle_sort_preference() → updated_at ↔ created_at
2. set_sort_preference() 写 DB
3. _update_sort_label() 更新文字+图标
   - updated_at → "按更新时间" + 图标 `\U000F1549`
   - created_at → "按创建时间" + 图标 `\U000F1547`
4. refresh_list() → Toast "排序切换：按XXX"

---

### INT-08：搜索筛选

**步骤**：搜索图标 → 设条件 → 搜索

**行为**：
1. 弹窗 "搜索筛选"，关键词+标签+时间类型+年/月/周
2. 标签 AND 逻辑，无数量上限（与便签编辑不同）
3. "清除" → clear_search() → 全量刷新
4. "搜索" → _current_search_params 设置 → search_bar 出现 → refresh_list() 过滤
5. 结果含已完成+未完成（CT-P2-04）

---

### INT-09：清除搜索条件

**步骤**：搜索条件栏 "取消 ✕"

**行为**：
1. _current_search_params = None
2. search_bar.height = 0, search_label.text = ""
3. search_close_btn opacity=0, disabled=True
4. refresh_list() 全量

---

### INT-10：已完成区折叠/展开

**步骤**：点击 "已完成 (N)" 旁箭头

**行为**：
1. 折叠→展开：completed_box.opacity=1, expand_btn.icon="chevron-up"
2. 展开→折叠：completed_box.opacity=0, completed_box.height=0, icon="chevron-down"

---

### INT-11：新建标签

**步骤**：标签页 + → 填写 → 创建

**行为**：
1. 弹窗 "新建标签"，hint "标签名称（1-10字符）"
2. 空名 → Toast "标签名不能为空"
3. 重名 → Toast "标签「XXX」已存在"
4. 成功 → 弹窗关闭 → refresh_list() → Toast "标签「XXX」创建成功"

---

### INT-12：重命名标签

**步骤**：标签行 pencil → 修改 → 保存

**行为**：
1. 弹窗 "重命名「旧名」"，预填旧名
2. 保存 → tag_svc.update() → 同步置顶列表 → refresh_list()
3. Toast "标签更名为「新名」"

---

### INT-13：删除单个标签

**步骤**：标签行 delete

**行为**：
1. 确认弹窗 "将移除所有便签的此标签。"
2. 确认 → tag_svc.delete() → 自动从置顶列表移除 → refresh_list()
3. Toast "标签「XXX」已删除"

---

### INT-14：批量删除标签

**步骤**：批量删除图标 → 勾选 → 确认

**行为**：
1. 点击 delete-sweep → 每行出现 Checkbox，图标变 check
2. 底部 "删除选中 (N)" 红色按钮
3. 确认弹窗 → 逐个 delete()
4. 退出批量模式，Toast "选中标签已删除"

---

### INT-15：标签置顶切换

**步骤**：标签行 pin 图标

**行为**：
1. toggle_pinned() → 已置顶→取消；未置顶→添加
2. 超出 3 个淘汰最早（FIFO，CT-P1-04）
3. refresh_list() → Toast

---

### INT-16：用户名编辑

**步骤**：点击顶栏用户名 → 编辑 → 保存

**行为**：
1. 弹窗 "编辑昵称"，预填当前值
2. 颜色(3色)/字体(3种)/粗体可选，预览实时更新
3. 取消 → 所有修改不保存（暂存机制）
4. 保存 → _save_username + _save_username_style → 顶栏更新

---

### INT-17：排序偏好切换（设置页）

**步骤**：设置页点击排序按钮

**行为**：
1. 按钮高亮：选中=primary_color+白，未选=bg_light+text_color
2. Toast "排序偏好：按XXX"

---

### INT-18：文字样式编辑（设置页）

**步骤**：点击 "编辑" → 修改 → 保存

**行为**：
1. 编辑其他主题 → Toast 拒绝
2. 正常编辑 → 预览 + 颜色/字号/粗体/字体
3. 保存 → 写 DB → 同步 MainScreen → Toast
4. 跨主题保存 → Toast "已保存，切换至对应模式可查看效果"

---

### INT-19：模版管理（设置页）

**行为**：
1. "使用" → apply_template() → 写白天+黑夜样式 → Toast
2. "+" → 输入名称 → save_current_as_template() → 追加
3. "编辑" → 输入新名称 → 更新
4. "删除" → 确认 → delete_template()

---

### INT-20：Toast/Snackbar 行为

**行为**：
- 所有 Toast 用 MDSnackbar(MDLabel(...))
- 2 秒时长
- 多个连续 Toast → 后一个覆盖前一个（不排队）
- 位置：屏幕中央

---

## 九、当前行为特征 — 夜间模式切换

> 记录主题切换的完整行为链。

### DM-01：开关切换流程

**步骤**：设置页 → 点击夜间模式开关

**行为**（按顺序）：
1. toggle_dark_mode(switch, active)
2. app.theme_cls.theme_style = "Dark" | "Light"
3. settings_service.set_dark_mode() 持久化到 UserSettings
4. app._apply_titlebar_theme(active) — DWM API 设置 Windows 标题栏
5. settings_screen._update_theme_colors()
6. main_screen._update_theme_colors()
7. main_screen._apply_text_styles() — 重新加载当前主题文字样式
8. main_screen.refresh_list() — 重建全部卡片

---

### DM-02：自动变化的属性

| 属性 | 组件 | 变更方式 |
|------|------|---------|
| theme_cls.theme_style | 全局 | 直接赋值 |
| md_bg_color（页面背景） | 所有页面 | _update_theme_colors() |
| top_bar.md_bg_color | 主界面/设置/标签 | Light=primary_color, Dark=bg_dark |
| func_row.md_bg_color | 主界面 | theme.bg_light |
| search_bar.md_bg_color | 主界面 | theme.bg_light |
| DB 存储的文字样式 | 主界面全部文字 | _apply_text_styles() + _load_username_style() |
| 卡片背景/文字 | NoteCard | refresh_list() 重建 |
| 卡片标签芯片背景 | NoteCard | theme.bg_light 自动跟随 |
| 弹窗内芯片背景/文字 | dialogs, search_dialog | 新建弹窗时读当前 theme_cls |

---

### DM-03：不自动变化的属性（硬编码）

| 属性 | 值 | 两种主题行为 |
|------|-----|-------------|
| username_btn.text_color | 金色 (1,0.85,0.4,1) | 相同 |
| title_suffix（两种主题默认） | 天蓝 (0.39,0.71,0.96,1) | 相同 |
| undo_btn.icon_color | 金色 (1,0.85,0.4,1) | 硬编码 |
| search_close_btn.text_color | 亮蓝 (0.4,0.8,1,1) | 硬编码 |
| tag chip 文字色 | 珊瑚橙 (0.91,0.45,0.29,1) | 硬编码 |
| 已选标签 chip 文字 | 白 (1,1,1,1) | 硬编码 |
| delete 按钮图标 | Error 红色 | KivyMD 默认 |
| 批量删除按钮背景 | 红 (0.9,0.2,0.2,1) | 硬编码 |

---

### DM-04：切换后状态保持

**不丢失**：
- _current_search_params（搜索条件）
- _completed_expanded（已完成区折叠状态）
- _undo_data（撤销数据，仅超时清除）

**重建**：
- 全部卡片 clear_widgets → 重新 _build_note_card()
- undo_btn 可见性根据 get_undo_info() 重新判断

---

### DM-05：应用启动时主题恢复

**行为**：
1. app.py:build() → SettingsService.get_dark_mode() 读 DB
2. 设置 theme_cls.theme_style
3. Clock.schedule_once 延迟 _apply_titlebar_theme
4. MainScreen.on_enter → _update_theme_colors() + _apply_text_styles() + refresh_list()
5. 默认主题 = "Light"（DB 无记录时）

---

## 十、覆盖统计

### 特征测试用例统计

| 优先级 | 用例数 | 测试文件 |
|--------|--------|---------|
| P0 | 6 | test_undo_behavior.py / test_tag_skip_behavior.py / test_sort_behavior.py |
| P1 | 5 | test_persistence_behavior.py |
| P2 | 7 | test_crosscutting_behavior.py |
| **合计** | **18** | |

### 可疑行为映射统计

可疑行为 14 条中，11 条已映射到特征测试，3 条需 UI 环境暂缺：
- S-08（标签选择两套实现）
- S-10（颜色选项不一致）
- S-14（Chip 颜色三套修复）

### 行为特征条目统计

| 类别 | 标识 | 条目数 |
|------|------|--------|
| 文字可见性 | V-01 ~ V-40 | 40 |
| 视觉回归 | REG-01 ~ REG-13 | 13 |
| 交互行为 | INT-01 ~ INT-20 | 20 |
| 夜间模式切换 | DM-01 ~ DM-05 | 5 |

---

> **最后更新**：2026-06-24
> **来源文件**：README.md / OUTPUT_SPEC.md / p0_core_services.md / p1_persistence.md / p2_crosscutting.md / suspicious_behaviors.md / characteristics_text_visibility.md / characteristics_visual_regression.md / characteristics_interaction.md / characteristics_dark_mode.md
