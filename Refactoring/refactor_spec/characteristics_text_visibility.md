# 当前行为特征记录 — 文字可见性

> 目标：记录 Light / Dark 两种主题下所有页面的文字可见性特征。
> 每条特征 = 一页中的一个文字区域 × 两种主题。

---

## 页面总览

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

## 一、主界面

### V-01：顶部标题栏

**位置**：main_screen.py KV FloatLayout > MDTopAppBar
**背景色（现状）**：
- Light: theme.primary_color（Indigo 蓝 ~ (0.25, 0.32, 0.71, 1)）
- Dark: theme.bg_dark

#### V-01a：用户名（username_btn）
- 默认文字色：(1, 0.85, 0.4, 1) 金色 — 两种主题相同
- 字体：AlimamaDongFangDaKai / 20sp / 非粗体

#### V-01b：后缀 "的专属便签本"（title_suffix_label）
- 默认文字色：(0.39, 0.71, 0.96, 1) 天蓝 — 两种主题相同
- 字体：Lemibo / 20sp / 非粗体
- 特殊：DB 中 color=None 时不设 text_color

#### V-01c：撤销按钮图标（undo_btn）
- 图标色：(1, 0.85, 0.4, 1) 金色 — 硬编码
- 正常 opacity=0, disabled=True
- 删除后 opacity=1, disabled=False

### V-02：功能栏

**背景**：theme.bg_light

#### V-02a：排序图标（func_sort_icon）
- 图标字体文字，28sp

#### V-02b：排序标签（sort_label）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (0.39, 0.71, 0.96, 1) 天蓝
- 字体：Lemibo / 12sp / 非粗体

#### V-02c：搜索标签 "便签检索"（func_search_label）
- 同 V-02b（共享 func_row_style）

#### V-02d：标签标签 "标签"（func_tag_label）
- 同 V-02b

#### V-02e：设置标签 "设置"（func_settings_label）
- 同 V-02b

### V-03：搜索条件栏（search_bar）

**背景**：theme.bg_light，初始 height=0

#### V-03a：搜索条件文字（search_label）
- Body2，theme.text_color

#### V-03b：取消 "取消 ✕"（search_close_btn）
- (0.4, 0.8, 1, 1) 亮蓝 — 硬编码
- 初始 opacity=0，有搜索后 opacity=1

### V-04：分类标题

#### V-04a："未完成"（incomplete_header）
- Light: (0.39, 0.71, 0.96, 1) 天蓝
- Dark: (1, 0.85, 0.4, 1) 金色
- 字体：AlimamaDongFangDaKai / 20sp / 非粗体

#### V-04b："已完成 (N)"（completed_label）
- 同 V-04a

#### V-04c：展开图标（expand_btn）
- chevron-down / chevron-up，默认图标色

### V-05：空态提示

"还没有便签，点击右下角 + 创建一个吧"
- Body1，Hint 色，居中

### V-06：便签卡片（NoteCard）

正常背景 theme.bg_normal，已完成背景 theme.bg_dark

#### V-06a：卡片标题（title_label）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (1, 1, 1, 1) 白
- 字体：AlimamaDongFangDaKai / 16sp / 粗体
- 已完成 opacity=0.6

#### V-06b：标签芯片文字
- (0.91, 0.45, 0.29, 1) 珊瑚橙 — 硬编码，两种主题相同
- 芯片背景 theme.bg_light
- 字体：Lemibo / 12sp / 非粗体
- KivyMD 1.2.0 MDChipText→MDLabel 转换需 _apply_chip_text_style 修复

#### V-06c：内容预览（content_preview）
- Light: (0.05, 0.05, 0.05, 1) 黑
- Dark: (1, 1, 1, 1) 白
- 字体：Lemibo / 12sp / 非粗体
- 已完成 opacity=0.5，max 2 行截断

#### V-06d：完成按钮（complete_btn）
- 未完成 check-circle，已完成 undo，默认图标色

#### V-06e：编辑按钮
- pencil，默认图标色

#### V-06f：删除按钮
- delete，theme_icon_color: "Error"（红色）

#### V-06g：置顶按钮（pin_btn）
- 未置顶 pin-outline + opacity=0.3
- 已置顶 pin + opacity=1

### V-07：FAB

- plus，theme.primary_color，右下角 16dp

---

## 二、便签编辑弹窗

**组件**：dialogs.py AddEditContent + build_add_edit_dialog()

### V-08：标题输入框
- hint "标题（可选）"，max 50，mode rectangle

### V-09：内容输入框
- hint "内容（必填）"，max 5000，multiline，mode rectangle

### V-10：标签选择区
- 提示 "标签（点击选择）："，Caption
- 未选芯片：bg_light 背景 + text_color
- 已选芯片：primary_color 背景 + (1,1,1,1) 白 — 硬编码
- 超限提示 "每个便签最多 3 个标签"，Error 色，2 秒消失

### V-11：弹窗按钮
- "取消" + "保存"，MDFlatButton 默认色

### V-12：保存校验
- 内容空 → error=True + "内容不能为空"

---

## 三、搜索弹窗

**组件**：search_dialog.py SearchContent + build_search_dialog()

### V-13：关键词输入框
- hint "搜索关键词"，mode rectangle

### V-14：标签筛选
- 提示 "标签筛选（点击选择，AND 逻辑）："
- 未选 bg_light + text_color
- 已选 primary_color + (1,1,1,1) 白 — 硬编码

### V-15：时间类型芯片
- "创建时间" / "完成时间"
- 选中 primary_color+白，未选 bg_light+text_color

### V-16~V-18：年/月/周下拉
- 按钮文字 "全部" 或具体值，MDFlatButton 默认

### V-19：弹窗按钮
- "清除" + "搜索"，MDFlatButton 默认

---

## 四、设置页面

### V-20：顶栏
- 标题 "设置" + arrow-left
- Light: primary_color，Dark: bg_dark

### V-21：夜间模式开关
- "夜间模式" Body1，MDSwitch 默认

### V-22：排序偏好
- "排序偏好" Body1
- 选中 primary_color+白，未选 bg_light+text_color

### V-23：文字样式模版区
- "文字样式模版" Subtitle1
- 模版名 + "使用"/"删除"/"编辑"
- "+ 保存当前为模版" primary_color+白

### V-24~V-25：白天/黑夜文字样式区
- 标题 Subtitle1
- 4 行编辑入口，每行 标签名 + 预览(Hint) + "编辑"

### V-26：关于
- "便签应用 v0.1.0" Body2 Hint 居中

### V-27：样式编辑弹窗
- 预览区 + 颜色/字号/粗体/字体控件
- 颜色按钮文字 sum(rgb)>1.8 → 黑，否则白
- "取消" + "保存"

### V-28：模版操作弹窗
- 保存/重命名：输入框 + 取消/保存
- 删除：确认弹窗

---

## 五、标签管理页面

### V-29：顶栏
- "标签管理" + arrow-left + plus + delete-sweep/check
- Light: primary_color，Dark: bg_dark

### V-30：标签列表行
- 标签名 Body1
- 已置顶 pin + primary_color，未置顶 pin-outline + secondary_text_color
- 删除图标 Error 红

### V-31：空态
- "暂无标签，点击右上角 + 创建" Hint

### V-32：批量删除按钮
- "删除选中 (N)"，(0.9, 0.2, 0.2, 1) 红背景 + 白字 — 硬编码

### V-33：新建/重命名弹窗
- hint "标签名称（1-10字符）"
- "取消" + "创建"/"保存"

---

## 六、昵称编辑弹窗

### V-34：输入框
- hint "请输入你的名字"，max 10

### V-35~V-37：颜色/字体/粗体
- 颜色 3 按钮（金/天蓝/珊瑚橙），sum(rgb)>1.8 黑字
- 字体 3 按钮（默认/东方大楷/乐米波波）
- 粗体 MDSwitch

### V-38：预览
- "预览" Caption Secondary + 实时预览文字

### V-39：按钮
- "取消" + "保存"

---

## 七、确认删除弹窗

### V-40：弹窗
- 可变标题 + 消息 + "取消" + "确认删除"

---

## 八、Toast

- MDSnackbar(MDLabel(...))，2 秒，中央

---

## 硬编码颜色汇总

| 位置 | 颜色 | 随主题 |
|------|------|--------|
| username_btn | 金色 (1,0.85,0.4) | 不变 |
| title_suffix 默认 | 天蓝 (0.39,0.71,0.96) | 不变 |
| undo_btn 图标 | 金色 (1,0.85,0.4) | 不变 |
| search_close_btn | 亮蓝 (0.4,0.8,1) | 不变 |
| tag chip 文字 | 珊瑚橙 (0.91,0.45,0.29) | 不变 |
| 已选标签 chip | 白 (1,1,1) | 不变 |
| 批量删除按钮 | 红 (0.9,0.2,0.2) | 不变 |
