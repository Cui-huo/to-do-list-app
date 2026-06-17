"""标签管理页：CRUD + 置顶 + 批量删除。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.selectioncontrol import MDCheckbox

from app_tool.ui.dialogs import build_confirm_dialog
from app_tool.config import MAX_TAG_NAME_LENGTH

KV = """
<TagManagerScreen>:
    md_bg_color: (0.96, 0.96, 0.98, 1)

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: top_bar
            title: "标签管理"
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

                MDIconButton:
                    id: new_tag_btn
                    icon: "plus"
                    on_release: root.open_new_tag_dialog()

                MDIconButton:
                    id: batch_delete_btn
                    icon: "delete-sweep"
                    on_release: root.toggle_batch_mode()

        ScrollView:
            do_scroll_x: False

            MDBoxLayout:
                id: tag_list
                orientation: "vertical"
                spacing: dp(2)
                padding: dp(8)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True
"""

Builder.load_string(KV)


class TagManagerScreen(MDScreen):
    tag_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_mode = False
        self._selected_tags: set[str] = set()

    def on_enter(self, *args):
        self.refresh_list()

    def _get_services(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        return app.tag_service, app.note_service

    def _toast(self, text: str):
        snackbar = MDSnackbar()
        snackbar.text = text
        snackbar.open()

    def refresh_list(self):
        tag_svc, _ = self._get_services()
        tags = tag_svc.get_all()
        pinned = set(tag_svc.get_pinned())

        self.ids.tag_list.clear_widgets()

        if not tags:
            self.ids.tag_list.add_widget(MDLabel(
                text="暂无标签，点击右上角 + 创建",
                font_style="Body1",
                halign="center",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(200),
            ))
            return

        for tag in tags:
            row = self._build_tag_row(tag.name, tag.name in pinned)
            self.ids.tag_list.add_widget(row)

        if self._batch_mode:
            self._add_batch_confirm_button()

    def _build_tag_row(self, name: str, is_pinned: bool) -> MDBoxLayout:
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            padding=dp(8),
            spacing=dp(8),
        )

        if self._batch_mode:
            cb = MDCheckbox(
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                active=name in self._selected_tags,
            )
            cb.bind(active=lambda c, v, n=name: self._toggle_select(n, v))
            row.add_widget(cb)

        label = MDLabel(text=name, font_style="Body1", size_hint_x=0.5)
        row.add_widget(label)

        pin_icon = "pin" if is_pinned else "pin-outline"
        pin_color = (0.25, 0.32, 0.71, 1) if is_pinned else (0.5, 0.5, 0.5, 1)
        pin_btn = MDIconButton(
            icon=pin_icon,
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=pin_color,
        )
        pin_btn.bind(on_release=lambda b, n=name: self._toggle_pin(n))
        row.add_widget(pin_btn)

        rename_btn = MDIconButton(
            icon="pencil", size_hint=(None, None), size=(dp(36), dp(36))
        )
        rename_btn.bind(on_release=lambda b, n=name: self._open_rename_dialog(n))
        row.add_widget(rename_btn)

        delete_btn = MDIconButton(
            icon="delete",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Error",
        )
        delete_btn.bind(on_release=lambda b, n=name: self._confirm_delete_tag(n))
        row.add_widget(delete_btn)

        return row

    def go_back(self):
        self._batch_mode = False
        self._selected_tags.clear()
        self.manager.current = "main"

    # ── 新建标签 ──

    def open_new_tag_dialog(self):
        tag_svc, _ = self._get_services()

        text_field = MDTextField(
            mode="rectangle",
            max_text_length=MAX_TAG_NAME_LENGTH,
            hint_text="标签名称（1-10字符）",
            multiline=False,
        )

        def on_save():
            name = text_field.text.strip()
            if not name:
                self._toast("标签名不能为空")
                return
            try:
                tag_svc.create(name)
                dialog.dismiss()
                self.refresh_list()
                self._toast(f"标签「{name}」创建成功")
            except ValueError as e:
                self._toast(str(e))

        from kivymd.uix.boxlayout import MDBoxLayout
        content = MDBoxLayout(
            text_field,
            orientation="vertical",
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            height=dp(60),
        )

        dialog = MDDialog(
            title="新建标签",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="创建", on_release=lambda *_: on_save()),
            ],
        )
        dialog.open()

    # ── 重命名 ──

    def _open_rename_dialog(self, old_name: str):
        tag_svc, _ = self._get_services()

        text_field = MDTextField(
            mode="rectangle",
            text=old_name,
            max_text_length=MAX_TAG_NAME_LENGTH,
            hint_text="新标签名称（1-10字符）",
            multiline=False,
        )

        def on_save():
            new_name = text_field.text.strip()
            if not new_name:
                self._toast("标签名不能为空")
                return
            try:
                tag_svc.update(old_name, new_name)
                dialog.dismiss()
                self.refresh_list()
                self._toast(f"标签更名为「{new_name}」")
            except ValueError as e:
                self._toast(str(e))

        from kivymd.uix.boxlayout import MDBoxLayout
        content = MDBoxLayout(
            text_field,
            orientation="vertical",
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            height=dp(60),
        )

        dialog = MDDialog(
            title=f"重命名「{old_name}」",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="保存", on_release=lambda *_: on_save()),
            ],
        )
        dialog.open()

    # ── 置顶切换 ──

    def _toggle_pin(self, tag_name: str):
        tag_svc, _ = self._get_services()
        try:
            result = tag_svc.toggle_pinned(tag_name)
            self.refresh_list()
            status = "已置顶" if tag_name in result else "已取消置顶"
            self._toast(f"标签「{tag_name}」{status}")
        except ValueError as e:
            self._toast(str(e))

    # ── 删除标签 ──

    def _confirm_delete_tag(self, tag_name: str):
        def on_confirm():
            tag_svc, _ = self._get_services()
            try:
                tag_svc.delete(tag_name)
                self.refresh_list()
                self._toast(f"标签「{tag_name}」已删除")
            except ValueError as e:
                self._toast(str(e))

        dialog = build_confirm_dialog(
            title="删除标签",
            message=f"确认删除标签「{tag_name}」？将移除所有便签的此标签。",
            on_confirm=on_confirm,
            confirm_text="确认删除",
        )
        dialog.open()

    # ── 批量删除 ──

    def toggle_batch_mode(self):
        self._batch_mode = not self._batch_mode
        self._selected_tags.clear()
        self.ids.batch_delete_btn.icon = (
            "delete-sweep" if not self._batch_mode else "check"
        )
        self.refresh_list()

    def _add_batch_confirm_button(self):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            padding=dp(8),
            spacing=dp(8),
        )
        from kivymd.uix.button import MDRaisedButton
        btn = MDRaisedButton(
            text=f"删除选中 ({len(self._selected_tags)})",
            md_bg_color=(0.9, 0.2, 0.2, 1),
            size_hint_x=1,
        )
        btn.bind(on_release=lambda *_: self._execute_batch_delete())
        row.add_widget(btn)
        self.ids.tag_list.add_widget(row)

    def _toggle_select(self, name: str, active: bool):
        if active:
            self._selected_tags.add(name)
        else:
            self._selected_tags.discard(name)
        self.refresh_list()

    def _execute_batch_delete(self):
        if not self._selected_tags:
            return
        tag_svc, _ = self._get_services()

        def on_confirm():
            for name in list(self._selected_tags):
                try:
                    tag_svc.delete(name)
                except ValueError:
                    pass
            self._batch_mode = False
            self._selected_tags.clear()
            self.ids.batch_delete_btn.icon = "delete-sweep"
            self.refresh_list()
            self._toast("选中标签已删除")

        count = len(self._selected_tags)
        names = "、".join(list(self._selected_tags)[:3])
        if count > 3:
            names += f" 等{count}个标签"

        dialog = build_confirm_dialog(
            title="批量删除标签",
            message=f"确认删除以下标签？\n{names}\n将移除所有便签的对应标签。",
            on_confirm=on_confirm,
            confirm_text="确认删除",
        )
        dialog.open()
