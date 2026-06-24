# 当前行为特征记录 — 夜间模式切换

> 目标：记录主题切换的完整行为链。

---

## DM-01：开关切换流程

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

## DM-02：自动变化的属性

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

## DM-03：不自动变化的属性（硬编码）

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

## DM-04：切换后状态保持

**不丢失**：
- _current_search_params（搜索条件）
- _completed_expanded（已完成区折叠状态）
- _undo_data（撤销数据，仅超时清除）

**重建**：
- 全部卡片 clear_widgets → 重新 _build_note_card()
- undo_btn 可见性根据 get_undo_info() 重新判断

---

## DM-05：应用启动时主题恢复

**行为**：
1. app.py:build() → SettingsService.get_dark_mode() 读 DB
2. 设置 theme_cls.theme_style
3. Clock.schedule_once 延迟 _apply_titlebar_theme
4. MainScreen.on_enter → _update_theme_colors() + _apply_text_styles() + refresh_list()
5. 默认主题 = "Light"（DB 无记录时）
