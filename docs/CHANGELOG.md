# Changelog

## [1.1.0] — 2026-06-19

### P1 部分完成 — 导出 / 夜间模式 / WebDAV 桩

- **新增**: 数据导出服务（JSON / TEXT），含空数据库处理（§5.5）
- **新增**: 夜间模式设置服务，持久化到 UserSettings（§5.6）
- **新增**: WebDAV 同步服务桩 + 凭据管理（P2 预备，§5.8）
- **重构**: export / settings / webdav 全部遵循 R26 统一返回结构 `(bool, result)`
- **修复**: 两个时序测试（`time.sleep` 解决 `:memory:` 同微秒竞争）
- **新增规则**: R29 时间戳竞争修复（`test_note_service.py` 两处 `time.sleep(0.001)`）
- **规则文档**: `rules.md` 拆分为 `rules/core_rules.md` + `rules/ui_rules.md`
- **测试**: 125 全绿（新增 12 个：export 5 + settings 3 + webdav 4）

## [1.0.0] — 2026-06-17

### 首个版本 — P0 基础核心功能

- 便签 CRUD（新增/编辑/删除/撤销删除/完成/取消完成）
- 手动置顶 + 标签置顶（最多 3 个置顶标签）
- 手动拖拽排序
- 标签管理（CRUD + 置顶 + 批量删除）
- FTS5 全文搜索 + LIKE 中文兜底
- 搜索筛选（关键词 + 标签 + 时间范围）
- 前端实时校验 + 后端提交校验
- SQLite 数据持久化
- 冒烟测试 + UI 测试通过
