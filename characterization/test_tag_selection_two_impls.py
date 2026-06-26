"""特征测试 — AddEditContent vs SearchContent 标签选择差异。

锁定现状：
- AddEditContent (dialogs.py)：有 MAX_TAGS_PER_NOTE 上限检查（3个）
- SearchContent (search_dialog.py)：无标签数量上限
- 两者都有 _selected_tags / _make_chip / _toggle_tag 等相同结构
- 两者都使用 chip_utils.make_chip（共享实现）
"""

import inspect
import pytest


class TestAddEditContentTagLimit:
    """dialogs.py 的 AddEditContent 有标签数量上限。"""

    def test_addedit_imports_max_tags(self):
        """现状：dialogs.py import MAX_TAGS_PER_NOTE。"""
        from app_tool.ui import dialogs

        source = inspect.getsource(dialogs)
        assert 'MAX_TAGS_PER_NOTE' in source, (
            "dialogs.py 应 import MAX_TAGS_PER_NOTE"
        )

    def test_addedit_checks_tag_limit(self):
        """现状：AddEditContent 在 _toggle_tag 中检查 len(self._selected_tags) >= MAX_TAGS_PER_NOTE。"""
        from app_tool.ui import dialogs

        source = inspect.getsource(dialogs)
        assert 'len(self._selected_tags) >= MAX_TAGS_PER_NOTE' in source, (
            "应检查选中标签数是否达上限"
        )

    def test_addedit_shows_limit_hint(self):
        """现状：超出上限时显示提示文字。"""
        from app_tool.ui import dialogs

        source = inspect.getsource(dialogs)
        assert '每个便签最多' in source, (
            "超出上限应显示提示"
        )

    def test_addedit_uses_chip_utils(self):
        """现状：dialogs.py 使用 chip_utils.make_chip。"""
        from app_tool.ui import dialogs

        source = inspect.getsource(dialogs)
        assert 'from app_tool.ui.chip_utils import make_chip' in source, (
            "应导入 chip_utils.make_chip"
        )


class TestSearchContentNoTagLimit:
    """search_dialog.py 的 SearchContent 无标签数量上限。"""

    def test_search_has_no_max_tags_import(self):
        """现状：search_dialog.py 不 import MAX_TAGS_PER_NOTE。"""
        from app_tool.ui import search_dialog

        source = inspect.getsource(search_dialog)
        assert 'MAX_TAGS_PER_NOTE' not in source, (
            "search_dialog.py 不应 import MAX_TAGS_PER_NOTE（无上限限制）"
        )

    def test_search_has_no_limit_check(self):
        """现状：SearchContent 的 _toggle_tag 不检查标签数量。"""
        from app_tool.ui import search_dialog

        source = inspect.getsource(search_dialog)
        # 不包含上限检查
        assert 'len(self._selected_tags) >=' not in source, (
            "SearchContent 不应有标签数量上限检查"
        )

    def test_search_uses_chip_utils(self):
        """现状：search_dialog.py 使用 chip_utils.make_chip。"""
        from app_tool.ui import search_dialog

        source = inspect.getsource(search_dialog)
        assert 'from app_tool.ui.chip_utils import' in source, (
            "应导入 chip_utils"
        )


class TestBothTagSelections:
    """两套标签选择的共性。"""

    def test_both_have_selected_tags_set(self):
        """现状：两套实现都维护 self._selected_tags set。"""
        from app_tool.ui import dialogs, search_dialog

        for name, module in [("dialogs", dialogs), ("search_dialog", search_dialog)]:
            source = inspect.getsource(module)
            assert '_selected_tags' in source, (
                f"{name} 应有 _selected_tags"
            )

    def test_both_have_toggle_tag(self):
        """现状：两套实现都有 _toggle_tag 方法。"""
        from app_tool.ui import dialogs, search_dialog

        for name, module in [("dialogs", dialogs), ("search_dialog", search_dialog)]:
            source = inspect.getsource(module)
            assert '_toggle_tag' in source, (
                f"{name} 应有 _toggle_tag"
            )

    def test_both_use_shared_make_chip(self):
        """现状：两套实现都使用 chip_utils.make_chip（共享的 chip 构建函数）。"""
        from app_tool.ui import dialogs, search_dialog

        for name, module in [("dialogs", dialogs), ("search_dialog", search_dialog)]:
            source = inspect.getsource(module)
            assert 'make_chip' in source, (
                f"{name} 应使用 make_chip"
            )
