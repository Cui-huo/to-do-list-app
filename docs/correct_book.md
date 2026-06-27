# 错题本 — 问题解决后记录归档
本文档专门用于记录解决技术问题的经验教训，沉淀可复用知识。

每次解决完一个技术问题后，必须主动询问：
1. 「问题是否已解决？」
2. 若已解决 →「是否需要保存到错题本 `correct_book.md`？」

错题本记录内容按**对话迭代过程**组织，保留用户与 AI 之间的完整交互链路：

1. **问题描述与背景** — 清晰详细的问题描述 + 发生背景
2. **解决过程（迭代循环）** — 按以下格式记录每一步：

```
   【用户要求】← 用户提出的原始需求和修改指令
       ↓
   【尝试方案】← AI 定位问题根因，提出修复方案并执行
       ↓
   【用户反馈】← 用户报告修复结果（成功/失败/新的要求）
       ↓  （若失败，重复上述循环直到成功）
   【最终方案】← 经过验证的正确解决方案
```

每次尝试必须标注：失败原因、关键发现、以及如何导向下一步。

3. **日期** — 问题解决的日期
4. **模型名称** — 当前与用户对话的底层大模型准确 ID（如 `DeepSeek V4 Pro`）。注意：这里是底层大模型名称，不是工具/平台名称（如 `Qwen Code`）

**Why:** 错题本是个人技术成长的重要资产——记录错误比记录成功更有价值。定期回顾避免重复踩坑。

**How to apply:** 每次 bug 修复、技术难题解决后，在回复末尾附加以上两个追问。待用户确认后，将内容追加写入项目根目录的 `correct_book.md`。
---

## 1. 夜间模式下标题栏（系统状态栏区域）不变黑

### 问题描述与背景

- **日期**：2026-06-22
- **背景**：便签应用支持夜间模式切换。开启夜间模式后，主界面 90% 的区域正常变黑，但 `MDTopAppBar` 所在区域和更上方的 Windows 系统标题栏始终是白色/亮色，未跟随主题变化。
- **测试环境**：Windows 桌面端

### 解决过程

**【用户要求】**
开启夜间模式后，顶部的标题栏区域和系统标题栏没有变黑。

**【尝试1 — 检查 MDTopAppBar 背景色】**
- 定位：三个页面的 `_update_theme_colors()` / `on_enter()` 均未设置 `top_bar.md_bg_color`
- 修复：Dark → `theme.bg_dark`，Light → `theme.primary_color`
- 涉及文件：`main_screen.py`、`tag_manager.py`、`settings_screen.py`

**【用户反馈】**
MDTopAppBar 区域修好了，但更上方的 Windows 系统标题栏仍然白色/亮色。

**【尝试2 — DWM API 设置系统标题栏暗色】**
- 定位：Windows 标题栏在 Kivy 客户区之外，需通过系统级 API 控制
- 修复：在 `app.py` 新增 `_apply_titlebar_theme(dark)` 方法，调用 `DwmSetWindowAttribute`（属性 20: `DWMWA_USE_IMMERSIVE_DARK_MODE`）
- 在 `settings_screen.py` 的 `toggle_dark_mode()` 中调用

**【用户反馈】**
有效，但标题栏颜色变更延迟 20-30 秒才生效。

**【尝试3 — DwmFlush 强制刷新】**
- 定位：DWM 默认在下一个合成帧才应用属性变更
- 修复：`DwmSetWindowAttribute` 后追加 `DwmFlush()`，立即生效

**【用户反馈】**
彻底修好！

### 最终方案

| 文件 | 方法 | 修改 |
|---|---|---|
| `app_tool/ui/main_screen.py` | `_update_theme_colors()` | Dark → `top_bar.md_bg_color = theme.bg_dark` |
| `app_tool/ui/tag_manager.py` | `on_enter()` | 同上 |
| `app_tool/ui/settings_screen.py` | `_update_theme_colors()` | 同上 |
| `app_tool/ui/app.py` | 新增 `_apply_titlebar_theme()` | `DwmSetWindowAttribute`(20) + `DwmFlush()`，`Clock.schedule_once` 延迟调用 |
| `app_tool/ui/settings_screen.py` | `toggle_dark_mode()` | 追加 `app._apply_titlebar_theme(active)` |

### 模型名称

DeepSeek V4 Pro

---

## 2. 标题栏文字垂直居中 — MDTopAppBar 子组件 pos_hint 失效

### 问题描述与背景

- **日期**：2026-06-22
- **背景**：标题栏显示"某某的专属便签本"，文字位于左侧偏下位置，期望垂直居中。

### 解决过程

**【用户要求】**
"某某的专属便签本"所在的背景中，文字显示在左侧偏下的位置，期望显示在左侧中间。

**【尝试1 — FloatLayout + adaptive_height】**
- 定位：`MDTopAppBar` 继承自 `BoxLayout`，子元素 `pos_hint` 不生效；需外层包 `FloatLayout` 使 `pos_hint` 生效
- 同时发现之前编辑导致 MDLabel 缩进错误（跑到 FloatLayout 层级而非 MDBoxLayout 内），一并修复
- 方案：`FloatLayout` 包裹 `title_box`，设 `adaptive_height: True` + `pos_hint: {"center_y": 0.5}`

**【用户反馈】**
标题还是没有左侧居中，当前仍然是左侧偏下位置。

**【尝试2 — title_box 挪出 MDTopAppBar】**
- 定位：MDTopAppBar 内部布局可能仍有干扰，`pos_hint` 无法正常工作
- 方案：把 `title_box` 从 MDTopAppBar 内部移到外层 56dp 的 `FloatLayout`，与 undo 按钮同级：
  ```
  FloatLayout(height: 56dp):
  ├── MDTopAppBar (背景层，无子元素)
  ├── MDBoxLayout id:title_box ← 直接受 FloatLayout 控制
  └── MDIconButton (undo_btn)
  ```
- 关键：`adaptive_height: True` + `pos_hint: {"center_y": 0.5}`

**【用户反馈】**
哇塞，彻底好了！

**【追加要求】**
标题放在标题栏居中（水平+垂直）看着更舒服。

**【尝试3 — 加 center_x】**
- 方案：`pos_hint` 从 `{"center_y": 0.5}` 改为 `{"center_x": 0.5, "center_y": 0.5}`

**【用户反馈】**
一次性修复完成！

### 最终方案

将 `title_box` 从 MDTopAppBar 内部移到外层 FloatLayout，直接控制 pos_hint：

```kv
FloatLayout(height: dp(56)):
    MDTopAppBar:           # 背景层，无子元素
        ...
    MDBoxLayout:           # 标题文字
        id: title_box
        adaptive_height: True
        adaptive_width: True
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        ...
    MDIconButton:          # 撤销按钮
        ...
```

### 模型名称

DeepSeek V4 Pro

---

## 3. func_row 图标与文字间距 — MDIconButton set_size 自动覆盖 + MDLabel Unicode 替代

### 问题描述与背景

- **日期**：2026-06-22
- **背景**：功能栏（func_row）中 4 个按钮（排序/搜索/标签/设置），图标与下方文字视觉间距过大，期望更紧凑但不能相互覆盖。

### 解决过程

**【用户要求】**
"下面功能栏中按创建时间、便签检索、标签、设置的文字和按钮图标离得有点远，期望是离得近些，但是不能相互覆盖。"

**【确认理解】**
- Q: 是指图标和文字之间垂直间距，还是四个功能列之间水平间距？
- A: 肉眼可见的按钮图标和文字之间的垂直距离远。

**【尝试1 — 调整布局间距】**
- 方案：内部 `spacing: dp(1)` → `dp(0)`，func_row 高度 `dp(60)` → `dp(52)`

**【用户反馈】**
改完视觉距离还是没啥变化。

**【用户提示】**
文字变大一号是否可行？

**【分析 — 字体方案不可行】**
- Caption(12sp)→Body2(14sp) 会使 label 高度增加，在 60dp func_row 内可能溢出
- 关键发现：问题不在于文字，而在于图标

**【用户要求】**
"能否让图标 MDIconButton 也尽可能紧凑，填满自身的边框，或者让图标紧贴下方的自身边框"

**【尝试2 — MDLabel 减少文字留白】**
- 方案：给 4 个 MDLabel 加 `text_size: self.size` + `valign: "top"`，让文字紧贴上边缘

**【用户反馈】**
改完视觉距离还是没啥变化。看来问题不在于文字，而在于图标。

**【尝试3 — MDIconButton icon_size 增大图标】**
- 方案：给 4 个 MDIconButton 加 `icon_size: "28sp"`，图标在按钮内变大，减少内部留白
- 同时恢复 func_row 高度到 `dp(60)`

**【用户反馈】**
有效果！

**【用户要求】**
"icon_size 保持不变，将图标按钮的整体尺寸缩小"

**【尝试4 — 显式设置 size】**
- 方案：`size: dp(36)` → `dp(32)`

**【用户反馈】**
"图标按钮尺寸真的可以修改吗，从结果来看，尺寸没有变化。"

**【尝试5 — 读源码发现根因】**
- 关键发现：MDIconButton 源码中 `set_size()` 方法自动计算按钮尺寸：
  ```python
  diameter = self._default_icon_pad + (self.icon_size or sp(24))
  self.width = diameter    # ← 强制覆盖显式 size！
  self.height = diameter
  ```
- 公式：`按钮尺寸 = 24dp + icon_size`，手动设的 `size` 被完全覆盖

**【最终方案 — MDLabel + 图标 Unicode 替代 MDIconButton】**
- 放弃 MDIconButton，改用 MDLabel + 图标字体 Unicode 字符，完全自主控制尺寸

| 原图标名 | Unicode |
|---|---|
| sort-clock-ascending | `\U000F1549` |
| magnify | `\U000F0349` |
| tag-multiple | `\U000F04FB` |
| cog | `\U000F0493` |

```kv
MDLabel:
    text: "\U000F1549"
    font_style: "Icon"
    font_size: "28sp"
    size_hint: None, None
    size: dp(32), dp(32)
    halign: "center"
    valign: "center"
    text_size: self.size
    on_touch_down: if self.collide_point(*args[1].pos): root.callback()
```

- 连带修改：`_update_sort_label()` 中 `.icon = "xxx"` → `.text = "\Uxxxxxxxx"`
- 排序切换图标：`sort-calendar-ascending` → `\U000F1547`

**【用户反馈】**
"哈哈，非常完美！这是你和我的成功！"

### 最终方案

用 MDLabel（`font_style: "Icon"`）+ Unicode 图标字符替代所有 func_row 的 MDIconButton，28sp 图标装进 32dp 容器，仅 2dp 边距。

**文件**：`app_tool/ui/main_screen.py`
- KV 字符串：4 个 MDIconButton → MDLabel
- `_update_sort_label()` 方法：`.icon` → `.text`

### 模型名称

DeepSeek V4 Pro

---

## 4. 标签颜色和大小不生效 — KivyMD 1.2.0 MDChipText 主题覆盖 + 多文件全局修复

### 问题描述与背景

- **日期**：2026-06-22
- **背景**：需求为便签卡片标签使用暖色（珊瑚橙）+ Caption 字号，同时卡片标题/内容换用自定义东方大楷字体，标题栏用户名可点击切换样式。实现后发现标签字体大小和颜色均不生效，仍为默认黑色默认字号。

### 解决过程

**【用户要求】**
便签卡片的标签移到标题下方、内容上方。标题栏字体放大2号。卡片标题用行楷粗体，标签暖色醒目且比标题小，内容用楷体。用户名可点击切换字体颜色粗细。

**【前置任务（一次通过）】**
- 标签位置：`note_card.py` KV 中 `chips_box` 与 `content_preview` 互换 → title → tags → content
- 标题栏字体：`main_screen.py` 两处 `font_style: "Subtitle2"` → `"H6"`
- 字体注册：`app.py` 注册 `AlimamaDongFangDaKai`、`Lemibo`（保持原名，不重命名）
- 卡片标题：`font_name: "AlimamaDongFangDaKai"` + `bold: True`
- 卡片内容：`font_name: "AlimamaDongFangDaKai"`（不加粗区分层级）

**【用户要求】**
用户名可点击弹出样式选择面板（颜色+字体+粗细）。

**【尝试1 — 用户名样式面板】**
- 方案：点击用户名 → `MDDialog`，内含昵称输入 + 3个颜色圆点按钮（金/天蓝/珊瑚橙）+ 3个字体按钮（默认/东方大楷/乐米波波）+ `MDSwitch` 粗体开关 + 预览行
- 持久化 JSON → `UserSettings` key=`username_style`

**【用户反馈】**
崩溃：`ModuleNotFoundError: No module named 'kivymd.uix.switch'`

**【尝试2 — 修复 MDSwitch 导入路径】**
- 定位：KivyMD 1.2.0 中 `MDSwitch` 在 `kivymd.uix.selectioncontrol`，不在 `kivymd.uix.switch`
- 修复：`from kivymd.uix.selectioncontrol import MDSwitch`

**【崩溃 — font_name 空字符串】**
- 崩溃：`OSError: Label: File '.ttf' not found`
- 根因：预览标签 `font_name=_selected_font`，默认值为空字符串 `""`，Kivy 将其拼接为 `".ttf"` 查找字体文件
- 修复：`font_name=_selected_font or "Roboto"` 两处（预览创建 + `_update_preview`）

**【用户反馈】**
标签字体明显对了（Caption 生效），但颜色仍然是黑色。

**【尝试3 — MDChipText 设 theme_text_color="Custom"】**
- 定位：KivyMD 的 `MDChipText` 继承 `MDLabel`，未设 `theme_text_color="Custom"` 时 KivyMD 主题自动覆盖 `color` 属性
- 修复：`MDChipText(text=name, color=chip_text, theme_text_color="Custom", font_style="Caption")`

**【用户反馈】**
仍然黑色。

**【尝试4 — MDChip.text_color 属性】**
- 方案：在 `MDChip()` 上设 `text_color=chip_text`
- 结果：启动日志显示 `Deprecated property "text_color"` 警告，颜色仍不生效

**【用户反馈】**
仍然黑色。

**【尝试5 — Clock.schedule_once 延迟设色】**
- 关键发现：KivyMD 1.2.0 的 `MDChip.add_widget(MDChipText)` 会在内部将 `MDChipText` 转换为普通 `MDLabel`（放入 `LabelTextContainer`），转换过程中颜色属性丢失
- 方案：

```python
# 创建芯片时不设颜色，仅设 font_style
label = MDChipText(text=name, theme_text_color="Custom", font_style="Caption")
chip.add_widget(label)

# 延迟一帧，KivyMD 完成内部转换后遍历树找到 Label 设颜色
Clock.schedule_once(lambda dt, c=chip: _set_chip_text_color(c, chip_text))
```

`_set_chip_text_color` 函数用 `chip.walk()` 遍历所有子孙，找到第一个 `Label` 实例设 `color`。

**【用户反馈】**
"很好，这次颜色对了！"

**【R30 全局排查】**
发现 `search_dialog.py`（3处）和 `dialogs.py`（1处）同样创建 `MDChipText` 时未设 `theme_text_color="Custom"`，其中选中态使用白色 `(1,1,1,1)` 等自定义颜色会被主题覆盖。一次性全部修复。

### 最终方案

| 文件 | 修改 |
|---|---|
| `app_tool/ui/app.py` | 注册 `AlimamaDongFangDaKai` + `Lemibo` 自定义字体 |
| `app_tool/ui/note_card.py` KV | title→tags→content 布局重组；标题加 `font_name`+`bold`；内容加 `font_name` |
| `app_tool/ui/note_card.py` `on_tag_names` | `MDChipText` 设 `theme_text_color="Custom"`+`font_style="Caption"`；`Clock.schedule_once` 延迟遍历树设最终颜色 |
| `app_tool/ui/note_card.py` 新增 | `_set_chip_text_color(chip, rgba)` — 全局函数遍历芯片树找 Label 设色 |
| `app_tool/ui/main_screen.py` | 新增 `username_font/color/bold` 属性 + `_load/_save_username_style` 持久化；`edit_username` 重写为统一样式面板 |
| `app_tool/ui/main_screen.py` KV | `username_btn` 绑定动态 `font_name/text_color/bold`；标题 `Subtitle2→H6` |
| `app_tool/ui/search_dialog.py` | 3处 `MDChipText` 加 `theme_text_color="Custom"` |
| `app_tool/ui/dialogs.py` | 1处 `MDChipText` 加 `theme_text_color="Custom"` |
| `app_tool/tests/test_ui.py` | 新增 9 个测试覆盖字体/颜色/持久化 |

**核心教训**：
- KivyMD 1.2.0 `MDChip` 的 `text_color` 属性已废弃不生效，`MDChipText` 的 `color` 会被主题覆盖
- 正确姿势：`theme_text_color="Custom"` + `Clock.schedule_once` 延迟设色（绕过内部转换）
- KivyMD 1.2.0 `MDSwitch` 在 `kivymd.uix.selectioncontrol`，非 `kivymd.uix.switch`
- `font_name=""` 空字符串会使 Kivy 查找 `".ttf"` 崩溃，需用 `"Roboto"` 兜底

### 模型名称

DeepSeek V4 Pro

---

## 5. 文字样式分组调整 — 6 项连锁 Bug 修复

### 问题描述与背景

- **日期**：2026-06-22
- **背景**：在设置页面新增 4 组文字样式调整功能，分别控制标题栏、功能栏、分类标题、便签卡片的颜色/字号/粗体/字体。初始实现后发现多个连锁问题。

---

### 5.1 MDSwitch(active=…) 初始化竞态闪退

**【用户要求】**
设置页各组弹窗正常打开，不闪退。

**【尝试1 — 直接使用 MDSwitch(active=True)】**
- 方案：`MDSwitch(active=style_state["bold"])` 通过构造参数设置初始状态
- 结果：打开弹窗闪退，报错 `AttributeError: 'super' object has no attribute '__getattr__'`

**【根因定位】**
- 定位：KivyMD 1.2.0 中 `MDSwitch(active=True)` 在 `__init__` 阶段触发 `on_active` 回调，回调内访问 `self.ids.thumb` 执行动画。但 `self.ids` 字典在 `__init__` 链中尚未完全初始化，`ids` 返回一个未就绪的 `super` 对象
- 报错路径：`selectioncontrol.py:875` → `Animation(...).start(self.ids.thumb)` → `__getattr__` 失败

**【最终方案 — Clock.schedule_once 延迟】**
```python
bold_switch = MDSwitch()
bold_switch.bind(active=lambda _, v: _on_change("bold", v))
# 延迟到下一帧设置 active，此时 ids 已就绪
Clock.schedule_once(lambda dt: setattr(bold_switch, 'active', val), 0)
```

**涉及文件**：
- `settings_screen.py` — `_add_single_style_section()` 中的 MDSwitch（影响全部 4 组）
- `main_screen.py` — `edit_username()` 中的 MDSwitch（R30 全局排查发现）

---

### 5.2 Kivy ObjectProperty 拒绝 None 值

**【用户要求】**
编辑颜色选择"默认"后保存不闪退。

**【尝试1 — 将 ObjectProperty 设为 None】**
- 方案：`self.func_row_color = tuple(color) if color else None`
- 结果：闪退，报错 `ValueError: None is not allowed for MainScreen.func_row_color`

**【根因定位】**
- 定位：Kivy `ObjectProperty` 在默认值为具体类型（如 `(1,1,1,1)` 元组）时，后续赋值 `None` 触发 `Property.check` 拒绝
- 涉及属性：`username_color`（默认 `(1,0.85,0.4,1)`）、`func_row_color`、`section_header_color`

**【最终方案 — 用 sentinel 值替代 None】**
```python
# 用 (0,0,0,0) 兜底，避免 None
self.func_row_color = tuple(color) if color else (0, 0, 0, 0)
self.section_header_color = tuple(color) if color else (0, 0, 0, 0)

# username_color 用默认金色兜底
main_screen.username_color = u_state["color"] if u_state["color"] else (1, 0.85, 0.4, 1)
```

**涉及文件**：
- `main_screen.py` — `_apply_func_row_style`、`_apply_section_header_style`
- `settings_screen.py` — Group 1 `_on_save` 同步 username_color

---

### 5.3 MDChipText 内部转换重置字体属性

**【用户要求】**
第四组设置卡片标签的颜色/字体/大小/粗体，在主界面生效。

**【尝试1 — 仅延迟恢复颜色】**
- 方案：`_set_chip_text_color(chip, rgba)` 只设置 `w.color`
- 结果：颜色生效，但字体大小和粗体不生效

**【根因定位】**
- 定位：KivyMD 1.2.0 的 `MDChip.add_widget(MDChipText)` 内部将 `MDChipText` 转为普通 `MDLabel`，此过程中颜色、字体、大小、粗体全部重置
- 原有 `_set_chip_text_color` 只修复了颜色，未修复字体属性

**【最终方案 — 延迟回调一次性恢复全部样式】**
```python
def _apply_chip_text_style(chip, rgba, font_size, font_name, bold):
    for w in chip.walk():
        if isinstance(w, Label):
            w.color = rgba
            w.font_size = font_size
            w.font_name = font_name or "Roboto"
            w.bold = bold
            return

Clock.schedule_once(
    lambda dt, c=chip, clr=..., fs=..., fn=..., b=...:
    _apply_chip_text_style(c, clr, fs, fn, b)
)
```

**涉及文件**：`note_card.py` — `_set_chip_text_color` → `_apply_chip_text_style`

---

### 5.4 颜色"默认"=None → 夜间模式字号不生效

**【用户要求】**
夜间模式下选择颜色"默认"+改字号，回到主界面字号应变化。

**【尝试1 — "默认"保存为白色 (1,1,1,1)】**
- 方案：`_on_save` 中 `list(s_state["color"]) if s_state["color"] else [1, 1, 1, 1]`
- 结果：选了"默认"后字号字体粗体全部不生效，但选金色等显式颜色时正常

**【根因定位】**
- 定位：保存为 `[1,1,1,1]` → `_apply_*_style` 走 `if color:` 分支 → 设 `theme_text_color="Custom"` + `text_color=(1,1,1,1)` → 可能触发 KivyMD 内部处理覆盖了字号设置
- **关键线索**：仅"默认"（=None→白色转换）时失效，显式颜色正常

**【尝试2 — "默认"保存为 None】**
- 方案：`_on_save` 存 `None`，`_apply_title_suffix_style` 中 color=None 时跳过颜色设置，只设字号
- 结果：仍然不生效

**【最终方案 — 彻底移除"默认"选项，全部显式颜色】**
- 方案：`_get_theme_color_options()` 不再返回 `("默认", None)`，改为根据主题返回显式颜色
- 夜间模式：白色 / 金色 / 天蓝 / 珊瑚橙
- 日间模式：黑色 / 金色 / 天蓝 / 珊瑚橙
- 根因消除：不再有 None → 不走任何 None 分支 → 字号字体的设置不再被颜色路径干扰

**涉及文件**：`settings_screen.py` — `_get_theme_color_options()`

---

### 5.5 KivyMD 可折叠区域 expand 失败（adaptive_height 高度拉回 0）

**【用户要求】**
第四组折叠后再点击展开，内容应可见且图标变回 ▼。

**【尝试1 — opacity + height 切换】**
- 方案：折叠 `opacity=0, height=0`；展开 `opacity=1, height=_expanded_height`
- 结果：展开后内容不可见（height=0），但点击空白区域会触发样式变化，说明内容存在但不可见

**【根因定位】**
- 定位：`section_content` 使用 `adaptive_height: True`。展开时设置 `height = _expanded_height`，但 `adaptive_height` 绑定立即将 `height` 拉回 `minimum_height`。刚设置 `opacity=1` 后，Kivy 还未重新计算 `minimum_height`（仍为 0），导致 `height` 被覆盖为 0

**【尝试2 — 去掉 adaptive_height】**
- 方案：`size_hint_y: None`
- 结果：初始页面全部重叠，所有控件堆在一起（高度为 0，无自然布局）

**【最终方案 — 展开时临时关闭 adaptive_height】**
```python
def _toggle(*_):
    if section_content.opacity:
        section_content._expanded_height = section_content.height or section_content.minimum_height
        section_content.opacity = 0
        section_content.height = 0
        header_btn.text = f"▶ {label_text}"
    else:
        section_content.opacity = 1
        header_btn.text = f"▼ {label_text}"
        section_content.adaptive_height = False
        section_content.height = section_content._expanded_height or 200
        Clock.schedule_once(lambda dt, sc=section_content: setattr(sc, 'adaptive_height', True), 0)
```
- 初始保持 `adaptive_height: True`（正常显示）
- 折叠：opacity 归零 + height 归零
- 展开：先设 `adaptive_height=False` 阻止自动覆盖 → 手动恢复保存的高度 → 下一帧恢复 `adaptive_height=True`

**涉及文件**：`settings_screen.py` — `_make_collapsible_section()`

---

### 5.6 全局排查清单（R30 贯穿全流程）

| 排查点 | 发现 |
|---|---|
| `MDSwitch(active=…)` | `main_screen.py:635` 同样构造参数设置（edit_username），一并修复 |
| `_set_chip_text_color` → `_apply_chip_text_style` | 函数名变更后 grep 确认 0 残留引用 |
| 模块级 `COLOR_OPTIONS` | 4 组调用统一切换为 `_get_theme_color_options()` |
| `list(None)` 风险 | 组1后缀、组4标签 `_on_save` 均已兜底 |
| `text_color=None`（MDLabel 拒绝） | 组1/组4 所有 `_refresh_preview` 均已加 `if color:` 守卫 |
| `font_name=""` 空字符串 | 沿用已有 `or "Roboto"` 模式 |
| 颜色选项主题感知 | 日间给黑色、夜间给白色，不再有"默认" |

### 模型名称

DeepSeek V4 Pro

---

## 6. 双主题文字样式默认值未生效 — 夜间模式全白、白天模式全黑

### 问题描述与背景

- **日期**：2026-06-23
- **背景**：实现了白天/黑夜模式各自独立的文字样式系统（10 个 UserSettings key），为两套样式分别设计了美观的显式默认值（金/天蓝/珊瑚橙/黑/白）。但用户运行后发现：夜间模式下所有文字全部显示为白色，白天模式下全部显示为黑色，明显不符合预设的默认配色。

---

### 解决过程

**【用户要求】**
"黑夜模式中文字样式出现大量白色，白天模式中出现大量黑色文字样式。明显不符合默认值"

**【尝试1 — 定位根因】**
- 检查 `_apply_*_style()` 方法的完整调用链：`_load_style()` → DB 无记录返回 `None` → `or {}` 兜底
- `{}` 中 `color` 字段为 `None` → `if color:` 分支不进入
- 结果：文字保持 KivyMD 主题色（深色模式 = 白色，浅色模式 = 深色）
- **关键发现**：`LIGHT_DEFAULTS` / `DARK_DEFAULTS` 字典定义在 `settings_screen.py` 中，但 `main_screen.py` 的消费端从未引用它们。默认值"定义但未消费"是根本原因。

**【最终方案】**
1. 将默认值从 `settings_screen.py` 移到 `main_screen.py`（消费端），重命名为 `LIGHT_STYLE_DEFAULTS` / `DARK_STYLE_DEFAULTS`（key 为基础名，不含 `dark_` 前缀）
2. 新增 `MainScreen._get_style_default(base_key)` — 根据当前 `theme_style` 选择对应的默认值字典
3. `_apply_title_suffix_style()`、`_apply_func_row_style()`、`_apply_section_header_style()`：`or {}` → `or self._get_style_default("base_key")`
4. `_build_note_card()`：`or {}` → `or self._get_style_default("note_card_styles")`
5. `_load_username_style()`：DB 无记录时 fallback 到默认值，追加显式 `return`（之前静默跳过导致属性保持空字符串）
6. `_save_username_style()`：修正为 theme-aware key（之前写死 `'username_style'` 无前缀，与 `_load` 的 prefix 逻辑不一致）
7. `settings_screen.py`：删除旧的 `LIGHT_DEFAULTS` / `DARK_DEFAULTS`，改为 `from app_tool.ui.main_screen import LIGHT_STYLE_DEFAULTS, DARK_STYLE_DEFAULTS`；4 个 `open_groupN_dialog` 的 `or {}` 全部改为 `or defaults.get("base_key", {})`
8. 连带修复测试：`test_default_font_is_empty`（期望 `""`）→ `test_default_font_is_dongfangdakai`（新默认字体为 `"AlimamaDongFangDaKai"`），因为 `MainScreen.__init__` 调用了 `_load_username_style()` 会立即应用默认值

**涉及文件**：
- `app_tool/ui/main_screen.py` — 新增 `LIGHT_STYLE_DEFAULTS` + `DARK_STYLE_DEFAULTS` + `_get_style_default()`
- `app_tool/ui/settings_screen.py` — 导入默认值，4 个 dialog 方法改 fallback
- `app_tool/tests/test_ui.py` — 更新测试 + 新增 6 个双主题样式测试

### 模型名称

DeepSeek V4 Pro

---

## 7. 特征测试护航的渐进式代码优化 — 代码去重 + SQL 性能 + UI 增量刷新

### 问题描述与背景

- **日期**：2026-06-24
- **背景**：便签应用功能已基本完备（特征测试 97 项全绿 + TDD 测试 177 项），但用户反馈操作卡顿严重：创建便签、排序切换、标签管理、批量删除、编辑便签均有明显延迟。同时代码存在多处重复实现。要求在特征测试全绿的前提下，分步安全重构。

---

### 第一阶段：代码去重（风险极低，无性能影响）

**问题：** 5 组方法在多个文件中重复实现。

| 重复方法 | 文件数 | 提取到 |
|---|---|---|
| `_toast()` | 3 | `utils.py:ToastMixin` |
| `_get_services()` | 3 | `utils.py:ServiceMixin._app` |
| `_fix_chip_label_color` + `_make_chip` | 2 | `chip_utils.py`（模块函数） |
| `_load_style` / `_load_style_dict` + `save_style` / `_save_style_dict` | 2 | `utils.py:load_setting/save_setting` |

**关键教训：重命名时需保留兼容包装**
- `MainScreen.save_style()` 和 `MainScreen._load_style()` 被 TDD 测试直接调用
- 提取为模块函数后测试报 `AttributeError`
- 修复：在 `MainScreen` 上保留同名包装方法，委托给模块函数
- **教训**：提取公共方法时，先 grep 所有调用方确认是 `self.method()` 还是模块级引用

---

### 第二阶段：SQL 性能优化（风险极低，消除 N 次数据库往返）

**2.1 — 批量获取标签消除 N+1 查询**

- `refresh_list()` 的 `_build_note_card()` 对每条便签调用 `get_tags(note_id)`（一次 SQL）
- 新增 `NoteService.get_tags_batch(note_ids)` — 一条 `WHERE nt.note_id IN (...)` 返回 `{note_id: [tag_name, ...]}`
- `refresh_list()` 在循环前批量查询，传给 `_build_note_card(note, tag_names)`
- **效果**：N 次 SQL → 1 次

**2.2 — 合并 create() 重复 commit**

- 原代码：`INSERT INTO Note` → `commit()` → `fts_insert()` → `commit()`
- 修复：`INSERT` → `fts_insert` → `commit()`（一次）
- `fts_insert` 仅执行 SQL 无独立 commit，两次合并安全

**2.3 — 标签批量删除**

- 原代码：`_execute_batch_delete()` 逐条调用 `tag_svc.delete()` = N 次 `commit`
- 新增 `TagService.batch_delete(names)` — 一条 `DELETE FROM Tag WHERE name IN (...)` + 一次 `commit`
- **效果**：N 次 commit → 1 次

---

### 第三阶段：UI 增量刷新（核心收益，但踩坑回退）

**3.1 — 排序切换就地重排 ✅**

- 新增 `_reorder_cards()`：收集现有卡片 → `remove_widget` 取下 → 按新顺序 `add_widget` 放回
- 0 次 widget 创建，完全复用现有 NoteCard 实例
- 搜索模式仍走 `refresh_list()`

**3.2 — 创建便签增量添加 ✅**

- 新增 `_add_new_card(note)`：构建单张卡片 → 移除空状态提示 → 找到置顶组之后的位置插入
- 替代 `refresh_list()` 全量重建

**3.3 — 编辑便签就地更新 ✅**

- `on_save` 回调中直接设 `card.note_title/content/tag_names` Kivy 属性
- 替代 `refresh_list()` 全量重建

**3.4 — 删除/完成/置顶/撤销增量 ❌ 已回退**

- **尝试**：用 `remove_widget` + `add_widget` 在容器间移动卡片，就地切换 `is_completed`/`is_pinned` 属性
- **结果**：用户反馈比修改前更卡顿
- **根因**：阶段二 SQL 优化后 `refresh_list()` 已足够快；增量移动引入了 Kivy 属性回调链 + `children` 遍历 + 容器间跨移，反而更重
- **教训**：当 SQL 瓶颈消除后，widget 树移动操作的开销可能超过全量重建；不要假设增量一定比全量快

**3.5 — 标签管理页跳过无变化刷新 ✅**

- 新增 `_needs_refresh` 标记：`on_leave` 置 `True`，`refresh_list` 后置 `False`，`on_enter` 按需调用
- 效果：切回标签管理页时若数据未变，跳过全量行重建

---

### 关键技术点

| 点 | 说明 |
|---|---|
| 特征测试 97 项全绿兜底 | 每步完成后跑全量，零回归才继续 |
| 保留兼容包装 | `save_style`/`_load_style` 留作委托方法 |
| N+1 消除用 `IN (...)` 批量查询 | 一次 SQL 替代循环查询 |
| Kivy `remove_widget` 不销毁 widget | 可安全取下再放回（3.1 的核心前提） |
| widget 树移动不一定比全量快 | 3.4 的回退证明 SQL 优化后 `refresh_list` 就够快 |

### 模型名称

Qwen Code

---

## 8. 已完成区折叠/展开视图跳动 — 两轮 TDD 暴露需求澄清不足

### 问题描述与背景

- **日期**：2026-06-25
- **背景**：便签主界面已完成的卡片默认为折叠状态。用户点击折叠图标展开或折叠已完成区时，出现视图跳动、响应延迟等问题。问题本质是需求澄清不充分——用户知道"我想要什么结果"但无法用技术术语准确表达，AI 按自己的理解直接动手，导致两轮返工。

---

### 第一轮（失败 — AI 误判根因）

**【用户要求（模糊版）】**
"展开已完成卡片时全部页面刷新。请改为观察视图不动，仅卡片变为展开状态。"

**【尝试方案 — 标记完成时增量更新】**
- AI 理解：`_handle_complete_toggle` 调用 `refresh_list()` 全量重建是问题
- 修复：改为增量移动卡片（`remove_widget` + `add_widget`），不调用 `refresh_list()`
- 连带实现：完成后自动展开已完成区、折叠时保存/恢复 scroll_y
- 测试：11 个特征测试全绿，全量 323 通过无回归

**【用户反馈】**
"展开后点击，会产生滚动位置的跳动。折叠时点击，需要 5 秒才能往下滚动，时间过长。"

**【根因分析】**
- AI 误判了"页面刷新"的原因：用户说的不是 `refresh_list()` 的数据重建，而是视图的**视觉跳动**
- `_update_completed_visibility` 中设置 `completed_box.height = 0` → `list_box` 内容高度缩小 → ScrollView 重算 → 视图跳
- "保存/恢复 scroll_y"方案试图用数学补偿来修复高度变化引起的跳动，但引入了 Clock 延迟回调，反而导致 5 秒延迟

---

### 第二轮（成功 — 用户明确需求后一次通过）

**【用户要求（明确版）】**
"点击折叠按钮时，不论是展开还是折叠，滚动视图下，内容高度不变，滚动位置不变，区别在于展开时卡片为可见可点击状态。折叠时用空白占位，不可点击不可见。"

**【最终方案 — 内容高度永不变化】**

核心思想：`completed_box.height` 始终由 KV 绑定 `height: self.minimum_height` 管理，代码**永不复写**。

| | 修改前 | 修改后 |
|---|---|---|
| 展开 | `opacity=1` + `height=minimum_height` | `opacity=1` + `disabled=False` |
| 折叠 | `opacity=0` + `height=0` + 保存/恢复 scroll_y | `opacity=0` + `disabled=True` |

- 移除 `_restore_scroll_after_collapse` 方法
- 移除 `Clock.schedule_once` 回调
- 折叠 = 空白占位（高度保留，opacity=0，disabled=True 阻止触摸穿透）
- 展开 = 瞬时可见（opacity=1，disabled=False）

**涉及文件**：
- `app_tool/ui/main_screen.py` — `_update_completed_visibility()` 简化（去 height + 去 scroll 恢复 → 仅 opacity + disabled）
- `app_tool/tests/characterization/test_complete_toggle_no_refresh.py` — 8 个特征测试

**全量回归**：324 通过，0 新增失败。

---

### 核心教训 — 新增 R33 规则

**关键发现**：两轮 TDD 合计 19 个测试（第一轮 11 个 + 第二轮 8 个）、3 次代码变更（第一轮增量更新 + scroll 恢复 → 第二轮彻底去高度），根因不是 AI 能力不足，而是**需求澄清不充分**。

用户的原始描述"页面刷新"在 AI 脑中映射为 `refresh_list()` 数据重建，但用户实际指的是视觉跳动。如果第一轮开始前就用结构化表格追问 5 个技术维度（内容高度、滚动位置、可见性、可点击性、响应时间），只需一轮即可完成。

这条教训已提炼为 **R33 规则**（写入 `rules/ui_rules.md`）：
> 当用户需求涉及 UI 交互且表达模糊时，AI 必须在动手前用表格形式逐维度追问（白话解释 + 互斥选项），确认全部细节后再开始 TDD。

**致用户的反思**（用户口述，AI 记录）：
> "真正限制问题解决的，是我向你描述问题的能力。我不知道'滚动视图'、'滚动位置'这些技术术语的准确含义，也没想清楚'内容高度要不要变'这种细节。但 AI 如果在我说不清楚的时候，能主动问'滚动位置要不要变？内容高度要不要变？'并解释这些词是什么意思，我们根本不需要两轮返工。"

---

### 模型名称

Qwen Code

---

## 9. 便签卡片顺序完全反转 — Kivy vertical BoxLayout children 顺序误解

### 日期

2026-06-25

### 模型名称

Qwen Code

### 问题描述与背景

用户报告：所有便签卡片的排列顺序与预期完全相反。手动置顶的卡片跑到了最下面，非置顶卡片按更新时间 DESC 排序也出现在最下面。问题表现为"整个列表完全反转"。

### 解决过程

```
   【用户要求】← 便签卡片排列顺序完全反转，置顶卡片跑最下面，
                  非置顶按更新时间应在顶上却在底下
       ↓
   【尝试1 — 检查代码中 add_widget 是否缺少 index= 参数】
   - 发现 fix-branch 已有 index=len(children)，main 分支没有
   - 推断 fix-branch 代码应该已经修复 → 检查 .pyc 缓存
   - 清除所有 .pyc 文件，用户重启应用 → 问题依旧
   - 关键失误：假设 index=len(children) 是正确的修复方向
       ↓
   【用户反馈】← 重启后问题仍然存在。指出 ui_spec.md §8.2 已记录此 bug
       ↓
   【尝试2 — 深入分析 Kivy 源码 _iterate_layout】
   - 逐行追踪服务层 SQL（DESC 排序确认正确）→ UI refresh_list → _add_new_card
   - 所有路径使用 index=len(children)，按假设应该正确
   - 写独立脚本验证 Kivy 行为 → 断言通过 → 陷入死循环
   - 用户反问：你真的检查了 Kivy 源码中 BoxLayout vertical 的布局方向吗？
       ↓
   【关键突破 — 阅读 Kivy boxlayout.py L285】
   - vertical 布局: y = padding_bottom + selfy（从底部开始）
   - for 循环 enumerate(zip(hint, sizes)) 正序遍历 children
   - children[0] 获得 y = padding_bottom（视觉底部）
   - children[-1] 获得最高的 y 值（视觉顶部）
   - 结论：**children[0]=视觉底部，children[-1]=视觉顶部**
   - 与之前所有假设（children[0]=视觉顶部）完全相反！
       ↓
   【最终方案】← 完全反转修复方向

   之前的"修复"（index=len(children)）基于错误假设，反而造成了反转：
   - index=0（默认 prepend）：保持顺序 → children[-1]=TOP=最新卡片 ✓
   - index=len(children)（append）：反转顺序 → children[0]=BOTTOM=最新卡片 ❌

   修改清单：
   | 位置 | 修改 |
   |------|------|
   | refresh_list() 3处 | add_widget(x, index=len(...)) → add_widget(x) |
   | _reorder_cards() 2处 | 同上 |
   | _add_new_card() | 查找第一个 is_pinned=True（替代 is_pinned=False） |
   | _handle_complete_toggle() | 同上逻辑修正 |
   | test_add_widget_reversal.py | 完全重写为反映真实 Kivy 行为 |

   全量测试：365/365 全绿
```

### 核心教训

**1. 框架源码是唯一真相来源**

当多轮推理都指向"代码正确"但用户坚持问题存在时，说明推理的前提假设有误。本例中，所有分析都建立在"children[0]=视觉顶部"的假设上，而这个假设从未被验证。直到阅读 Kivy `_iterate_layout` 源码（`y = padding_bottom` + 正序遍历），才发现真相完全相反。

**2. 特征测试也会成为"假绿灯"**

`test_add_widget_with_explicit_index_preserves_order` 测试通过了，但它是"假绿灯"——测试验证 `children[0]=='first'`，错误地假定 children[0] 是视觉顶部。实际上 children[0] 是视觉底部，所以视觉顺序是反转的，但断言恰好通过。这印证了错题本已有教训（假绿灯）：测试通过不代表行为正确。

**3. "修复"可能比 bug 更糟糕**

`index=len(children)` 是为了修复 `add_widget()` 默认 index=0 的"反转"而添加的。但默认 index=0 在 vertical BoxLayout 中实际上是正确行为（prepend 使第一个元素最终在 children[-1]=TOP）。这个"修复"本身才是造成反转的根因。

**4. 跨层追踪需要走到最底层**

从 Service SQL → Note 对象 → refresh_list → add_widget → BoxLayout._iterate_layout，只有追踪到 Kivy 源码层才暴露真相。在中间任何一层停止都会得出错误结论。

### 致用户的反思

> "这个错误太隐蔽了。好几轮下来都没检查出来，因为所有人都默认 children[0]=TOP——这是直觉，但 Kivy 的垂直布局偏偏是 children[0]=BOTTOM。我们被自己的假设困住了。多亏你坚持问题存在，让我继续深挖源码，才最终发现这个反直觉的事实。"

---

## 7.4 test_ui.py 27 个测试因 _load_username() 裸数据库访问崩溃

### 日期

2026-06-25

### 模型名称

Qwen Code

### 问题描述与背景

全量测试 7 fail + 21 error 集中在 `test_ui.py`，错误均为 `sqlite3.ProgrammingError: Cannot operate on a closed database`，调用栈指向 `main_screen.py:592` 的 `_load_username()`。

56 个测试中 27 个崩溃：
- **23 个纯 UI 测试**（`TestFuncRowSizes`、`TestUsernameStyle`、`TestSearchBarCloseButton` 等）——仅验证组件尺寸/字体/定位，不该碰数据库，但 `MainScreen.__init__()` 强制调用 `_load_username()` 被牵连
- **4 个持久化测试**（`TestTextStylePersistence`）——确实需要数据库，但 `kivy_app.db_conn` 被前序测试污染

### 解决过程

```
   【用户要求】← 分析失败原因，给出方案
       ↓
   【尝试方案】← AI 提出 A/B/C 三个方案
       ↓
   【用户反馈】← 选 C，立刻修复
       ↓
   【最终方案】← 两步修改：

① conftest.py — kivy_app_instance fixture 增加强制重置：
   kivy_app.db_conn = None  # function 级别，每次测试前清空
   ↓
② main_screen.py — _load_username() 增加防御性兜底：
   if not app or not app.db_conn: return
   try: ... except Exception: pass
```

**关键发现：**
- `if app and app.db_conn:` 守卫对 `None` 有效，但对**已关闭的 sqlite3.Connection 对象**无效（已关闭连接仍为 truthy）
- session 级别 `kivy_app` fixture 可被前序测试函数体内 `app.db_conn = db_conn` 污染
- 纯 UI 测试不应因数据库不可用而崩溃

**修复后：** `test_ui.py` 56/56 全绿。

### 沉淀规则

→ `rules/core_rules.md` **R39**：UI 初始化禁止裸数据库访问，必须 `try/except` 防御
→ `rules/core_rules.md` **R39-A**：测试 conftest 的 `kivy_app_instance` fixture 必须在返回前重置 `kivy_app.db_conn = None`

---

## 10. GitHub Actions APK 构建：从反复失败到成功生成 — 8 轮试错全记录

### 日期

2026-06-26 ~ 2026-06-27

### 模型名称

Qwen Code

### 问题描述与背景

通过 GitHub Actions + Buildozer 构建 Android APK，从首次提交到最终成功安装运行，跨越 8 个独立错误。每个错误都是跨层问题（Python 版本 → SDK 许可 → C 编译 → glibc 兼容 → Gradle → Python 版本不匹配），覆盖了 Buildozer 工具链的全部层级。

### 解决过程

```
   【用户要求】← 构建 APK 失败了，帮我看看
       ↓
   ┌─ 第一层：Python 运行时 ─────────────────────────────┐
   │                                                      │
   │ 【尝试1】pip install setuptools 提供 distutils        │
   │   错误: ModuleNotFoundError: No module named          │
   │         'distutils'                                   │
   │   修复: pip install ... setuptools                    │
   │         ↓                                            │
   │ 【用户反馈】❌ 失败 — setuptools shim 对 buildozer    │
   │             的 import 路径无效                        │
   │         ↓                                            │
   │ 【尝试2】降级 Python 3.12 → 3.11                      │
   │   修复: python-version: '3.11'                        │
   │         ↓                                            │
   │ 【用户反馈】✅ distutils 关通过                       │
   └──────────────────────────────────────────────────────┘
       ↓
   ┌─ 第二层：SDK 许可 ──────────────────────────────────┐
   │                                                      │
   │ 【尝试3】预创建 licenses 目录 + 写入 license hash     │
   │   错误: "License android-sdk-license: Accept?"        │
   │   修复: mkdir licenses/ && echo hash > license        │
   │         ↓                                            │
   │ 【用户反馈】❌ 失败 — "sdkmanager path does not       │
   │             exist, sdkmanager is not installed"       │
   │   根因: 预创建目录让 buildozer 误判 SDK 已安装，      │
   │         跳过 SDK tools 下载                           │
   │         ↓                                            │
   │ 【尝试4】yes | buildozer android debug（标准方案）    │
   │         ↓                                            │
   │ 【用户反馈】✅ 管道自动应答许可，SDK 下载成功          │
   └──────────────────────────────────────────────────────┘
       ↓
   ┌─ 第三层：C 扩展编译 — libffi ───────────────────────┐
   │                                                      │
   │ 【尝试5】安装 libtool + autoconf + automake           │
   │   错误: configure.ac:215: possibly undefined macro:   │
   │         LT_SYS_SYMBOL_USCORE                          │
   │   修复: apt install libtool autoconf automake         │
   │         ↓                                            │
   │ 【用户反馈】❌ 失败 — 同样的宏缺失错误                 │
   │   根本原因: LT_SYS_SYMBOL_USCORE 来自 libltdl-dev，   │
   │            不是 libtool。搜索社区找到精确答案。       │
   │         ↓                                            │
   │ 【尝试6】安装 libltdl-dev                             │
   │   ③ 社区: CSDN 文章 + GitHub libffi issue #210        │
   │   → "sudo apt-get install libltdl-dev"                │
   │         ↓                                            │
   │ 【用户反馈】✅ libffi 编译通过                        │
   └──────────────────────────────────────────────────────┘
       ↓
   ┌─ 第四层：glibc/NDK 交叉编译冲突 ────────────────────┐
   │                                                      │
   │ 【尝试7】用户质疑"你真的参考行业最佳实践了吗？"       │
   │   → 搜索社区：多篇独立文章指出 Ubuntu 24.04 与       │
   │     Buildozer 存在已知兼容性问题                      │
   │   错误: __GNUC_PREREQ is not defined                  │
   │         (宿主机 glibc 2.39 cdefs.h 泄露到 NDK Clang)  │
   │   修复: runs-on: ubuntu-latest → ubuntu-22.04         │
   │         ↓                                            │
   │ 【用户反馈】✅ glibc 兼容问题解决                     │
   └──────────────────────────────────────────────────────┘
       ↓
   ┌─ 第五层：Gradle Java 版本 ──────────────────────────┐
   │                                                      │
   │ 【尝试8】设置 JAVA_HOME 为 Java 17                    │
   │   错误: "Android Gradle plugin requires Java 17.      │
   │          You are currently using Java 11."            │
   │   修复: export JAVA_HOME=temurin-17-jdk               │
   │         ↓                                            │
   │ 【用户反馈】✅ APK 成功生成！                          │
   └──────────────────────────────────────────────────────┘
       ↓
   ┌─ 第六层：APK 运行时崩溃 ────────────────────────────┐
   │                                                      │
   │ 【用户反馈】❌ 安装后点击闪退，电脑上运行正常          │
   │   根因: requirements = python3 拉取 Python 3.14       │
   │         → 与 Kivy 2.3.1 / KivyMD 1.2.0 不兼容       │
   │         → 用户验证："不是可能不兼容，是一定不兼容"    │
   │   修复: requirements = python3==3.11,...              │
   │          （与 CI 构建环境 Python 3.11 一致）          │
   │         ↓                                            │
   │ 【最终状态】修正后的 APK 待验证                        │
   └──────────────────────────────────────────────────────┘
```

### 核心教训

**1. AI 自有知识与社区共识的差距（→ R42）**

AI 最初引用的"最佳实践"实际来自 auto-skill（对话回放），而非真正的行业共识。用户质问后搜索社区发现：
- Ubuntu 24.04 不兼容 Buildozer（社区早已知晓，AI 不知）
- `libltdl-dev` 而非 `libtool` 提供 `LT_SYS_SYMBOL_USCORE`
- 标准 apt 依赖列表（zip/unzip/cmake/pkg-config/libffi-dev 等）AI 初次未列全

**教训**：AI 预训练知识 ≠ 实时社区状态，必须 ①②③ 交叉验证。

**2. Python 版本在桌面 vs APK 中的不对称性**

桌面开发环境用 Python 3.12（本地 .python312），CI 构建用 Python 3.11（运行 buildozer），APK 内置 Python 由 `requirements` 中的 `python3` 决定。`python3` 无版本约束时 p4a master 拉取最新 Python 3.14 → 与 Kivy 生态不兼容。**三处 Python 版本必须显式管理，不能依赖默认值。**

**3. 8 个错误覆盖 Buildozer 全栈层级**

| 层级 | 错误 | 修复 |
|------|------|------|
| Python 运行时 | distutils 缺失 | CI Python 3.12→3.11 |
| SDK 工具 | License 未接受 + SDK 未下载 | `yes \|` 管道 |
| C 扩展 | libffi autoreconf 失败 | libltdl-dev |
| 系统库 | glibc/NDK 交叉编译冲突 | ubuntu-24.04→22.04 |
| Java 工具链 | Gradle 要求 Java 17 | JAVA_HOME 设置 |
| APK 内置 | Python 3.14 不兼容 | python3→python3==3.11 |

没有一个错误是重复的，每个都在不同层。这种跨层错误链是 Buildozer 首次配置的常见模式。

**4. "先查后做"原则的价值（→ R41）**

如果第一轮就：
1. Invoke `buildozer-github-actions` skill → 跳过 distutils 试错
2. 搜索社区标准 apt 列表 → 跳过 libtool vs libltdl-dev 试错
3. 搜索 Ubuntu 版本兼容性 → 跳过 24.04 试错
4. 检查 APK 内置 Python 版本 → 跳过 Python 3.14 崩溃

8 轮错误可压缩到 2-3 轮。

### 涉及文件

| 文件 | 关键修改 |
|------|---------|
| `.github/workflows/build-apk.yml` | Python 3.11 + ubuntu-22.04 + libltdl-dev + cmake/pkg-config 等完整 apt 列表 + JAVA_HOME 设置 + `yes \|` 管道 |
| `buildozer.spec` | `android.build_tools = 34.0.0` + `requirements = python3==3.11,...` |

### 沉淀规则

→ `rules/core_rules.md` **R41**：先查后做 — 先查知识再定方案最后动手
→ `rules/core_rules.md` **R42**：知识来源分级 — 按置信度决策，最高置信度 ①②③ 交叉验证
