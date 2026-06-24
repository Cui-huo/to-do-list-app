# 重构前特征测试输出规格

> 本文档定义特征测试的**输出格式**，供后续 TDD 流程参考。

---

## 命名规范

每个特征测试函数名必须以 `_current_behavior` 结尾：
```
test_<描述>_current_behavior
```

每个测试函数的 docstring 第一行必须以 `现状：` 开头：
```python
def test_undo_getter_clears_expired_data_current_behavior():
    """现状：get_undo_info() 在超时后自动清除 _undo_data。"""
```

---

## 测试文件组织

特征测试与现有测试分开放置，不污染现有测试套件：

```
app_tool/tests/
├── conftest.py              # 现有 fixtures（复用）
├── test_database.py         # 现有测试（不改动）
├── test_note_service.py     # 现有测试（不改动）
├── ...
└── characterization/        # 新增特征测试目录
    ├── __init__.py
    ├── test_undo_behavior.py        # CT-P0-01
    ├── test_tag_skip_behavior.py    # CT-P0-02, CT-P0-03
    ├── test_sort_behavior.py        # CT-P0-04, CT-P0-05, CT-P0-06
    ├── test_persistence_behavior.py # CT-P1-01 ~ CT-P1-05
    ├── test_crosscutting_behavior.py # CT-P2-01 ~ CT-P2-07
    └── conftest.py                  # 特征测试专用 fixtures
```

---

## 每条测试的输出格式

```
## CT-XX-YY：简短标题

**来源**：`文件路径:方法名()`

**现状行为**：
- 用 1-3 句话描述当前代码实际做什么

**对应的可疑行为**（如有）：
- S-XX

**测试伪代码**：
```python
def test_xxx_current_behavior():
    """现状：..."""
    # 测试代码
```
```

---

## 状态标记

| 状态 | 含义 |
|------|------|
| 📝 规格已写 | 测试规格文档已完成 |
| 🟢 绿灯 | 测试通过，行为已锁住 |
| ⚠️ 需 UI 环境 | 测试需要完整 KivyMD App 环境 |

---

## 当前覆盖统计

| 优先级 | 规格数 | 已实现 |
|--------|--------|--------|
| P0 | 6 | 0 |
| P1 | 5 | 0 |
| P2 | 7 | 0 |
| **合计** | **18** | **0** |

可疑行为 14 条中，11 条已映射到特征测试，3 条需 UI 环境暂缺。
