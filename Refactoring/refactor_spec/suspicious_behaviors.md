# 可疑行为清单 — 当前现状

> 以下 14 条行为看起来像 bug 或不合理的设计，但在重构时必须**原样锁住**。
> 是否修复由后续决策决定，特征测试仅记录"现状如此"。

---

## S-01：`_update_theme_colors` — 标题栏颜色逻辑

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

## S-02：`get_undo_info()` — 有副作用的 getter

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

## S-03：`create()` / `update()` — 用异常消息字符串做控制流

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

## S-04：`_get_sort_preference()` — 私有方法被外部调用

**来源**：`note_service.py:_get_sort_preference()`, `main_screen.py:_update_sort_label`

**现状**：以下划线开头的方法被 `MainScreen._update_sort_label()` 和 `toggle_sort_preference()` 直接调用。

**为什么可疑**：命名约定被破坏。

**已映射测试**：CT-P0-06

---

## S-05：UI 层直接访问 `db_conn`

**来源**：`main_screen.py`, `settings_screen.py`

**现状**：`_load_style()`, `save_style()`, `_load_username()`, `_save_username()`, `_load_templates()`, `_save_templates()` 等方法直接执行 `app.db_conn.execute(sql)`，绕过了 Service 层。

**为什么可疑**：重构时如果改了表结构，这些位置不会报编译错误。

**已映射测试**：CT-P1-01, CT-P1-02, CT-P1-03

---

## S-06：`get_incomplete()` — 双分支 SQL 列别名不一致

**来源**：`note_service.py:get_incomplete()`

**现状**：
- 有置顶标签：`n.updated_at DESC`（有 `n.` 前缀，有 JOIN + DISTINCT）
- 无置顶标签：`updated_at DESC`（无前缀，无 JOIN）

**为什么可疑**：两路 SQL 对同一功能的列引用方式不同。

**已映射测试**：CT-P0-04, CT-P0-05

---

## S-07：提醒不校验时间

**来源**：`reminder_service.py:create()`

**现状**：注释说"允许过去/未来任意时间"，但没有实际的时间校验逻辑。`remind_at` 可以是任意字符串。

**为什么可疑**：如果将来加校验，会破坏现有调用方依赖的无校验行为。

**已映射测试**：CT-P2-03

---

## S-08：标签选择逻辑两套实现但有细微差异

**来源**：`dialogs.py:AddEditContent` vs `search_dialog.py:SearchContent`

**现状**：
- 两者都有 `_selected_tags: set` + `set_all_tags` + `get_selected_tags` + `_make_chip` + `_toggle_tag`
- 但 `AddEditContent` 有 `MAX_TAGS_PER_NOTE` 上限检查，`SearchContent` 没有

**为什么可疑**：合并时可能误把上限检查带到搜索面板。

**已映射测试**：暂无（需 UI 测试环境）

---

## S-09：username 存储格式与其他设置不一致

**来源**：`main_screen.py:_load_username()` vs `_load_style()`

**现状**：
- `username` → 纯文本，读 `row[0]`
- 其他所有设置 → `json.dumps/loads`

**为什么可疑**：统一序列化时可能需要数据迁移。

**已映射测试**：CT-P1-01

---

## S-10：两套颜色选项不一致

**来源**：`main_screen.py:edit_username()` vs `settings_screen.py:_get_theme_color_options()`

**现状**：

| 入口 | 可选颜色 |
|------|---------|
| edit_username（昵称编辑） | 金色、天蓝、珊瑚橙（3色） |
| settings_screen（样式编辑） | 亮色：黑/金/天蓝/珊瑚橙；暗色：白/金/天蓝/珊瑚橙（4色） |

**为什么可疑**：同一"金色"在两处独立定义，昵称编辑缺白色/黑色选项。

**已映射测试**：暂无（需 UI 测试环境）

---

## S-11：Toast 文案不引用常量

**来源**：`main_screen.py:_handle_delete()`

**现状**：
```python
self._toast("应用未关闭的12小时内，可以撤销最近1条删除")
```
`UNDO_TIMEOUT_SECONDS = 12 * 3600`（43200 秒）

**为什么可疑**：修改 `UNDO_TIMEOUT_SECONDS` 后 Toast 文案不会自动更新。

**已映射测试**：CT-P2-07

---

## S-12：跨主题编辑器双重守卫

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

## S-13：`_apply_title_suffix_style` 在 color=None 时不设置 text_color

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

## S-14：三套 Chip 颜色修复实现

**来源**：`note_card.py:_apply_chip_text_style`, `dialogs.py:_fix_chip_label_color`, `search_dialog.py:_fix_chip_label_color`

**现状**：
- 三处都用 `chip.walk()` 遍历查找 `isinstance(w, Label)` 设置颜色
- `note_card.py` 版额外设置 `font_size/font_name/bold`
- `dialogs.py` 和 `search_dialog.py` 版只设置 `color`
- 都没有处理多层嵌套深度

**为什么可疑**：同一问题的三个独立修复，合并时可能遗漏某个变体的额外行为。

**已映射测试**：暂无（需 UI 测试环境）

---

## 映射表：可疑行为 → 特征测试

| 可疑行为 | 已映射测试 | 测试文件 |
|---------|-----------|---------|
| S-01 标题栏颜色不一致 | CT-P2-06 | p2_crosscutting.md |
| S-02 get_undo_info 副作用 | CT-P0-01 | p0_core_services.md |
| S-03 异常消息做控制流 | CT-P0-02, CT-P0-03 | p0_core_services.md |
| S-04 私有方法被外部调用 | CT-P0-06 | p0_core_services.md |
| S-05 UI 直连 DB | CT-P1-01, CT-P1-02, CT-P1-03 | p1_persistence.md |
| S-06 双分支 SQL | CT-P0-04, CT-P0-05 | p0_core_services.md |
| S-07 提醒无校验 | CT-P2-03 | p2_crosscutting.md |
| S-08 标签选择两套 | 暂无 | — |
| S-09 username 格式不一致 | CT-P1-01 | p1_persistence.md |
| S-10 颜色选项不一致 | 暂无 | — |
| S-11 Toast 不引用常量 | CT-P2-07 | p2_crosscutting.md |
| S-12 双守卫 | CT-P2-06 | p2_crosscutting.md |
| S-13 color=None 不设颜色 | CT-P1-02 | p1_persistence.md |
| S-14 Chip 颜色三套 | 暂无 | — |
