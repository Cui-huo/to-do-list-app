# 当前行为特征记录 — 交互行为

> 目标：记录用户操作链路的完整行为特征。
> 每条 = 一个完整交互流程（触发→状态变更→UI反馈）。

---

## INT-01：创建便签

**步骤**：FAB → 填写 → 保存

**行为**：
1. 点击 FAB → 弹窗标题 "新增便签"
2. 标签芯片点击切换选中/未选，选中=primary_color背景+白字
3. 超过 3 个标签 → "每个便签最多 3 个标签" + 2秒后消失
4. 内容为空时保存 → content_field.error=True + "内容不能为空" → 弹窗不关闭
5. 保存成功 → note_svc.create() + add_tag() → 弹窗关闭 → Toast "便签创建成功" → refresh_list()
6. 不存在的标签 → 静默跳过（见 CT-P0-02）

---

## INT-02：编辑便签

**步骤**：卡片 pencil → 修改 → 保存

**行为**：
1. 弹窗标题 "编辑便签"，标题/内容/标签预填当前值
2. 保存 → note_svc.update() + 标签 add/remove → 弹窗关闭
3. **现状：编辑保存后无显式成功 Toast** — refresh_list() 直接刷新

---

## INT-03：删除便签

**步骤**：卡片 delete → 确认

**行为**：
1. 确认弹窗 "确认删除此便签吗？"
2. 取消 → 无任何变化
3. 确认 → note_svc.delete() → refresh_list()
4. Toast "应用未关闭的12小时内，可以撤销最近1条删除"
5. undo_btn 出现（opacity=1, disabled=False）
6. 连续删两条 → _undo_data 只保留最后一条

---

## INT-04：撤销删除

**步骤**：删除后 → 点击 undo 按钮

**行为**：
1. 删除后 undo_btn 可见（金色图标）
2. 点击 → note_svc.undo_delete() → refresh_list() → Toast "便签已恢复"
3. undo_btn 消失
4. 12小时后 get_undo_info() 返回 None → undo_btn 不可见

---

## INT-05：标记完成/取消完成

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

## INT-06：手动置顶/取消

**步骤**：卡片 pin_btn

**行为**：
1. 未置顶 → 点击 pin-outline → pin_note()
   - 已置顶报 ValueError → Toast 错误
   - 否则卡片排最前，图标变 pin + opacity=1
2. 已置顶 → 点击 pin → unpin_note()
   - 未置顶报 ValueError → Toast 错误
   - 否则图标变 pin-outline + opacity=0.3

---

## INT-07：排序切换

**步骤**：功能栏排序图标

**行为**：
1. toggle_sort_preference() → updated_at ↔ created_at
2. set_sort_preference() 写 DB
3. _update_sort_label() 更新文字+图标
   - updated_at → "按更新时间" + 图标 `\U000F1549`
   - created_at → "按创建时间" + 图标 `\U000F1547`
4. refresh_list() → Toast "排序切换：按XXX"

---

## INT-08：搜索筛选

**步骤**：搜索图标 → 设条件 → 搜索

**行为**：
1. 弹窗 "搜索筛选"，关键词+标签+时间类型+年/月/周
2. 标签 AND 逻辑，无数量上限（与便签编辑不同）
3. "清除" → clear_search() → 全量刷新
4. "搜索" → _current_search_params 设置 → search_bar 出现 → refresh_list() 过滤
5. 结果含已完成+未完成（CT-P2-04）

---

## INT-09：清除搜索条件

**步骤**：搜索条件栏 "取消 ✕"

**行为**：
1. _current_search_params = None
2. search_bar.height = 0, search_label.text = ""
3. search_close_btn opacity=0, disabled=True
4. refresh_list() 全量

---

## INT-10：已完成区折叠/展开

**步骤**：点击 "已完成 (N)" 旁箭头

**行为**：
1. 折叠→展开：completed_box.opacity=1, expand_btn.icon="chevron-up"
2. 展开→折叠：completed_box.opacity=0, completed_box.height=0, icon="chevron-down"

---

## INT-11：新建标签

**步骤**：标签页 + → 填写 → 创建

**行为**：
1. 弹窗 "新建标签"，hint "标签名称（1-10字符）"
2. 空名 → Toast "标签名不能为空"
3. 重名 → Toast "标签「XXX」已存在"
4. 成功 → 弹窗关闭 → refresh_list() → Toast "标签「XXX」创建成功"

---

## INT-12：重命名标签

**步骤**：标签行 pencil → 修改 → 保存

**行为**：
1. 弹窗 "重命名「旧名」"，预填旧名
2. 保存 → tag_svc.update() → 同步置顶列表 → refresh_list()
3. Toast "标签更名为「新名」"

---

## INT-13：删除单个标签

**步骤**：标签行 delete

**行为**：
1. 确认弹窗 "将移除所有便签的此标签。"
2. 确认 → tag_svc.delete() → 自动从置顶列表移除 → refresh_list()
3. Toast "标签「XXX」已删除"

---

## INT-14：批量删除标签

**步骤**：批量删除图标 → 勾选 → 确认

**行为**：
1. 点击 delete-sweep → 每行出现 Checkbox，图标变 check
2. 底部 "删除选中 (N)" 红色按钮
3. 确认弹窗 → 逐个 delete()
4. 退出批量模式，Toast "选中标签已删除"

---

## INT-15：标签置顶切换

**步骤**：标签行 pin 图标

**行为**：
1. toggle_pinned() → 已置顶→取消；未置顶→添加
2. 超出 3 个淘汰最早（FIFO，CT-P1-04）
3. refresh_list() → Toast

---

## INT-16：用户名编辑

**步骤**：点击顶栏用户名 → 编辑 → 保存

**行为**：
1. 弹窗 "编辑昵称"，预填当前值
2. 颜色(3色)/字体(3种)/粗体可选，预览实时更新
3. 取消 → 所有修改不保存（暂存机制）
4. 保存 → _save_username + _save_username_style → 顶栏更新

---

## INT-17：排序偏好切换（设置页）

**步骤**：设置页点击排序按钮

**行为**：
1. 按钮高亮：选中=primary_color+白，未选=bg_light+text_color
2. Toast "排序偏好：按XXX"

---

## INT-18：文字样式编辑（设置页）

**步骤**：点击 "编辑" → 修改 → 保存

**行为**：
1. 编辑其他主题 → Toast 拒绝
2. 正常编辑 → 预览 + 颜色/字号/粗体/字体
3. 保存 → 写 DB → 同步 MainScreen → Toast
4. 跨主题保存 → Toast "已保存，切换至对应模式可查看效果"

---

## INT-19：模版管理（设置页）

**行为**：
1. "使用" → apply_template() → 写白天+黑夜样式 → Toast
2. "+" → 输入名称 → save_current_as_template() → 追加
3. "编辑" → 输入新名称 → 更新
4. "删除" → 确认 → delete_template()

---

## INT-20：Toast/Snackbar 行为

**行为**：
- 所有 Toast 用 MDSnackbar(MDLabel(...))
- 2 秒时长
- 多个连续 Toast → 后一个覆盖前一个（不排队）
- 位置：屏幕中央
