"""特征测试 — 三处 _update_theme_colors 实现。

锁定现状：三处独立实现 Light/Dark 主题颜色切换。
- main_screen.py: _update_theme_colors() — 设置 bg_normal, bg_light, top_bar
- settings_screen.py: _update_theme_colors() — 设置 bg_normal, top_bar
- tag_manager.py: on_enter — 内联设置 bg_normal, top_bar
"""

import inspect
import pytest


class TestThemeColorsMainScreen:
    """main_screen._update_theme_colors 行为。"""

    def test_main_screen_sets_bg_normal(self):
        """现状：设置 self.md_bg_color = theme.bg_normal。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'self.md_bg_color = theme.bg_normal' in source

    def test_main_screen_sets_func_row_bg(self):
        """现状：设置 func_row.md_bg_color = theme.bg_light。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'func_row.md_bg_color = theme.bg_light' in source

    def test_main_screen_sets_search_bar_bg(self):
        """现状：设置 search_bar.md_bg_color = theme.bg_light。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'search_bar.md_bg_color = theme.bg_light' in source

    def test_main_screen_dark_top_bar_bg_dark(self):
        """现状：Dark 模式 top_bar.md_bg_color = theme.bg_dark。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'theme.theme_style == "Dark"' in source
        assert 'top_bar.md_bg_color = theme.bg_dark' in source

    def test_main_screen_light_top_bar_primary(self):
        """现状：Light 模式 top_bar.md_bg_color = theme.primary_color。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'top_bar.md_bg_color = theme.primary_color' in source

    def test_main_screen_imports_mdapp(self):
        """现状：_update_theme_colors 内部 import MDApp。"""
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_theme_colors)
        assert 'from kivymd.app import MDApp' in source


class TestThemeColorsSettingsScreen:
    """settings_screen._update_theme_colors 行为。"""

    def test_settings_screen_sets_bg_normal(self):
        """现状：设置 self.md_bg_color = theme.bg_normal。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen._update_theme_colors)
        assert 'self.md_bg_color = theme.bg_normal' in source

    def test_settings_screen_dark_top_bar_bg_dark(self):
        """现状：Dark 模式 top_bar.md_bg_color = theme.bg_dark。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen._update_theme_colors)
        assert 'theme.theme_style == "Dark"' in source
        assert 'top_bar.md_bg_color = theme.bg_dark' in source

    def test_settings_screen_light_top_bar_primary(self):
        """现状：Light 模式 top_bar.md_bg_color = theme.primary_color。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen._update_theme_colors)
        assert 'top_bar.md_bg_color = theme.primary_color' in source

    def test_settings_screen_no_func_row(self):
        """现状：settings_screen 不设置 func_row 或 search_bar（与 MainScreen 不同）。"""
        from app_tool.ui.settings_screen import SettingsScreen

        source = inspect.getsource(SettingsScreen._update_theme_colors)
        assert 'func_row' not in source, "settings_screen 无 func_row"
        assert 'search_bar' not in source, "settings_screen 无 search_bar"


class TestThemeColorsTagManager:
    """tag_manager.on_enter 内联主题设置。"""

    def test_tag_manager_sets_bg_normal(self):
        """现状：on_enter 中设置 self.md_bg_color = theme.bg_normal。"""
        from app_tool.ui.tag_manager import TagManagerScreen

        source = inspect.getsource(TagManagerScreen.on_enter)
        assert 'self.md_bg_color = theme.bg_normal' in source

    def test_tag_manager_dark_top_bar_bg_dark(self):
        """现状：Dark 模式 top_bar.md_bg_color = theme.bg_dark。"""
        from app_tool.ui.tag_manager import TagManagerScreen

        source = inspect.getsource(TagManagerScreen.on_enter)
        assert 'theme.theme_style == "Dark"' in source
        assert 'top_bar.md_bg_color = theme.bg_dark' in source

    def test_tag_manager_light_top_bar_primary(self):
        """现状：Light 模式 top_bar.md_bg_color = theme.primary_color。"""
        from app_tool.ui.tag_manager import TagManagerScreen

        source = inspect.getsource(TagManagerScreen.on_enter)
        assert 'top_bar.md_bg_color = theme.primary_color' in source

    def test_tag_manager_no_func_row(self):
        """现状：tag_manager 不设置 func_row 或 search_bar。"""
        from app_tool.ui.tag_manager import TagManagerScreen

        source = inspect.getsource(TagManagerScreen.on_enter)
        assert 'func_row' not in source, "tag_manager 无 func_row"
        assert 'search_bar' not in source, "tag_manager 无 search_bar"


class TestThemeColorsConsistency:
    """三处实现的共性。"""

    def test_all_three_check_dark_mode_same_way(self):
        """现状：三处都通过 'theme.theme_style == "Dark"' 判断暗色模式。"""
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui.settings_screen import SettingsScreen
        from app_tool.ui.tag_manager import TagManagerScreen

        for cls_name, cls in [
            ("MainScreen._update_theme_colors", MainScreen),
            ("SettingsScreen._update_theme_colors", SettingsScreen),
            ("TagManagerScreen.on_enter", TagManagerScreen),
        ]:
            source = inspect.getsource(
                cls._update_theme_colors if cls_name != "TagManagerScreen.on_enter"
                else cls.on_enter
            )
            assert 'theme.theme_style == "Dark"' in source, (
                f"{cls_name} 应使用 theme.theme_style == 'Dark' 判断"
            )

    def test_all_three_use_same_dark_bg(self):
        """现状：三处 Dark 模式都用 theme.bg_dark 设置 top_bar。"""
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui.settings_screen import SettingsScreen
        from app_tool.ui.tag_manager import TagManagerScreen

        for cls_name, cls in [
            ("MainScreen", MainScreen),
            ("SettingsScreen", SettingsScreen),
            ("TagManagerScreen.on_enter", TagManagerScreen),
        ]:
            source = inspect.getsource(
                cls._update_theme_colors if hasattr(cls, '_update_theme_colors')
                else cls.on_enter
            )
            assert 'top_bar.md_bg_color = theme.bg_dark' in source, (
                f"{cls_name} TopBar Dark 模式应使用 theme.bg_dark"
            )

    def test_all_three_use_same_light_bg(self):
        """现状：三处 Light 模式都用 theme.primary_color 设置 top_bar。"""
        from app_tool.ui.main_screen import MainScreen
        from app_tool.ui.settings_screen import SettingsScreen
        from app_tool.ui.tag_manager import TagManagerScreen

        for cls_name, cls in [
            ("MainScreen", MainScreen),
            ("SettingsScreen", SettingsScreen),
            ("TagManagerScreen.on_enter", TagManagerScreen),
        ]:
            source = inspect.getsource(
                cls._update_theme_colors if hasattr(cls, '_update_theme_colors')
                else cls.on_enter
            )
            assert 'top_bar.md_bg_color = theme.primary_color' in source, (
                f"{cls_name} TopBar Light 模式应使用 theme.primary_color"
            )
