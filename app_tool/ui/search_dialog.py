"""搜索筛选面板：关键词 + 标签 + 时间条件 AND 组合。"""

from datetime import datetime

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.menu import MDDropdownMenu
from app_tool.ui.chip_utils import fix_chip_label_color, make_chip

KV = """
<SearchContent>:
    orientation: "vertical"
    spacing: dp(12)
    padding: dp(16)
    size_hint_y: None
    height: self.minimum_height

    MDTextField:
        id: keyword_field
        mode: "rectangle"
        hint_text: "搜索关键词"
        multiline: False
        size_hint_y: None
        height: dp(48)

    MDLabel:
        text: "标签筛选（点击选择，AND 逻辑）："
        font_style: "Caption"
        size_hint_y: None
        height: dp(20)

    ScrollView:
        size_hint_y: None
        height: dp(56)
        do_scroll_x: True
        do_scroll_y: False

        MDBoxLayout:
            id: search_tags_box
            orientation: "horizontal"
            spacing: dp(4)
            size_hint_x: None
            width: self.minimum_width
            adaptive_width: True

    MDBoxLayout:
        id: time_type_box
        orientation: "horizontal"
        spacing: dp(8)
        size_hint_y: None
        height: dp(36)

    MDBoxLayout:
        orientation: "horizontal"
        spacing: dp(8)
        size_hint_y: None
        height: dp(56)

        MDBoxLayout:
            id: year_field
            orientation: "vertical"
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(56)
            spacing: dp(2)

            MDLabel:
                text: "年份"
                font_style: "Caption"
                size_hint_y: None
                height: dp(14)

            MDFlatButton:
                id: year_btn
                text: "全部"
                size_hint_y: None
                height: dp(36)

        MDBoxLayout:
            id: month_field
            orientation: "vertical"
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(56)
            spacing: dp(2)

            MDLabel:
                text: "月份"
                font_style: "Caption"
                size_hint_y: None
                height: dp(14)

            MDFlatButton:
                id: month_btn
                text: "全部"
                size_hint_y: None
                height: dp(36)

        MDBoxLayout:
            id: week_field
            orientation: "vertical"
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(56)
            spacing: dp(2)

            MDLabel:
                text: "第N周"
                font_style: "Caption"
                size_hint_y: None
                height: dp(14)

            MDFlatButton:
                id: week_btn
                text: "全部"
                size_hint_y: None
                height: dp(36)
"""

Builder.load_string(KV)


class SearchContent(MDBoxLayout):
    keyword_field = ObjectProperty(None)
    search_tags_box = ObjectProperty(None)
    year_field = ObjectProperty(None)   # 容器，非 MDTextField
    month_field = ObjectProperty(None)  # 容器，非 MDTextField
    selected_year = NumericProperty(0)
    selected_month = NumericProperty(0)
    selected_week = NumericProperty(0)
    time_type = StringProperty("创建时间")

    def __init__(self, **kwargs):
        self._selected_tags: set[str] = set()
        self._all_tags: list[str] = []
        self._menus: list[MDDropdownMenu] = []
        super().__init__(**kwargs)

    def on_kv_post(self, *args):
        """KV 加载完成后初始化下拉菜单和时间类型芯片。"""
        super().on_kv_post(*args)
        self._build_year_menu()
        self._build_month_menu()
        self._build_week_menu()
        self._build_time_type_chips()

    def _build_year_menu(self):
        current_year = datetime.now().year
        items = [
            {"text": "全部", "viewclass": "OneLineListItem",
             "on_release": lambda: self._on_year_select(None)}
        ]
        for y in range(current_year - 5, current_year + 6):
            items.append({
                "text": str(y), "viewclass": "OneLineListItem",
                "on_release": lambda y=y: self._on_year_select(y)
            })
        menu = MDDropdownMenu(
            caller=self.ids.year_btn,
            items=items,
            width_mult=3,
        )
        self._menus.append(menu)
        self.ids.year_btn.bind(on_release=lambda *_: menu.open())

    def _build_month_menu(self):
        items = [
            {"text": "全部", "viewclass": "OneLineListItem",
             "on_release": lambda: self._on_month_select(None)}
        ]
        for m in range(1, 13):
            items.append({
                "text": f"{m}月", "viewclass": "OneLineListItem",
                "on_release": lambda m=m: self._on_month_select(m)
            })
        menu = MDDropdownMenu(
            caller=self.ids.month_btn,
            items=items,
            width_mult=3,
        )
        self._menus.append(menu)
        self.ids.month_btn.bind(on_release=lambda *_: menu.open())

    def _build_week_menu(self):
        items = [
            {"text": "全部", "viewclass": "OneLineListItem",
             "on_release": lambda: self._on_week_select(None)}
        ]
        for w in range(1, 6):
            items.append({
                "text": f"第{w}周", "viewclass": "OneLineListItem",
                "on_release": lambda w=w: self._on_week_select(w)
            })
        menu = MDDropdownMenu(
            caller=self.ids.week_btn,
            items=items,
            width_mult=3,
        )
        self._menus.append(menu)
        self.ids.week_btn.bind(on_release=lambda *_: menu.open())

    def _on_year_select(self, value):
        self.selected_year = value or 0
        self.ids.year_btn.text = str(value) if value else "全部"

    def _on_month_select(self, value):
        self.selected_month = value or 0
        self.ids.month_btn.text = f"{value}月" if value else "全部"

    def _on_week_select(self, value):
        self.selected_week = value or 0
        self.ids.week_btn.text = f"第{value}周" if value else "全部"

    def _build_time_type_chips(self):
        """时间类型芯片切换（创建时间 | 完成时间）。"""
        box = self.ids.time_type_box
        box.clear_widgets()

        active_bg = self.theme_cls.primary_color
        active_tc = (1, 1, 1, 1)
        inactive_bg = self.theme_cls.bg_light
        inactive_tc = self.theme_cls.text_color

        created_chip = MDChip(
            size_hint=(None, None),
            height=32,
            md_bg_color=active_bg if self.time_type == "创建时间" else inactive_bg,
        )
        created_chip.add_widget(MDChipText(
            text="创建时间",
            color=active_tc if self.time_type == "创建时间" else inactive_tc,
            theme_text_color="Custom",
        ))
        Clock.schedule_once(lambda dt, c=created_chip: fix_chip_label_color(c, self.time_type == "创建时间"))
        created_chip.bind(on_press=lambda *_: self._set_time_type("创建时间"))

        completed_chip = MDChip(
            size_hint=(None, None),
            height=32,
            md_bg_color=active_bg if self.time_type == "完成时间" else inactive_bg,
        )
        completed_chip.add_widget(MDChipText(
            text="完成时间",
            color=active_tc if self.time_type == "完成时间" else inactive_tc,
            theme_text_color="Custom",
        ))
        Clock.schedule_once(lambda dt, c=completed_chip: fix_chip_label_color(c, self.time_type == "完成时间"))
        completed_chip.bind(on_press=lambda *_: self._set_time_type("完成时间"))

        box.add_widget(created_chip)
        box.add_widget(completed_chip)

    def _set_time_type(self, value: str):
        self.time_type = value
        self._build_time_type_chips()

    # ── 标签管理 ──

    def set_all_tags(self, tag_names: list[str]):
        self._all_tags = tag_names
        self.ids.search_tags_box.clear_widgets()
        for name in tag_names:
            chip = make_chip(name, name in self._selected_tags, self.theme_cls, self._toggle_tag)
            self.ids.search_tags_box.add_widget(chip)

    def get_selected_tags(self) -> list[str]:
        return list(self._selected_tags)

    def _toggle_tag(self, name: str):
        if name in self._selected_tags:
            self._selected_tags.discard(name)
        else:
            self._selected_tags.add(name)
        self.set_all_tags(self._all_tags)


def build_search_dialog(
    all_tag_names: list[str],
    on_search=None,
) -> MDDialog:
    content = SearchContent()
    content.set_all_tags(all_tag_names)

    dialog = MDDialog(
        title="搜索筛选",
        type="custom",
        content_cls=content,
        buttons=[
            MDFlatButton(
                text="清除",
                on_release=lambda *_: _handle_clear(dialog, content, on_search),
            ),
            MDFlatButton(
                text="搜索",
                on_release=lambda *_: _handle_search(dialog, content, on_search),
            ),
        ],
    )
    return dialog


def _handle_search(dialog: MDDialog, content: SearchContent, on_search):
    keyword = content.ids.keyword_field.text.strip() or None
    tag_names = content.get_selected_tags() or None
    year = content.selected_year or None
    month = content.selected_month or None
    week = content.selected_week or None
    time_type = content.time_type

    dialog.dismiss()
    if on_search:
        on_search(
            keyword=keyword,
            tag_names=tag_names,
            year=year,
            month=month,
            week=week,
            time_type=time_type,
        )


def _handle_clear(dialog: MDDialog, content: SearchContent, on_search):
    dialog.dismiss()
    if on_search:
        on_search(keyword=None, tag_names=None, year=None, month=None, week=None, time_type=None)
