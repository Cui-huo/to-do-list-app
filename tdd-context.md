# TDD 代码生成上下文

> 本片段提炼自 `spec.md` + `rules/core_rules.md`，用于配合 spec 段落生成 TDD 代码。
> 每次生成时，将本片段 + 目标 spec 章节一起传入 prompt。

---

## 技术栈

- **UI**: Kivy + KivyMD（卡片式 Material Design）
- **存储**: SQLite (sqlite3)，Python 内置零依赖
- **搜索**: FTS5 独立表（ASCII）+ LIKE 兜底（中文 CJK）
- **测试**: pytest，`:memory:` SQLite 隔离（单元测试），`tempfile.NamedTemporaryFile`（集成测试）
- **环境**: 项目内 `.python312/` 嵌入式 Python，禁止触碰系统全局

---

## 核心架构约束（直接影响代码结构）

### R26 — 统一返回结构
所有 Service 层公开方法必须返回 `(success: bool, result: Any)`：
- `success=True` → `result` 为有效数据
- `success=False` → `result` 为错误信息字符串
- 禁止返回 `None` 表示失败，禁止 raise 未捕获异常

```python
def add_tag(name: str) -> tuple[bool, int | str]:
    if not name or len(name) > 10:
        return False, "标签名 1-10 个字符"
    if self.tag_repo.exists(name):
        return False, f"标签「{name}」已存在"
    tag_id = self.tag_repo.create(name)
    return True, tag_id
```

### R14 — 校验分层
| 层 | 时机 | 职责 |
|---|---|---|
| 前端实时 | 输入过程中 | 字符计数、格式高亮、空白拦截 |
| 后端提交 | 保存时 | 唯一性检查、关联完整性、重名检测 |

**补充**: 后端校验必须在前端同步复现（后端是最终防线，前端是体验层）。

### R24 — 状态流转一致性
每个状态变更操作必须定义：
1. 前置条件（什么状态允许执行）
2. 后置条件（执行后状态变化）
3. 关联副作用（排序刷新、动画后重新渲染）
4. 失败原因（前置条件不满足时返回明确字符串）

### R15 — 每功能四段式
```
输入 → 校验 → 输出 → 副作用
```
四个部分缺一不可。

### R28 — 关键操作日志
以下操作必须 `logging.info()`：便签增删改/标记完成、标签增删改、提醒创建与触发、数据导入导出、数据库初始化/迁移。
格式: `[时间] [模块] 操作描述: 关键参数`

---

## 数据模型（字段级约束）

### Note
| 字段 | 类型 | 默认 | NULL含义 | 约束 |
|---|---|---|---|---|
| id | INTEGER PK | 自增 | — | — |
| title | TEXT NOT NULL | '' | — | 0–50 字符 |
| content | TEXT NOT NULL | — | — | 1–5000 字符，Markdown |
| created_at | TEXT NOT NULL | — | — | ISO8601 |
| updated_at | TEXT NOT NULL | — | — | ISO8601 |
| completed_at | TEXT | NULL | NULL=未完成 | ISO8601 |
| is_completed | INTEGER | 0 | — | 0=未完成 1=已完成 |
| position | REAL | 0 | — | 拖拽排序；0=未排序，>0 值越大越靠前 |
| is_pinned | INTEGER | 0 | — | 0=正常 1=手动置顶 |
| pinned_at | TEXT | NULL | NULL=未置顶 | ISO8601 |

### Tag
| 字段 | 类型 | 约束 |
|---|---|---|
| id | INTEGER PK | 自增 |
| name | TEXT UNIQUE | 1–10 字符 |

种子标签（可改可删）: `紧急重要`、`紧急`、`重要不紧急`、`P1`、`P2`、`P3`

### NoteTag
`(note_id, tag_id)` 联合主键，CASCADE 删除。

### Reminder
`note_id` FK → Note，`remind_at` TEXT ISO8601，`is_triggered` INTEGER 默认 0。
每条便签最多 3 个提醒。CASCADE 删除。

### UserSettings
`(key TEXT PK, value TEXT)` — JSON 格式存储偏好。

---

## 关键常量（config.py）

```python
DB_FILENAME = "notes.db"
SEED_TAGS = ["紧急重要", "紧急", "重要不紧急", "P1", "P2", "P3"]
MAX_REMINDERS_PER_NOTE = 3
MAX_PINNED_TAGS = 3
UNDO_TIMEOUT_SECONDS = 12 * 3600  # 12小时
MAX_TITLE_LENGTH = 50
MAX_CONTENT_LENGTH = 5000
MAX_TAG_NAME_LENGTH = 10
```

---

## 排序逻辑（R12 伪代码）

```python
# 未完成便签排序
ORDER BY
  CASE WHEN is_pinned=1 THEN 0 ELSE 1 END ASC,   -- 手动置顶最前
  CASE WHEN tag IN pinned_tags THEN 0 ELSE 1 END, -- 标签置顶次之
  CASE WHEN position > 0 THEN -position END DESC, -- 拖拽排序（值大靠前）
  {sort_preference} DESC                           -- 时间偏好
```

---

## 搜索策略

- ASCII 关键词 → `notes_fts MATCH '{keyword}'`
- 非 ASCII（中文）→ `title LIKE '%keyword%' OR content LIKE '%keyword%'`
- 搜索始终同时匹配已完成和未完成便签
- 条件全部 AND 组合，支持 keyword + tag_names + year/month + week

---

## 撤销机制（R10 / R13）

- 仅存 Python 进程内存，应用关闭即丢
- 12 小时超时自动清空
- 首次删除时 Toast "撤销仅在应用运行期间有效"
- 撤销创建新便签（原标题+原内容+原标签），不清空原有 FTS 索引

---

## 测试规范（R18 / R25 / R27）

### 目录结构
```
app_tool/tests/
├── conftest.py          ← :memory: SQLite fixtures
├── test_models.py
├── test_database.py
├── test_tag_service.py
├── test_note_service.py
├── test_search_service.py
└── test_reminder_service.py
```

### 强制要求
- **R27**: 单元测试用 `:memory:`，集成测试用 `tempfile.NamedTemporaryFile`
- **R25**: 每个测试函数 docstring 标注对应 spec/rules 条目：
  ```python
  def test_tag_name_length_limit():
      """R8: 标签名 1-10 字符，超限时拒绝"""
  ```
- **R18**: TDD 红灯 → 绿灯 → 重构

---

## AI 行为边界（R22）

- ✅ 仅生成 spec.md 和 rules.md 中明确定义的功能
- ❌ 禁止自行添加 "辅助功能""扩展特性""隐藏彩蛋"
- ⚠️ 若 spec 缺失导致无法实现，必须主动提问，不得自行 "补全"

## 明确不做（R16）

- 多设备实时协作
- 数据加密存储
- 非 WebDAV 云同步
- 离线冲突解决
- 富文本编辑（仅 Markdown 源码）
- 标签进回收站（直接硬删除，有确认框）
- 批量操作（批量删除/批量完成）
