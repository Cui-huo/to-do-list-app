"""红灯测试 — 排序切换 Toast 反馈（预期行为 vs 现状 gap）。

验证 ui_spec.md §8.3：排序切换时弹出可见 Toast。
当前代码 toggle_sort_preference() 无 Toast → 红灯。

对应 spec: ui_spec.md §8.3, FEATURE_TESTS.md CT-P0-07
"""

import json
import inspect
import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService


@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


# ═══════════════════════════════════════════════════════════
# 红灯-05：排序切换无 Toast 反馈
# ═══════════════════════════════════════════════════════════

class TestSortToggleToast:
    """预期：排序切换时弹出 Toast 提示。现状：无 Toast。"""

    def test_toggle_sort_preference_lacks_toast_call(self):
        """FIXME-RED：toggle_sort_preference() 源码中无 _toast 调用。

        当前代码只更新标签文字和图标，用户看不到排序切换的确认反馈。
        预期修复：方法末尾应调用 self._toast("按更新时间排序") 或
        self._toast("按创建时间排序")。
        """
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen.toggle_sort_preference)

        # FIXME-RED: 源码中应有 _toast 调用
        assert '_toast(' in source, (
            f"toggle_sort_preference() 缺少 _toast() 调用。\n"
            f"当前源码:\n{source}"
        )

    def test_sort_toggle_changes_preference_correctly(self, note_svc):
        """服务层：排序偏好切换本身工作正常（基础验证）。"""
        assert note_svc._get_sort_preference() == "updated_at"

        note_svc.set_sort_preference("created_at")
        assert note_svc._get_sort_preference() == "created_at"

        note_svc.set_sort_preference("updated_at")
        assert note_svc._get_sort_preference() == "updated_at"

    def test_sort_toggle_has_no_toast_side_effect(self, note_svc):
        """服务层：sort_preference 变更本身正确（Toast 缺失是 UI 层问题）。"""
        pref_before = note_svc._get_sort_preference()
        new_pref = "created_at" if pref_before == "updated_at" else "updated_at"

        note_svc.set_sort_preference(new_pref)
        pref_after = note_svc._get_sort_preference()

        assert pref_after == new_pref
        assert pref_after != pref_before

    def test_sort_preference_persists_as_json(self, note_svc, db_conn):
        """排序偏好持久化格式不变（回归保护）。"""
        note_svc.set_sort_preference("created_at")

        row = db_conn.execute(
            "SELECT value FROM UserSettings WHERE key='sort_preference'"
        ).fetchone()
        assert row["value"] == '"created_at"'
        assert json.loads(row["value"]) == "created_at"


# ═══════════════════════════════════════════════════════════
# 红灯-06：排序切换不应刷新标题栏/功能栏
# ═══════════════════════════════════════════════════════════

class TestSortToggleTitlebarStability:
    """预期：排序切换不引起标题栏/功能栏刷新。现状：_reorder_cards 更新了 completed_label。"""

    def test_reorder_cards_updates_completed_label_unnecessarily(self):
        """FIXME-RED：_reorder_cards() 无条件更新 completed_label.text。

        排序切换不应该引起标题栏区域（completed_label）的任何变化。
        当前 _reorder_cards() 中：
          self.ids.completed_label.text = f"已完成 ({len(completed_notes)})"
        即使文本值不变，也触发了 Kivy 属性变更事件和重新渲染。
        """
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._reorder_cards)

        # FIXME-RED: _reorder_cards 不应设置 completed_label.text
        # 该文本在排序前后没有变化，多余赋值触发不必要的 UI 渲染
        assert 'completed_label.text' not in source, (
            f"_reorder_cards() 不应更新 completed_label.text，"
            f"排序切换不应引起标题栏刷新。\n"
            f"当前源码包含 completed_label.text 赋值"
        )

    def test_toggle_sort_preference_does_not_call_refresh_list(self):
        """FIXME-RED：toggle_sort_preference 在无搜索参数时应走 _reorder_cards。

        当前有搜索参数时才走 refresh_list()（全量重建，会刷新标题栏），
        但无搜索参数时走 _reorder_cards()——验证这一点。
        """
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen.toggle_sort_preference)

        # 确认有搜索参数时走 refresh_list（当前行为，正确）
        assert 'refresh_list()' in source
        # 确认无搜索参数时走 _reorder_cards（当前行为，正确）
        assert '_reorder_cards()' in source
        # FIXME-RED: 但 _reorder_cards 内部不应刷新标题栏（见上一个测试）
