"""设置页：夜间模式 + 排序偏好 + 文字样式分组调整。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog

# 颜色预设
COLOR_OPTIONS = [
    ("默认", None),
    ("白色", (1, 1, 1, 1)),
    ("金色", (1, 0.85, 0.4, 1)),
    ("天蓝", (0.39, 0.71, 0.96, 1)),
    ("珊瑚橙", (0.91, 0.45, 0.29, 1)),
    ("深灰", (0.2, 0.2, 0.2, 1)),
]

# 字号预设
FONT_SIZE_OPTIONS = [
    ("特大", "20sp"),
    ("大", "16sp"),
    ("中", "14sp"),
    ("小", "12sp"),
    ("特小", "10sp"),
]

# 字体预设
FONT_OPTIONS = [
    ("默认", ""),
    ("东方大楷", "AlimamaDongFangDaKai"),
    ("乐米波波", "Lemibo"),
]

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
                    text: "文字样式模版"
                    font_style: "Subtitle1"
                    size_hint_y: None
                    height: dp(32)

                MDBoxLayout:
                    id: template_list
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    adaptive_height: True
                    spacing: dp(8)

                MDRaisedButton:
                    id: save_template_btn
                    text: "+ 保存当前为模版"
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(40)
                    md_bg_color: app.theme_cls.primary_color
                    text_color: 1, 1, 1, 1
                    on_release: root._on_save_as_template()

                MDLabel:
                    text: "白天模式文字样式"
                    font_style: "Subtitle1"
                    size_hint_y: None
                    height: dp(32)

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "标题栏文字"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "用户名 + 的专属便签本"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45
                        shorten: True

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group1_dialog()

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "功能栏文字"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "按更新时间 / 便签检索..."
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45
                        shorten: True

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group2_dialog()

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "分类标题"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "未完成 / 已完成"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group3_dialog()

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "便签卡片样式"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "标题 / 标签 / 内容"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group4_dialog()

                MDLabel:
                    text: "黑夜模式文字样式"
                    font_style: "Subtitle1"
                    size_hint_y: None
                    height: dp(32)

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "标题栏文字"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "用户名 + 的专属便签本"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45
                        shorten: True

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group1_dialog("dark")

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "功能栏文字"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "按更新时间 / 便签检索..."
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45
                        shorten: True

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group2_dialog("dark")

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "分类标题"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "未完成 / 已完成"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group3_dialog("dark")

                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(8), 0
                    spacing: dp(12)

                    MDLabel:
                        text: "便签卡片样式"
                        font_style: "Body1"
                        size_hint_x: 0.3

                    MDLabel:
                        text: "标题 / 标签 / 内容"
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        size_hint_x: 0.45

                    MDFlatButton:
                        text: "编辑"
                        size_hint_x: 0.25
                        pos_hint: {"center_y": 0.5}
                        on_release: root.open_group4_dialog("dark")

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


# ── 双主题文字样式默认值（从 main_screen 导入，key 为基础名） ──
from app_tool.ui.main_screen import LIGHT_STYLE_DEFAULTS, DARK_STYLE_DEFAULTS


def _style_key(base: str, theme: str) -> str:
    """返回带主题前缀的 UserSettings key。theme="dark" 时加 dark_ 前缀。"""
    return f"dark_{base}" if theme == "dark" else base


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
        from kivymd.uix.label import MDLabel
        MDSnackbar(
            MDLabel(text=text, font_style="Body2"),
            duration=2,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ).open()

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

        # 生成文字样式模版按钮
        self._load_template_buttons()

    def _load_template_buttons(self):
        """在 template_list 中动态生成模板行（名称 + 使用/删除/编辑按钮）。"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        main_screen = self.manager.get_screen("main")
        templates = main_screen._load_templates()
        container = self.ids.template_list
        container.clear_widgets()
        for i, t in enumerate(templates):
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(40),
                spacing=dp(6),
            )
            # 模版名
            row.add_widget(MDLabel(
                text=t["name"],
                font_style="Body1",
                size_hint_x=0.3,
                halign="left",
                valign="center",
                shorten=True,
            ))
            # 使用按钮
            use_btn = MDFlatButton(
                text="使用",
                size_hint_x=0.2,
                on_release=lambda _, idx=i: self._on_apply_template(idx),
            )
            row.add_widget(use_btn)
            # 删除按钮
            del_btn = MDFlatButton(
                text="删除",
                size_hint_x=0.2,
                theme_text_color="Error",
                on_release=lambda _, idx=i: self._on_delete_template(idx),
            )
            row.add_widget(del_btn)
            # 编辑名称按钮
            edit_btn = MDFlatButton(
                text="编辑",
                size_hint_x=0.2,
                on_release=lambda _, idx=i: self._on_rename_template(idx),
            )
            row.add_widget(edit_btn)
            container.add_widget(row)

    def _on_apply_template(self, template_index: int):
        """点击使用按钮：写入 DB + 刷新主界面。"""
        main_screen = self.manager.get_screen("main")
        ok, name = main_screen.apply_template(template_index)
        if ok:
            self._toast(f"已应用「{name}」模版")
            self._load_settings()

    def _on_rename_template(self, template_index: int):
        """弹出名称输入框，修改模版名称。"""
        main_screen = self.manager.get_screen("main")
        templates = main_screen._load_templates()
        if template_index < 0 or template_index >= len(templates):
            return
        old_name = templates[template_index]["name"]
        from kivymd.uix.textfield import MDTextField
        content = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12), adaptive_height=True)
        name_field = MDTextField(hint_text="输入新名称", text=old_name, max_text_length=20)
        content.add_widget(name_field)
        dialog = MDDialog(
            title="编辑模版名称",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=lambda *_: self._do_rename_template(
                    template_index, name_field.text.strip(), dialog)),
            ],
        )
        dialog.open()

    def _do_rename_template(self, template_index: int, new_name: str, dialog):
        if not new_name:
            self._toast("名称不能为空")
            return
        main_screen = self.manager.get_screen("main")
        templates = main_screen._load_templates()
        templates[template_index]["name"] = new_name
        main_screen._save_templates(templates)
        dialog.dismiss()
        self._toast("模版名已更新")
        self._load_template_buttons()

    def _on_save_as_template(self):
        """弹出名称输入框，保存当前样式为自定义模版。"""
        from kivymd.uix.textfield import MDTextField
        content = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12), adaptive_height=True)
        content.add_widget(MDLabel(
            text="保存当前白天+黑夜文字样式为模版",
            font_style="Body2",
            theme_text_color="Secondary",
            adaptive_height=True,
        ))
        name_field = MDTextField(hint_text="输入模版名称", max_text_length=20)
        content.add_widget(name_field)
        dialog = MDDialog(
            title="保存为模版",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=lambda *_: self._do_save_template(name_field.text.strip(), dialog)),
            ],
        )
        dialog.open()

    def _do_save_template(self, name: str, dialog):
        if not name:
            self._toast("模版名不能为空")
            return
        main_screen = self.manager.get_screen("main")
        ok, saved_name = main_screen.save_current_as_template(name)
        if ok:
            dialog.dismiss()
            self._toast(f"模版「{saved_name}」已保存")
            self._load_template_buttons()

    def _on_delete_template(self, template_index: int):
        """确认后删除模版。"""
        main_screen = self.manager.get_screen("main")
        templates = main_screen._load_templates()
        if template_index < 0 or template_index >= len(templates):
            return
        name = templates[template_index]["name"]
        dialog = MDDialog(
            title="确认删除",
            text=f"确认删除模版「{name}」？\n此操作不可撤销。",
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="确认删除", on_release=lambda *_: self._do_delete_template(template_index, dialog)),
            ],
        )
        dialog.open()

    def _do_delete_template(self, template_index: int, dialog):
        main_screen = self.manager.get_screen("main")
        ok, name = main_screen.delete_template(template_index)
        if ok:
            dialog.dismiss()
            self._toast(f"模版「{name}」已删除")
            self._load_template_buttons()

    def toggle_dark_mode(self, switch, active):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        new_theme = "Dark" if active else "Light"
        app.theme_cls.theme_style = new_theme
        app.settings_service.set_dark_mode(new_theme)
        app._apply_titlebar_theme(active)
        self._update_theme_colors()
        self._load_settings()
        # 同步主界面主题 + 文字样式
        main_screen = self.manager.get_screen("main")
        main_screen._update_theme_colors()
        main_screen._apply_text_styles()
        main_screen.refresh_list()

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

    # ── 样式编辑对话框 ──

    @staticmethod
    def _default_style():
        return {"color": None, "font_size": "16sp", "font": "", "bold": False}

    def _load_style_dict(self, key):
        import json
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app and app.db_conn:
            row = app.db_conn.execute(
                "SELECT value FROM UserSettings WHERE key=?", (key,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
        return None

    def _save_style_dict(self, key, style: dict):
        import json
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app and app.db_conn:
            app.db_conn.execute(
                "INSERT OR REPLACE INTO UserSettings (key, value) VALUES (?, ?)",
                (key, json.dumps(style)),
            )
            app.db_conn.commit()

    def _build_color_buttons(self, selected_rgba, on_select, parent, is_dark=None):
        """构建颜色选择按钮行，根据指定主题过滤选项。"""
        row = MDBoxLayout(orientation="horizontal", spacing=dp(8), adaptive_height=True)
        btns = []
        for cname, crgba in self._get_theme_color_options(is_dark=is_dark):
            btn = MDFlatButton(
                text=cname,
                size_hint=(None, None),
                size=(dp(56), dp(36)),
            )
            if crgba:
                btn.md_bg_color = crgba
                btn.theme_text_color = "Custom"
                btn.text_color = (0, 0, 0, 1) if sum(crgba[:3]) > 1.8 else (1, 1, 1, 1)
            btn._crgba = crgba
            btn.bind(on_release=lambda b, clr=crgba: on_select(clr))
            btns.append(btn)
            row.add_widget(btn)
        parent.add_widget(row)
        return btns

    def _build_size_buttons(self, selected_size, on_select, parent):
        """构建字号选择按钮行。"""
        row = MDBoxLayout(orientation="horizontal", spacing=dp(6), adaptive_height=True)
        btns = []
        for sname, sval in FONT_SIZE_OPTIONS:
            btn = MDFlatButton(
                text=sname,
                size_hint=(None, None),
                size=(dp(48), dp(36)),
            )
            btn._sval = sval
            btn.bind(on_release=lambda b, sv=sval: on_select(sv))
            btns.append(btn)
            row.add_widget(btn)
        parent.add_widget(row)
        return btns

    def _build_font_buttons(self, selected_font, on_select, parent):
        """构建字体选择按钮行。"""
        row = MDBoxLayout(orientation="horizontal", spacing=dp(6), adaptive_height=True)
        btns = []
        for fname, fval in FONT_OPTIONS:
            btn = MDFlatButton(
                text=fname,
                size_hint=(None, None),
                size=(dp(72), dp(36)),
            )
            btn._fval = fval
            btn.bind(on_release=lambda b, fv=fval: on_select(fv))
            btns.append(btn)
            row.add_widget(btn)
        parent.add_widget(row)
        return btns

    def _add_single_style_section(self, parent, section_label, style_state, on_change, is_dark=None):
        """添加一组样式控制（颜色+字号+粗体+字体），返回按钮引用用于高亮更新。"""
        sec = MDBoxLayout(orientation="vertical", spacing=dp(4), adaptive_height=True)

        if section_label:
            sec.add_widget(MDLabel(
                text=section_label,
                font_style="Caption",
                theme_text_color="Secondary",
                adaptive_height=True,
            ))

        # 颜色
        sec.add_widget(MDLabel(text="颜色", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        color_btns = self._build_color_buttons(
            style_state["color"],
            lambda clr: _on_style_change("color", clr),
            sec,
            is_dark=is_dark,
        )

        # 字号
        sec.add_widget(MDLabel(text="字号", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        size_btns = self._build_size_buttons(
            style_state["font_size"],
            lambda sv: _on_style_change("font_size", sv),
            sec,
        )

        # 粗体
        bold_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), adaptive_height=True)
        bold_row.add_widget(MDLabel(
            text="粗体", font_style="Caption", theme_text_color="Hint",
            adaptive_height=True, adaptive_width=True,
        ))
        bold_switch = MDSwitch()
        bold_switch.bind(active=lambda _, v: _on_style_change("bold", v))
        # 延迟设置 active，避免 KivyMD 1.2.0 在 ids 就绪前触发动画崩溃
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt, bs=bold_switch, val=style_state["bold"]: setattr(bs, 'active', val), 0)
        bold_row.add_widget(bold_switch)
        sec.add_widget(bold_row)

        # 字体
        sec.add_widget(MDLabel(text="字体", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        font_btns = self._build_font_buttons(
            style_state["font"],
            lambda fv: _on_style_change("font", fv),
            sec,
        )

        parent.add_widget(sec)

        def _on_style_change(key, value):
            style_state[key] = value
            on_change()

        return {"color": color_btns, "size": size_btns, "font": font_btns, "bold": bold_switch}

    # ── 组1：标题栏文字（用户名 + 后缀） ──

    def open_group1_dialog(self, theme="light"):
        is_dark = (theme == "dark")
        from kivymd.app import MDApp
        current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        if is_dark != current_dark:
            self._toast("请关闭黑夜模式，再点击进行文字样式编辑！" if current_dark else "请开启黑夜模式，再点击进行文字样式编辑！")
            return
        app = MDApp.get_running_app()
        main_screen = self.manager.get_screen("main")
        username = main_screen.username or "某某"

        # 加载当前样式
        defaults = DARK_STYLE_DEFAULTS if is_dark else LIGHT_STYLE_DEFAULTS
        u_key = _style_key("username_style", theme)
        s_key = _style_key("title_suffix_style", theme)
        u_raw = self._load_style_dict(u_key) or defaults.get("username_style", {})
        s_raw = self._load_style_dict(s_key) or defaults.get("title_suffix_style", {})

        u_color = tuple(u_raw["color"]) if u_raw.get("color") else (1, 0.85, 0.4, 1)
        s_color = tuple(s_raw["color"]) if s_raw.get("color") else (1, 1, 1, 1)

        u_state = {
            "color": u_color,
            "font_size": u_raw.get("font_size", "20sp"),
            "font": u_raw.get("font", ""),
            "bold": u_raw.get("bold", False),
        }
        s_state = {
            "color": s_color,
            "font_size": s_raw.get("font_size", "20sp"),
            "font": s_raw.get("font", ""),
            "bold": s_raw.get("bold", False),
        }

        content = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12), adaptive_height=True)

        # 预览
        preview_user = MDLabel(
            text=username,
            font_size=u_state["font_size"],
            font_name=u_state["font"] or "Roboto",
            bold=u_state["bold"],
            theme_text_color="Custom",
            text_color=u_state["color"],
            adaptive_width=True,
            size_hint_y=None,
            height=dp(32),
        )
        preview_suffix = MDLabel(
            text="的专属便签本",
            font_size=s_state["font_size"],
            font_name=s_state["font"] or "Roboto",
            bold=s_state["bold"],
            theme_text_color="Custom",
            text_color=s_state["color"],
            adaptive_width=True,
            size_hint_y=None,
            height=dp(32),
        )
        content.add_widget(MDLabel(text="预览", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        # 预览背景：模拟主界面标题栏蓝色
        preview_bg = MDBoxLayout(
            orientation="horizontal",
            md_bg_color=app.theme_cls.primary_color,
            padding=dp(8),
            spacing=dp(0),
            adaptive_height=True,
            adaptive_width=True,
            radius=dp(8),
        )
        preview_bg.add_widget(preview_user)
        preview_bg.add_widget(preview_suffix)
        content.add_widget(preview_bg)

        def _refresh_preview():
            preview_user.text = username
            preview_user.font_size = u_state["font_size"]
            preview_user.font_name = u_state["font"] or "Roboto"
            preview_user.bold = u_state["bold"]
            if u_state["color"]:
                preview_user.theme_text_color = "Custom"
                preview_user.text_color = u_state["color"]
            else:
                preview_user.theme_text_color = "Primary"
            preview_suffix.font_size = s_state["font_size"]
            preview_suffix.font_name = s_state["font"] or "Roboto"
            preview_suffix.bold = s_state["bold"]
            if s_state["color"]:
                preview_suffix.theme_text_color = "Custom"
                preview_suffix.text_color = s_state["color"]
            else:
                preview_suffix.theme_text_color = "Primary"

        self._add_single_style_section(content, "用户名样式", u_state, _refresh_preview, is_dark=is_dark)
        self._add_single_style_section(content, "后缀\"的专属便签本\"样式", s_state, _refresh_preview, is_dark=is_dark)

        def _on_save(*_):
            u_save = {
                "font_size": u_state["font_size"],
                "font": u_state["font"],
                "bold": u_state["bold"],
            }
            if u_state["color"]:
                u_save["color"] = list(u_state["color"])
            self._save_style_dict(u_key, u_save)
            self._save_style_dict(s_key, {
                "color": list(s_state["color"]) if s_state["color"] else None,
                "font_size": s_state["font_size"],
                "font": s_state["font"],
                "bold": s_state["bold"],
            })
            # 仅当编辑当前主题时同步回主界面
            current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
            if is_dark == current_dark:
                main_screen.username_color = u_state["color"] if u_state["color"] else (1, 0.85, 0.4, 1)
                main_screen.username_font = u_state["font"]
                main_screen.username_bold = u_state["bold"]
                main_screen._apply_title_suffix_style()
                dialog.dismiss()
                self._toast("标题栏文字样式已保存")
            else:
                dialog.dismiss()
                self._toast("已保存，切换至对应模式可查看效果")

        dialog = MDDialog(
            title="编辑：标题栏文字",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=_on_save),
            ],
        )
        dialog.open()

    # ── 组2：功能栏文字 ──

    def open_group2_dialog(self, theme="light"):
        is_dark = (theme == "dark")
        from kivymd.app import MDApp
        current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        if is_dark != current_dark:
            self._toast("请关闭黑夜模式，再点击进行文字样式编辑！" if current_dark else "请开启黑夜模式，再点击进行文字样式编辑！")
            return
        main_screen = self.manager.get_screen("main")
        key = _style_key("func_row_style", theme)
        defaults = DARK_STYLE_DEFAULTS if is_dark else LIGHT_STYLE_DEFAULTS
        raw = self._load_style_dict(key) or defaults.get("func_row_style", {})
        _color = tuple(raw["color"]) if raw.get("color") else None
        state = {
            "color": _color,
            "font_size": raw.get("font_size", "12sp"),
            "font": raw.get("font", ""),
            "bold": raw.get("bold", False),
        }

        content = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12), adaptive_height=True)

        # 预览
        content.add_widget(MDLabel(text="预览", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        preview = MDLabel(
            text="按更新时间  便签检索  标签  设置",
            font_size=state["font_size"],
            font_name=state["font"] or "Roboto",
            bold=state["bold"],
            adaptive_height=True,
        )
        if state["color"]:
            preview.theme_text_color = "Custom"
            preview.text_color = state["color"]
        else:
            preview.theme_text_color = "Primary"
        content.add_widget(preview)

        def _refresh_preview():
            preview.font_size = state["font_size"]
            preview.font_name = state["font"] or "Roboto"
            preview.bold = state["bold"]
            if state["color"]:
                preview.theme_text_color = "Custom"
                preview.text_color = state["color"]
            else:
                preview.theme_text_color = "Primary"

        self._add_single_style_section(content, "", state, _refresh_preview, is_dark=is_dark)

        def _on_save(*_):
            self._save_style_dict(key, {
                "color": list(state["color"]) if state["color"] else None,
                "font_size": state["font_size"],
                "font": state["font"],
                "bold": state["bold"],
            })
            current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
            if is_dark == current_dark:
                main_screen._apply_func_row_style()
                dialog.dismiss()
                self._toast("功能栏文字样式已保存")
            else:
                dialog.dismiss()
                self._toast("已保存，切换至对应模式可查看效果")

        dialog = MDDialog(
            title="编辑：功能栏文字",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=_on_save),
            ],
        )
        dialog.open()

    # ── 组3：分类标题 ──

    def open_group3_dialog(self, theme="light"):
        is_dark = (theme == "dark")
        from kivymd.app import MDApp
        current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        if is_dark != current_dark:
            self._toast("请关闭黑夜模式，再点击进行文字样式编辑！" if current_dark else "请开启黑夜模式，再点击进行文字样式编辑！")
            return
        main_screen = self.manager.get_screen("main")
        key = _style_key("section_header_style", theme)
        defaults = DARK_STYLE_DEFAULTS if is_dark else LIGHT_STYLE_DEFAULTS
        raw = self._load_style_dict(key) or defaults.get("section_header_style", {})
        _color = tuple(raw["color"]) if raw.get("color") else None
        state = {
            "color": _color,
            "font_size": raw.get("font_size", "20sp"),
            "font": raw.get("font", ""),
            "bold": raw.get("bold", False),
        }

        content = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12), adaptive_height=True)

        content.add_widget(MDLabel(text="预览", font_style="Caption", theme_text_color="Hint", adaptive_height=True))
        preview = MDLabel(
            text="未完成  已完成 (3)",
            font_size=state["font_size"],
            font_name=state["font"] or "Roboto",
            bold=state["bold"],
            adaptive_height=True,
        )
        if state["color"]:
            preview.theme_text_color = "Custom"
            preview.text_color = state["color"]
        else:
            preview.theme_text_color = "Primary"
        content.add_widget(preview)

        def _refresh_preview():
            preview.font_size = state["font_size"]
            preview.font_name = state["font"] or "Roboto"
            preview.bold = state["bold"]
            if state["color"]:
                preview.theme_text_color = "Custom"
                preview.text_color = state["color"]
            else:
                preview.theme_text_color = "Primary"

        self._add_single_style_section(content, "", state, _refresh_preview, is_dark=is_dark)

        def _on_save(*_):
            self._save_style_dict(key, {
                "color": list(state["color"]) if state["color"] else None,
                "font_size": state["font_size"],
                "font": state["font"],
                "bold": state["bold"],
            })
            current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
            if is_dark == current_dark:
                main_screen._apply_section_header_style()
                dialog.dismiss()
                self._toast("分类标题样式已保存")
            else:
                dialog.dismiss()
                self._toast("已保存，切换至对应模式可查看效果")

        dialog = MDDialog(
            title="编辑：分类标题",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=_on_save),
            ],
        )
        dialog.open()

    # ── 组4：便签卡片样式（可折叠 + ScrollView + 预览卡片跟随主题） ──

    def _get_theme_color_options(self, is_dark=None):
        """根据主题返回颜色选项，全部显式颜色。夜间含白色，日间含黑色。"""
        if is_dark is None:
            from kivymd.app import MDApp
            is_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        if is_dark:
            return [
                ("白色", (1, 1, 1, 1)),
                ("金色", (1, 0.85, 0.4, 1)),
                ("天蓝", (0.39, 0.71, 0.96, 1)),
                ("珊瑚橙", (0.91, 0.45, 0.29, 1)),
            ]
        else:
            return [
                ("黑色", (0.05, 0.05, 0.05, 1)),
                ("金色", (1, 0.85, 0.4, 1)),
                ("天蓝", (0.39, 0.71, 0.96, 1)),
                ("珊瑚橙", (0.91, 0.45, 0.29, 1)),
            ]

    def open_group4_dialog(self, theme="light"):
        is_dark = (theme == "dark")
        from kivymd.app import MDApp
        current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        if is_dark != current_dark:
            self._toast("请关闭黑夜模式，再点击进行文字样式编辑！" if current_dark else "请开启黑夜模式，再点击进行文字样式编辑！")
            return
        from kivymd.uix.card import MDCard
        from kivymd.uix.scrollview import MDScrollView
        from kivymd.app import MDApp
        theme_cls = MDApp.get_running_app().theme_cls
        main_screen = self.manager.get_screen("main")
        key = _style_key("note_card_styles", theme)
        defaults = DARK_STYLE_DEFAULTS if is_dark else LIGHT_STYLE_DEFAULTS
        raw = self._load_style_dict(key) or defaults.get("note_card_styles", {})
        t_raw = raw.get("title", {})
        g_raw = raw.get("tag", {})
        c_raw = raw.get("content", {})

        t_color = tuple(t_raw["color"]) if t_raw.get("color") else None
        g_color = tuple(g_raw["color"]) if g_raw.get("color") else None
        c_color = tuple(c_raw["color"]) if c_raw.get("color") else None

        t_state = {
            "color": t_color,
            "font_size": t_raw.get("font_size", "16sp"),
            "font": t_raw.get("font", "AlimamaDongFangDaKai"),
            "bold": t_raw.get("bold", True),
        }
        g_state = {
            "color": g_color,
            "font_size": g_raw.get("font_size", "12sp"),
            "font": g_raw.get("font", ""),
            "bold": g_raw.get("bold", False),
        }
        c_state = {
            "color": c_color,
            "font_size": c_raw.get("font_size", "12sp"),
            "font": c_raw.get("font", "AlimamaDongFangDaKai"),
            "bold": c_raw.get("bold", False),
        }

        # ScrollView 包裹，限制最大高度并支持滚动
        scroll = MDScrollView(do_scroll_x=False, size_hint=(1, None), height=dp(480))

        body = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8), adaptive_height=True)

        # ── 预览卡片（跟随主题背景） ──
        body.add_widget(Widget(size_hint_y=None, height=dp(8)))
        body.add_widget(MDLabel(text="预览", font_style="Caption", theme_text_color="Hint", adaptive_height=True))

        card_inner = MDBoxLayout(orientation="vertical", spacing=dp(6), adaptive_height=True)
        preview_title = MDLabel(
            text="示例便签标题",
            font_size=t_state["font_size"],
            font_name=t_state["font"] or "Roboto",
            bold=t_state["bold"],
            adaptive_height=True,
            shorten=True,
            shorten_from="right",
        )
        if t_state["color"]:
            preview_title.theme_text_color = "Custom"
            preview_title.text_color = t_state["color"]
        else:
            preview_title.theme_text_color = "Primary"
        card_inner.add_widget(preview_title)

        # 标签行 — 直接存 label 引用
        chip_row = MDBoxLayout(orientation="horizontal", spacing=dp(4), adaptive_height=True)
        preview_chip_labels = []
        for tname in ["工作", "紧急"]:
            chip = MDCard(
                size_hint=(None, None),
                size=(dp(64), dp(26)),
                md_bg_color=(0.91, 0.45, 0.29, 0.2),
                radius=dp(8),
                padding=dp(2),
            )
            chip_label = MDLabel(
                text=tname,
                font_size=g_state["font_size"],
                font_name=g_state["font"] or "Roboto",
                bold=g_state["bold"],
                theme_text_color="Custom" if g_state["color"] else "Primary",
                text_color=g_state["color"] if g_state["color"] else (0, 0, 0, 0),
                halign="center",
                valign="center",
                adaptive_width=True,
                size_hint_y=None,
                height=dp(22),
            )
            chip_label.shorten = True
            chip_label.shorten_from = "right"
            chip_label.text_size = (dp(60), None)
            chip.add_widget(chip_label)
            preview_chip_labels.append(chip_label)
            chip_row.add_widget(chip)
        card_inner.add_widget(chip_row)

        preview_content = MDLabel(
            text="这是便签内容的预览文字，最多显示两行效果...",
            font_size=c_state["font_size"],
            font_name=c_state["font"] or "Roboto",
            bold=c_state["bold"],
            adaptive_height=True,
            max_lines=2,
            shorten=True,
            shorten_from="right",
        )
        if c_state["color"]:
            preview_content.theme_text_color = "Custom"
            preview_content.text_color = c_state["color"]
        else:
            preview_content.theme_text_color = "Secondary"
        card_inner.add_widget(preview_content)

        preview_card = MDCard(
            size_hint=(None, None),
            width=dp(320),
            padding=dp(12),
            elevation=2,
            radius=dp(12),
            md_bg_color=theme_cls.bg_normal,
        )
        preview_card.add_widget(card_inner)
        # 卡片高度跟随内容
        card_inner.bind(height=lambda _, h: setattr(preview_card, 'height', h + dp(24)))
        body.add_widget(preview_card)

        # ── 预览刷新 ──
        def _refresh_preview():
            preview_title.font_size = t_state["font_size"]
            preview_title.font_name = t_state["font"] or "Roboto"
            preview_title.bold = t_state["bold"]
            if t_state["color"]:
                preview_title.theme_text_color = "Custom"
                preview_title.text_color = t_state["color"]
            else:
                preview_title.theme_text_color = "Primary"
            for lbl in preview_chip_labels:
                lbl.font_size = g_state["font_size"]
                lbl.font_name = g_state["font"] or "Roboto"
                lbl.bold = g_state["bold"]
                if g_state["color"]:
                    lbl.theme_text_color = "Custom"
                    lbl.text_color = g_state["color"]
                else:
                    lbl.theme_text_color = "Primary"
            preview_content.font_size = c_state["font_size"]
            preview_content.font_name = c_state["font"] or "Roboto"
            preview_content.bold = c_state["bold"]
            if c_state["color"]:
                preview_content.theme_text_color = "Custom"
                preview_content.text_color = c_state["color"]
            else:
                preview_content.theme_text_color = "Secondary"

        # ── 可折叠样式区 ──
        def _make_collapsible_section(label_text, style_state):
            """创建可折叠区域。默认展开；折叠时保存高度以便恢复。"""
            from kivy.clock import Clock
            container = MDBoxLayout(orientation="vertical", spacing=dp(2), adaptive_height=True)
            header_btn = MDFlatButton(
                text=f"▼ {label_text}",
                size_hint_y=None,
                height=dp(36),
            )
            section_content = MDBoxLayout(orientation="vertical", spacing=dp(2), adaptive_height=True)
            section_content._expanded_height = None

            def _toggle(*_):
                if section_content.opacity:
                    section_content._expanded_height = section_content.height or section_content.minimum_height
                    section_content.opacity = 0
                    section_content.height = 0
                    header_btn.text = f"▶ {label_text}"
                else:
                    section_content.opacity = 1
                    header_btn.text = f"▼ {label_text}"
                    section_content.adaptive_height = False
                    section_content.height = section_content._expanded_height or 200
                    # 下一帧恢复 adaptive_height
                    Clock.schedule_once(lambda dt, sc=section_content: setattr(sc, 'adaptive_height', True), 0)

            header_btn.bind(on_release=_toggle)
            container.add_widget(header_btn)
            container.add_widget(section_content)
            body.add_widget(container)

            self._add_single_style_section(section_content, "", style_state, _refresh_preview, is_dark=is_dark)

        _make_collapsible_section("标题样式", t_state)
        _make_collapsible_section("标签样式", g_state)
        _make_collapsible_section("内容样式", c_state)

        scroll.add_widget(body)

        def _on_save(*_):
            self._save_style_dict(key, {
                "title": {
                    "color": list(t_state["color"]) if t_state["color"] else None,
                    "font_size": t_state["font_size"],
                    "font": t_state["font"],
                    "bold": t_state["bold"],
                },
                "tag": {
                    "color": list(g_state["color"]) if g_state["color"] else None,
                    "font_size": g_state["font_size"],
                    "font": g_state["font"],
                    "bold": g_state["bold"],
                },
                "content": {
                    "color": list(c_state["color"]) if c_state["color"] else None,
                    "font_size": c_state["font_size"],
                    "font": c_state["font"],
                    "bold": c_state["bold"],
                },
            })
            current_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
            if is_dark == current_dark:
                main_screen.refresh_list()
                dialog.dismiss()
                self._toast("便签卡片样式已保存")
            else:
                dialog.dismiss()
                self._toast("已保存，切换至对应模式可查看效果")

        dialog = MDDialog(
            title="编辑：便签卡片样式",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=_on_save),
            ],
        )
        dialog.open()
