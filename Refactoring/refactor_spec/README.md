# 重构特征测试规格

> 目的：锁住当前行为，不作为对合理性的判断。
> 这些是"特征测试"（characterization tests），不是"正确性测试"。
> 每条测试描述当前代码**实际做什么**，不论 spec 怎么说。

---

## 使用方式

- 每个测试必须标注 `# 现状` 以明确"这是锁住现有行为，不是验证正确性"
- 测试名含 `_current_behavior` 后缀或注释标明"现状"
- 测试失败意味着重构改变了行为，需人工判断是"有意修复"还是"意外破坏"

## 文件索引

### 特征测试规格

| 文件 | 优先级 | 覆盖范围 |
|------|--------|---------|
| [p0_core_services.md](p0_core_services.md) | P0 | NoteService 核心行为（撤销副作用、标签跳过、排序SQL） |
| [p1_persistence.md](p1_persistence.md) | P1 | 持久化格式（username纯文本、样式JSON、模版、置顶标签、完成状态） |
| [p2_crosscutting.md](p2_crosscutting.md) | P2 | 跨模块行为（标签删除联动、提醒无校验、搜索、FTS同步、跨主题守卫） |
| [suspicious_behaviors.md](suspicious_behaviors.md) | — | 全部 14 条可疑行为清单 + 测试映射 |

### 当前行为特征记录

| 文件 | 类别 | 条目数 |
|------|------|--------|
| [characteristics_text_visibility.md](characteristics_text_visibility.md) | 文字可见性 | V-01 ~ V-40 |
| [characteristics_visual_regression.md](characteristics_visual_regression.md) | 视觉回归 | REG-01 ~ REG-13 |
| [characteristics_interaction.md](characteristics_interaction.md) | 交互行为 | INT-01 ~ INT-20 |
| [characteristics_dark_mode.md](characteristics_dark_mode.md) | 夜间模式切换 | DM-01 ~ DM-05 |
