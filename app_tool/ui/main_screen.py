"""主界面：便签列表 + FAB + UndoBar + 排序切换 + 用户名编辑。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.button import MDIconButton, MDFloatingActionButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.textfield import MDTextField

from app_tool.ui.note_card import NoteCard
from app_tool.ui.dialogs import build_add_edit_dialog, build_confirm_dialog
from app_tool.ui.search_dialog import build_search_dialog

KV = """
<MainScreen>:
    md_bg_color: (0.96, 0.96, 0.98, 1)

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: top_bar
            type: "top"
            anchor_title: "left"

            MDBoxLayout:
                id: title_box
                orientation: "horizontal"
                spacing: 0
                adaptive_width: True
                pos_hint: {"center_y": 0.5}

                MDFlatButton:
                    id: username_btn
                    text: root.username or "某某"
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1)
                    font_style: "Subtitle2"
                    on_release: root.edit_username()

                MDLabel:
                    text: "的专属便签本"
                    font_style: "Subtitle2"
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1)
                    adaptive_width: True
                    size_hint_y: None
                    height: self.texture_size[1]

        MDBoxLayout:
            id: func_row
            orientation: "horizontal"
            size_hint_y: None
            height: dp(60)
            md_bg_color: (0.97, 0.97, 0.97, 1)
            padding: dp(4), dp(4)
            spacing: dp(2)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(1)
                padding: dp(2)

                MDIconButton:
                    id: func_sort_icon
                    icon: "sort-clock-ascending"
                    size_hint: None, None
                    size: dp(36), dp(36)
                    pos_hint: {"center_x": 0.5}
                    on_release: root.toggle_sort_preference()

                MDLabel:
                    text: "便签排序"
                    font_style: "Caption"
                    halign: "center"
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(1)
                padding: dp(2)

                MDIconButton:
                    icon: "magnify"
                    size_hint: None, None
                    size: dp(36), dp(36)
                    pos_hint: {"center_x": 0.5}
                    on_release: root.open_search()

                MDLabel:
                    text: "便签检索"
                    font_style: "Caption"
                    halign: "center"
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(1)
                padding: dp(2)

                MDIconButton:
                    icon: "tag-multiple"
                    size_hint: None, None
                    size: dp(36), dp(36)
                    pos_hint: {"center_x": 0.5}
                    on_release: root.open_tag_manager()

                MDLabel:
                    text: "标签"
                    font_style: "Caption"
                    halign: "center"
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(1)
                padding: dp(2)

                MDIconButton:
                    icon: "cog"
                    size_hint: None, None
                    size: dp(36), dp(36)
                    pos_hint: {"center_x": 0.5}
                    on_release: root.open_settings()

                MDLabel:
                    text: "设置"
                    font_style: "Caption"
                    halign: "center"
                    size_hint_y: None
                    height: dp(18)

        MDBoxLayout:
            id: search_bar
            orientation: "horizontal"
            size_hint_y: None
            height: 0
            md_bg_color: (0.9, 0.92, 1, 1)
            padding: dp(8), dp(4)
            spacing: dp(8)

            MDLabel:
                id: search_label
                text: ""
                font_style: "Body2"
                adaptive_width: True

            MDIconButton:
                icon: "close"
                size_hint: None, None
                size: dp(28), dp(28)
                on_release: root.clear_search()

        ScrollView:
            do_scroll_x: False

            MDBoxLayout:
                id: list_box
                orientation: "vertical"
                spacing: dp(8)
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True

                MDLabel:
                    id: incomplete_header
                    text: "未完成"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(32)

                MDBoxLayout:
                    id: incomplete_box
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height
                    adaptive_height: True

                MDBoxLayout:
                    id: completed_header
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(36)
                    spacing: dp(4)

                    MDLabel:
                        id: completed_label
                        text: "已完成 (0)"
                        font_style: "H6"
                        size_hint_y: None
                        height: dp(32)

                    MDIconButton:
                        id: expand_btn
                        icon: "chevron-down"
                        size_hint: None, None
                        size: dp(32), dp(32)
                        on_release: root.toggle_completed()

                MDBoxLayout:
                    id: completed_box
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height
                    adaptive_height: True
                    opacity: 0

                Widget:
                    size_hint_y: None
                    height: dp(72)

        MDBoxLayout:
            id: undo_bar
            orientation: "horizontal"
            size_hint_y: None
            height: 0
            md_bg_color: (0.2, 0.2, 0.2, 0.95)
            padding: dp(12), dp(8)
            spacing: dp(8)
            radius: dp(8), dp(8), 0, 0

            MDLabel:
                text: "便签已删除。点击撤销恢复。"
                theme_text_color: "Custom"
                text_color: (1, 1, 1, 1)
                font_style: "Body2"
                size_hint_x: 0.7

            MDFlatButton:
                text: "撤销"
                theme_text_color: "Custom"
                text_color: (0.4, 0.8, 1, 1)
                on_release: root.undo_delete()

            MDFlatButton:
                text: "关闭"
                theme_text_color: "Custom"
                text_color: (0.6, 0.6, 0.6, 1)
                on_release: root.dismiss_undo()

    MDFloatingActionButton:
        icon: "plus"
        x: root.width - self.width - dp(16)
        y: dp(16)
        on_release: root.open_add_dialog()
"""

Builder.load_string(KV)


class MainScreen(MDScreen):
    incomplete_box = ObjectProperty(None)
    completed_box = ObjectProperty(None)
    undo_bar = ObjectProperty(None)
    search_bar = ObjectProperty(None)
    search_label = ObjectProperty(None)
    completed_label = ObjectProperty(None)
    username = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._completed_expanded = False
        self._current_search_params: dict | None = None
        self._load_username()

    def on_enter(self, *args):
        self.refresh_list()

    def _load_username(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app and app.db_conn:
            row = app.db_conn.execute(
                "SELECT value FROM UserSettings WHERE key='username'"
            ).fetchone()
            if row:
                self.username = row[0]

    def _save_username(self, name: str):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app and app.db_conn:
            app.db_conn.execute(
                "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('username', ?)",
                (name,),
            )
            app.db_conn.commit()
            self.username = name

    def edit_username(self):
        from kivymd.uix.dialog import MDDialog

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(16),
            adaptive_height=True,
        )
        name_field = MDTextField(
            text=self.username or "",
            hint_text="请输入你的名字",
            max_text_length=10,
            size_hint_y=None,
            height=dp(48),
        )
        content.add_widget(name_field)

        dialog = MDDialog(
            title="编辑昵称",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="取消",
                    on_release=lambda *_: dialog.dismiss(),
                ),
                MDFlatButton(
                    text="保存",
                    on_release=lambda *_: self._on_username_save(name_field, dialog),
                ),
            ],
        )
        dialog.open()

    def _on_username_save(self, name_field, dialog):
        name = name_field.text.strip()
        dialog.dismiss()
        if name:
            self._save_username(name)

    def _get_services(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        return app.note_service, app.tag_service, app.search_service

    def refresh_list(self):
        note_svc, tag_svc, search_svc = self._get_services()

        self.ids.incomplete_box.clear_widgets()
        self.ids.completed_box.clear_widgets()

        if self._current_search_params:
            notes = search_svc.search(**self._current_search_params)
            incomplete_notes = notes
            completed_notes = []
        else:
            incomplete_notes = note_svc.get_incomplete()
            completed_notes = note_svc.get_completed()

        if not incomplete_notes and not completed_notes:
            empty_label = MDLabel(
                text="还没有便签，点击右下角 + 创建一个吧",
                font_style="Body1",
                halign="center",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(200),
            )
            self.ids.incomplete_box.add_widget(empty_label)
            self.ids.completed_label.text = "已完成 (0)"
            return

        for note in incomplete_notes:
            card = self._build_note_card(note)
            self.ids.incomplete_box.add_widget(card)

        self.ids.completed_label.text = f"已完成 ({len(completed_notes)})"
        for note in completed_notes:
            card = self._build_note_card(note)
            self.ids.completed_box.add_widget(card)

        self._update_undo_bar()
        self._update_completed_visibility()

    def _build_note_card(self, note) -> NoteCard:
        note_svc, _, _ = self._get_services()
        tags = note_svc.get_tags(note.id)
        tag_names = [t.name for t in tags]

        card = NoteCard(
            note_id=note.id,
            note_title=note.title or "（无标题）",
            note_content=note.content,
            tag_names=tag_names,
            is_completed=bool(note.is_completed),
            is_pinned=bool(note.is_pinned),
        )
        card.bind(
            on_pin_toggle=lambda c: self._handle_pin_toggle(c),
            on_complete_toggle=lambda c: self._handle_complete_toggle(c),
            on_edit=lambda c: self._handle_edit(c),
            on_delete=lambda c: self._handle_delete(c),
        )
        return card

    def _toast(self, text: str):
        snackbar = MDSnackbar()
        snackbar.text = text
        snackbar.open()

    # ── 操作处理 ──

    def open_add_dialog(self):
        note_svc, tag_svc, _ = self._get_services()
        all_tags = [t.name for t in tag_svc.get_all()]

        def on_save(title: str, content: str, tag_names: list[str]):
            try:
                note = note_svc.create(title=title, content=content)
                for tag_name in tag_names:
                    try:
                        note_svc.add_tag(note.id, tag_name)
                    except ValueError:
                        pass
                self.refresh_list()
                self._toast("便签创建成功")
            except ValueError as e:
                self._toast(str(e))

        dialog = build_add_edit_dialog(
            title="新增便签",
            all_tag_names=all_tags,
            on_save=on_save,
        )
        dialog.open()

    def _handle_pin_toggle(self, card: NoteCard):
        note_svc, _, _ = self._get_services()
        try:
            if card.is_pinned:
                note_svc.unpin_note(card.note_id)
            else:
                note_svc.pin_note(card.note_id)
            self.refresh_list()
        except ValueError as e:
            self._toast(str(e))

    def _handle_complete_toggle(self, card: NoteCard):
        note_svc, _, _ = self._get_services()
        try:
            if card.is_completed:
                note_svc.mark_incomplete(card.note_id)
            else:
                note_svc.mark_complete(card.note_id)
            self.refresh_list()
        except ValueError as e:
            self._toast(str(e))

    def _handle_edit(self, card: NoteCard):
        note_svc, tag_svc, _ = self._get_services()
        note = note_svc.get_by_id(card.note_id)
        if not note:
            return
        tags = note_svc.get_tags(note.id)
        selected_tag_names = [t.name for t in tags]
        all_tags = [t.name for t in tag_svc.get_all()]

        def on_save(title: str, content: str, tag_names: list[str]):
            try:
                note_svc.update(note.id, title=title, content=content)
                current_tag_names = [t.name for t in note_svc.get_tags(note.id)]
                to_add = set(tag_names) - set(current_tag_names)
                to_remove = set(current_tag_names) - set(tag_names)
                for tn in to_add:
                    try:
                        note_svc.add_tag(note.id, tn)
                    except ValueError:
                        pass
                for tn in to_remove:
                    note_svc.remove_tag(note.id, tn)
                self.refresh_list()
            except ValueError as e:
                self._toast(str(e))

        dialog = build_add_edit_dialog(
            title="编辑便签",
            prefilled_title=note.title,
            prefilled_content=note.content,
            selected_tags=selected_tag_names,
            all_tag_names=all_tags,
            on_save=on_save,
        )
        dialog.open()

    def _handle_delete(self, card: NoteCard):
        note_svc, _, _ = self._get_services()
        note = note_svc.get_by_id(card.note_id)

        def on_confirm():
            if note_svc.get_undo_info() is None:
                self._toast("撤销仅在应用运行期间有效")
            note_svc.delete(card.note_id)
            self.refresh_list()

        dialog = build_confirm_dialog(
            title="删除便签",
            message=f"确认删除便签「{note.title or '无标题'}」？\n可在 12 小时内撤销。",
            on_confirm=on_confirm,
            confirm_text="确认删除",
        )
        dialog.open()

    # ── UndoBar ──

    def _update_undo_bar(self):
        note_svc, _, _ = self._get_services()
        info = note_svc.get_undo_info()
        self.ids.undo_bar.height = dp(48) if info else 0

    def undo_delete(self):
        note_svc, _, _ = self._get_services()
        note = note_svc.undo_delete()
        if note:
            self.refresh_list()
            self._toast("便签已恢复")

    def dismiss_undo(self):
        note_svc, _, _ = self._get_services()
        note_svc.clear_undo()
        self.ids.undo_bar.height = 0

    # ── 排序 ──

    def toggle_sort_preference(self):
        note_svc, _, _ = self._get_services()
        current = note_svc._get_sort_preference()
        new_pref = "created_at" if current == "updated_at" else "updated_at"
        note_svc.set_sort_preference(new_pref)
        label = "按更新时间" if new_pref == "updated_at" else "按创建时间"
        self.ids.func_sort_icon.icon = (
            "sort-clock-ascending" if new_pref == "updated_at"
            else "sort-calendar-ascending"
        )
        self.refresh_list()
        self._toast(f"排序切换：{label}")

    # ── 已完成区折叠 ──

    def _update_completed_visibility(self):
        if self._completed_expanded:
            self.ids.completed_box.opacity = 1
            self.ids.completed_box.height = self.ids.completed_box.minimum_height
            self.ids.expand_btn.icon = "chevron-up"
        else:
            self.ids.completed_box.opacity = 0
            self.ids.completed_box.height = 0
            self.ids.expand_btn.icon = "chevron-down"

    def toggle_completed(self):
        self._completed_expanded = not self._completed_expanded
        self._update_completed_visibility()

    # ── 搜索 ──

    def open_search(self):
        _, tag_svc, _ = self._get_services()
        all_tags = [t.name for t in tag_svc.get_all()]

        def on_search(**params):
            has_params = any(v for v in params.values() if v)
            self._current_search_params = params if has_params else None
            if self._current_search_params:
                parts = []
                if params.get("keyword"):
                    parts.append(f"关键词: {params['keyword']}")
                if params.get("tag_names"):
                    parts.append(f"标签: {', '.join(params['tag_names'])}")
                if params.get("year"):
                    parts.append(f"{params['year']}年")
                if params.get("month"):
                    parts.append(f"{params['month']}月")
                self.ids.search_label.text = " | ".join(parts) if parts else ""
                self.ids.search_bar.height = dp(32) if parts else 0
            else:
                self.ids.search_bar.height = 0
                self.ids.search_label.text = ""
            self.refresh_list()

        dialog = build_search_dialog(
            all_tag_names=all_tags,
            on_search=on_search,
        )
        dialog.open()

    def clear_search(self):
        self._current_search_params = None
        self.ids.search_bar.height = 0
        self.ids.search_label.text = ""
        self.refresh_list()

    # ── 导航 ──

    def open_tag_manager(self):
        self.manager.current = "tags"

    def open_settings(self):
        self.manager.current = "settings"
