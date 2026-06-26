"""特征测试 — 撤销 Toast 文案硬编码，不引用常量。

锁定现状：_handle_delete 中 Toast 写死为 "应用未关闭的12小时内..."，
不引用 UNDO_TIMEOUT_SECONDS 常量。修改该常量时 Toast 不会自动更新。
"""

import inspect
import pytest

from app_tool.config import UNDO_TIMEOUT_SECONDS


class TestUndoToastHardcoded:
    """撤销 Toast 文案硬编码行为。"""

    def test_undo_timeout_is_12_hours(self):
        """现状：UNDO_TIMEOUT_SECONDS = 12 * 3600 = 43200 秒。"""
        assert UNDO_TIMEOUT_SECONDS == 12 * 3600

    def test_toast_text_hardcoded_in_source(self):
        """现状：_handle_delete 中 Toast 文案是硬编码字符串。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._handle_delete)

        # 硬编码的 12 小时文案
        assert '应用未关闭的12小时内' in source, (
            "Toast 文案应为硬编码字符串，不引用常量"
        )

        # 不引用 UNDO_TIMEOUT_SECONDS
        assert 'UNDO_TIMEOUT_SECONDS' not in source, (
            "Toast 文案不应引用 UNDO_TIMEOUT_SECONDS 常量，"
            "当前为硬编码，修改常量不会自动更新文案"
        )

    def test_toast_text_matches_constant_value(self):
        """现状：硬编码的 12 小时与 UNDO_TIMEOUT_SECONDS 实际值一致。

        此测试仅记录巧合一致，不代表代码引用了常量。
        如果修改 UNDO_TIMEOUT_SECONDS 为 6*3600，
        此测试应提示人工确认是否更新 Toast 文案。
        """
        hours = UNDO_TIMEOUT_SECONDS // 3600
        assert hours == 12, (
            f"UNDO_TIMEOUT_SECONDS = {UNDO_TIMEOUT_SECONDS} 秒 = {hours} 小时，"
            "Toast 硬编码为 '12小时内'，需人工确认是否一致"
        )
