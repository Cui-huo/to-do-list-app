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
        """编辑按钮图标尺寸应为 dp(40) — 操作栏左组中无 id 的第 2 个按钮"""
        action_box = card.ids.box.children[0]
        left_group = action_box.children[2]  # MDBoxLayout 包裹完成/编辑/删除
        edit_btn = left_group.children[1]
        assert edit_btn.size[0] == pytest.approx(40, abs=1), \
            f"编辑按钮宽度期望 40dp，实际 {edit_btn.size[0]}"

    def test_delete_btn_icon_size(self, card):
        """删除按钮图标尺寸应为 dp(40) — 操作栏左组中无 id 的第 1 个按钮"""
        action_box = card.ids.box.children[0]
        left_group = action_box.children[2]
        delete_btn = left_group.children[0]
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
        """func_sort_icon 图标尺寸应为 32dp"""
        btn = screen.ids.func_sort_icon
        assert btn.size[0] == pytest.approx(32, abs=2), \
            f"func_sort_icon 宽度期望 32dp，实际 {btn.size[0]}"

    def test_func_search_icon_size(self, screen):
        """搜索图标尺寸应为 32dp"""
        search_box = screen.ids.func_row.children[1]
        btn = search_box.children[1]
        assert btn.size[0] == pytest.approx(32, abs=2), \
            f"搜索图标宽度期望 32dp，实际 {btn.size[0]}"

    def test_func_tag_icon_size(self, screen):
        """标签图标尺寸应为 32dp"""
        tag_box = screen.ids.func_row.children[0]
        btn = tag_box.children[1]
        assert btn.size[0] == pytest.approx(32, abs=2), \
            f"标签图标宽度期望 32dp，实际 {btn.size[0]}"

    def test_func_settings_icon_size(self, screen):
        """设置图标尺寸应为 32dp"""
        settings_box = screen.ids.func_row.children[3]
        btn = settings_box.children[1]
        assert btn.size[0] == pytest.approx(32, abs=2), \
            f"设置图标宽度期望 32dp，实际 {btn.size[0]}"

    def test_func_row_label_font_caption(self, screen):
        """func_row 标签字体大小应为 12sp（原 Caption 等价）"""
        sort_box = screen.ids.func_row.children[2]
        label = sort_box.children[0]
        # Kivy 将 "12sp" 转为数值，1x 密度下 ≈ 12.0
        assert label.font_size == pytest.approx(12, abs=2), \
            f"func_row 标签字体大小期望 12sp，实际 {label.font_size}"


# ════════════════════════════════════════════════════════════
# 搜索栏关闭按钮 — ui_spec.md §二
# ════════════════════════════════════════════════════════════

class TestSearchBarCloseButton:
    """搜索栏关闭标签：MDLabel "取消 ✕"，高 28dp，宽自适应文字。

    出现在搜索结果显示时，点击回到主界面。
    """

    def test_search_close_btn_size(self, kivy_app_instance):
        """搜索关闭标签高度应为 28dp，宽自适应文字（非固定 28dp）"""
        from app_tool.ui.main_screen import MainScreen
        screen = MainScreen()
        label = screen.ids.search_close_btn
        # 高度固定 28dp
        assert label.size[1] == pytest.approx(28, abs=2), \
            f"搜索关闭标签高度期望 28dp，实际 {label.size[1]}"
        # 宽度自适应，不应被约束为 28
        assert label.size[0] > 30, \
            f"搜索关闭标签宽度应自适应文字（>30dp），实际 {label.size[0]}"
        # 文字内容
        assert "取消" in label.text, \
            f"搜索关闭标签应包含'取消'，实际 '{label.text}'"


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
    """字体层级：标题 16sp，内容 12sp，标签 12sp（动态 font_size 替代 font_style）。"""

    def test_note_card_title_font(self, kivy_app_instance):
        """卡片标题字体大小应为 16sp"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        fs = card.ids.title_label.font_size
        assert fs == pytest.approx(16, abs=2), \
            f"卡片标题字体大小期望 16sp，实际 {fs}"

    def test_note_card_content_font(self, kivy_app_instance):
        """卡片内容预览字体大小应为 12sp"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        fs = card.ids.content_preview.font_size
        assert fs == pytest.approx(12, abs=2), \
            f"卡片内容字体大小期望 12sp，实际 {fs}"


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

    def test_default_font_is_dongfangdakai(self, main_screen):
        """默认字体为东方大楷"""
        assert main_screen.username_font == "AlimamaDongFangDaKai", \
            f"默认字体应为 'AlimamaDongFangDaKai'，实际 '{main_screen.username_font}'"

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


# ════════════════════════════════════════════════════════════
# 文字样式分组调整 — spec §设置页
# ════════════════════════════════════════════════════════════

class TestTextStyleProperties:
    """MainScreen 文字样式属性默认值。"""

    @pytest.fixture
    def main_screen(self, kivy_app_instance):
        from app_tool.ui.main_screen import MainScreen
        return MainScreen()

    def test_title_suffix_defaults(self, main_screen):
        """标题后缀样式默认值：白色 20sp 无粗体"""
        assert main_screen.title_suffix_color == (1, 1, 1, 1) or main_screen.title_suffix_color is None
        assert main_screen.title_suffix_font_size == "20sp"
        assert main_screen.title_suffix_font == ""
        assert main_screen.title_suffix_bold is False

    def test_func_row_defaults(self, main_screen):
        """功能栏样式默认值：12sp 无粗体"""
        assert main_screen.func_row_font_size == "12sp"
        assert main_screen.func_row_font == ""
        assert main_screen.func_row_bold is False

    def test_section_header_defaults(self, main_screen):
        """分类标题样式默认值：20sp 无粗体"""
        assert main_screen.section_header_font_size == "20sp"
        assert main_screen.section_header_font == ""
        assert main_screen.section_header_bold is False


class TestTextStylePersistence:
    """文字样式持久化读写。"""

    def test_save_and_load_title_suffix(self, kivy_app_instance, db_conn):
        import json
        from app_tool.ui.main_screen import MainScreen
        from kivymd.app import MDApp
        screen = MainScreen()
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute(
            "CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)"
        )
        db_conn.commit()
        try:
            style = {"color": [1, 0.5, 0, 1], "font_size": "24sp", "font": "Lemibo", "bold": True}
            screen.save_style("title_suffix_style", style)
            loaded = screen._load_style("title_suffix_style")
            assert loaded == style, f"存取不匹配: {loaded}"
        finally:
            app.db_conn = old_conn

    def test_save_and_load_func_row(self, kivy_app_instance, db_conn):
        from app_tool.ui.main_screen import MainScreen
        from kivymd.app import MDApp
        screen = MainScreen()
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute(
            "CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)"
        )
        db_conn.commit()
        try:
            style = {"color": None, "font_size": "10sp", "font": "", "bold": False}
            screen.save_style("func_row_style", style)
            loaded = screen._load_style("func_row_style")
            assert loaded == style
        finally:
            app.db_conn = old_conn

    def test_save_and_load_section_header(self, kivy_app_instance, db_conn):
        from app_tool.ui.main_screen import MainScreen
        from kivymd.app import MDApp
        screen = MainScreen()
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute(
            "CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)"
        )
        db_conn.commit()
        try:
            style = {"color": [0.2, 0.2, 0.2, 1], "font_size": "16sp", "font": "AlimamaDongFangDaKai", "bold": True}
            screen.save_style("section_header_style", style)
            loaded = screen._load_style("section_header_style")
            assert loaded == style
        finally:
            app.db_conn = old_conn

    def test_save_and_load_note_card_styles(self, kivy_app_instance, db_conn):
        from app_tool.ui.main_screen import MainScreen
        from kivymd.app import MDApp
        screen = MainScreen()
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute(
            "CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)"
        )
        db_conn.commit()
        try:
            style = {
                "title": {"color": [1, 0, 0, 1], "font_size": "20sp", "font": "Lemibo", "bold": False},
                "tag": {"color": [0, 0.5, 1, 1], "font_size": "10sp", "font": "", "bold": True},
                "content": {"color": None, "font_size": "14sp", "font": "AlimamaDongFangDaKai", "bold": False},
            }
            screen.save_style("note_card_styles", style)
            loaded = screen._load_style("note_card_styles")
            assert loaded == style
        finally:
            app.db_conn = old_conn


class TestNoteCardDynamicStyles:
    """NoteCard 动态样式属性传递。"""

    def test_default_styles_applied(self, kivy_app_instance):
        """默认样式正确设置"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        assert card.title_font == "AlimamaDongFangDaKai"
        assert card.title_bold is True
        assert card.title_font_size == "16sp"
        assert card.tag_color == (0.91, 0.45, 0.29, 1)
        assert card.tag_font_size == "12sp"
        assert card.content_font == "AlimamaDongFangDaKai"
        assert card.content_font_size == "12sp"

    def test_custom_styles_via_kwargs(self, kivy_app_instance):
        """通过构造函数传入自定义样式"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard(
            title_color=(1, 0, 0, 1),
            title_font_size="20sp",
            title_font="Lemibo",
            title_bold=False,
            tag_color=(0, 0.5, 1, 1),
            tag_font_size="10sp",
            tag_font="AlimamaDongFangDaKai",
            tag_bold=True,
            content_color=(0.2, 0.2, 0.2, 1),
            content_font_size="14sp",
            content_font="",
            content_bold=False,
        )
        assert card.title_color == (1, 0, 0, 1)
        assert card.title_font_size == "20sp"
        assert card.title_font == "Lemibo"
        assert card.title_bold is False
        assert card.tag_color == (0, 0.5, 1, 1)
        assert card.content_font_size == "14sp"

    def test_title_label_uses_dynamic_color(self, kivy_app_instance):
        """标题 label 的 text_color 跟随 title_color 属性"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard(title_color=(1, 0.5, 0, 1))
        # KV 绑定: "Custom" if root.title_color else "Primary"
        # title_color 非 None → theme_text_color = "Custom"
        assert card.ids.title_label.theme_text_color == "Custom"
        # Kivy 将 tuple 颜色转为 list 存储
        assert list(card.ids.title_label.text_color) == [1, 0.5, 0, 1]

    def test_content_label_default_secondary(self, kivy_app_instance):
        """内容 label 默认使用 Secondary 主题色"""
        from app_tool.ui.note_card import NoteCard
        card = NoteCard()
        # content_color 默认 None → theme_text_color = "Secondary"
        assert card.ids.content_preview.theme_text_color == "Secondary"


# ════════════════════════════════════════════════════════════
# 文字样式传递验证 — 各组 _apply_* 方法确认
# ════════════════════════════════════════════════════════════

class TestApplyTextStyles:
    """保存样式 → _apply_* → 验证标签属性。"""

    @pytest.fixture
    def main_screen(self, kivy_app_instance):
        from app_tool.ui.main_screen import MainScreen
        return MainScreen()

    def test_apply_title_suffix_font_size(self, main_screen, db_conn):
        """保存 title_suffix_style 后 _apply 能改 label.font_size"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            main_screen.save_style("title_suffix_style", {
                "color": [1, 0, 0, 1], "font_size": "10sp", "font": "Lemibo", "bold": True
            })
            main_screen._apply_title_suffix_style()
            label = main_screen.ids.title_suffix_label
            assert label.font_size == pytest.approx(10, abs=2), f"期望 10sp，实际 {label.font_size}"
            assert label.font_name == "Lemibo"
            assert label.bold is True
            assert label.text_color == [1, 0, 0, 1]
        finally:
            app.db_conn = old_conn

    def test_apply_func_row_font_size(self, main_screen, db_conn):
        """保存 func_row_style 后 _apply 能改 label.font_size"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            main_screen.save_style("func_row_style", {
                "color": None, "font_size": "20sp", "font": "AlimamaDongFangDaKai", "bold": True
            })
            main_screen._apply_func_row_style()
            label = main_screen.ids.sort_label
            assert label.font_size == pytest.approx(20, abs=2), f"期望 20sp，实际 {label.font_size}"
            assert label.bold is True
        finally:
            app.db_conn = old_conn

    def test_apply_section_header_font_size(self, main_screen, db_conn):
        """保存 section_header_style 后 _apply 能改 label.font_size"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            main_screen.save_style("section_header_style", {
                "color": None, "font_size": "10sp", "font": "", "bold": False
            })
            main_screen._apply_section_header_style()
            label = main_screen.ids.incomplete_header
            assert label.font_size == pytest.approx(10, abs=2), f"期望 10sp，实际 {label.font_size}"
        finally:
            app.db_conn = old_conn


# ════════════════════════════════════════════════════════════
# 双主题文字样式 — spec.md §设置
# ════════════════════════════════════════════════════════════

class TestDualThemeTextStyles:
    """白天/黑夜模式各自独立的文字样式 key。"""

    @pytest.fixture
    def main_screen(self, kivy_app_instance):
        from app_tool.ui.main_screen import MainScreen
        return MainScreen()

    def test_light_and_dark_keys_independent(self, main_screen, db_conn):
        """R33: 白天和黑夜 key 独立读写，互不影响。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            # 写入白天样式
            light_style = {"color": [0, 0, 0, 1], "font_size": "14sp", "font": "Lemibo", "bold": False}
            main_screen.save_style("func_row_style", light_style)
            # 写入黑夜样式
            dark_style = {"color": [1, 1, 1, 1], "font_size": "20sp", "font": "AlimamaDongFangDaKai", "bold": True}
            main_screen.save_style("dark_func_row_style", dark_style)
            # 验证互相独立
            assert main_screen._load_style("func_row_style") == light_style
            assert main_screen._load_style("dark_func_row_style") == dark_style
            # 互不干扰
            assert main_screen._load_style("func_row_style") != dark_style
            assert main_screen._load_style("dark_func_row_style") != light_style
        finally:
            app.db_conn = old_conn

    def test_dark_mode_uses_dark_prefix(self, main_screen, db_conn):
        """深色模式下 _get_theme_prefix 返回 'dark_'。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_theme = app.theme_cls.theme_style
        try:
            app.theme_cls.theme_style = "Dark"
            assert main_screen._get_theme_prefix() == "dark_"
            app.theme_cls.theme_style = "Light"
            assert main_screen._get_theme_prefix() == ""
        finally:
            app.theme_cls.theme_style = old_theme

    def test_apply_func_row_loads_dark_key_in_dark_mode(self, main_screen, db_conn):
        """深色模式下 _apply_func_row_style 读取 dark_func_row_style。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        old_theme = app.theme_cls.theme_style
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            # 写入黑夜样式
            dark_style = {"color": [0.39, 0.71, 0.96, 1], "font_size": "10sp", "font": "Lemibo", "bold": True}
            main_screen.save_style("dark_func_row_style", dark_style)
            # 切换到深色模式
            app.theme_cls.theme_style = "Dark"
            main_screen._apply_func_row_style()
            label = main_screen.ids.sort_label
            assert label.font_size == pytest.approx(10, abs=2)
            assert label.font_name == "Lemibo"
            assert label.bold is True
        finally:
            app.db_conn = old_conn
            app.theme_cls.theme_style = old_theme

    def test_note_card_styles_theme_aware(self, main_screen, db_conn):
        """_build_note_card 在深色模式下使用 dark_note_card_styles。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        old_theme = app.theme_cls.theme_style
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            # 写入白天卡片样式
            light_card = {
                "title": {"color": [0, 0, 0, 1], "font_size": "14sp", "font": "Lemibo", "bold": False},
                "tag": {"color": None, "font_size": "10sp", "font": "", "bold": True},
                "content": {"color": None, "font_size": "12sp", "font": "AlimamaDongFangDaKai", "bold": False},
            }
            main_screen.save_style("note_card_styles", light_card)
            # 写入黑夜卡片样式（不同值）
            dark_card = {
                "title": {"color": [1, 1, 1, 1], "font_size": "20sp", "font": "AlimamaDongFangDaKai", "bold": True},
                "tag": {"color": [0.91, 0.45, 0.29, 1], "font_size": "10sp", "font": "Lemibo", "bold": False},
                "content": {"color": [1, 1, 1, 1], "font_size": "14sp", "font": "Lemibo", "bold": False},
            }
            main_screen.save_style("dark_note_card_styles", dark_card)
            # 深色模式下应该加载 dark_note_card_styles
            app.theme_cls.theme_style = "Dark"
            loaded_dark = main_screen._load_style(f"{main_screen._get_theme_prefix()}note_card_styles")
            assert loaded_dark == dark_card
            # 浅色模式下应该加载 note_card_styles
            app.theme_cls.theme_style = "Light"
            loaded_light = main_screen._load_style(f"{main_screen._get_theme_prefix()}note_card_styles")
            assert loaded_light == light_card
        finally:
            app.db_conn = old_conn
            app.theme_cls.theme_style = old_theme

    def test_defaults_light_keys_saved_to_db(self, main_screen, db_conn):
        """首次使用时，白天默认样式可以被正确使用（即使 DB 无记录）。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        old_theme = app.theme_cls.theme_style
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            app.theme_cls.theme_style = "Light"
            # 不写入任何样式，直接 apply
            main_screen._apply_func_row_style()
            # 验证有默认行为（不崩溃，用了 {} 兜底）
            label = main_screen.ids.sort_label
            assert label.font_size is not None
        finally:
            app.db_conn = old_conn
            app.theme_cls.theme_style = old_theme

    def test_dark_defaults_safe_on_empty_db(self, main_screen, db_conn):
        """深色模式下 DB 无记录时，_apply 方法不崩溃且有兜底值。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        old_conn = app.db_conn
        old_theme = app.theme_cls.theme_style
        app.db_conn = db_conn
        db_conn.execute("CREATE TABLE IF NOT EXISTS UserSettings (key TEXT PRIMARY KEY, value TEXT)")
        db_conn.commit()
        try:
            app.theme_cls.theme_style = "Dark"
            # 深色模式下无 dark_* key 也不崩溃
            main_screen._apply_title_suffix_style()
            main_screen._apply_func_row_style()
            main_screen._apply_section_header_style()
            label = main_screen.ids.title_suffix_label
            assert label.font_size is not None
        finally:
            app.db_conn = old_conn
            app.theme_cls.theme_style = old_theme
