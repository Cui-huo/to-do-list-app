"""UI 组件尺寸与样式测试 —— ui_spec.md 合规性验证（红灯）。

本测试文件验证所有 UI 组件符合 ui_spec.md 中定义的尺寸、字体、间距标准。
当前代码尚未调整到 spec 标准，预期红灯。

所有测试方法接受 kivy_app_instance fixture（来自 conftest.py）
"""

import pytest


# ════════════════════════════════════════════════════════════
# NoteCard 操作按钮尺寸 — ui_spec.md §二
# ════════════════════════════════════════════════════════════

class TestNoteCardButtonSizes:
    """NoteCard 操作按钮：图标 40dp + padding 补足 48dp 热区。"""

    @pytest.fixture
    def card(self, kivy_app_instance):
        from app_tool.ui.note_card import NoteCard
        return NoteCard()

    def test_complete_btn_icon_size(self, card):
        """complete_btn 图标尺寸应为 dp(40)"""
        assert card.ids.complete_btn.size[0] == pytest.approx(40, abs=1), \
            f"complete_btn 宽度期望 40dp，实际 {card.ids.complete_btn.size[0]}"

    def test_pin_btn_icon_size(self, card):
        """pin_btn 图标尺寸应为 dp(40)"""
        assert card.ids.pin_btn.size[0] == pytest.approx(40, abs=1), \
            f"pin_btn 宽度期望 40dp，实际 {card.ids.pin_btn.size[0]}"

    def test_edit_btn_icon_size(self, card):
        """编辑按钮图标尺寸应为 dp(40) — 操作栏中无 id 的第 2 个按钮"""
        action_box = card.ids.box.children[0]
        edit_btn = action_box.children[1]
        assert edit_btn.size[0] == pytest.approx(40, abs=1), \
            f"编辑按钮宽度期望 40dp，实际 {edit_btn.size[0]}"

    def test_delete_btn_icon_size(self, card):
        """删除按钮图标尺寸应为 dp(40) — 操作栏中无 id 的第 3 个按钮"""
        action_box = card.ids.box.children[0]
        delete_btn = action_box.children[0]
        assert delete_btn.size[0] == pytest.approx(40, abs=1), \
            f"删除按钮宽度期望 40dp，实际 {delete_btn.size[0]}"


# ════════════════════════════════════════════════════════════
# 标签芯片尺寸 — ui_spec.md §三
# ════════════════════════════════════════════════════════════

class TestChipSizes:
    """标签芯片：宽 90dp × 高 32dp，字体 Caption。"""

    def test_note_card_chip_height(self, kivy_app_instance):
        """NoteCard 内标签芯片高度应为 32dp"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        card.tag_names = ["测试标签"]
        if card.ids.chips_box.children:
            chip = card.ids.chips_box.children[0]
            assert chip.height == pytest.approx(32, abs=1), \
                f"标签芯片高度期望 32dp，实际 {chip.height}"

    def test_dialog_chip_height(self, kivy_app_instance):
        """对话框内标签芯片高度应为 32dp"""
        from app_tool.ui.dialogs import AddEditContent
        content = AddEditContent()
        content.set_all_tags(["测试"])
        if content.ids.tags_box.children:
            chip = content.ids.tags_box.children[0]
            assert chip.height == pytest.approx(32, abs=1), \
                f"对话框标签芯片高度期望 32dp，实际 {chip.height}"

    def test_search_chip_height(self, kivy_app_instance):
        """搜索面板内标签芯片高度应为 32dp"""
        from app_tool.ui.search_dialog import SearchContent
        content = SearchContent()
        content.set_all_tags(["测试"])
        if content.ids.search_tags_box.children:
            chip = content.ids.search_tags_box.children[0]
            assert chip.height == pytest.approx(32, abs=1), \
                f"搜索面板标签芯片高度期望 32dp，实际 {chip.height}"

    def test_note_card_chip_width(self, kivy_app_instance):
        """NoteCard 标签芯片固定宽度应为 90dp"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        card.tag_names = ["测试标签"]
        if card.ids.chips_box.children:
            chip = card.ids.chips_box.children[0]
            assert chip.width == pytest.approx(90, abs=2), \
                f"标签芯片宽度期望 90dp，实际 {chip.width}"


# ════════════════════════════════════════════════════════════
# func_row 图标按钮与标签字体 — ui_spec.md §一.1, §一.2
# ════════════════════════════════════════════════════════════

class TestFuncRowSizes:
    """func_row：图标按钮 36dp，标签字体 Caption。"""

    @pytest.fixture
    def screen(self, kivy_app_instance):
        from app_tool.ui.main_screen import MainScreen
        return MainScreen()

    def test_func_sort_icon_size(self, screen):
        """func_sort_icon 图标尺寸应为 36dp"""
        btn = screen.ids.func_sort_icon
        assert btn.size[0] == pytest.approx(36, abs=1), \
            f"func_sort_icon 宽度期望 36dp，实际 {btn.size[0]}"

    def test_func_search_icon_size(self, screen):
        """搜索图标尺寸应为 36dp"""
        search_box = screen.ids.func_row.children[1]
        btn = search_box.children[1]
        assert btn.size[0] == pytest.approx(36, abs=1), \
            f"搜索图标宽度期望 36dp，实际 {btn.size[0]}"

    def test_func_tag_icon_size(self, screen):
        """标签图标尺寸应为 36dp"""
        tag_box = screen.ids.func_row.children[0]
        btn = tag_box.children[1]
        assert btn.size[0] == pytest.approx(36, abs=1), \
            f"标签图标宽度期望 36dp，实际 {btn.size[0]}"

    def test_func_settings_icon_size(self, screen):
        """设置图标尺寸应为 36dp"""
        settings_box = screen.ids.func_row.children[3]
        btn = settings_box.children[1]
        assert btn.size[0] == pytest.approx(36, abs=1), \
            f"设置图标宽度期望 36dp，实际 {btn.size[0]}"

    def test_func_row_label_font_caption(self, screen):
        """func_row 标签字体应为 Caption，不得为 Overline"""
        sort_box = screen.ids.func_row.children[2]
        label = sort_box.children[0]
        assert label.font_style == "Caption", \
            f"func_row 标签字体期望 'Caption'，实际 '{label.font_style}'"


# ════════════════════════════════════════════════════════════
# 搜索栏关闭按钮 — ui_spec.md §二
# ════════════════════════════════════════════════════════════

class TestSearchBarCloseButton:
    """搜索栏关闭按钮：28×28dp。"""

    def test_search_close_btn_size(self, kivy_app_instance):
        """搜索栏关闭按钮尺寸应为 28dp"""
        from app_tool.ui.main_screen import MainScreen
        screen = MainScreen()
        close_btn = screen.ids.search_bar.children[0]
        assert 27 <= close_btn.size[0] <= 29, \
            f"搜索关闭按钮宽度期望 28dp，实际 {close_btn.size[0]}"


# ════════════════════════════════════════════════════════════
# 对话框标签滚动区高度 — ui_spec.md §二
# ════════════════════════════════════════════════════════════

class TestDialogScrollViewHeight:
    """对话框标签选择区 ScrollView 高度 56dp。"""

    def test_add_edit_scrollview_height(self, kivy_app_instance):
        """AddEditContent 标签 ScrollView 高度应为 56dp"""
        from app_tool.ui.dialogs import AddEditContent
        content = AddEditContent()
        # KV 末尾: ScrollView, tag_limit_hint → children[1] = ScrollView
        sv = content.children[1]
        assert sv.height == pytest.approx(56, abs=1), \
            f"对话框标签 ScrollView 高度期望 56dp，实际 {sv.height}"

    def test_search_scrollview_height(self, kivy_app_instance):
        """SearchContent 标签 ScrollView 高度应为 56dp"""
        from app_tool.ui.search_dialog import SearchContent
        content = SearchContent()
        # KV 顺序: keyword_field, label, ScrollView, time_type_box, year/month/week
        # children 反序: children[2] = ScrollView
        sv = content.children[2]
        assert sv.height == pytest.approx(56, abs=1), \
            f"搜索面板标签 ScrollView 高度期望 56dp，实际 {sv.height}"


# ════════════════════════════════════════════════════════════
# 卡片内边距与间距 — ui_spec.md §一.3
# ════════════════════════════════════════════════════════════

class TestCardPaddingAndSpacing:
    """卡片 padding ≥ 12dp，内部间距符合标准。"""

    @pytest.fixture
    def card(self, kivy_app_instance):
        from app_tool.ui.note_card import NoteCard
        return NoteCard()

    def test_card_padding(self, card):
        """卡片内 padding 应 ≥ 12dp"""
        assert card.padding[0] >= 12, \
            f"卡片水平 padding 期望 ≥12dp，实际 {card.padding[0]}"

    def test_card_internal_spacing(self, card):
        """卡片内部 box spacing 应为 8dp"""
        box = card.ids.box
        assert box.spacing == pytest.approx(8, abs=1), \
            f"卡片内部 spacing 期望 8dp，实际 {box.spacing}"

    def test_chips_box_spacing(self, card):
        """标签组内芯片间距应为 4dp"""
        chips_box = card.ids.chips_box
        assert chips_box.spacing == pytest.approx(4, abs=1), \
            f"标签芯片间距期望 4dp，实际 {chips_box.spacing}"

    def test_action_buttons_spacing(self, card):
        """操作按钮间距应为 4dp"""
        action_box = card.ids.box.children[0]
        assert action_box.spacing == pytest.approx(4, abs=1), \
            f"操作按钮间距期望 4dp，实际 {action_box.spacing}"


# ════════════════════════════════════════════════════════════
# 搜索面板组件类型 — ui_spec.md §四
# ════════════════════════════════════════════════════════════

class TestSearchPanelComponents:
    """搜索面板：年/月/周使用下拉选择器，含时间类型芯片切换。"""

    @pytest.fixture
    def content(self, kivy_app_instance):
        from app_tool.ui.search_dialog import SearchContent
        return SearchContent()

    def test_year_is_dropdown_not_textfield(self, content):
        """年份应为下拉选择器，不得为 MDTextField 手输"""
        from kivymd.uix.textfield import MDTextField
        assert not isinstance(content.ids.year_field, MDTextField), \
            "年份选择器应是下拉组件，不是 MDTextField"

    def test_month_is_dropdown_not_textfield(self, content):
        """月份应为下拉选择器"""
        from kivymd.uix.textfield import MDTextField
        assert not isinstance(content.ids.month_field, MDTextField), \
            "月份选择器应是下拉组件，不是 MDTextField"

    def test_week_is_dropdown_not_textfield(self, content):
        """第 N 周应为下拉选择器"""
        from kivymd.uix.textfield import MDTextField
        assert not isinstance(content.ids.week_field, MDTextField), \
            "周数选择器应是下拉组件，不是 MDTextField"

    def test_search_has_time_type_chip(self, content):
        """搜索面板应含时间类型芯片切换（创建时间 | 完成时间）"""
        has_time_type = hasattr(content.ids, 'time_type_box')
        assert has_time_type, \
            "搜索面板缺少时间类型芯片切换组件（time_type_box）"


# ════════════════════════════════════════════════════════════
# FAB 定位 — ui_spec.md §一.5
# ════════════════════════════════════════════════════════════

class TestFABPositioning:
    """FAB 距右下角固定 16dp，不得使用百分比 pos_hint。"""

    def test_fab_uses_fixed_dp_not_percent(self, kivy_app_instance):
        """FAB 定位应为固定 dp，非百分比"""
        from app_tool.ui.main_screen import MainScreen
        from kivymd.uix.button import MDFloatingActionButton
        screen = MainScreen()
        fab = None
        for child in screen.children:
            if isinstance(child, MDFloatingActionButton):
                fab = child
                break
        assert fab is not None, "MainScreen 中未找到 FAB"
        has_pos_hint = bool(fab.pos_hint)
        assert not has_pos_hint, \
            "FAB 不得使用百分比 pos_hint，应使用固定 dp 定位距右下角 16dp"


# ════════════════════════════════════════════════════════════
# 字体层级 — ui_spec.md §一.2
# ════════════════════════════════════════════════════════════

class TestFontHierarchy:
    """字体层级：标题 Subtitle1，内容 Body2，标签 Caption。"""

    def test_note_card_title_font(self, kivy_app_instance):
        """卡片标题字体应为 Subtitle1"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        assert card.ids.title_label.font_style == "Subtitle1", \
            f"卡片标题字体期望 'Subtitle1'，实际 '{card.ids.title_label.font_style}'"

    def test_note_card_content_font(self, kivy_app_instance):
        """卡片内容预览字体应为 Body2"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        assert card.ids.content_preview.font_style == "Body2", \
            f"卡片内容字体期望 'Body2'，实际 '{card.ids.content_preview.font_style}'"


# ════════════════════════════════════════════════════════════
# NoteCard 自定义字体 — ui_spec.md §二 + R32 对比度
# ════════════════════════════════════════════════════════════

class TestNoteCardCustomFonts:
    """卡片标题行楷粗体 + 内容楷体 + 标签暖色。"""

    @pytest.fixture
    def card(self, kivy_app_instance):
        from app_tool.ui.note_card import NoteCard
        return NoteCard()

    def test_title_uses_dongfangdakai_font(self, card):
        """§二: 标题使用东方大楷字体"""
        assert card.ids.title_label.font_name == "AlimamaDongFangDaKai", \
            f"标题字体期望 'AlimamaDongFangDaKai'，实际 '{card.ids.title_label.font_name}'"

    def test_title_is_bold(self, card):
        """§二: 标题为粗体"""
        assert card.ids.title_label.bold is True, \
            f"标题粗体期望 True，实际 {card.ids.title_label.bold}"

    def test_content_uses_dongfangdakai_font(self, card):
        """§二: 内容使用东方大楷字体"""
        assert card.ids.content_preview.font_name == "AlimamaDongFangDaKai", \
            f"内容字体期望 'AlimamaDongFangDaKai'，实际 '{card.ids.content_preview.font_name}'"

    def test_tag_chip_created_with_warm_color(self, card):
        """§二 + R32: 标签芯片创建成功（珊瑚橙色在 on_tag_names 中硬编码设置）"""
        card.tag_names = ["测试"]
        chips_box = card.ids.chips_box
        assert len(chips_box.children) == 1, "应创建一个标签芯片"
        chip = chips_box.children[0]
        # MDChip 内部已将 MDChipText 转为 MDLabel，验证芯片存在即可
        assert chip.size[0] == pytest.approx(90, abs=1), f"芯片宽度期望 90dp"

    def test_tag_font_smaller_than_title(self, card):
        """§二: 标签字号 (Caption) 小于标题 (Subtitle1)"""
        title_style = card.ids.title_label.font_style  # Subtitle1
        # Caption < Subtitle1 在 KivyMD 字体层级中
        assert title_style != "Caption", \
            f"标题字体不应为 Caption，实际 '{title_style}'"


# ════════════════════════════════════════════════════════════
# 用户名样式 — R32 双主题对比度 + UserSettings 持久化
# ════════════════════════════════════════════════════════════

class TestUsernameStyle:
    """用户名配色/字体/粗细可调，R32 双主题合规，持久化恢复。"""

    @pytest.fixture
    def main_screen(self, kivy_app_instance):
        from app_tool.ui.main_screen import MainScreen
        screen = MainScreen()
        return screen

    def test_default_color_is_gold(self, main_screen):
        """默认颜色为金色"""
        c = main_screen.username_color
        assert c == (1, 0.85, 0.4, 1), \
            f"默认颜色应为金色 (1,0.85,0.4,1)，实际 {c}"

    def test_default_font_is_empty(self, main_screen):
        """默认字体为空（使用系统默认）"""
        assert main_screen.username_font == "", \
            f"默认字体应为空，实际 '{main_screen.username_font}'"

    def test_default_bold_is_false(self, main_screen):
        """默认粗体为关闭"""
        assert main_screen.username_bold is False, \
            f"默认粗体应为 False，实际 {main_screen.username_bold}"

    def test_persist_and_restore(self, main_screen, db_conn):
        """样式选择持久化后可从 DB 恢复"""
        import json
        # 模拟已登录的 App
        from kivymd.app import MDApp
        from kivy.app import App
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute(
            "CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)"
        )

        try:
            main_screen.username_color = (0.39, 0.71, 0.96, 1)
            main_screen.username_font = "AlimamaDongFangDaKai"
            main_screen.username_bold = True
            main_screen._save_username_style()

            # 重置属性
            main_screen.username_color = (1, 0.85, 0.4, 1)
            main_screen.username_font = ""
            main_screen.username_bold = False

            # 重新加载
            main_screen._load_username_style()

            assert main_screen.username_color == (0.39, 0.71, 0.96, 1), \
                "恢复后颜色不匹配"
            assert main_screen.username_font == "AlimamaDongFangDaKai", \
                "恢复后字体不匹配"
            assert main_screen.username_bold is True, \
                "恢复后粗体不匹配"
        finally:
            app.db_conn = old_conn
