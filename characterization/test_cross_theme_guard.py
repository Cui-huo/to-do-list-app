"""特征测试 — 跨主题样式编辑双重守卫。

锁定现状：
- 入口守卫（is_dark != current_dark）：Toast 拒绝 + return，不打开弹窗
- _on_save 守卫（is_dark == current_dark）：正常保存 vs Toast 提示
- 由于入口守卫已挡掉不匹配主题，_on_save 的 else 分支在当前代码路径不可达
"""

import inspect
import pytest


class TestCrossThemeGuardEntry:
    """入口守卫：open_group1~4_dialog 在主题不匹配时拒绝。"""

    def test_open_group1_has_guard(self):
        """现状：open_group1_dialog 入口检查 is_dark != current_dark。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group1_dialog)
        assert 'is_dark != current_dark' in source, (
            "入口守卫应检查主题是否匹配"
        )
        assert 'self._toast' in source, (
            "主题不匹配时应弹出 Toast"
        )
        # return 出现在 if 块内（紧跟 toast 之后）
        lines = source.split('\n')
        in_guard = False
        has_return = False
        for line in lines:
            if 'is_dark != current_dark' in line:
                in_guard = True
            if in_guard and 'return' in line:
                has_return = True
                break
        assert has_return, "主题不匹配时应 return 不打开弹窗"

    def test_open_group2_has_guard(self):
        """现状：open_group2_dialog 入口检查 is_dark != current_dark。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group2_dialog)
        assert 'is_dark != current_dark' in source

    def test_open_group3_has_guard(self):
        """现状：open_group3_dialog 入口检查 is_dark != current_dark。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group3_dialog)
        assert 'is_dark != current_dark' in source

    def test_open_group4_has_guard(self):
        """现状：open_group4_dialog 入口检查 is_dark != current_dark。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group4_dialog)
        assert 'is_dark != current_dark' in source


class TestCrossThemeGuardOnSave:
    """_on_save 内双重守卫逻辑。"""

    def test_on_save_has_second_guard(self):
        """现状：_on_save 内有 is_dark == current_dark 的二次检查。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group1_dialog)
        # _on_save 嵌套在 open_group1_dialog 内部
        assert 'is_dark == current_dark' in source, (
            "_on_save 内应有 is_dark == current_dark 二次守卫"
        )

    def test_on_save_else_branch_exists(self):
        """现状：_on_save 的 else 分支存在但入口守卫已挡掉不匹配主题。

        如果 is_dark != current_dark，入口守卫已经 return，
        _on_save 永远不会被传入不匹配的主题参数。
        因此 else 分支在当前代码路径中不可达。
        """
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group1_dialog)
        # else 分支的 Toast
        assert '已保存，切换至对应模式可查看效果' in source or '切换至对应模式' in source, (
            "_on_save else 分支存在 Toast 提示，但入口已拦截"
        )

    def test_all_four_dialogs_have_on_save_second_guard(self):
        """现状：4 个 dialog 的 _on_save 都有 is_dark == current_dark 检查。"""
        from app_tool.ui.settings_screen import SettingsScreen

        for method in [
            SettingsScreen.open_group1_dialog,
            SettingsScreen.open_group2_dialog,
            SettingsScreen.open_group3_dialog,
            SettingsScreen.open_group4_dialog,
        ]:
            source = inspect.getsource(method)
            assert 'is_dark == current_dark' in source, (
                f"{method.__name__} 的 _on_save 应有二次守卫"
            )


class TestCrossThemeGuardToastMessages:
    """Toast 消息文案。"""

    def test_entry_guard_toast_messages(self):
        """现状：入口守卫的 Toast 提示用户切换主题后编辑。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group1_dialog)
        assert '请关闭黑夜模式' in source or '请开启黑夜模式' in source, (
            "入口守卫应提示用户切换主题"
        )

    def test_themes_cannot_cross_edit(self):
        """现状：不能跨主题编辑样式——在 Light 模式下不能编辑 Dark 样式，反之亦然。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen.open_group1_dialog)
        # 入口守卫
        lines = source.split('\n')
        guard_found = False
        for i, line in enumerate(lines):
            if 'is_dark != current_dark' in line:
                guard_found = True
                # 下一行应有 toast 或 return
                next_lines = '\n'.join(lines[i:i+3])
                assert 'self._toast' in next_lines or 'return' in next_lines, (
                    "入口守卫后应有 Toast 或 return"
                )
        assert guard_found, "应有入口守卫逻辑"
