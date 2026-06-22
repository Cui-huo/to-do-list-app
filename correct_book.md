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
