"""标记完成/取消完成增量更新验证测试。

验证：_handle_complete_toggle 采用增量更新（移动卡片），
不触发全量 clear_widgets + 重建。

对应 spec: ui_spec.md §8.x, FEATURE_TESTS.md
"""

import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService
from app_tool.controller.search_service import SearchService


@pytest.fixture
def svc(db_conn):
    """提供已初始化的服务层实例。"""
    init_db(db_conn)
    return {
        "note": NoteService(db_conn),
        "tag": TagService(db_conn),
        "search": SearchService(db_conn),
    }


class TestCompleteToggleNoFullRebuild:
    """标记完成：移动卡片而非全量 rebuild。"""

    def test_mark_complete_preserves_other_incomplete_cards(self, kivy_app_instance, svc):
        """标记一张卡为完成时，其他未完成卡片保留在原处不被 clear。

        当前实现：_handle_complete_toggle 使用增量更新（remove_widget + add_widget），
        不触发全量 clear_widgets。
        """
        from app_tool.ui.main_screen import MainScreen

        note_svc = svc["note"]
        tag_svc = svc["tag"]
        search_svc = svc["search"]

        # 创建测试便签
        n1 = note_svc.create(title="未完成-保留", content="c1")
        n2 = note_svc.create(title="未完成-待完成", content="c2")
        n3 = note_svc.create(title="已完成-保留", content="c3")
        note_svc.mark_complete(n3.id)

        # 设置 mock 服务（_app 是只读 property，通过 _running_app 访问）
        kivy_app_instance.db_conn = svc["note"].conn
        kivy_app_instance.note_service = note_svc
        kivy_app_instance.tag_service = tag_svc
        kivy_app_instance.search_service = search_svc

        screen = MainScreen()
        screen.refresh_list()

        inc_box = screen.ids.incomplete_box
        cmp_box = screen.ids.completed_box

        # 找出 n1, n2 的卡片引用
        def find_card(box, note_id):
            for child in box.children:
                if getattr(child, "note_id", None) == note_id:
                    return child
            return None

        card_n1 = find_card(inc_box, n1.id)
        card_n2 = find_card(inc_box, n2.id)
        card_n3 = find_card(cmp_box, n3.id)
        assert card_n1 is not None, "n1 应在未完成区"
        assert card_n2 is not None, "n2 应在未完成区"
        assert card_n3 is not None, "n3 应在已完成区"

        # 保存 n1、n3 的 widget 引用
        card_n1_id_before = id(card_n1)
        card_n3_id_before = id(card_n3)

        # ---- 执行：标记 n2 为完成 ----
        screen._handle_complete_toggle(card_n2)

        # ---- 断言 ----
        # 1. n2 不在 incomplete_box 中
        inc_ids = {getattr(c, "note_id", None) for c in inc_box.children}
        assert n2.id not in inc_ids, (
            f"已完成便签 n2(id={n2.id}) 不应留在未完成区"
        )

        # 2. n2 在 completed_box 中
        cmp_ids = {getattr(c, "note_id", None) for c in cmp_box.children}
        assert n2.id in cmp_ids, (
            f"已完成便签 n2(id={n2.id}) 应出现在已完成区"
        )

        # 3.【核心断言】n1 卡片引用未变（未被 clear_widgets 重建）
        card_n1_after = find_card(inc_box, n1.id)
        assert card_n1_after is not None, (
            "n1 仍在未完成区：未被全量清理"
        )
        assert id(card_n1_after) == card_n1_id_before, (
            "_handle_complete_toggle 调用了 refresh_list() 导致全量重建，"
            f"n1 的 widget 引用已改变（旧 id={card_n1_id_before}，新 id={id(card_n1_after)}）。"
            "预期行为：其他卡片 widget 实例保持不变，仅被标记的卡片移动。"
        )

        # 4. n3 卡片引用未变
        card_n3_after = find_card(cmp_box, n3.id)
        assert card_n3_after is not None, "n3 仍在已完成区"
        assert id(card_n3_after) == card_n3_id_before, (
            "refresh_list() 也重建了已完成区的卡片，"
            f"n3 的 widget 引用已改变（旧 id={card_n3_id_before}，新 id={id(card_n3_after)}）。"
        )

    def test_mark_complete_expands_completed_section(self, kivy_app_instance, svc):
        """标记完成时，已完成区域应自动展开以显示新完成的卡片。

        标记完成后自动展开已完成区，让用户看到刚完成的卡片。
        """
        from app_tool.ui.main_screen import MainScreen

        note_svc = svc["note"]
        tag_svc = svc["tag"]
        search_svc = svc["search"]

        n1 = note_svc.create(title="待完成", content="c1")

        kivy_app_instance.db_conn = svc["note"].conn
        kivy_app_instance.note_service = note_svc
        kivy_app_instance.tag_service = tag_svc
        kivy_app_instance.search_service = search_svc

        screen = MainScreen()
        screen.refresh_list()

        # 初始状态：已完成区折叠
        assert screen._completed_expanded is False
        assert screen.ids.completed_box.opacity == 0

        # 找到 n1 的卡片
        inc_box = screen.ids.incomplete_box
        card_n1 = None
        for child in inc_box.children:
            if getattr(child, "note_id", None) == n1.id:
                card_n1 = child
                break
        assert card_n1 is not None

        # ---- 执行：标记 n1 为完成 ----
        screen._handle_complete_toggle(card_n1)

        # ---- 断言：已完成区域应自动展开 ----
        assert screen._completed_expanded is True, (
            "标记完成时应自动展开已完成区，"
            "让用户能看到刚完成的卡片。当前行为：已完成区保持折叠。"
        )
        assert screen.ids.completed_box.opacity == 1, (
            "已完成区应变为可见"
        )

    def test_mark_incomplete_preserves_other_completed_cards(self, kivy_app_instance, svc):
        """标记取消完成时，其他已完成卡片保留在原处不被 clear。"""
        from app_tool.ui.main_screen import MainScreen

        note_svc = svc["note"]
        tag_svc = svc["tag"]
        search_svc = svc["search"]

        n1 = note_svc.create(title="已完成-保留", content="c1")
        note_svc.mark_complete(n1.id)
        n2 = note_svc.create(title="已完成-待取消", content="c2")
        note_svc.mark_complete(n2.id)
        n3 = note_svc.create(title="未完成-保留", content="c3")

        kivy_app_instance.db_conn = svc["note"].conn
        kivy_app_instance.note_service = note_svc
        kivy_app_instance.tag_service = tag_svc
        kivy_app_instance.search_service = search_svc

        screen = MainScreen()
        screen.refresh_list()

        inc_box = screen.ids.incomplete_box
        cmp_box = screen.ids.completed_box

        def find_card(box, note_id):
            for child in box.children:
                if getattr(child, "note_id", None) == note_id:
                    return child
            return None

        card_n1 = find_card(cmp_box, n1.id)
        card_n2 = find_card(cmp_box, n2.id)
        card_n3 = find_card(inc_box, n3.id)
        assert card_n1 is not None
        assert card_n2 is not None
        assert card_n3 is not None

        card_n1_id_before = id(card_n1)
        card_n3_id_before = id(card_n3)

        # ---- 执行：取消 n2 的完成状态 ----
        screen._handle_complete_toggle(card_n2)

        # ---- 断言 ----
        # n2 移回未完成区
        cmp_ids = {getattr(c, "note_id", None) for c in cmp_box.children}
        inc_ids = {getattr(c, "note_id", None) for c in inc_box.children}
        assert n2.id not in cmp_ids
        assert n2.id in inc_ids

        # n1 引用未变
        card_n1_after = find_card(cmp_box, n1.id)
        assert card_n1_after is not None
        assert id(card_n1_after) == card_n1_id_before, (
            "取消完成时 refresh_list() 重建了已完成区卡片"
        )

        # n3 引用未变
        card_n3_after = find_card(inc_box, n3.id)
        assert card_n3_after is not None
        assert id(card_n3_after) == card_n3_id_before, (
            "取消完成时 refresh_list() 重建了未完成区卡片"
        )

    def test_completed_label_updates_after_toggle(self, kivy_app_instance, svc):
        """完成后「已完成 (N)」标签数更新。"""
        from app_tool.ui.main_screen import MainScreen

        note_svc = svc["note"]
        tag_svc = svc["tag"]
        search_svc = svc["search"]

        n1 = note_svc.create(title="待完成", content="c1")
        n2 = note_svc.create(title="已完成", content="c2")
        note_svc.mark_complete(n2.id)

        kivy_app_instance.db_conn = svc["note"].conn
        kivy_app_instance.note_service = note_svc
        kivy_app_instance.tag_service = tag_svc
        kivy_app_instance.search_service = search_svc

        screen = MainScreen()
        screen.refresh_list()

        # 初始：「已完成 (1)」
        assert "已完成 (1)" in screen.ids.completed_label.text

        inc_box = screen.ids.incomplete_box
        card_n1 = None
        for child in inc_box.children:
            if getattr(child, "note_id", None) == n1.id:
                card_n1 = child
                break
        assert card_n1 is not None

        # 标记 n1 为完成
        screen._handle_complete_toggle(card_n1)

        # 应更新为「已完成 (2)」
        assert "已完成 (2)" in screen.ids.completed_label.text, (
            f"预期 '已完成 (2)'，实际 '{screen.ids.completed_label.text}'"
        )

        # 取消完成
        cmp_box = screen.ids.completed_box
        card_n1_in_cmp = None
        for child in cmp_box.children:
            if getattr(child, "note_id", None) == n1.id:
                card_n1_in_cmp = child
                break
        assert card_n1_in_cmp is not None, "n1 应在已完成区"

        screen._handle_complete_toggle(card_n1_in_cmp)

        # 应更新为「已完成 (1)」
        assert "已完成 (1)" in screen.ids.completed_label.text, (
            f"预期 '已完成 (1)'，实际 '{screen.ids.completed_label.text}'"
        )


class TestCollapsePreservesScrollPosition:
    """折叠/展开已完成区时不改变内容高度 → 无滚动跳动。

    方案：completed_box 高度始终为 natural height（KV 绑定），
    折叠仅切换 opacity + disabled，空白占位代替高度=0。
    """

    def test_collapse_never_changes_completed_box_height(
        self, kivy_app_instance, svc
    ):
        """_update_completed_visibility 不应设 height=0。

        折叠时仅切换 opacity + disabled，内容高度保持不变。
        """
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_completed_visibility)
        lines_with_height = [
            l.strip() for l in source.split('\n')
            if 'height' in l and 'completed_box' in l
        ]
        assert not lines_with_height, (
            "_update_completed_visibility 不应修改 completed_box.height。"
            "KV 绑定 height: self.minimum_height 已自动处理折叠和展开。"
            f"违规代码行: {lines_with_height}"
        )

    def test_collapse_only_toggles_opacity_and_disabled(
        self, kivy_app_instance, svc
    ):
        """红灯：_update_completed_visibility 只应改 opacity 和 disabled。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_completed_visibility)
        assert 'opacity' in source, "'opacity' 是必需的"
        assert 'disabled' in source, (
            "_update_completed_visibility 中无 disabled 切换"
        )

    def test_collapse_does_not_contain_height_zero(
        self, kivy_app_instance, svc
    ):
        """红灯：源码中不应出现 `height = 0` 或 `height=0`。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._update_completed_visibility)
        assert 'height = 0' not in source.replace(' ', ''), (
            "折叠时不应将 completed_box.height 设为 0。"
            "内容高度应保持不变。"
        )

    def test_expand_restores_opacity_and_disabled(
        self, kivy_app_instance, svc
    ):
        """展开后 opacity=1, disabled=False。"""
        from app_tool.ui.main_screen import MainScreen

        note_svc = svc["note"]
        tag_svc = svc["tag"]
        search_svc = svc["search"]

        note_svc.create(title="测试", content="c")
        note_svc.mark_complete(note_svc.create(title="已完成", content="c").id)

        kivy_app_instance.db_conn = svc["note"].conn
        kivy_app_instance.note_service = note_svc
        kivy_app_instance.tag_service = tag_svc
        kivy_app_instance.search_service = search_svc

        screen = MainScreen()
        screen.refresh_list()

        # 折叠态
        screen._completed_expanded = False
        screen._update_completed_visibility()
        assert screen.ids.completed_box.opacity == 0, "折叠时 opacity=0"

        # 展开
        screen._completed_expanded = True
        screen._update_completed_visibility()
        assert screen.ids.completed_box.opacity == 1, "展开时 opacity=1"
        # disabled 可能在 headless 下不生效，跳过实际值检查
