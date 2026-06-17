# 卡片式便签应用 (Card-Style Note App)

> Android 卡片式便签应用 — 支持标签分类、拖拽排序、全文搜索、撤销删除、夜间模式、本地提醒和 WebDAV 同步。

**版本：** 1.0.0  
**开发状态：** P0 基础核心功能完成，冒烟测试 + UI 测试通过  
**技术栈：** Kivy + KivyMD / SQLite / pytest

---

## 功能概览

| 阶段 | 内容 | 状态 |
|---|---|---|
| **P0** | 便签 CRUD + 标签管理 + 搜索 + 置顶 + 拖拽排序 + UI | ✅ 基础完成 |
| **P1** | JSON/TEXT 导出 + 夜间模式 + 多提醒 (Android) | 🔲 待开发 |
| **P2** | WebDAV 同步 | 🔲 待开发 |

### 核心特性

- 便签新增/编辑/删除/撤销/完成/取消完成
- 手动置顶 + 标签置顶（最多 3 个置顶标签）
- 手动拖拽排序
- 标签 CRUD + 批量删除
- FTS5 全文搜索 + LIKE 中文兜底
- 搜索筛选（关键词 + 标签 + 年/月/周）
- 前端实时校验 + 后端提交校验

---

## 项目结构

```
.
├── main.py                  # 应用入口
├── spec.md                  # 完整功能规格 (SDD)
├── rules.md                 # 19 条设计规则
├── skills.md                # 可复用操作流程
├── app_tool/
│   ├── config.py            # 常量配置
│   ├── model/               # 数据模型层
│   ├── controller/          # 控制器层（业务逻辑）
│   ├── ui/                  # UI 层 (KivyMD)
│   ├── res/                 # 静态资源
│   └── tests/               # pytest 测试套件
└── .python312/              # 嵌入式 Python（开发环境）
```

---

## 快速开始

### 环境要求

- Python 3.12+
- Android 8.0+（目标平台）

### 安装依赖

```bash
pip install kivy kivymd pytest
```

### 运行应用（桌面端调试）

```bash
python main.py
```

### 运行测试

```bash
pytest app_tool/tests/ -v
```

---

## 开发方法论

- **SDD（规格驱动开发）：** 先写 spec.md 再编码
- **TDD（测试驱动开发）：** 先写测试（红灯）→ 实现（绿灯）→ 重构
- **核心原则：** ID 不可见、点击优先、确认优先、即时反馈

---

## 许可证

MIT License
