# 便签 APP 规格文档 (SDD)

> **配套文档：** `rules.md`（设计规则）| `skills.md`（可复用操作流程）
> 本文档定义功能规格、数据模型、输入/输出、边界条件。交互流程细节见 skills.md。

---

## 0. 核心设计规则（摘要）

完整规则见 [`rules.md`](./rules.md)。

> **R1. ID 不可见** — 用户不接触 ID，只用可读名称。
> **R2. 点击优先** — 非编辑操作全部点击/滑动/选择器。
> **R3. 确认优先** — 不可逆操作必须确认框。
> **R4. 即时反馈** — 每个操作有 UI 反馈（Toast/位移/高亮）。

---

## 0.5. 视觉过渡规范（R11）

所有状态变更操作必须统一定义动画时序，禁止无过渡地刷新 UI。

| 操作 | 动画 | 时长 |
|---|---|---|
| 新增便签 | 卡片从 FAB 位置放大弹出到列表顶部 | 0.3s |
| 标记完成 | 卡片透明度 1→0.4 + 向已完成区下沉滑动 | 0.3s，动画结束后刷新列表 |
| 取消完成 | 卡片透明度 0.4→1 + 从未完成区顶部插入 | 0.25s |
| 删除便签 | 卡片向右滑出 + 淡出 | 0.2s，滑出后顶栏右侧显示[撤销]按钮 |
| 撤销删除 | 新卡片恢复到列表原位置 | 0.3s |
| 拖拽排序 | 拖动时卡片抬起阴影 + 其他卡片实时让位 | 实时（0 延迟） |
| 置顶/取消置顶 | 卡片瞬移到目标区（无动画，避免混淆） | — |
| 展开已完成区 | 已完成区从折叠态向下展开 | 0.25s |
| 搜索筛选 | 列表交叉淡入淡出 | 0.2s |
| 进入提醒页面 | 页面从右侧滑入 | 0.2s |
| 退出提醒页面 | 页面从右侧滑出 | 0.2s |

---

## 1. 概述

Android 卡片式便签应用。Kivy + KivyMD 构建 UI，SQLite 本地存储，FTS5 全文搜索，支持标签分类、手动拖拽排序、撤销删除、夜间模式、本地提醒和 WebDAV 同步。

---

## 2. 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| UI | Kivy + KivyMD | 卡片式 Material Design |
| 存储 | SQLite (sqlite3) | Python 内置，零依赖 |
| 全文搜索 | SQLite FTS5（独立表，手动同步） + LIKE 中文兜底 | ASCII 走 FTS5，中文走 LIKE |
| Markdown | markdown 库 | 便签内容预览渲染 |
| 后台提醒 | pyjnius → Android AlarmManager | 应用关闭后仍触发 |
| WebDAV | webdavclient3 | 手动 + 启动自动同步 |
| 测试 | pytest | :memory: SQLite 隔离测试 |

---

## 3. 边界条件 & 校验规则

### 3.1 字段约束

> **R14 补充**：后端提交校验的全部逻辑必须在前端同步复现（后端为最终防线，前端为体验层）。例如 content"不可为空/纯空白同空"在后端校验，前端也须在输入阶段做同样检测。

| 字段 | 约束 | 前端实时反馈（输入过程中） | 后端提交校验（保存时） |
|---|---|---|---|
| title | 0–50 字符 | 字符计数器实时显示；超 50 输入框变红、禁止继续输入 | 可空（默认 ''） |
| content | 1–5000 字符 | 字符计数器实时显示；超 5000 输入框变红、禁止继续输入 | 不可为空；纯空白同空处理 |
| 标签名 | 1–10 字符 | 字符计数器；空/纯空白时边框变红、[确认] 按钮置灰 | 不可重名；重名弹窗提示并聚焦 |
| remind_at | 允许任意时间（过去/未来） | 日期时间选择器默认值=当前时间 | 无 |
| pinned_tags | 最多 3 个 | 第 4 个置顶点击时 Toast 提示"最多 3 个置顶标签" | 自动淘汰最早置顶 |
| 每条便签提醒 | 最多 3 个 | 添加第 4 个时按钮置灰 + Toast "最多 3 个提醒" | 提交时拒绝 |
| 每个便签标签数 | ≤ 3 | 标签芯片数实时计数；超出时无法继续添加 + Toast "每个便签最多 3 个标签" | 提交时拒绝 |

### 3.3 反馈时序（R4）

| 操作 | 反馈 | 要求 |
|---|---|---|
| 任何保存操作 | 按钮变灰 → 显示结果 | <100ms 内开始反馈 |
| 置顶/取消置顶 | Toast/卡片位移 | 瞬时 |
| 重复操作（幂等） | Toast 提示原因 | 瞬时 |
| 校验失败 | 输入框变红 + 提示文字 | 输入停止 300ms 后 |

### 3.4 边界条件

#### 3.4.1 空态与边界场景

| 场景 | 行为 |
|---|---|
| 便签列表为空 | 空状态："还没有便签，点击右下角 + 创建一个吧" |
| 已完成区为空 | 标题"已完成 (0)"，无展开箭头 |
| 标签列表为空 | "暂无标签，点击右上角 + 创建" |
| 搜索无结果 | "没有匹配的便签，试试修改筛选条件" |
| 标签全部被删除 | 置顶标签自动清空 |
| 重复添加标签 | Toast 提示"该便签已包含此标签"（R6 幂等拒绝） |
| 拖拽排序精度耗尽 | 相邻 position 间距 < 1e-10 时自动批量重整（间隔 1.0 重新分配所有 position） |
| 搜索时 | 始终同时返回未完成和已完成便签（不按完成状态过滤） |
| 导出时空数据库 | 导出空数组 `[]` 或空文本 |

#### 3.4.2 状态流转（R24）

| 场景 | 前置条件 | 后置条件 | 副作用 | 失败原因 |
|---|---|---|---|---|
| 标记完成 | is_completed=0 | is_completed=1, completed_at=now, position=0 | 卡片透明度 1→0.4 + 向已完成区下沉滑动 0.3s，动画结束后刷新列表 | is_completed 已为 1 → 不显示[完成]按钮（UI 层拦截） |
| 取消完成 | is_completed=1 | is_completed=0, completed_at=NULL | 卡片透明度 0.4→1 + 从未完成区顶部插入 0.25s | is_completed 已为 0 → 不显示[取消完成]按钮（UI 层拦截） |
| 手动置顶 | is_pinned=0 | is_pinned=1, pinned_at=now | 卡片瞬移到列表顶部（无动画） | is_pinned 已为 1 → Toast "该便签已置顶" |
| 取消手动置顶 | is_pinned=1 | is_pinned=0, pinned_at=NULL | 卡片移回原位 | is_pinned 已为 0 → 长按菜单不显示[取消置顶] |
| 删除便签 | — | 物理删除 + 级联删除 NoteTag/Reminder/FTS5 索引 | 卡片右滑淡出 0.2s，顶栏右侧显示[撤销]按钮 + Toast(2s) "应用未关闭的12小时内，可以撤销最近1条删除" | — |
| 撤销删除 | 撤销缓存中有数据且未超时 | 新便签恢复原数据，撤销缓存清空 | 新卡片恢复到列表原位置 + Toast(2s) "便签已恢复" | 缓存为空/超时 → 撤销按钮不可见 |
| 删除标签 | — | 级联删除 NoteTag；若在置顶列表中自动移除 | 标签从列表移除 | — |

> 其他明确不做的事项见 [§6 明确不做](#6-明确不做explicit-non-goals)。

---

## 4. 数据模型

### 4.1 Note 便签

| 字段 | 类型 | 默认值 | NULL 含义 | 约束 |
|---|---|---|---|---|
| id | INTEGER PK | 自增 | — | — |
| title | TEXT NOT NULL | '' | — | 0–50 字符 |
| content | TEXT NOT NULL | — | — | 1–5000 字符，Markdown |
| created_at | TEXT NOT NULL | — | — | ISO8601 |
| updated_at | TEXT NOT NULL | — | — | ISO8601 |
| completed_at | TEXT | NULL | NULL=未完成 | ISO8601 |
| is_completed | INTEGER | 0 | — | 0=未完成 1=已完成 |
| position | REAL | 0 | — | 手动拖拽排序；0=未排序，>0 值越大越靠前 |
| is_pinned | INTEGER | 0 | — | 0=正常 1=手动置顶（长按触发） |
| pinned_at | TEXT | NULL | NULL=未置顶 | ISO8601 |

### 4.2 Tag 标签

| 字段 | 类型 | 默认值 | NULL 含义 | 约束 |
|---|---|---|---|---|
| id | INTEGER PK | 自增 | — | — |
| name | TEXT UNIQUE | — | — | 1–10 字符 |

种子标签（可改可删）：`紧急重要`、`紧急`、`重要不紧急`、`P1`、`P2`、`P3`

### 4.3 NoteTag 关联

| 字段 | 类型 | 默认值 | NULL 含义 | 约束 |
|---|---|---|---|---|
| note_id | INTEGER FK → Note | — | — | 联合主键 |
| tag_id | INTEGER FK → Tag | — | — | 联合主键 |

主键 (note_id, tag_id)，CASCADE 删除。

### 4.4 Reminder 提醒

| 字段 | 类型 | 默认值 | NULL 含义 | 约束 |
|---|---|---|---|---|
| id | INTEGER PK | 自增 | — | — |
| note_id | INTEGER FK → Note | — | — | — |
| remind_at | TEXT NOT NULL | — | — | ISO8601 |
| is_triggered | INTEGER | 0 | — | 0=未触发 1=已触发 |

最多 3 条/便签。CASCADE 删除。

### 4.5 UserSettings

| 字段 | 类型 | 默认值 | NULL 含义 | 约束 |
|---|---|---|---|---|
| key | TEXT PK | — | — | — |
| value | TEXT | — | — | JSON 格式 |

常用键：`pinned_tags`、`sort_preference`、`dark_mode`、`webdav_url`、`webdav_user`、`webdav_pass`

---

## 5. 功能规格（含输入/输出）

### 5.1 便签 CRUD

#### 新增

```
输入：title(可选, 默认''), content(必填), tag_names(可选, list[str] — 用户点击标签芯片多选)
校验：content 非空且 ≤5000；纯空白（空格/换行/制表符）视为空，拒绝提交；title 若提供则 ≤50；tag_names 中不存在的 → Toast "标签「XXX」不存在，已自动跳过"
输出：(True, Note 对象) | (False, "错误信息字符串")
副作用：写入 Note 表 + FTS5 索引 + NoteTag 关联；写入日志（INFO 级别）
```

#### 编辑

```
输入：note_id(内部), title(可选), content(可选), tag_names(可选, list[str]) — 用户点击编辑按钮弹出预填对话框（预填当前标题/内容/标签芯片，标签通过点击已有标签芯片多选）
校验：
  前端实时：title 字符计数(≤50)，content 字符计数(≤5000)，标签芯片数 ≤ 3（超出时 [确认] 按钮置灰 + Toast "每个便签最多 3 个标签"）
  后端提交：content 若提供则非空且 1–5000；title 若提供则 ≤50；tag_names 中不存在的标签 → Toast "标签「XXX」不存在，已自动跳过"
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + FTS5 索引同步更新(fts_update)；标签变更时同步更新 NoteTag 关联（仅增/删关联，Tag 的创建、删除、改名只能在标签管理页进行）；写入日志（INFO 级别）
```

#### 删除

```
输入：note_id(内部) — 用户点击删除按钮 → 确认框 → [确认删除]
校验：前端弹出确认框「确认删除此便签吗？」（R3 安全确认）；后端无额外校验
输出：(True, None) | (False, "错误信息字符串")
副作用：
  - 内存暂存当前便签数据（title/content/tag_names），覆盖上次暂存
  - 物理删除 Note + 级联 NoteTag、Reminder、FTS5
  - 顶栏右侧显示[撤销]按钮（金色 undo 图标）
  - Toast(2s) "应用未关闭的12小时内，可以撤销最近1条删除"
  - 应用关闭或 12 小时后暂存清空，撤销按钮消失
  - 写入日志（INFO 级别）
```

#### 撤销删除

```
输入：无（用户点击顶栏右侧 [撤销] 按钮）
校验：内存中有暂存数据且未超时（12h）且应用未被关闭；无暂存时按钮不可见
输出：(True, 新建的 Note 对象) | (False, "错误信息字符串")
副作用：
  - 创建新便签（title=原标题，content=原内容，tags=原标签名列表）
  - 清除内存暂存数据
  - 撤销按钮隐藏
  - Toast(2s) "便签已恢复"
  - 写入日志（INFO 级别）
```

#### 撤销超时

```
输入：无（自动触发）
校验：暂存时间 > 12h 或 应用关闭
输出：(True, None)
副作用：内存暂存数据清空，撤销按钮消失
```

#### 标记完成

```
输入：note_id(内部) — 用户点击 [完成] 按钮
校验：便签未完成（is_completed=0）；已完成便签不显示 [完成] 按钮（R6 幂等拒绝）
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + 动画（0.3s 透明度渐变 + 位移）后刷新列表；写入日志（INFO 级别）
```

#### 取消完成

```
输入：note_id(内部) — 用户点击 [取消完成] 按钮
校验：便签已完成（is_completed=1）
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + 动画（0.25s 透明度恢复 + 顶部插入）后刷新列表；写入日志（INFO 级别）
```

#### 手动置顶便签

```
输入：note_id(内部) — 用户长按便签卡片 → 弹出菜单 → [置顶]
校验：is_pinned=0；已置顶则返回失败 Toast"该便签已置顶"（R6 幂等拒绝）
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + 卡片瞬移到置顶区；写入日志（INFO 级别）
```

#### 取消手动置顶

```
输入：note_id(内部) — 长按已置顶便签 → [取消置顶]
校验：is_pinned=1
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + 卡片移回原位；写入日志（INFO 级别）
```

#### 拖拽排序

```
输入：note_id(内部) + 目标位置 — 用户长按并拖拽
校验：无额外校验
输出：(True, 更新后 Note) | (False, "错误信息字符串")
副作用：更新 Note 表 + 其他卡片实时让位动画（0 延迟）
内部计算：new_position = (上.position + 下.position) / 2（插中间）或 = 最大 position + 1（插顶端）
规则：
  - position > 0 表示手动排序，值越大越靠前
  - 标记完成时 position 归零
  - 相邻 position 间距 < 1e-10 时触发批量重整（间隔 1.0 重新分配所有 position）
```

### 5.4 搜索筛选

```
输入：
  keyword(可选, str)        — 搜索框输入
  tag_names(可选, list[str]) — 点击标签芯片多选
  year/month(可选)           — 下拉选择器
  week(可选, 1–5)            — 下拉选择
  time_type(可选)            — 芯片切换「完成时间 | 创建时间」
校验：无必填字段；至少一个条件非空时 [搜索] 按钮可用
输出：(True, list[Note]) | (False, "错误信息字符串")；空时显示"没有匹配的便签，试试修改筛选条件"
副作用：无

搜索始终同时匹配已完成和未完成便签（不限定 is_completed）。

搜索逻辑（伪代码 — 条件动态拼接，全部 AND 组合）：

```sql
-- tag_names 非空时追加 JOIN
{tag_join}  -- INNER JOIN NoteTag nt ON n.id = nt.note_id
            -- INNER JOIN Tag t ON nt.tag_id = t.id

SELECT DISTINCT n.* FROM Note n
{tag_join}
WHERE 1=1
  -- keyword 非空：ASCII → FTS5 MATCH；非 ASCII → LIKE 兜底
  {keyword_clause}
    -- ASCII:  AND n.id IN (SELECT rowid FROM notes_fts WHERE notes_fts MATCH '{keyword}')
    -- 中文:   AND (n.title LIKE '%{keyword}%' OR n.content LIKE '%{keyword}%')
  -- tag_names 非空时追加
  {tag_clause}    -- AND t.name IN ('{tag1}','{tag2}',...)
  -- year/month 非空时追加（time_type 决定用 created_at 或 completed_at）
  {time_clause}   -- AND CAST(substr({time_field}, 1, 4) AS INTEGER) = {year}
                   -- AND CAST(substr({time_field}, 6, 2) AS INTEGER) = {month}
  -- week 非空时追加
  {week_clause}   -- AND CEIL(CAST(substr({time_field}, 9, 2) AS REAL) / 7.0) = {week}
ORDER BY n.updated_at DESC
```
```

### 5.5 数据导出 (P1)

```
输入：format('json'|'text') — 设置页点击 [导出] → 选择 JSON 或 TEXT 芯片
校验：format 必须为 'json' 或 'text'
输出：(True, 文件路径) | (False, "错误信息字符串")
  - JSON: 文件 notes_export.json，内容 [{id,title,content,...}]
  - TEXT: 文件 notes_export.txt，每便签一段"【标题】\n内容\n标签:...\n---"
副作用：写入文件到本地存储；数据库为空时导出空数组 `[]` 或空文本；写入日志（INFO 级别）
```

### 5.6 夜间模式 (P1)

```
输入：theme('Light'|'Dark') — 设置页开关切换
校验：无
输出：(True, 当前 theme_style) | (False, "错误信息字符串")
副作用：全局主题即时切换 + 持久化到 UserSettings(key='dark_mode')
```

### 5.7 本地提醒

#### 提醒页面

```
入口：便签卡片点击提醒按钮 → 跳转 ReminderScreen
输入：note_id（内部，由卡片传递）
页面展示：
  - 顶部标题栏「提醒」+ [返回] 按钮
  - 中部已设提醒列表（每条显示日期+时间 + [✕ 删除] 按钮）
  - 底部 [+ 新建提醒] 按钮
空态：无提醒时显示「暂无提醒，点击下方按钮创建」
```

#### 创建提醒

```
输入：note_id(内部), remind_at(ISO8601) — 点击 [+ 新建提醒] → 弹出日期选择器(MDDatePicker) → 弹出时间选择器(MDTimePicker)，默认值=点击时的当前时间
校验：
  前端实时：该便签现有提醒 < 3（达到上限时按钮置灰 + Toast "最多 3 个提醒"）
  后端提交：note_id 存在；remind_at 无时间范围限制（允许过去/未来任意时间；若为过去时间，闹钟/Timer 立即触发通知）
输出：(True, Reminder 对象) | (False, "错误信息字符串")
副作用：写入 Reminder 表 + 注册系统闹钟（Android AlarmManager / Desktop threading.Timer）；写入日志（INFO 级别）
```

#### 删除提醒

```
输入：reminder_id(内部) — 提醒列表点击 ✕ → 确认框「删除此提醒？」
校验：前端确认框（R3 安全确认）
输出：(True, None) | (False, "错误信息字符串")
副作用：删除 Reminder 记录 + 取消闹钟；写入日志（INFO 级别）
```

#### 提醒触发

```
输入：自动触发（系统闹钟/定时器）
校验：is_triggered=0
输出：(True, None)
副作用：is_triggered=1；发送系统通知；写入日志（INFO 级别）
```

### 5.8 WebDAV 同步 (P2)

```
输入：
  - 手动同步：用户点击 [同步] 按钮
  - 自动同步：应用启动（无用户输入）
校验：WebDAV 凭据已配置（url/user/pass 均非空）；未配置时按钮置灰
输出：(True, "同步成功") | (False, "错误信息字符串")
副作用：
  - 上传：本地 db 文件 → 远程
  - 下载：远程 db 文件 → 本地（覆盖）
  - 凭据持久化到 UserSettings
  - 写入日志（INFO 级别）
```

---

## 6. 明确不做（Explicit Non-Goals）

| 不做的事项 | 原因 |
|---|---|
| 多设备实时协作 | 单用户本地应用 |
| 数据加密存储 | 不处理敏感数据 |
| 非 WebDAV 云同步 | 仅支持 WebDAV |
| 离线冲突解决 | 单用户，最后写入胜出 |
| 富文本编辑 | 仅 Markdown 源码编辑 |
| 标签进回收站 | 标签直接硬删除（有确认框） |
| 批量操作 | 不支持批量删除/批量完成 |

---

## 7. 索引策略（已实现）

```sql
CREATE VIRTUAL TABLE notes_fts USING fts5(title, content);
CREATE INDEX idx_note_created_at   ON Note(created_at);
CREATE INDEX idx_note_updated_at   ON Note(updated_at);
CREATE INDEX idx_note_completed_at ON Note(completed_at);
CREATE INDEX idx_note_is_completed ON Note(is_completed);
CREATE INDEX idx_reminder_remind_at ON Reminder(remind_at);
```

---

## 8. UI 架构

| 屏幕/组件 | KivyMD 组件 | 职责 |
|---|---|---|
| `MainScreen` | `MDTopAppBar` + `MDFloatingActionButton` + `ScrollView` + 撤销按钮 | 主界面 + 排序切换 + 撤销提示 |
| `NoteCard` | `MDCard` + `MDLabel` + `MDChip`×3 + `MDIconButton`×6 | 便签卡片：长按置顶 / 拖拽 / 标题 / 内容 / 标签芯片(MDChip)×最多3个 / 提醒⏰ / 编辑 / 完成 / 删除 |
| `AddEditDialog` | `MDDialog` + `MDTextField`×2 + `MDChip` | 新增/编辑弹窗 |
| `SearchFilter` | `MDTextField` + `MDDropDownItem`×3 + `MDChip` | 搜索面板 |
| `TagManager` | `MDList` + `MDTextField` + `MDCheckbox` | 标签管理页：新建 / 改名 / 批量删除 / 置顶选择 |
| `ReminderScreen` | `MDTopAppBar` + `MDList` + `MDIconButton` | 提醒管理页：已设提醒列表 / [+新建提醒] 按钮（触发 MDDatePicker + MDTimePicker Dialog）/ [✕删除] |
| `SettingsScreen` | `MDSwitch` + `MDTextField` | 设置页 |

导航：`MDScreenManager` → 主屏 / 设置 / 提醒；从便签卡片提醒按钮进入 ReminderScreen；撤销按钮在顶栏右侧显示。

---

## 9. 测试策略

```
app_tool/tests/
├── conftest.py          ← :memory: SQLite fixtures
├── test_models.py       ← 数据类字段
├── test_database.py     ← DDL / FTS5 / 种子 / CRUD
├── test_tag_service.py  ← 标签 CRUD / 置顶
├── test_note_service.py ← 便签 CRUD / 软删除 / 排序 / 拖拽 / 标签关联 / 标签不存在 Toast 反馈
├── test_search_service.py ← 组合搜索
└── test_reminder_service.py ← 提醒 CRUD
```

- `:memory:` SQLite 隔离测试（单元测试）；集成测试使用 `tempfile.NamedTemporaryFile`
- TDD：红灯 → 绿灯 → 重构
- P0 覆盖：models / database / tag_service / note_service / search_service / reminder_service(Desktop)
- **R25**：每个测试函数在 docstring 中标注对应 spec.md 条目（如 `§5.1 新增`）或 rules.md 编号（如 `R8`）

---

## 10. 开发阶段

| 阶段 | 内容 |
|---|---|
| **P0** | 便签 CRUD（含撤销删除）+ 手动/标签置顶 + 拖拽排序 + 标签系统 + 搜索 + 提醒(Desktop) + UI |
| **P1** | JSON/TEXT 导出 + 夜间模式 + 提醒(Android AlarmManager) |
| **P2** | WebDAV 同步 |

### P0 Definition of Done

- [ ] 应用启动 → 主界面
- [ ] FAB 新增便签（title 可选 + content 必填 + 标签可选）→ 未完成列表
- [ ] 允许无标题、无标签，仅内容即可创建
- [ ] 未完成排序：手动置顶 → 标签置顶 → 拖拽 → 排序偏好
- [ ] 已完成排序：手动置顶 → 拖拽 → completed_at；默认折叠
- [ ] 长按便签 → 手动置顶/取消置顶；重复置顶提示失败
- [ ] 标签管理页：点击改名 / 📌置顶（超3自动淘汰）/ +新建 / 批量删除
- [ ] 编辑 → updated_at 刷新
- [ ] 删除 → 确认框 → 物理删除；顶栏右侧显示[撤销]按钮 + Toast(2s) "应用未关闭的12小时内，可以撤销最近1条删除"
- [ ] 撤销 → 创建新便签（原标题 + 原内容 + 原标签）+ 撤销按钮隐藏 + Toast(2s) "便签已恢复"
- [ ] 标签 → 增删改 + 删除确认框 + 置顶
- [ ] 搜索：关键词 + 标签 + 年/月/周 + 时间类型组合 AND
- [ ] 提醒：便签卡片提醒按钮 → ReminderScreen → 创建/删除提醒 → 系统闹钟触发
- [ ] 校验：content 必填/长度、标签重名、提醒上限、不存在的标签友好提示
- [ ] pytest 全绿

### P1 Definition of Done

- [ ] JSON 导出 — 生成 `notes_export.json`，包含所有便签完整数据（id/title/content/tags/时间戳等）
- [ ] TEXT 导出 — 生成 `notes_export.txt`，每便签按 `【标题】\n内容\n标签:...\n---` 格式分段
- [ ] 空数据库导出空数组 `[]`（JSON）或空文本（TEXT），不报错
- [ ] 夜间模式 — 设置页开关切换 Light/Dark，全局主题即时切换
- [ ] 夜间模式偏好持久化到 UserSettings (`dark_mode`)，重启自动恢复（R9 持久化）
- [ ] Android AlarmManager 提醒 — 取代 Desktop Timer，应用关闭后系统闹钟仍触发通知
- [ ] 提醒触发后 `is_triggered` 标记为 1 + 发送系统通知（R4 即时反馈）
- [ ] pytest 全绿（含导出、夜间模式、Android 提醒相关测试，R18/R25/R27）

### P2 Definition of Done

- [ ] WebDAV 凭据配置 — 设置页填写服务器 URL + 用户名 + 密码，持久化到 UserSettings
- [ ] 未配置凭据时 [同步] 按钮置灰
- [ ] 手动同步 — 点击 [同步] 按钮，应用内直连 WebDAV 服务器，上传本地 db + 下载远程 db 覆盖本地，无需跳转第三方应用
- [ ] 启动自动同步 — 应用启动时在后台线程执行，不阻塞 UI，用户可立即使用
- [ ] 同步超时（15s）自动放弃，Toast 提示"同步超时，请稍后重试"（R21 不静默忽略）
- [ ] 同步进行中 [同步] 按钮显示加载态（R4 即时反馈）
- [ ] 同步失败不影响本地使用，仅 Toast 提示失败原因（R23 用户可读错误信息）
- [ ] 同步冲突策略：最后写入胜出
- [ ] 同步操作写入日志（INFO 级别，R28）
- [ ] pytest 全绿（含 WebDAV 同步相关测试，R18/R25/R27）
