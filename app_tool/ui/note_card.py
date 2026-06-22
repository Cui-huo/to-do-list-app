"""便签卡片组件：标题/内容/标签/操作按钮。"""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty, ObjectProperty,
)
from kivymd.uix.card import MDCard
from kivymd.uix.behaviors import TouchBehavior
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton

KV = """
<NoteCard>:
    size_hint_y: None
    height: content_layout.height + dp(24)
    padding: dp(12)
    elevation: 2
    radius: dp(12)

    RelativeLayout:
        id: content_layout
        size_hint_y: None
        height: box.height

        MDBoxLayout:
            id: box
            orientation: "vertical"
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {"center_y": 0.5}

            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: title_label.height if title_label.text else dp(4)
                spacing: dp(8)

                MDLabel:
                    id: title_label
                    text: root.note_title
                    font_style: "Subtitle1"
                    font_name: "AlimamaDongFangDaKai"
                    bold: True
                    size_hint_x: 0.9
                    size_hint_y: None
                    height: self.texture_size[1] if self.text else dp(4)
                    shorten: True
                    shorten_from: "right"

                MDIconButton:
                    id: pin_btn
                    icon: "pin-outline"
                    size_hint: None, None
                    size: dp(40), dp(40)
                    on_release: root.dispatch("on_pin_toggle")

            MDBoxLayout:
                id: chips_box
                orientation: "horizontal"
                spacing: dp(4)
                size_hint_y: None
                height: dp(36) if root.tag_names else 0
                adaptive_width: True

            MDLabel:
                id: content_preview
                text: root._make_preview()
                font_style: "Body2"
                font_name: "AlimamaDongFangDaKai"
                size_hint_y: None
                height: self.texture_size[1]
                max_lines: 2
                shorten: True
                shorten_from: "right"
                theme_text_color: "Secondary"

            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(44)
                spacing: dp(4)
                pos_hint: {"right": 1}

                MDIconButton:
                    id: complete_btn
                    icon: "check-circle"
                    size_hint: None, None
                    size: dp(40), dp(40)
                    on_release: root.dispatch("on_complete_toggle")

                MDIconButton:
                    icon: "pencil"
                    size_hint: None, None
                    size: dp(40), dp(40)
                    on_release: root.dispatch("on_edit")

                MDIconButton:
                    icon: "delete"
                    size_hint: None, None
                    size: dp(40), dp(40)
                    theme_icon_color: "Error"
                    on_release: root.dispatch("on_delete")
"""

Builder.load_string(KV)


def _set_chip_text_color(chip, rgba):
    """KivyMD 1.2.0 内部转换后，遍历芯片树找到 Label 设颜色。"""
    from kivy.uix.label import Label
    for w in chip.walk():
        if isinstance(w, Label):
            w.color = rgba
            return


class NoteCard(MDCard, TouchBehavior):
    note_id = NumericProperty(0)
    note_title = StringProperty("")
    note_content = StringProperty("")
    tag_names = ObjectProperty([])
    is_completed = BooleanProperty(False)
    is_pinned = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type("on_pin_toggle")
        self.register_event_type("on_complete_toggle")
        self.register_event_type("on_edit")
        self.register_event_type("on_delete")
        self.register_event_type("on_drag_start")
        super().__init__(**kwargs)
        self.duration_long_touch = 0.5
        Clock.schedule_once(lambda dt: self._apply_visual_state(), 0)
        Clock.schedule_once(lambda dt: self.on_tag_names(None, self.tag_names), 0)

    def on_is_completed(self, instance, value):
        if self.ids:
            self._apply_visual_state()

    def on_is_pinned(self, instance, value):
        if self.ids:
            self._apply_visual_state()

    def on_tag_names(self, instance, value):
        """标签名变更时重建标签芯片。"""
        if "chips_box" not in self.ids:
            return
        chips_box = self.ids.chips_box
        chips_box.clear_widgets()
        chip_bg = self.theme_cls.bg_light
        chip_text = (0.91, 0.45, 0.29, 1)  # 珊瑚橙暖色
        for name in value:
            chip = MDChip(
                size_hint=(None, None),
                size=(dp(90), dp(32)),
                md_bg_color=chip_bg,
            )
            label = MDChipText(
                text=name,
                theme_text_color="Custom",
                font_style="Caption",
            )
            label.shorten = True
            label.shorten_from = 'right'
            label.text_size = (dp(82), None)
            chip.add_widget(label)
            # KivyMD 1.2.0 内部会将 MDChipText 转为 MDLabel 并重置颜色，
            # 延迟一帧后遍历芯片子树找到最终 Label 设置暖色
            Clock.schedule_once(lambda dt, c=chip: _set_chip_text_color(c, chip_text))
            chips_box.add_widget(chip)

    def _apply_visual_state(self):
        if self.is_completed:
            self.elevation = 0
            self.md_bg_color = self.theme_cls.bg_dark
            self.ids.title_label.opacity = 0.6
            self.ids.content_preview.opacity = 0.5
            self.ids.complete_btn.icon = "undo"
        else:
            self.elevation = 2
            self.md_bg_color = self.theme_cls.bg_normal
            self.ids.title_label.opacity = 1
            self.ids.content_preview.opacity = 0.8
            self.ids.complete_btn.icon = "check-circle"

        if self.is_pinned:
            self.ids.pin_btn.icon = "pin"
            self.ids.pin_btn.opacity = 1
        else:
            self.ids.pin_btn.icon = "pin-outline"
            self.ids.pin_btn.opacity = 0.3

    def _make_preview(self) -> str:
        content = self.note_content or ""
        if len(content) > 80:
            return content[:77] + "..."
        return content

    def on_long_touch(self, touch, *args):
        """长按触发拖拽排序（仅限卡片主体区域，按钮上不触发）。"""
        for btn_id in ("pin_btn", "complete_btn", "edit_btn", "delete_btn"):
            btn = self.ids.get(btn_id)
            if btn and btn.collide_point(*self.to_widget(touch.x, touch.y)):
                return
        self.dispatch("on_drag_start", touch)

    def on_pin_toggle(self, *args):
        pass

    def on_complete_toggle(self, *args):
        pass

    def on_edit(self, *args):
        pass

    def on_delete(self, *args):
        pass

    def on_drag_start(self, *args):
        pass
