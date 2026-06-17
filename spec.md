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
| 删除便签 | 卡片向右滑出 + 淡出 | 0.2s，滑出后 UndoBar 从底部升起 |
| 撤销删除 | 新卡片从 UndoBar 位置弹出到列表顶部 | 0.3s |
| 拖拽排序 | 拖动时卡片抬起阴影 + 其他卡片实时让位 | 实时（0 延迟） |
| 置顶/取消置顶 | 卡片瞬移到目标区（无动画，避免混淆） | — |
| 展开已完成区 | 已完成区从折叠态向下展开 | 0.25s |
| 搜索筛选 | 列表交叉淡入淡出 | 0.2s |

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

| 字段 | 约束 | 前端实时反馈（输入过程中） | 后端提交校验（保存时） |
|---|---|---|---|
| title | 0–50 字符 | 字符计数器实时显示；超 50 输入框变红、禁止继续输入 | 可空（默认 ''） |
| content | 1–5000 字符 | 字符计数器实时显示；超 5000 输入框变红、禁止继续输入 | 不可为空；纯空白同空处理 |
| 标签名 | 1–10 字符 | 字符计数器；空/纯空白时边框变红、[确认] 按钮置灰 | 不可重名；重名弹窗提示并聚焦 |
| remind_at | ≥ 当前时间 | 日期选择器中今天之前的日期置灰不可选 | 保存时二次校验 |
| pinned_tags | 最多 3 个 | 第 4 个置顶点击时 Toast 提示"最多 3 个置顶标签" | 自动淘汰最早置顶 |
| 每条便签提醒 | 最多 3 个 | 添加第 4 个时按钮置灰 + Toast "最多 3 个提醒" | 提交时拒绝 |

### 3.3 反馈时序（R4）

| 操作 | 反馈 | 要求 |
|---|---|---|
| 任何保存操作 | 按钮变灰 → 显示结果 | <100ms 内开始反馈 |
| 置顶/取消置顶 | Toast/卡片位移 | 瞬时 |
| 重复操作（幂等） | Toast 提示原因 | 瞬时 |
| 校验失败 | 输入框变红 + 提示文字 | 输入停止 300ms 后 |

### 3.4 边界条件

| 场景 | 行为 |
|---|---|
| 便签列表为空 | 空状态："还没有便签，点击右下角 + 创建一个吧" |
| 已完成区为空 | 标题"已完成 (0)"，无展开箭头 |
| 标签列表为空 | "暂无标签，点击右上角 + 创建" |
| 搜索无结果 | "没有匹配的便签，试试修改筛选条件" |
| 标签全部被删除 | 置顶标签自动清空 |
| 便签手动置顶 | 不限数量；已因标签或手动置顶的便签再次置顶 → Toast "该便签已置顶" |
| 取消手动置顶 | 长按 → [取消置顶] → 卡片移回原位 |
| 重复标记完成 | 已完成便签不显示 [完成] 按钮 |
| 重复添加标签 | Toast 提示"该便签已包含此标签"（R6 幂等拒绝） |
| 拖拽排序精度耗尽 | 相邻 position 间距 < 1e-10 时自动批量重整（间隔 1.0 重新分配所有 position） |
| 删除便签 | 确认框 → 物理删除 + 级联 → UndoBar 弹出 |
| 撤销删除 | 点击 [撤销] → 新便签；仅保留最后一次 |
| 撤销生命周期 | 仅 Python 进程内存；应用关闭即丢失；**首次删除时 Toast "撤销仅在应用运行期间有效"** |
| 永久删除便签 | 级联删除 NoteTag、Reminder、FTS5 索引 |
| 删除标签 | 确认框 → 级联删除 NoteTag；若在置顶列表中自动移除 |
| 导出时空数据库 | 导出空数组 `[]` 或空文本 |

---

## 4. 数据模型

### 4.1 Note 便签

| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER PK | 自增 |
| title | TEXT NOT NULL DEFAULT '' | 0–50 字符，可为空 |
| content | TEXT NOT NULL | 1–5000 字符，Markdown |
| created_at | TEXT NOT NULL | ISO8601 |
| updated_at | TEXT NOT NULL | ISO8601 |
| completed_at | TEXT NULLABLE | NULL=未完成 |
| is_completed | INTEGER DEFAULT 0 | 0=未完成 1=已完成 |
| position | REAL DEFAULT 0 | 手动拖拽排序位置；0=未手动排序 |
| is_pinned | INTEGER DEFAULT 0 | 0=正常 1=手动置顶（长按触发） |
| pinned_at | TEXT NULLABLE | 手动置顶时间，NULL=未置顶 |

### 4.2 Tag 标签

| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER PK | 自增 |
| name | TEXT UNIQUE | 1–10 字符 |

种子标签（可改可删）：`紧急重要`、`紧急`、`重要不紧急`、`P1`、`P2`、`P3`

### 4.3 NoteTag 关联

| 字段 | 类型 |
|---|---|
| note_id | INTEGER FK → Note |
| tag_id | INTEGER FK → Tag |

主键 (note_id, tag_id)，CASCADE 删除。

### 4.4 Reminder 提醒

| 字段 | 类型 |
|---|---|
| id | INTEGER PK |
| note_id | INTEGER FK → Note |
| remind_at | TEXT NOT NULL, ISO8601 |
| is_triggered | INTEGER DEFAULT 0 |

最多 3 条/便签。CASCADE 删除。

### 4.5 UserSettings

| 字段 | 类型 |
|---|---|
| key | TEXT PK |
| value | TEXT (JSON) |

常用键：`pinned_tags`、`sort_preference`、`dark_mode`、`webdav_url`、`webdav_user`、`webdav_pass`

---

## 5. 功能规格（含输入/输出）

### 5.1 便签 CRUD

#### 新增

```
输入：title(可选, 默认''), content(必填), tag_names(可选, list[str] — 用户点击标签芯片多选)
校验：content 非空且 ≤5000；title 若提供则 ≤50；tag_names 中不存在的静默忽略
输出：Note 对象（含 id、时间戳、position=0）
副作用：写入 Note 表 + FTS5 索引 + NoteTag 关联
```

#### 编辑

```
输入：note_id(内部), title(可选), content(可选) — 用户点击编辑按钮弹出预填对话框
校验：
  前端实时：title 字符计数(≤50)，content 字符计数(≤5000)
  后端提交：content 若提供则非空且 1–5000；title 若提供则 ≤50
输出：更新后 Note（含新 updated_at）
副作用：更新 Note 表 + FTS5 索引同步更新(fts_update)
```

#### 删除

```
输入：note_id(内部) — 用户点击删除按钮 → 确认框 → [确认删除]
校验：前端弹出确认框「是否删除？」（R3 安全确认）；后端无额外校验
输出：None（物理删除）
副作用：
  - 内存暂存当前便签数据（title/content/tag_names），覆盖上次暂存
  - 物理删除 Note + 级联 NoteTag、Reminder、FTS5
  - UI 底部弹出 UndoBar：「为防止误删，应用关闭前 12 小时内可恢复最后一条  [撤销]」
  - 应用关闭或 12 小时后暂存清空，UndoBar 自动消失
```

#### 撤销删除

```
输入：无（用户点击 UndoBar [撤销] 按钮）
校验：内存中有暂存数据且未超时（12h）且应用未被关闭；无暂存时按钮不可见
输出：新建的 Note 对象
副作用：
  - 创建新便签（title=NULL，content=原内容，tags=NULL）
  - 清除内存暂存数据
  - UndoBar 消失
```

#### 撤销超时

```
输入：无（自动触发）
校验：暂存时间 > 12h 或 应用关闭
输出：None
副作用：内存暂存数据清空，UndoBar 消失
```

#### 标记完成

```
输入：note_id(内部) — 用户点击 [完成] 按钮
校验：便签未完成（is_completed=0）；已完成便签不显示 [完成] 按钮（R6 幂等拒绝）
输出：更新后 Note（is_completed=1, completed_at=now, position=0）
副作用：更新 Note 表 + 动画（0.3s 透明度渐变 + 位移）后刷新列表
```

#### 取消完成

```
输入：note_id(内部) — 用户点击 [取消完成] 按钮
校验：便签已完成（is_completed=1）
输出：更新后 Note（is_completed=0, completed_at=NULL）
副作用：更新 Note 表 + 动画（0.25s 透明度恢复 + 顶部插入）后刷新列表
```

#### 手动置顶便签

```
输入：note_id(内部) — 用户长按便签卡片 → 弹出菜单 → [置顶]
校验：is_pinned=0；已置顶则返回失败 Toast"该便签已置顶"（R6 幂等拒绝）
输出：更新后 Note（is_pinned=1, pinned_at=now）
副作用：更新 Note 表 + 卡片瞬移到置顶区
```

#### 取消手动置顶

```
输入：note_id(内部) — 长按已置顶便签 → [取消置顶]
校验：is_pinned=1
输出：更新后 Note（is_pinned=0, pinned_at=NULL）
副作用：更新 Note 表 + 卡片移回原位
```

#### 拖拽排序

```
输入：note_id(内部) + 目标位置 — 用户长按并拖拽
校验：无额外校验
输出：更新后 Note（含新 position）
副作用：更新 Note 表 + 其他卡片实时让位动画（0 延迟）
内部计算：new_position = (上.position + 下.position) / 2（插中间）或 = 最大 position + 1（插顶端）
规则：
  - position > 0 表示手动排序，值越大越靠前
  - 标记完成时 position 归零
  - 相邻 position 间距 < 1e-10 时触发批量重整（间隔 1.0 重新分配所有 position）
```

### 5.2 排序查询

#### 用户排序偏好

```
UI：主屏顶栏切换按钮「按更新时间 | 按创建时间」
持久化：UserSettings(key='sort_preference', value='updated_at'|'created_at')
默认值：'updated_at'
```

#### 获取未完成便签

```
输入：无（隐式读取 sort_preference）
输出：list[Note], is_completed=0
排序规则：
  1. **手动置顶便签**（is_pinned=1）→ 按 pinned_at DESC 最前
  2. **标签置顶便签**（含 pinned_tags 中的标签）→ 按 updated_at DESC
  3. 以上两组内：position > 0 的按 position DESC（手动拖拽）
  4. 剩余按 sort_preference 对应时间字段降序

等价 SQL 伪码：
```sql
SELECT DISTINCT n.* FROM Note n
LEFT JOIN NoteTag nt ON n.id = nt.note_id
LEFT JOIN Tag t ON nt.tag_id = t.id
WHERE n.is_completed = 0
ORDER BY
  CASE WHEN n.is_pinned = 1 THEN 0 ELSE 1 END,
  CASE WHEN t.name IN ({pinned_tags}) THEN 0 ELSE 1 END,
  CASE WHEN n.position > 0 THEN -n.position END DESC,
  CASE WHEN '{sort_pref}' = 'updated_at' THEN n.updated_at ELSE n.created_at END DESC
```
> 说明：
> - `DISTINCT` 防止多标签便签因 LEFT JOIN 产生重复行。
> - 无标签便签 `t.name IS NULL` → `IN (...)` 结果为 NULL → 落入 ELSE 分支，正确不获得标签置顶优先级。
```


#### 获取已完成便签

```
输入：无
输出：list[Note], is_completed=1
排序规则：
  1. **手动置顶便签**（is_pinned=1）→ 按 pinned_at DESC 最前
  2. 置顶区内：position > 0 的按 position DESC（手动拖拽）
  3. 剩余按 completed_at DESC
  完成区默认折叠

等价 SQL 伪码：
```sql
SELECT n.* FROM Note n
WHERE n.is_completed = 1
ORDER BY
  CASE WHEN n.is_pinned = 1 THEN 0 ELSE 1 END,
  CASE WHEN n.position > 0 THEN -n.position END DESC,
  n.completed_at DESC
```

### 5.3 标签 CRUD

#### 标签管理页

```
入口：主屏标签按钮
右上角：[+新建标签] [批量删除]
标签列表每行：
  [标签名] ← 点击弹出改名对话框
  [📌置顶]  ← 点击切换置顶状态

置顶规则：
  - 每个标签独立置顶按钮
  - 最多 3 个置顶标签；超出时自动淘汰最早置顶的标签
  - 标签按置顶时间 DESC 排列
批量删除：
  - 点击右上角 [批量删除] 进入多选模式
  - 勾选标签 → 确认删除 → 级联移除所有便签的该标签
```

#### 创建标签

```
输入：name(str) — 用户点击 [+新建标签] → 输入框 → 确认
校验：
  前端实时：字符计数(1–10)，空/纯空白时边框变红、[确认] 按钮置灰
  后端提交：不可重名（重名弹窗 "标签「XXX」已存在" 并聚焦输入框）
输出：Tag 对象（含 id）
副作用：写入 Tag 表
```

#### 更新标签

```
输入：tag_name(内部), new_name(str) — 用户点击标签名 → 改名对话框 → 确认
校验：
  前端实时：字符计数(1–10)
  后端提交：不可重名（自身原名除外）
输出：更新后 Tag
副作用：更新 Tag 表 + 所有引用该标签的便签展示名称同步更新
```

#### 单删标签

```
输入：tag_name(内部) — 用户点击标签旁的删除按钮 → 确认框 → [确认删除]
校验：前端弹出确认框「确认删除标签"{name}"？将移除所有便签的此标签。」（R3 安全确认）
输出：None
副作用：级联删除 NoteTag 关联 + 若在置顶列表中自动移除 + 持久化更新 pinned_tags
```

#### 置顶标签

```
输入：tag_name(内部) — 用户点击标签旁的 [📌] 按钮
校验：若已置顶 → 取消置顶（切换行为）；最多 3 个置顶标签，超出时自动淘汰最早置顶的标签
输出：更新后 pinned_tags 列表
副作用：持久化到 UserSettings(key='pinned_tags') + 触发排序规则刷新
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
输出：list[Note] 匹配结果（空时显示"没有匹配的便签，试试修改筛选条件"）
副作用：无

搜索逻辑：
  1. keyword → **ASCII 字符优先走 FTS5 MATCH**，中文等非 ASCII 走 LIKE '%keyword%' 兜底
  2. tag_names → 解析为 tag_id → INNER JOIN NoteTag
  3. 时间     → CAST(substr(time_field,1,4) AS INTEGER) 等
  4. 周       → CEIL(substr(time_field,9,2) / 7.0) 计算月内第N周
  5. 所有条件 AND 组合
```

### 5.5 数据导出 (P1)

```
输入：format('json'|'text') — 设置页点击 [导出] → 选择 JSON 或 TEXT 芯片
校验：format 必须为 'json' 或 'text'
输出：
  - JSON: 文件 notes_export.json，内容 [{id,title,content,...}]
  - TEXT: 文件 notes_export.txt，每便签一段"【标题】\n内容\n标签:...\n---"
副作用：写入文件到本地存储；数据库为空时导出空数组 `[]` 或空文本
```

### 5.6 夜间模式 (P1)

```
输入：theme('Light'|'Dark') — 设置页开关切换
校验：无
输出：当前 theme_style
副作用：全局主题即时切换 + 持久化到 UserSettings(key='dark_mode')
```

### 5.7 本地提醒 (P1)

#### 创建提醒

```
输入：note_id(内部), remind_at(ISO8601) — 便签卡片提醒按钮 → 日期时间选择器点击选择
校验：note_id 存在；该便签现有提醒 < 3（达到上限时按钮置灰+Toast"最多3个提醒"）；remind_at ≥ 当前时间
输出：Reminder 对象
副作用：写入 Reminder 表 + 注册 AlarmManager（Android）/ threading.Timer（Desktop）
```

#### 删除提醒

```
输入：reminder_id(内部) — 便签详情点击 ✕ 按钮
校验：无
输出：None
副作用：删除 Reminder 记录 + 取消闹钟
```

#### 提醒触发

```
输入：自动触发（系统闹钟）
校验：is_triggered=0
输出：系统通知
副作用：is_triggered=1
```

### 5.8 WebDAV 同步 (P2)

```
输入：
  - 手动同步：用户点击 [同步] 按钮
  - 自动同步：应用启动（无用户输入）
校验：WebDAV 凭据已配置（url/user/pass 均非空）；未配置时按钮置灰
输出：同步结果 Toast（成功 / 失败原因）
副作用：
  - 上传：本地 db 文件 → 远程
  - 下载：远程 db 文件 → 本地（覆盖）
  - 凭据持久化到 UserSettings
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
| `MainScreen` | `MDTopAppBar` + `MDFloatingActionButton` + `RecycleView` + `UndoBar` | 主界面 + 排序切换 + 撤销提示条 |
| `NoteCard` | `MDCard` + `MDLabel` + `MDIconButton`×5 | 便签卡片：长按置顶 / 拖拽 / 标题 / 内容 / 标签 / 编辑 / 完成 / 删除 |
| `AddEditDialog` | `MDDialog` + `MDTextField`×2 + `MDChip` | 新增/编辑弹窗 |
| `SearchFilter` | `MDTextField` + `MDDropDownItem`×3 + `MDChip` | 搜索面板 |
| `TagManager` | `MDList` + `MDTextField` + `MDCheckbox` | 标签管理页：新建 / 改名 / 批量删除 / 置顶选择 |
| `SettingsScreen` | `MDSwitch` + `MDTextField` | 设置页 |

导航：`MDScreenManager` → 主屏 / 设置；UndoBar 在主屏底部弹出。

---

## 9. 测试策略

```
app_tool/tests/
├── conftest.py          ← :memory: SQLite fixtures
├── test_models.py       ← 数据类字段
├── test_database.py     ← DDL / FTS5 / 种子 / CRUD
├── test_tag_service.py  ← 标签 CRUD / 置顶
├── test_note_service.py ← 便签 CRUD / 软删除 / 排序 / 拖拽 / 标签关联
├── test_search_service.py ← 组合搜索
└── test_reminder_service.py ← 提醒 CRUD
```

- `:memory:` SQLite 隔离测试
- TDD：红灯 → 绿灯 → 重构
- P0 覆盖：models / database / tag_service / note_service / search_service / reminder_service(Desktop)

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
- [ ] 删除 → 确认框 → 物理删除；底部弹出撤销箭头（12h 或关闭消失）
- [ ] 撤销 → 创建新便签（随机标题 + 原内容 + 原标签）
- [ ] 标签 → 增删改 + 删除确认框 + 置顶
- [ ] 搜索：关键词 + 标签 + 年/月/周 + 时间类型组合 AND
- [ ] 校验：content 必填/长度、标签重名、提醒上限
- [ ] pytest 全绿
