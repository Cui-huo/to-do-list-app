# 错题本

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
