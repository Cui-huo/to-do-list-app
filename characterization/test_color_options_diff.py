"""特征测试 — 颜色选项不一致。

锁定现状：
- main_screen.edit_username 内 COLOR_OPTIONS：3 色（金/天蓝/珊瑚橙）
- settings_screen._get_theme_color_options：4 色（主题感知，Light含黑/Dark含白）
"""

import inspect
import pytest


class TestColorOptionsDiff:
    """颜色选项两套实现的差异。"""

    def test_edit_username_has_3_colors(self):
        """现状：昵称编辑只有 3 个颜色选项，不含黑/白。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen.edit_username)

        # 3 个颜色名称
        assert '金色' in source
        assert '天蓝' in source
        assert '珊瑚橙' in source

        # 不含白色
        assert '白色' not in source, (
            "昵称编辑 COLOR_OPTIONS 不含白色，"
            "与 settings_screen._get_theme_color_options(Dark) 不同"
        )
        # 不含黑色
        assert '黑色' not in source, (
            "昵称编辑 COLOR_OPTIONS 不含黑色，"
            "与 settings_screen._get_theme_color_options(Light) 不同"
        )

    def test_theme_color_options_has_4_colors(self):
        """现状：_get_theme_color_options 返回 4 个颜色，主题感知。"""
        import inspect
        from app_tool.ui import settings_screen

        source = inspect.getsource(settings_screen)

        # Light 模式：含黑色不含白色
        assert '黑色' in source, "Light 模式应含黑色"
        assert '白色' in source, "Dark 模式应含白色"

        # 4 色核心颜色名称
        for name in ['金色', '天蓝', '珊瑚橙']:
            assert name in source, f"应含 {name}"

        # 确认有两个 return 分支（Light / Dark）
        return_count = source.count('return [')
        assert return_count >= 2, f"应有 Light 和 Dark 两个 return 分支，实际 {return_count}"

    def test_color_name_labels_exist(self):
        """现状：两处颜色名称独立维护（同一颜色在两处可能用不同标签）。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui import settings_screen

        edit_source = inspect.getsource(MainScreen.edit_username)
        settings_source = inspect.getsource(settings_screen)

        # 共同颜色名称
        for name in ['金色', '天蓝', '珊瑚橙']:
            assert name in edit_source, f"edit_username 应含 {name}"
            assert name in settings_source, f"settings_screen 应含 {name}"

    def test_color_rgba_values_identical(self):
        """现状：昵称编辑的 3 色 RGBA 与 settings_screen 中的同名颜色一致。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui import settings_screen

        edit_source = inspect.getsource(MainScreen.edit_username)
        settings_source = inspect.getsource(settings_screen)

        # 金 (1, 0.85, 0.4, 1), 天蓝 (0.39, 0.71, 0.96, 1), 珊瑚橙 (0.91, 0.45, 0.29, 1)
        assert '(1, 0.85, 0.4, 1)' in edit_source, "金色 RGBA 在 edit_username"
        assert '(0.39, 0.71, 0.96, 1)' in edit_source, "天蓝 RGBA 在 edit_username"
        assert '(0.91, 0.45, 0.29, 1)' in edit_source, "珊瑚橙 RGBA 在 edit_username"

        # 确认 settings_screen 中相同颜色 RGBA 一致
        assert '(1, 0.85, 0.4, 1)' in settings_source, "金色 RGBA 在 settings_screen"
        assert '(0.39, 0.71, 0.96, 1)' in settings_source, "天蓝 RGBA 在 settings_screen"
        assert '(0.91, 0.45, 0.29, 1)' in settings_source, "珊瑚橙 RGBA 在 settings_screen"
