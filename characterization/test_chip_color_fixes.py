"""特征测试 — Chip 文字颜色修复实现。

锁定现状：
- chip_utils.fix_chip_label_color — 共享实现，只设 color
- chip_utils.make_chip — 共享 chip 构建器
- note_card._apply_chip_text_style — 独立实现，额外设 font_size/font_name/bold
"""

import inspect
import pytest


class TestChipUtilsFixLabelColor:
    """chip_utils.fix_chip_label_color 行为。"""

    def test_fix_label_color_exists(self):
        """现状：chip_utils 模块提供 fix_chip_label_color 函数。"""
        from app_tool.ui import chip_utils

        assert hasattr(chip_utils, 'fix_chip_label_color'), (
            "chip_utils 应有 fix_chip_label_color"
        )

    def test_fix_label_color_uses_walk(self):
        """现状：fix_chip_label_color 使用 chip.walk() 遍历查找 Label。"""
        from app_tool.ui.chip_utils import fix_chip_label_color

        source = inspect.getsource(fix_chip_label_color)
        assert '.walk()' in source, "应使用 walk() 遍历组件树"
        assert 'isinstance(w, Label)' in source, "应检查 isinstance(w, Label)"

    def test_fix_label_color_only_sets_color(self):
        """现状：fix_chip_label_color 只设置 color，不设 font_size/font_name/bold。

        与 note_card._apply_chip_text_style 不同。
        """
        from app_tool.ui.chip_utils import fix_chip_label_color

        source = inspect.getsource(fix_chip_label_color)
        assert 'w.color' in source, "应设置 color"
        assert 'font_size' not in source, (
            "fix_chip_label_color 不应设置 font_size（与 note_card 不同）"
        )
        assert 'font_name' not in source, (
            "fix_chip_label_color 不应设置 font_name（与 note_card 不同）"
        )
        assert 'bold' not in source, (
            "fix_chip_label_color 不应设置 bold（与 note_card 不同）"
        )

    def test_fix_label_color_active_vs_inactive(self):
        """现状：选中时白色 (1,1,1,1)，未选中时 theme.text_color。"""
        from app_tool.ui.chip_utils import fix_chip_label_color

        source = inspect.getsource(fix_chip_label_color)
        assert '(1, 1, 1, 1)' in source, "选中时应用白色"
        assert 'theme.text_color' in source, "未选中时应用主题文字色"


class TestChipUtilsMakeChip:
    """chip_utils.make_chip 行为。"""

    def test_make_chip_exists(self):
        """现状：chip_utils 提供 make_chip 函数。"""
        from app_tool.ui import chip_utils

        assert hasattr(chip_utils, 'make_chip'), (
            "chip_utils 应有 make_chip"
        )

    def test_make_chip_uses_fix_label_color(self):
        """现状：make_chip 内部调用 fix_chip_label_color 修复颜色。"""
        from app_tool.ui.chip_utils import make_chip

        source = inspect.getsource(make_chip)
        assert 'fix_chip_label_color' in source, (
            "make_chip 应调用 fix_chip_label_color"
        )

    def test_make_chip_uses_clock_schedule_once(self):
        """现状：make_chip 使用 Clock.schedule_once 延迟修复（解决 MDChipText 转换时序）。"""
        from app_tool.ui.chip_utils import make_chip

        source = inspect.getsource(make_chip)
        assert 'Clock.schedule_once' in source, (
            "应使用 Clock.schedule_once 延迟修复（KivyMD 1.2.0 时序）"
        )

    def test_make_chip_size_fixed(self):
        """现状：chip 尺寸固定为 90dp × 32dp。"""
        from app_tool.ui.chip_utils import make_chip

        source = inspect.getsource(make_chip)
        assert 'dp(90)' in source, "宽度 90dp"
        assert 'dp(32)' in source, "高度 32dp"


class TestNoteCardChipTextStyle:
    """note_card._apply_chip_text_style 行为。"""

    def test_apply_chip_text_style_exists(self):
        """现状：note_card._apply_chip_text_style 是独立实现。"""
        from app_tool.ui import note_card

        assert hasattr(note_card, '_apply_chip_text_style'), (
            "note_card 应有 _apply_chip_text_style"
        )

    def test_apply_chip_text_style_uses_walk(self):
        """现状：_apply_chip_text_style 使用 chip.walk() 遍历。"""
        from app_tool.ui.note_card import _apply_chip_text_style

        source = inspect.getsource(_apply_chip_text_style)
        assert '.walk()' in source, "应使用 walk() 遍历"
        assert 'isinstance(w, Label)' in source, "应检查 isinstance(w, Label)"

    def test_apply_chip_text_style_sets_all_props(self):
        """现状：_apply_chip_text_style 设置 color + font_size + font_name + bold。

        与 chip_utils.fix_chip_label_color 不同，后者只设 color。
        """
        from app_tool.ui.note_card import _apply_chip_text_style

        source = inspect.getsource(_apply_chip_text_style)
        assert 'w.color' in source, "应设置 color"
        assert 'w.font_size' in source, "应设置 font_size"
        assert 'w.font_name' in source, "应设置 font_name"
        assert 'w.bold' in source, "应设置 bold"

    def test_apply_chip_text_style_returns_early(self):
        """现状：找到第一个 Label 后 return（不处理多层嵌套）。"""
        from app_tool.ui.note_card import _apply_chip_text_style

        source = inspect.getsource(_apply_chip_text_style)
        assert 'return' in source, "找到第一个 Label 后 return"


class TestChipFixImplementationsCount:
    """锁定三处实现的共存关系。"""

    def test_chip_utils_is_shared(self):
        """现状：dialogs 和 search_dialog 共享 chip_utils，note_card 独立。"""
        from app_tool.ui import dialogs, search_dialog, note_card

        # dialogs 和 search_dialog 都导入 chip_utils
        dialogs_source = inspect.getsource(dialogs)
        search_source = inspect.getsource(search_dialog)
        assert 'chip_utils' in dialogs_source
        assert 'chip_utils' in search_source

        # note_card 有自己的 _apply_chip_text_style
        note_source = inspect.getsource(note_card)
        assert 'def _apply_chip_text_style' in note_source, (
            "note_card 有自己的独立实现，不依赖 chip_utils"
        )

    def test_note_card_does_not_import_chip_utils(self):
        """现状：note_card.py 不导入 chip_utils（使用自己的实现）。"""
        from app_tool.ui import note_card

        source = inspect.getsource(note_card)
        assert 'chip_utils' not in source, (
            "note_card 不导入 chip_utils，使用自己的 _apply_chip_text_style"
        )
