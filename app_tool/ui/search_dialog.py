"""搜索筛选面板：关键词 + 标签 + 时间条件 AND 组合。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.chip import MDChip

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
        height: dp(40)
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
        orientation: "horizontal"
        spacing: dp(8)
        size_hint_y: None
        height: dp(52)

        MDTextField:
            id: year_field
            mode: "rectangle"
            hint_text: "年份"
            input_filter: "int"
            multiline: False
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(48)

        MDTextField:
            id: month_field
            mode: "rectangle"
            hint_text: "月份"
            input_filter: "int"
            multiline: False
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(48)

        MDTextField:
            id: week_field
            mode: "rectangle"
            hint_text: "第N周"
            helper_text: "1-5"
            input_filter: "int"
            multiline: False
            size_hint_x: 0.33
            size_hint_y: None
            height: dp(48)
"""

Builder.load_string(KV)


class SearchContent(MDBoxLayout):
    keyword_field = ObjectProperty(None)
    search_tags_box = ObjectProperty(None)
    year_field = ObjectProperty(None)
    month_field = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_tags: set[str] = set()
        self._all_tags: list[str] = []

    def set_all_tags(self, tag_names: list[str]):
        self._all_tags = tag_names
        self.ids.search_tags_box.clear_widgets()
        for name in tag_names:
            chip = self._make_chip(name, name in self._selected_tags)
            self.ids.search_tags_box.add_widget(chip)

    def get_selected_tags(self) -> list[str]:
        return list(self._selected_tags)

    def _make_chip(self, name: str, selected: bool):
        if selected:
            bg = (0.25, 0.32, 0.71, 1)
            tc = (1, 1, 1, 1)
        else:
            bg = (0.9, 0.9, 0.9, 1)
            tc = (0.3, 0.3, 0.3, 1)
        chip = MDChip(
            text=name,
            size_hint=(None, None),
            height=28,
            md_bg_color=bg,
            text_color=tc,
        )
        chip.bind(on_press=lambda c, n=name: self._toggle_tag(n))
        return chip

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
    year_str = content.ids.year_field.text.strip()
    month_str = content.ids.month_field.text.strip()
    week_str = content.ids.week_field.text.strip()

    year = int(year_str) if year_str else None
    month = int(month_str) if month_str else None
    week = int(week_str) if week_str else None

    dialog.dismiss()
    if on_search:
        on_search(
            keyword=keyword,
            tag_names=tag_names,
            year=year,
            month=month,
            week=week,
            time_type="创建时间",
        )


def _handle_clear(dialog: MDDialog, content: SearchContent, on_search):
    dialog.dismiss()
    if on_search:
        on_search(keyword=None, tag_names=None, year=None, month=None, week=None, time_type=None)
