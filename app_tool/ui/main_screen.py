"""主界面：便签列表 + FAB + 排序切换 + 用户名编辑。"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
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

    MDBoxLayout:
        orientation: "vertical"

        FloatLayout:
            size_hint_y: None
            height: dp(56)

            MDTopAppBar:
                id: top_bar
                type: "top"
                pos_hint: {"x": 0, "y": 0}
                size_hint: 1, 1

            MDBoxLayout:
                id: title_box
                orientation: "horizontal"
                spacing: 0
                adaptive_width: True
                adaptive_height: True
                pos_hint: {"center_x": 0.5, "center_y": 0.5}

                MDLabel:
                    id: username_btn
                    text: root.username or "某某"
                    font_style: "Subtitle2"
                    theme_text_color: "Custom"
                    text_color: (1, 0.85, 0.4, 1)
                    adaptive_width: True
                    size_hint_y: None
                    height: self.texture_size[1]
                    on_touch_down: if self.collide_point(*args[1].pos) and not self.disabled: root.edit_username()

                MDLabel:
                    text: "的专属便签本"
                    font_style: "Subtitle2"
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1)
                    adaptive_width: True
                    size_hint_y: None
                    height: self.texture_size[1]

            MDIconButton:
                id: undo_btn
                icon: "undo"
                size_hint: None, None
                size: dp(40), dp(40)
                pos_hint: {"right": 1, "center_y": 0.5}
                opacity: 0
                disabled: True
                theme_icon_color: "Custom"
                icon_color: (1, 0.85, 0.4, 1)
                on_release: root.undo_delete()

        MDBoxLayout:
            id: func_row
            orientation: "horizontal"
            size_hint_y: None
            height: dp(60)
            padding: dp(4), dp(4)
            spacing: dp(2)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(0)
                padding: dp(2)

                MDLabel:
                    id: func_sort_icon
                    text: "\U000F1549"
                    font_style: "Icon"
                    font_size: "28sp"
                    size_hint: None, None
                    size: dp(32), dp(32)
                    pos_hint: {"center_x": 0.5}
                    halign: "center"
                    valign: "center"
                    text_size: self.size
                    on_touch_down: if self.collide_point(*args[1].pos): root.toggle_sort_preference()

                MDLabel:
                    id: sort_label
                    text: "按更新时间"
                    font_style: "Caption"
                    halign: "center"
                    valign: "top"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(0)
                padding: dp(2)

                MDLabel:
                    text: "\U000F0349"
                    font_style: "Icon"
                    font_size: "28sp"
                    size_hint: None, None
                    size: dp(32), dp(32)
                    pos_hint: {"center_x": 0.5}
                    halign: "center"
                    valign: "center"
                    text_size: self.size
                    on_touch_down: if self.collide_point(*args[1].pos): root.open_search()

                MDLabel:
                    text: "便签检索"
                    font_style: "Caption"
                    halign: "center"
                    valign: "top"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(0)
                padding: dp(2)

                MDLabel:
                    text: "\U000F04FB"
                    font_style: "Icon"
                    font_size: "28sp"
                    size_hint: None, None
                    size: dp(32), dp(32)
                    pos_hint: {"center_x": 0.5}
                    halign: "center"
                    valign: "center"
                    text_size: self.size
                    on_touch_down: if self.collide_point(*args[1].pos): root.open_tag_manager()

                MDLabel:
                    text: "标签"
                    font_style: "Caption"
                    halign: "center"
                    valign: "top"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(18)

            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.25
                adaptive_height: True
                spacing: dp(0)
                padding: dp(2)

                MDLabel:
                    text: "\U000F0493"
                    font_style: "Icon"
                    font_size: "28sp"
                    size_hint: None, None
                    size: dp(32), dp(32)
                    pos_hint: {"center_x": 0.5}
                    halign: "center"
                    valign: "center"
                    text_size: self.size
                    on_touch_down: if self.collide_point(*args[1].pos): root.open_settings()

                MDLabel:
                    text: "设置"
                    font_style: "Caption"
                    halign: "center"
                    valign: "top"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(18)

        MDBoxLayout:
            id: search_bar
            orientation: "horizontal"
            size_hint_y: None
            height: 0
            padding: dp(8), dp(4)
            spacing: dp(8)

            MDLabel:
                id: search_label
                text: ""
                font_style: "Body2"
                adaptive_width: True
                size_hint_y: None
                height: dp(28)

            MDLabel:
                id: search_close_btn
                text: "取消 ✕"
                font_style: "Body2"
                theme_text_color: "Custom"
                text_color: (0.4, 0.8, 1, 1)
                adaptive_width: True
                size_hint_y: None
                height: dp(28)
                opacity: 0
                disabled: True
                on_touch_down: if self.collide_point(*args[1].pos) and not self.disabled: root.clear_search()

        ScrollView:
            id: scroll_view
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
    search_bar = ObjectProperty(None)
    search_label = ObjectProperty(None)
    completed_label = ObjectProperty(None)
    username = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._completed_expanded = False
        self._current_search_params: dict | None = None
        self._dragged_card: NoteCard | None = None
        self._ghost_card = None
        self._drag_touch_uid: int | None = None
        self._load_username()

    def on_enter(self, *args):
        self._update_theme_colors()
        self.refresh_list()
        self._update_sort_label()

    def _update_theme_colors(self):
        from kivymd.app import MDApp
        theme = MDApp.get_running_app().theme_cls
        self.md_bg_color = theme.bg_normal
        self.ids.func_row.md_bg_color = theme.bg_light
        self.ids.search_bar.md_bg_color = theme.bg_light
        if theme.theme_style == "Dark":
            self.ids.top_bar.md_bg_color = theme.bg_dark
        else:
            self.ids.top_bar.md_bg_color = theme.primary_color

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
            incomplete_notes = [n for n in notes if not n.is_completed]
            completed_notes = [n for n in notes if n.is_completed]
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

        self._update_undo_btn_visibility()
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
            on_drag_start=lambda c, touch: self._on_card_drag_start(c, touch),
        )
        return card

    def _on_card_drag_start(self, card: NoteCard, touch):
        """长按卡片开始拖拽排序 —— 幽灵卡方案，零布局重算。"""
        if self._dragged_card is not None:
            return
        if card.is_completed:
            self._toast("已完成便签不支持拖拽排序")
            return
        if card.parent is None:
            return

        self._toast("拖拽排序：拖动便签到目标位置后松手")

        touch.grab(self)
        self._drag_touch_uid = touch.uid

        # 原卡片变半透明 + 提升 elevation（零布局重算）
        card.opacity = 0.4
        card.elevation = 8
        self._dragged_card = card

        # 创建幽灵卡片（轻量占位卡，仅含标题文字）
        from kivymd.uix.card import MDCard
        ghost_bg = list(self.theme_cls.bg_normal)
        ghost_bg[3] = 0.92
        ghost = MDCard(
            size_hint=(None, None),
            size=(card.width, dp(48)),
            md_bg_color=ghost_bg,
            elevation=12,
            radius=(dp(12), dp(12), dp(12), dp(12)),
            padding=(dp(12), dp(8), dp(12), dp(8)),
        )
        ghost_label = MDLabel(
            text=card.note_title or "（无标题）",
            font_style="Subtitle1",
            bold=True,
            size_hint_y=None,
            height=dp(24),
            shorten=True,
            shorten_from="right",
        )
        ghost.add_widget(ghost_label)

        # 定位幽灵卡 — 初始位置在卡片中心
        card_center_w = card.to_window(card.width / 2, card.height / 2)
        card_center_self = self.to_widget(*card_center_w)
        ghost.center_x = card_center_self[0]
        ghost.center_y = card_center_self[1]

        self.add_widget(ghost)
        self._ghost_card = ghost

        self.ids.scroll_view.do_scroll = False

    def on_touch_move(self, touch):
        if self._ghost_card and touch.uid == self._drag_touch_uid:
            self._ghost_card.center_x = touch.x
            self._ghost_card.center_y = touch.y
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._dragged_card and self._ghost_card and touch.uid == self._drag_touch_uid:
            card = self._dragged_card
            ghost = self._ghost_card
            self._drag_touch_uid = None

            note_svc, _, _ = self._get_services()
            incomplete_box = self.ids.incomplete_box
            remaining_cards = [
                c for c in incomplete_box.children
                if isinstance(c, NoteCard) and c.note_id != card.note_id
            ]

            # 幽灵卡中心 Y — 统一走 to_window 确保在窗口坐标系比较
            ghost_wy = self.to_window(touch.x, touch.y)[1]

            def _card_wy(c):
                """卡片中心在窗口坐标系中的 Y。"""
                return c.to_window(c.width / 2, c.height / 2)[1]

            remaining_sorted = sorted(
                remaining_cards, key=_card_wy, reverse=True
            )

            new_order = []
            inserted = False
            for other in remaining_sorted:
                other_wy = _card_wy(other)
                if not inserted and ghost_wy > other_wy:
                    new_order.append(card.note_id)
                    inserted = True
                new_order.append(other.note_id)
            if not inserted:
                new_order.append(card.note_id)

            note_svc.rebalance_positions(new_order)

            # 恢复原卡片
            card.opacity = 1
            card.elevation = 2 if not card.is_completed else 0

            # 销毁幽灵卡片
            self.remove_widget(ghost)
            self._dragged_card = None
            self._ghost_card = None
            self.ids.scroll_view.do_scroll = True
            self.refresh_list()
            return True
        return super().on_touch_up(touch)

    def _toast(self, text: str):
        from kivymd.uix.label import MDLabel
        from kivymd.uix.snackbar import MDSnackbar

        MDSnackbar(
            MDLabel(text=text, font_style="Body2"),
            duration=2,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ).open()

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
            note_svc.delete(card.note_id)
            self.refresh_list()
            self._toast("应用未关闭的12小时内，可以撤销最近1条删除")

        dialog = build_confirm_dialog(
            title="删除便签",
            message="确认删除此便签吗？",
            on_confirm=on_confirm,
            confirm_text="确认删除",
        )
        dialog.open()

    # ── 撤销按钮 ──

    def _update_undo_btn_visibility(self):
        note_svc, _, _ = self._get_services()
        info = note_svc.get_undo_info()
        self.ids.undo_btn.opacity = 1 if info else 0
        self.ids.undo_btn.disabled = not bool(info)

    def undo_delete(self):
        note_svc, _, _ = self._get_services()
        note = note_svc.undo_delete()
        if note:
            self.refresh_list()
            self._toast("便签已恢复")

    # ── 排序 ──

    def _update_sort_label(self):
        note_svc, _, _ = self._get_services()
        current = note_svc._get_sort_preference()
        if current == "updated_at":
            self.ids.sort_label.text = "按更新时间"
            self.ids.func_sort_icon.text = "\U000F1549"
        else:
            self.ids.sort_label.text = "按创建时间"
            self.ids.func_sort_icon.text = "\U000F1547"

    def toggle_sort_preference(self):
        note_svc, _, _ = self._get_services()
        current = note_svc._get_sort_preference()
        new_pref = "created_at" if current == "updated_at" else "updated_at"
        note_svc.set_sort_preference(new_pref)
        self._update_sort_label()
        self.refresh_list()
        self._toast(f"排序切换：{self.ids.sort_label.text}")

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
                self.ids.search_close_btn.opacity = 1
                self.ids.search_close_btn.disabled = False
            else:
                self.ids.search_bar.height = 0
                self.ids.search_label.text = ""
                self.ids.search_close_btn.opacity = 0
                self.ids.search_close_btn.disabled = True
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
        self.ids.search_close_btn.opacity = 0
        self.ids.search_close_btn.disabled = True
        self.refresh_list()

    # ── 导航 ──

    def open_tag_manager(self):
        self.manager.current = "tags"

    def open_settings(self):
        self.manager.current = "settings"
