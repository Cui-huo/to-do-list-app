# 特征测试规格文档

> **目的**：记录当前代码的实际行为，作为重构的回归安全网。
> 这些是"特征测试"（characterization tests），锁住现有行为。
>
> **使用方式**：
> - 每个测试标注 `_current_behavior` 后缀或注释标明"现状"
> - 测试失败意味着重构改变了行为，需人工判断是"有意修复"还是"意外破坏"

---

## 一、测试文件组织

```
app_tool/tests/
├── conftest.py                       # 共享 fixtures（:memory: SQLite + kivy_app）
├── test_models.py                    # 数据类字段
├── test_database.py                  # DDL / FTS5 / 种子数据
├── test_note_service.py              # 便签 CRUD + 排序 + 标签关联
├── test_tag_service.py               # 标签 CRUD + 置顶管理
├── test_search_service.py            # 搜索筛选
├── test_reminder_service.py          # 提醒 CRUD
├── test_export_service.py            # JSON/TEXT 导出
├── test_settings_service.py          # 夜间模式持久化
├── test_webdav_service.py            # WebDAV 同步
├── test_ui.py                        # UI 组件尺寸/字体/间距合规
│
└── characterization/                 # 特征测试（锁住行为）
    ├── conftest.py                   # 特征测试专用 fixtures
    ├── test_note_service_behavior.py # 撤销副作用 / 标签静默跳过 / 排序偏好
    ├── test_tag_service_behavior.py  # 置顶标签顺序 / FIFO淘汰 / 联动
    ├── test_search_behavior.py       # 搜索不过滤完成状态 / FTS5 / 中文LIKE
    ├── test_reminder_behavior.py     # 提醒不校验时间
    ├── test_persistence_behavior.py  # 持久化格式（username/样式/模版/completed_at）
    ├── test_settings_behavior.py     # 夜间模式持久化 + R26返回结构
    ├── test_dark_mode_behavior.py    # 主题切换 + 启动恢复
    ├── test_pin_sort_behavior.py     # 手动置顶区免疫排序按钮
    ├── test_pin_zone_sort_update.py  # 三大功能区排序规则（updated_at DESC）
    ├── test_ui_sort_toast_behavior.py # 排序切换 Toast + 标题栏稳定性
    ├── test_complete_toggle_no_refresh.py # 标记完成增量更新
    ├── test_add_widget_reversal.py   # Kivy BoxLayout children 顺序验证
    ├── test_interaction_flows.py     # CRUD 交互链路端到端
    └── qwen3.7-max/
        ├── test_reported_issues.py   # 用户报告5大问题验证
        └── test_delete_crash.py      # 删除闪退修复验证
```

---

## 二、特征测试覆盖总览

| 测试文件 | 覆盖内容 | 测试数 |
|---------|---------|--------|
| `test_note_service_behavior.py` | 撤销超时清除、标签静默跳过、排序SQL双分支、排序偏好持久化 | ~18 |
| `test_tag_service_behavior.py` | 置顶标签顺序保持、FIFO淘汰、删除/重命名联动 | ~14 |
| `test_search_behavior.py` | 搜索不过滤完成状态、FTS5同步、中文LIKE兜底 | ~12 |
| `test_reminder_behavior.py` | 提醒不校验时间格式/范围 | ~6 |
| `test_persistence_behavior.py` | username纯文本、样式JSON、模版种子、completed_at NULL | ~12 |
| `test_settings_behavior.py` | 夜间模式持久化、默认Light、R26返回结构 | ~5 |
| `test_dark_mode_behavior.py` | 主题切换持久化、启动恢复 | ~4 |
| `test_pin_sort_behavior.py` | 手动置顶区免疫排序、标签置顶区updated_at排序、冲突去重 | ~10 |
| `test_pin_zone_sort_update.py` | pin_note刷新updated_at、两大置顶区免疫、冲突去重详情 | ~10 |
| `test_ui_sort_toast_behavior.py` | 排序切换Toast反馈、_reorder_cards不碰标题栏 | ~7 |
| `test_complete_toggle_no_refresh.py` | 标记完成增量更新、自动展开已完成区、折叠仅用opacity | ~9 |
| `test_add_widget_reversal.py` | Kivy BoxLayout children顺序 = Service层DESC | ~A few |
| `test_interaction_flows.py` | CRUD完整链路端到端 | ~15 |
| `test_reported_issues.py` | 搜索返回/Toast/功能栏/新便签位置/置顶混乱 | ~20 |
| `test_delete_crash.py` | 删除闪退修复 + refresh_list布局冻结 | ~7 |

---

## 三、核心行为特征（排序与置顶）

### 3.1 排序规则（当前实现）

`note_service.py:get_incomplete()` 的 SQL 排序三层：

```sql
ORDER BY
  CASE WHEN n.is_pinned = 1 THEN 0           -- 手动置顶最前
       WHEN t.name IN (置顶标签) THEN 1       -- 标签置顶次之
       ELSE 2                                  -- 非置顶
  END,
  CASE WHEN n.is_pinned = 1 OR t.name IN (置顶标签)
    THEN n.updated_at END DESC,               -- 置顶区统一按 updated_at DESC
  CASE WHEN 非置顶 THEN n.{sort_col} END DESC -- 非置顶区响应排序偏好
```

**关键特征**：
- 手动置顶区：按 `updated_at DESC`，免疫排序按钮
- 标签置顶区：按 `updated_at DESC`，免疫排序按钮
- 非置顶区：响应 `sort_preference`（`created_at`/`updated_at`）
- 冲突去重：手动置顶优先（CASE 0 < CASE 1），含置顶标签的便签不会重复出现在标签置顶区

### 3.2 `pin_note()` 刷新 `updated_at`

```python
# note_service.py L199
"UPDATE Note SET is_pinned=1, pinned_at=?, updated_at=? WHERE id=?"
```
置顶操作同时刷新 `pinned_at` 和 `updated_at`，取消置顶不刷新 `updated_at`。

### 3.3 排序偏好持久化

- 存储在 `UserSettings` 表，key=`sort_preference`
- value 为 JSON 字符串（如 `"\"updated_at\""`，带引号）
- 默认值 `"updated_at"`
- `set_sort_preference()` 只接受 `'updated_at'` 或 `'created_at'`

### 3.4 排序切换 UI 行为（已验证）

- `toggle_sort_preference()` 调用 `_toast("按更新时间排序")` 或 `_toast("按创建时间排序")`
- 无搜索参数时走 `_reorder_cards()`（复用卡片，避免全量重建）
- `_reorder_cards()` 不修改 `completed_label.text`、不碰标题栏/功能栏
- 有搜索参数时走 `refresh_list()`（全量重建）

### 3.5 `add_widget` 顺序

Kivy `BoxLayout`（vertical）的 children 顺序：`children[0]`=视觉底部，`children[-1]`=视觉顶部。
`add_widget(widget)` 默认 `index=0` 将新 widget prepend：
```
add A → children=[A]             → A在底部
add B → children=[B, A]          → B在底部，A在顶部
add C → children=[C, B, A]       → C在底部，A在顶部 ✓
```
Service 层返回 DESC（最新在前），逐张 `add_widget` 后 UI 顺序 = Service 层顺序。

---

## 四、核心行为特征（完成/撤销/标签）

### 4.1 `_handle_complete_toggle` 增量更新

- 标记完成：`remove_widget` 从 `incomplete_box` 移除 → `add_widget` 到 `completed_box`
- 取消完成：`remove_widget` 从 `completed_box` 移除 → `add_widget` 到 `incomplete_box`
- 其他卡片 widget 实例保持不变（不触发 `clear_widgets`）
- 标记完成时自动展开已完成区（`_completed_expanded = True`）

### 4.2 已完成区折叠

- `_update_completed_visibility()` 仅切换 `opacity` 和 `disabled`
- 不修改 `completed_box.height`（KV 绑定 `height: self.minimum_height` 自动处理）
- 折叠：`opacity=0, disabled=True`
- 展开：`opacity=1, disabled=False`

### 4.3 标签不存在时的处理

- `create()` 和 `update()` 对不存在的标签静默跳过
- 判断依据：`ValueError` 异常消息中是否包含 `"不存在"` 字符串
- 其他类型 `ValueError`（如标签数量超限）会向上传播

### 4.4 撤销删除

- `get_undo_info()` 在超时后自动清除 `_undo_data`（有副作用的 getter）
- 超时时间：`UNDO_TIMEOUT_SECONDS = 12 * 3600`（12小时）
- 撤销缓存仅存 Python 进程内存，应用关闭即丢失
- Toast 文案硬编码为 `"应用未关闭的12小时内，可以撤销最近1条删除"`

### 4.5 置顶标签管理

- 置顶标签存储为 JSON 数组，按添加顺序排列
- `toggle_pinned()`：已置顶→移除，未置顶→追加到末尾
- 超出 `MAX_PINNED_TAGS=3` 时 FIFO 淘汰最早置顶的
- 标签删除时自动从置顶列表移除
- 标签重命名时同步更新置顶列表

---

## 五、核心行为特征（搜索/提醒/持久化）

### 5.1 搜索

- `search()` 不过滤 `is_completed`，同时返回已完成+未完成
- ASCII 关键词走 FTS5 MATCH，中文走 LIKE 兜底
- 标签筛选使用 AND 逻辑
- 排序始终按 `updated_at DESC`

### 5.2 FTS5 同步

- `create()` → `fts_insert()` + 独立 `commit()`
- `update()` → `fts_update()`
- `delete()` → `fts_delete()`

### 5.3 提醒

- `create()` 接受任意 `remind_at` 字符串，不做时间格式或范围校验
- 只校验便签是否存在、数量上限（`MAX_REMINDERS_PER_NOTE=3`）

### 5.4 持久化格式

| 存储项 | 格式 | 说明 |
|--------|------|------|
| `sort_preference` | JSON 字符串 | `"\"updated_at\""` |
| `pinned_tags` | JSON 数组 | `["工作","生活"]` |
| `dark_mode` | JSON 布尔 | `true` / `false` |
| 文字样式 | JSON 字典 | `{"color": [...], "font_size":"16sp", ...}` |
| `username` | 纯文本 | **非** JSON（与其他设置不一致） |
| `text_templates` | JSON 数组 | 2套内置模版 + 用户自定义 |
| `completed_at` | NULL | 取消完成时设为 NULL |

---

## 六、UI 交互行为（已验证）

| 交互 | 行为 |
|------|------|
| 创建便签 | FAB → 弹窗 → `note_svc.create()` → `_add_new_card()` 增量添加 → Toast "便签创建成功" |
| 编辑便签 | 卡片 pencil → 弹窗预填 → `update()` → 就地更新 card 属性（不触发全量刷新） |
| 删除便签 | 卡片 delete → 确认弹窗 → 物理删除 → undo_btn 出现 → Toast 12小时提示 |
| 撤销删除 | undo_btn → `undo_delete()` → 恢复便签 → Toast "便签已恢复" |
| 标记完成 | check-circle → `mark_complete()` → 增量移动卡片 → 自动展开已完成区 |
| 取消完成 | undo 图标 → `mark_incomplete()` → 增量移动卡片 |
| 手动置顶 | pin-outline → `pin_note()` → 卡片排最前 + updated_at 刷新 |
| 取消置顶 | pin → `unpin_note()` → 卡片移回 |
| 排序切换 | 功能栏排序图标 → `toggle_sort_preference()` → Toast + `_reorder_cards()` |
| 搜索筛选 | 搜索图标 → 弹窗设条件 → `_current_search_params` 设置 → `refresh_list()` |
| 清除搜索 | "取消 ✕" → `_current_search_params = None` → `refresh_list()` |
| 折叠已完成 | 箭头 → `_completed_expanded` 切换 → `_update_completed_visibility()` |
| 标签CRUD | 标签管理页 → 新建/重命名/删除/批量删除/置顶 |

---

## 七、夜间模式行为

### 7.1 切换流程

1. `toggle_dark_mode(switch, active)`
2. `app.theme_cls.theme_style = "Dark" | "Light"`
3. `settings_service.set_dark_mode()` 持久化
4. `app._apply_titlebar_theme(active)` — Windows 标题栏 DWM API
5. `_update_theme_colors()` — 各页面
6. `_apply_text_styles()` — 重新加载当前主题文字样式
7. `refresh_list()` — 重建全部卡片

### 7.2 双主题文字样式

- 白天模式 key：`username_style`、`title_suffix_style`、`func_row_style`、`section_header_style`、`note_card_styles`
- 黑夜模式 key：`dark_username_style`、`dark_title_suffix_style`、`dark_func_row_style`、`dark_section_header_style`、`dark_note_card_styles`
- 跨主题编辑被守卫拦截（Toast 提示）

### 7.3 硬编码颜色（不随主题变化）

| 位置 | 颜色 | 说明 |
|------|------|------|
| username_btn | 金色 (1, 0.85, 0.4) | 两种主题相同 |
| title_suffix 默认 | 天蓝 (0.39, 0.71, 0.96) | 两种主题相同 |
| undo_btn 图标 | 金色 (1, 0.85, 0.4) | 硬编码 |
| search_close_btn | 亮蓝 (0.4, 0.8, 1) | 硬编码 |
| 标签芯片文字 | 珊瑚橙 (0.91, 0.45, 0.29) | 硬编码 |
| 已选标签芯片文字 | 白 (1, 1, 1) | 硬编码 |
| 批量删除按钮 | 红 (0.9, 0.2, 0.2) | 硬编码 |

---

## 八、可疑行为清单

> 以下行为看起来像 bug 或不合理的设计，但已通过特征测试锁住。
> 是否修复由后续决策决定。

| 编号 | 描述 | 文件 |
|------|------|------|
| S-01 | `get_undo_info()` — 有副作用的 getter（超时自动清除 `_undo_data`） | `note_service.py` |
| S-02 | `create()`/`update()` 用异常消息字符串 `"不存在"` 做控制流分支 | `note_service.py` |
| S-03 | `_get_sort_preference()` 以下划线开头但被外部直接调用 | `note_service.py` |
| S-04 | UI 层 `_load_style`/`_save_username` 等方法直接 `app.db_conn.execute()`，绕过 Service | `main_screen.py` |
| S-05 | `get_incomplete()` 双分支 SQL 列别名不一致（有/无置顶标签时 `n.` 前缀差异） | `note_service.py` |
| S-06 | 提醒 `create()` 不做时间校验，接受任意字符串 | `reminder_service.py` |
| S-07 | username 纯文本存储，与其他 JSON 格式不一致 | `main_screen.py` |
| S-08 | 标签选择逻辑两套实现（`dialogs.py` vs `search_dialog.py`），上限检查差异 | `dialogs.py` |
| S-09 | 颜色选项不一致：昵称编辑 3 色 vs 样式编辑 4 色 | `main_screen.py` |
| S-10 | Toast 文案不引用 `UNDO_TIMEOUT_SECONDS` 常量 | `main_screen.py` |
| S-11 | 跨主题编辑器双重守卫（守卫#2 else 分支在当前代码路径不可达） | `settings_screen.py` |
| S-12 | Chip 文字颜色三套独立修复（`note_card.py` / `dialogs.py` / `search_dialog.py`） | 三文件 |

---

## 九、测试统计

| 类别 | 数量 |
|------|------|
| 核心单元测试文件 | 11 |
| 特征测试文件 | 15 |
| 特征测试总数（不含UI） | ~150 |
| UI 测试（test_ui.py） | 56 |
| **全量测试总计** | **365** |

---

> **最后更新**：2026-06-26
> **状态**：所有 365 个测试全绿通过，文档与代码同步。
