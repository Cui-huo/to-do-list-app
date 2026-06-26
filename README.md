# 卡片式便签应用 (Card-Style Note App)

> Android 卡片式便签应用 — 支持标签分类、全文搜索、撤销删除、夜间模式、本地提醒和 WebDAV 同步。

**版本：** 7.0
**测试状态：** 426 测试全绿
**开发阶段：**  此时刚刚完成P0阶段+夜间模式+文字样式模版和自定义功能
**技术栈：** Kivy + KivyMD / SQLite / pytest

---

## 功能概览

| 阶段 | 内容 | 状态 |
|---|---|---|
| **P0** | 便签 CRUD + 标签管理 + 搜索 + 置顶 + UI | ✅ 完成 |
| **P1** | JSON/TEXT 导出 + 夜间模式 + 多提醒 + 文字样式模版和文字样式自定义 | ✅ 部分完成 |
| **P2** | WebDAV 同步 | 🔲 待开发 |

### 核心特性

- 便签新增/编辑/删除/撤销/完成/取消完成
- 手动置顶 + 标签置顶（最多 3 个置顶标签）
- 标签 CRUD + 批量删除
- FTS5 全文搜索 + LIKE 中文兜底
- 搜索筛选（关键词 + 标签 + 年/月/周 + 时间类型）
- 前端实时校验 + 后端提交校验
- JSON/TEXT 数据导出
- 夜间模式（双主题独立文字样式）
- 本地提醒（桌面 Timer / Android AlarmManager）
- 文字样式自定义（颜色/字体/字号/粗体）

---

## 项目结构

```
.
├── main.py                     # 应用入口
├── requirements.txt            # Python 依赖
├── buildozer.spec              # Android APK 构建配置
├── app_tool/                   # 应用核心代码
│   ├── config.py               # 常量配置
│   ├── model/                  # 数据模型层
│   ├── controller/             # 控制器层（业务逻辑）
│   ├── ui/                     # UI 层 (KivyMD)
│   ├── res/                    # 静态资源（图标等）
│   └── tests/                  # 核心单元测试（365 测试）
├── characterization/           # 特征测试 + 文档（独立目录，61 测试）
├── docs/                       # 项目文档
│   ├── spec.md                 # 完整功能规格 (SDD)
│   ├── ui_spec.md              # UI 布局规格
│   └── rules/                  # 设计规则
├── font/                       # 自定义字体
└── .github/workflows/          # CI/CD
```

---

## 快速开始

### 环境要求

- Python 3.12+
- Android 8.0+（目标平台）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用（桌面端调试）

```bash
python main.py
```

### 运行测试

```bash
pytest app_tool/tests/ characterization/ -v
```

---

## Android APK 构建

### 方式一：GitHub Actions（推荐）

1. Fork 本项目到你的 GitHub 账号
2. 进入 Actions 标签页 → 选择 **"Build Android APK"**
3. 点击 **"Run workflow"** 手动触发，或推送代码/tag 自动触发
4. 构建完成后，在 workflow 详情页下载 `notesapp-apk` 产物

### 方式二：本地 Buildozer

```bash
# 安装 Buildozer
pip install buildozer

# 构建调试版 APK
buildozer android debug

# APK 输出路径：bin/*.apk
```

### 图标和启动画面

在 `app_tool/res/` 下放入以下文件：
- `icon.png` — 应用图标（512×512 或更大，PNG 格式）
- `presplash.png` — 启动画面（Android 启动时显示）

---

## Android 权限说明

| 权限 | 用途 |
|------|------|
| `INTERNET` | WebDAV 同步 |
| `VIBRATE` | 提醒通知震动 |
| `RECEIVE_BOOT_COMPLETED` | 重启后恢复闹钟提醒 |
| `POST_NOTIFICATIONS` | Android 13+ 通知权限 |

---

## 开发方法论

- **SDD（规格驱动开发）：** 先写 spec.md 再编码
- **TDD（测试驱动开发）：** 先写测试（红灯）→ 实现（绿灯）→ 重构
- **核心原则：** ID 不可见、点击优先、确认优先、即时反馈

---

## 下载

最新 APK：前往 [Releases](https://github.com/cuihuo/notesapp/releases) 页面下载。

---

## 许可证

MIT License
