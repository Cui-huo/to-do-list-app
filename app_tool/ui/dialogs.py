"""对话框：新增/编辑便签 + 确认删除。"""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.chip import MDChip, MDChipText
from app_tool.config import MAX_TAGS_PER_NOTE
from app_tool.ui.chip_utils import make_chip

KV = """
<AddEditContent>:
    orientation: "vertical"
    spacing: dp(12)
    padding: dp(16)
    size_hint_y: None
    height: self.minimum_height

    MDTextField:
        id: title_field
        mode: "rectangle"
        max_text_length: 50
        hint_text: "标题（可选）"
        multiline: False
        size_hint_y: None
        height: dp(48)

    MDTextField:
        id: content_field
        mode: "rectangle"
        max_text_length: 5000
        hint_text: "内容（必填）"
        multiline: True
        size_hint_y: None
        height: dp(100)

    MDLabel:
        text: "标签（点击选择）："
        font_style: "Caption"
        size_hint_y: None
        height: dp(20)

    ScrollView:
        size_hint_y: None
        height: dp(56)
        do_scroll_x: True
        do_scroll_y: False

        MDBoxLayout:
            id: tags_box
            orientation: "horizontal"
            spacing: dp(4)
            size_hint_x: None
            width: self.minimum_width
            adaptive_width: True

    MDLabel:
        id: tag_limit_hint
        text: ""
        font_style: "Caption"
        theme_text_color: "Error"
        size_hint_y: None
        height: 0
"""

Builder.load_string(KV)


class AddEditContent(MDBoxLayout):
    title_field = ObjectProperty(None)
    content_field = ObjectProperty(None)
    tags_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_tags: set[str] = set()
        self._all_tags: list[str] = []

    def set_all_tags(self, tag_names: list[str]):
        self._all_tags = tag_names
        self.ids.tags_box.clear_widgets()
        for name in tag_names:
            chip = make_chip(name, name in self._selected_tags, self.theme_cls, self._toggle_tag)
            self.ids.tags_box.add_widget(chip)

    def set_selected_tags(self, tag_names: list[str]):
        self._selected_tags = set(tag_names)

    def get_selected_tags(self) -> list[str]:
        return list(self._selected_tags)

    def _toggle_tag(self, name: str):
        if name in self._selected_tags:
            self._selected_tags.discard(name)
        else:
            if len(self._selected_tags) >= MAX_TAGS_PER_NOTE:
                self.ids.tag_limit_hint.text = f"每个便签最多 {MAX_TAGS_PER_NOTE} 个标签"
                self.ids.tag_limit_hint.height = dp(18)
                Clock.schedule_once(lambda dt: self._clear_tag_hint(), 2)
                return
            self._selected_tags.add(name)
        self.set_all_tags(self._all_tags)

    def _clear_tag_hint(self):
        self.ids.tag_limit_hint.text = ""
        self.ids.tag_limit_hint.height = 0


def build_add_edit_dialog(
    title: str = "新增便签",
    prefilled_title: str = "",
    prefilled_content: str = "",
    selected_tags: list[str] | None = None,
    all_tag_names: list[str] | None = None,
    on_save=None,
) -> MDDialog:
    content = AddEditContent()
    if selected_tags:
        content.set_selected_tags(selected_tags)
    if all_tag_names:
        content.set_all_tags(all_tag_names)

    if prefilled_title:
        content.ids.title_field.text = prefilled_title
    if prefilled_content:
        content.ids.content_field.text = prefilled_content

    dialog = MDDialog(
        title=title,
        type="custom",
        content_cls=content,
        buttons=[
            MDFlatButton(
                text="取消",
                on_release=lambda *_: dialog.dismiss(),
            ),
            MDFlatButton(
                text="保存",
                on_release=lambda *_: _handle_save(dialog, content, on_save),
            ),
        ],
    )
    return dialog


def _handle_save(dialog: MDDialog, content: AddEditContent, on_save):
    title_text = content.ids.title_field.text.strip()
    content_text = content.ids.content_field.text.strip()

    if not content_text:
        content.ids.content_field.error = True
        content.ids.content_field.helper_text = "内容不能为空"
        return

    dialog.dismiss()
    if on_save:
        on_save(
            title=title_text,
            content=content_text,
            tag_names=content.get_selected_tags(),
        )


def build_confirm_dialog(
    title: str,
    message: str,
    on_confirm=None,
    confirm_text: str = "确认",
) -> MDDialog:
    dialog = MDDialog(
        title=title,
        text=message,
        buttons=[
            MDFlatButton(
                text="取消",
                on_release=lambda *_: dialog.dismiss(),
            ),
            MDFlatButton(
                text=confirm_text,
                on_release=lambda *_: _handle_confirm(dialog, on_confirm),
            ),
        ],
    )
    return dialog


def _handle_confirm(dialog, on_confirm):
    dialog.dismiss()
    if on_confirm:
        on_confirm()
