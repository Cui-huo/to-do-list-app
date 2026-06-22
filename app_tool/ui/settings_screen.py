"""设置页：夜间模式 + 排序偏好。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.toolbar import MDTopAppBar

KV = """
<SettingsScreen>:

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: top_bar
            title: "设置"
            type: "top"
            anchor_title: "left"

            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(4)
                pos_hint: {"center_y": 0.5}
                adaptive_width: True

                MDIconButton:
                    icon: "arrow-left"
                    on_release: root.go_back()

        ScrollView:
            do_scroll_x: False

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(12)
                padding: dp(16)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "夜间模式"
                        font_style: "Body1"
                        size_hint_x: 0.7

                    MDSwitch:
                        id: dark_mode_switch
                        size_hint: None, None
                        size: dp(48), dp(48)
                        pos_hint: {"center_y": 0.5}
                        on_active: root.toggle_dark_mode(*args)

                MDBoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(80)
                    spacing: dp(8)

                    MDLabel:
                        text: "排序偏好"
                        font_style: "Body1"
                        size_hint_y: None
                        height: dp(28)

                    MDBoxLayout:
                        orientation: "horizontal"
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(40)

                        MDRaisedButton:
                            id: sort_updated_btn
                            text: "按更新时间"
                            size_hint_x: 0.45
                            on_release: root.set_sort_updated()

                        MDFlatButton:
                            id: sort_created_btn
                            text: "按创建时间"
                            size_hint_x: 0.45
                            on_release: root.set_sort_created()

                MDLabel:
                    text: "关于\\n便签应用 v0.1.0"
                    font_style: "Body2"
                    size_hint_y: None
                    height: dp(60)
                    padding: dp(8), dp(12)
                    halign: "center"
                    theme_text_color: "Hint"
"""

Builder.load_string(KV)


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self, *args):
        self._load_settings()

    def _get_services(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        return app.note_service, app.tag_service

    def _toast(self, text: str):
        snackbar = MDSnackbar()
        snackbar.text = text
        snackbar.open()

    def _load_settings(self):
        note_svc, _ = self._get_services()
        from kivymd.app import MDApp
        app = MDApp.get_running_app()

        self.ids.dark_mode_switch.active = (app.theme_cls.theme_style == "Dark")

        inactive_bg = app.theme_cls.bg_light
        inactive_text = app.theme_cls.text_color

        pref = note_svc._get_sort_preference()
        if pref == "created_at":
            self.ids.sort_created_btn.md_bg_color = app.theme_cls.primary_color
            self.ids.sort_created_btn.text_color = (1, 1, 1, 1)
            self.ids.sort_updated_btn.md_bg_color = inactive_bg
            self.ids.sort_updated_btn.text_color = inactive_text
        else:
            self.ids.sort_updated_btn.md_bg_color = app.theme_cls.primary_color
            self.ids.sort_updated_btn.text_color = (1, 1, 1, 1)
            self.ids.sort_created_btn.md_bg_color = inactive_bg
            self.ids.sort_created_btn.text_color = inactive_text

    def toggle_dark_mode(self, switch, active):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        new_theme = "Dark" if active else "Light"
        app.theme_cls.theme_style = new_theme
        app.settings_service.set_dark_mode(new_theme)
        app._apply_titlebar_theme(active)
        self._update_theme_colors()
        self._load_settings()

    def _update_theme_colors(self):
        from kivymd.app import MDApp
        theme = MDApp.get_running_app().theme_cls
        self.md_bg_color = theme.bg_normal
        if theme.theme_style == "Dark":
            self.ids.top_bar.md_bg_color = theme.bg_dark
        else:
            self.ids.top_bar.md_bg_color = theme.primary_color

    def set_sort_updated(self):
        note_svc, _ = self._get_services()
        note_svc.set_sort_preference("updated_at")
        self._load_settings()
        self._toast("排序偏好：按更新时间")

    def set_sort_created(self):
        note_svc, _ = self._get_services()
        note_svc.set_sort_preference("created_at")
        self._load_settings()
        self._toast("排序偏好：按创建时间")

    def go_back(self):
        self.manager.current = "main"
