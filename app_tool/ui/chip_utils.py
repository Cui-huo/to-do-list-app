"""Chip utilities — shared MDChip builder and KivyMD 1.2.0 colour fix."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.label import Label
from kivymd.app import MDApp
from kivymd.uix.chip import MDChip, MDChipText


def fix_chip_label_color(chip, is_active):
    """KivyMD 1.2.0 内部转换 MDChipText→MDLabel 后重新应用颜色，运行时读取主题色。"""
    theme = MDApp.get_running_app().theme_cls
    color = (1, 1, 1, 1) if is_active else theme.text_color
    for w in chip.walk():
        if isinstance(w, Label):
            w.color = color


def make_chip(name: str, selected: bool, theme_cls, on_press):
    """构建一个 MDChip，含 MDChipText + 颜色修复 + 点击回调。"""
    if selected:
        bg = theme_cls.primary_color
        tc = (1, 1, 1, 1)
    else:
        bg = theme_cls.bg_light
        tc = theme_cls.text_color
    chip = MDChip(
        size_hint=(None, None),
        size=(dp(90), dp(32)),
        md_bg_color=bg,
    )
    chip.add_widget(MDChipText(text=name, color=tc, theme_text_color="Custom"))
    Clock.schedule_once(lambda dt, c=chip: fix_chip_label_color(c, selected))
    chip.bind(on_press=lambda c, n=name: on_press(n))
    return chip
