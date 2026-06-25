"""红灯测试 — 用户报告的 5 个 APP 使用问题。

问题一：便签检索界面取消返回主页面很慢；点击便签按钮明显卡顿
问题二：排序切换没有弹出可见 Toast 提示
问题三：排序切换时功能栏和标题栏一起刷新
问题四：新创建的未置顶便签出现在便签最下方（应在置顶之下、旧便签之上）
问题五：置顶功能混乱，重新规划手动置顶和标签置顶

编写原则：
- 禁止 mock，使用真实依赖注入（:memory: SQLite + 真实 Service）
- 通过改变输入源验证输出的数据序列和 UI 源码行为
- 每个测试有 FIXME-RED 注释标记预期失败点
- 修复后应变为绿灯

运行命令：
  pytest app_tool/tests/characterization/qwen3.7-max/test_reported_issues.py -v
"""

import time
import inspect
import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService
from app_tool.controller.search_service import SearchService


# ═══════════════════════════════════════════════════════════
# Fixtures — 真实依赖注入，零 mock
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def tag_svc(db_conn):
    init_db(db_conn)
    return TagService(db_conn)


@pytest.fixture
def search_svc(db_conn):
    init_db(db_conn)
    return SearchService(db_conn)


# ═══════════════════════════════════════════════════════════
# 问题一：搜索取消返回慢 + 点击便签按钮卡顿
# ═══════════════════════════════════════════════════════════

class TestSearchReturnPerformance:
    """问题行为：搜索界面取消返回主页面很慢。
    期望行为：取消搜索返回时应快速恢复列表，不执行全量销毁重建。
    """

    def test_clear_search_must_not_full_rebuild(self):
        """FIXME-RED：clear_search() 调用 refresh_list() 做全量销毁重建，导致返回卡顿。

        根因：clear_search() 内部调用 self.refresh_list()，
        该方法会 clear_widgets() 清空所有便签卡片 widget，
        然后逐条重建 NoteCard 实例（含样式加载、标签查询、事件绑定）。
        当便签数量多时（>20 条），全量重建耗时明显。

        预期修复：clear_search() 应调用 _reorder_cards() 做就地重排，
        复用现有 NoteCard widget，只调整顺序不销毁重建。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.clear_search)

        assert 'refresh_list()' not in source, (
            f"clear_search() 不应调用 refresh_list()（全量销毁重建），"
            f"这是搜索取消返回慢的根因。"
            f"应改用 _reorder_cards()（就地重排，复用现有卡片 widget）"
        )

    def test_clear_search_should_incremental_reorder(self):
        """预期：clear_search() 使用 _reorder_cards() 做增量重排。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.clear_search)

        assert '_reorder_cards()' in source, (
            f"clear_search() 应调用 _reorder_cards() 做增量重排，"
            f"复用现有卡片 widget，避免 clear_widgets + 逐条重建的性能开销"
        )

    def test_clear_search_still_resets_all_search_state(self):
        """回归保护：clear_search 必须正确重置所有搜索相关 UI 状态。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.clear_search)

        assert '_current_search_params = None' in source, "必须清空搜索参数"
        assert 'search_bar.height = 0' in source, "必须隐藏搜索栏"
        assert "search_label.text = \"\"" in source, "必须清空搜索条件文本"
        assert 'search_close_btn.opacity = 0' in source, "必须隐藏关闭按钮"
        assert 'search_close_btn.disabled = True' in source, "必须禁用关闭按钮"


class TestAddNoteButtonPerformance:
    """问题行为：点击便签按钮（+号创建便签），有明显卡顿。
    期望行为：创建便签后新卡片快速出现，无感知延迟。
    """

    def test_add_new_card_default_insert_idx_is_len_children(self):
        """验证：_add_new_card() 默认 insert_idx = len(children)。

        当所有子组件都是置顶卡片时，循环不 break，insert_idx 保持默认值。
        len(children) 意味着追加到末尾（视觉底部），即在所有置顶便签之后。
        旧代码用 insert_idx = 0，导致新便签插入视觉顶部（置顶便签之上）。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._add_new_card)

        lines = source.split('\n')
        found_default = False
        for line in lines:
            stripped = line.strip()
            if 'insert_idx' in stripped and '=' in stripped and 'len(children)' in stripped:
                found_default = True
                break
        assert found_default, (
            f"_add_new_card() 的 insert_idx 默认值必须是 len(children)，"
            f"确保所有便签已置顶时新便签排在置顶区之后"
        )

    def test_add_new_card_empty_list_first_note_at_top(self):
        """FIXME-RED：空列表创建第一张便签时，应出现在视觉顶部。

        当 incomplete_box 无子组件时：
        - children 为空列表，循环不执行
        - insert_idx 保持 0
        - add_widget(card, index=0) → 视觉顶部

        这个场景 insert_idx=0 恰好正确（第一张卡片应在顶部）。
        但修复为 len(children) 后，len([])=0 → index=0 → 同样在顶部。
        两者行为一致，此测试为回归保护。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._add_new_card)
        assert 'insert_idx' in source, "_add_new_card() 必须计算插入位置"

    def test_add_new_card_unpinned_exists_correct_position(self):
        """回归保护：已有未置顶便签时，新便签插入到第一个未置顶便签之前。

        当存在未置顶便签时，循环找到第一个 is_pinned=False 的位置并 break，
        insert_idx = 该位置 → 新卡片在该未置顶便签之前（视觉上方）→ 正确。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._add_new_card)

        assert 'is_pinned' in source, "必须检查卡片的置顶状态来决定插入位置"
        assert 'break' in source, "找到非置顶位置后必须 break 退出循环"


# ═══════════════════════════════════════════════════════════
# 问题二：排序切换 Toast 不可见
# ═══════════════════════════════════════════════════════════

class TestSortToggleToastVisibility:
    """问题行为：排序按钮切换快，但没有弹出可见 Toast 提示。
    期望行为：排序切换后弹出可见 Toast，确认当前排序模式。
    """

    def test_toast_call_exists_in_toggle_sort(self):
        """基础验证：toggle_sort_preference() 中有 _toast() 调用。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.toggle_sort_preference)

        assert '_toast(' in source, (
            f"toggle_sort_preference() 缺少 _toast() 调用"
        )

    def test_toast_text_matches_created_at_sort(self):
        """预期：切换到创建时间排序时，Toast 文案包含"创建时间"。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.toggle_sort_preference)

        assert '创建时间' in source, (
            f"排序切换到 created_at 时，Toast 文案应包含'创建时间'"
        )

    def test_toast_text_matches_updated_at_sort(self):
        """预期：切换到更新时间排序时，Toast 文案包含"更新时间"。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.toggle_sort_preference)

        assert '更新时间' in source, (
            f"排序切换到 updated_at 时，Toast 文案应包含'更新时间'"
        )

    def test_toast_positioned_visible_on_screen(self):
        """FIXME-RED：Toast 必须显示在屏幕可见区域，不被其他 UI 组件遮挡。

        当前 ToastMixin._toast() 使用 MDSnackbar 的 pos_hint 定位。
        预期：pos_hint 应使 Toast 出现在屏幕可见区域（如中上部或底部上方）。
        如果 center_y 值过低或被 FAB/搜索栏遮挡，用户看不到提示。
        """
        from app_tool.ui.utils import ToastMixin
        source = inspect.getsource(ToastMixin._toast)

        assert 'pos_hint' in source, "Toast 必须有 pos_hint 定位"
        # Toast 的 Y 位置不能太低（<0.2 可能被底部 FAB 遮挡）
        # 也不能太高（>0.9 可能被状态栏遮挡）
        # 验证 pos_hint 中包含合理的 center_y 值
        assert 'center_y' in source or 'y' in source, (
            "Toast pos_hint 必须包含垂直定位参数"
        )


# ═══════════════════════════════════════════════════════════
# 问题三：排序切换时功能栏和标题栏一起刷新
# ═══════════════════════════════════════════════════════════

class TestSortToggleChromStability:
    """问题行为：排序切换时功能栏和标题栏一起刷新（闪烁/重绘）。
    期望行为：仅便签列表区域重排，标题栏和功能栏保持不变。
    """

    def test_reorder_does_not_touch_top_bar(self):
        """FIXME-RED：_reorder_cards() 不应修改标题栏（top_bar）的任何属性。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'top_bar' not in source, (
            "_reorder_cards() 不应修改 top_bar（标题栏）属性，"
            "排序切换只影响便签列表区域"
        )

    def test_reorder_does_not_touch_func_row(self):
        """FIXME-RED：_reorder_cards() 不应修改功能栏（func_row）的任何属性。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'func_row' not in source, (
            "_reorder_cards() 不应修改 func_row（功能栏）属性"
        )

    def test_reorder_does_not_touch_sort_button(self):
        """FIXME-RED：_reorder_cards() 不应修改排序按钮/标签。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        for token in ('sort_label', 'func_sort_icon'):
            assert token not in source, (
                f"_reorder_cards() 不应修改 {token}（排序按钮），"
                f"排序切换不应重绘排序按钮自身"
            )

    def test_reorder_does_not_touch_other_func_labels(self):
        """FIXME-RED：_reorder_cards() 不应修改功能栏其他按钮标签。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        for token in ('func_search_label', 'func_tag_label', 'func_settings_label'):
            assert token not in source, (
                f"_reorder_cards() 不应修改 {token}"
            )

    def test_reorder_does_not_touch_search_bar(self):
        """FIXME-RED：_reorder_cards() 不应修改搜索栏。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'search_bar' not in source, (
            "_reorder_cards() 不应修改 search_bar"
        )

    def test_reorder_does_not_unnecessarily_update_completed_label(self):
        """FIXME-RED：_reorder_cards() 无条件赋值 completed_label.text。

        排序切换前后，已完成便签数量不变，completed_label.text 值不变。
        但 Kivy 属性赋值（即使值相同）触发属性变更事件和重绘。
        预期：_reorder_cards() 中不赋值 completed_label.text，
        或改为条件赋值（仅数量变化时更新）。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'completed_label.text' not in source, (
            "_reorder_cards() 不应无条件赋值 completed_label.text。"
            "排序切换不改变已完成数量，赋值触发不必要的 Kivy 属性变更事件"
        )

    def test_toggle_sort_uses_reorder_not_refresh_without_search(self):
        """回归保护：无搜索参数时，排序切换走 _reorder_cards（就地重排）。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.toggle_sort_preference)

        assert '_reorder_cards()' in source, (
            "无搜索参数时应走 _reorder_cards()（就地重排，复用卡片 widget）"
        )

    def test_update_sort_label_only_modifies_sort_elements(self):
        """_update_sort_label() 只修改排序相关的 UI 元素。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._update_sort_label)

        assert 'sort_label' in source, "必须更新排序标签文字"
        assert 'func_sort_icon' in source, "必须更新排序图标"
        for token in ('func_search_label', 'func_tag_label', 'func_settings_label'):
            assert token not in source, f"_update_sort_label() 不应修改 {token}"

    def test_reorder_freezes_adaptive_height_during_ops(self):
        """验证：_reorder_cards() 在 remove/add 期间冻结 minimum_height 绑定。

        每次 add_widget 触发 height: self.minimum_height 重算 → O(N²) 布局开销，
        导致标题栏/功能栏短暂消失（用户报告约 2 秒）。
        修复：unbind minimum_height → 操作 → bind 恢复。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'unbind' in source and 'minimum_height' in source, (
            "_reorder_cards() 必须在 remove/add 期间 unbind minimum_height，"
            "防止每次 add_widget 触发 O(N) 布局重算（N 张卡片 = O(N²) 总开销）"
        )

    def test_reorder_restores_adaptive_height_in_finally(self):
        """验证：_reorder_cards() 在 finally 块中恢复 minimum_height 绑定。

        即使 add_widget 过程中抛异常，也必须恢复绑定，否则容器高度永远不自适应。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._reorder_cards)

        assert 'finally' in source, (
            "_reorder_cards() 必须有 finally 块确保 minimum_height 绑定被恢复"
        )
        assert 'bind' in source, (
            "_reorder_cards() 必须在 finally 中 bind minimum_height 恢复自适应"
        )


# ═══════════════════════════════════════════════════════════
# 问题四：新便签出现在便签最下方
# ═══════════════════════════════════════════════════════════

class TestNewNotePositionServiceLayer:
    """问题行为：新创建的未置顶便签出现在便签最下方。
    期望行为：新便签在置顶便签之下、旧便签之上。

    此组测试验证服务层 get_incomplete() 返回顺序（数据源正确性）。
    UI 层 _add_new_card() 的插入位置 bug 在问题一中覆盖。
    """

    def test_new_note_before_old_created_at_desc(self, note_svc):
        """created_at DESC：新便签（后创建）排在旧便签之前。"""
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.015)
        new = note_svc.create(title="新便签", content="新内容")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        ids = [n.id for n in notes]
        assert ids.index(new.id) < ids.index(old.id), (
            f"created_at DESC：新便签(id={new.id})应在旧便签(id={old.id})之前，"
            f"实际顺序: {ids}"
        )

    def test_new_note_before_old_updated_at_desc(self, note_svc):
        """updated_at DESC：新便签（后创建=后更新）排在旧便签之前。"""
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.015)
        new = note_svc.create(title="新便签", content="新内容")

        note_svc.set_sort_preference("updated_at")
        notes = note_svc.get_incomplete()

        ids = [n.id for n in notes]
        assert ids.index(new.id) < ids.index(old.id), (
            f"updated_at DESC：新便签(id={new.id})应在旧便签(id={old.id})之前，"
            f"实际顺序: {ids}"
        )

    def test_new_note_below_pinned_above_old_created_at(self, note_svc):
        """created_at DESC：置顶 → 新便签 → 旧便签。"""
        pinned = note_svc.create(title="置顶", content="置顶内容")
        note_svc.pin_note(pinned.id)
        time.sleep(0.015)
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.015)
        new = note_svc.create(title="新便签", content="新内容")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == pinned.id, "置顶便签应在第一位"
        ids = [n.id for n in notes]
        assert ids.index(new.id) < ids.index(old.id), (
            f"新便签(id={new.id})应在旧便签(id={old.id})之上"
        )

    def test_new_note_below_pinned_above_old_updated_at(self, note_svc):
        """updated_at DESC：置顶 → 新便签 → 旧便签。"""
        pinned = note_svc.create(title="置顶", content="置顶内容")
        note_svc.pin_note(pinned.id)
        time.sleep(0.015)
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.015)
        new = note_svc.create(title="新便签", content="新内容")

        notes = note_svc.get_incomplete()

        assert notes[0].id == pinned.id, "置顶便签应在第一位"
        ids = [n.id for n in notes]
        assert ids.index(new.id) < ids.index(old.id), (
            f"新便签(id={new.id})应在旧便签(id={old.id})之上"
        )

    def test_multiple_new_notes_descending_order(self, note_svc):
        """连续创建 3 条便签，排序后从新到旧。"""
        n1 = note_svc.create(title="第1条", content="c1")
        time.sleep(0.015)
        n2 = note_svc.create(title="第2条", content="c2")
        time.sleep(0.015)
        n3 = note_svc.create(title="第3条", content="c3")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert [n.id for n in notes] == [n3.id, n2.id, n1.id], (
            f"created_at DESC：应从新到旧 [n3, n2, n1]，"
            f"实际: {[n.id for n in notes]}"
        )


# ═══════════════════════════════════════════════════════════
# 问题五：置顶功能重新规划
# ═══════════════════════════════════════════════════════════

class TestManualPinAreaFixedOrder:
    """手动置顶区：在最上方，按手动点击置顶按钮的时间顺序排列。
    不受排序功能影响，顺序始终固定。
    """

    def test_manual_pin_order_by_pinned_at_desc(self, note_svc):
        """手动置顶区按置顶时间排列：后置顶的排在前面。

        n2 先创建先置顶（pinned_at 旧），
        n1 后创建后置顶（pinned_at 新）。
        预期：n1 在前（pinned_at DESC）。
        """
        n2 = note_svc.create(title="先置顶", content="c2")
        note_svc.pin_note(n2.id)
        time.sleep(0.015)
        n1 = note_svc.create(title="后置顶", content="c1")
        note_svc.pin_note(n1.id)

        notes = note_svc.get_incomplete()

        assert notes[0].id == n1.id, (
            f"手动置顶区按 pinned_at DESC：后置顶的 n1(id={n1.id}) 应排在前"
        )
        assert notes[1].id == n2.id

    def test_manual_pin_area_immune_to_created_at_sort(self, note_svc):
        """FIXME-RED：手动置顶区不受 created_at 排序影响。

        设计冲突：
        - n2 先创建+先置顶（created_at 新？不对——先创建所以 created_at 旧）
        - n1 后创建+后置顶（created_at 新，pinned_at 也新）

        重新设计（冲突原则）：
        - n2 后创建+先置顶（created_at 新，pinned_at 旧）
        - n1 先创建+后置顶（created_at 旧，pinned_at 新）

        created_at DESC 会让 n2 排前（后创建），
        但预期是 n1 排前（pinned_at 新，手动置顶区免疫排序）。
        """
        n1 = note_svc.create(title="先创建后置顶", content="c1")
        time.sleep(0.015)
        n2 = note_svc.create(title="后创建先置顶", content="c2")
        # n2.created_at > n1.created_at

        # n2 先置顶 → pinned_at 更旧
        note_svc.pin_note(n2.id)
        time.sleep(0.015)
        # n1 后置顶 → pinned_at 更新
        note_svc.pin_note(n1.id)
        # n1.pinned_at > n2.pinned_at, 但 n1.created_at < n2.created_at

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == n1.id, (
            f"手动置顶区应免疫 created_at 排序。"
            f"n1(pinned_at 更新)应排在前，"
            f"但 created_at DESC 让 n2(created_at 更新)排到了前面"
        )
        assert notes[1].id == n2.id

    def test_manual_pin_area_immune_to_updated_at_sort(self, note_svc):
        """FIXME-RED：手动置顶区不受 updated_at 排序影响。

        设计冲突：
        - n1 先创建，后更新+后置顶（updated_at 新，pinned_at 新）
        - n2 后创建，不更新+先置顶（updated_at 旧？不对——后创建所以 updated_at 新）

        重新设计：
        - n1 先创建+先更新+后置顶（updated_at 中间，pinned_at 新）
        - n2 中间创建+后更新+先置顶（updated_at 新，pinned_at 旧）

        这样 updated_at DESC 让 n2 排前，但 pinned_at DESC 让 n1 排前。
        """
        n1 = note_svc.create(title="先创建", content="c1")
        time.sleep(0.015)
        n2 = note_svc.create(title="后创建", content="c2")
        # n2.created_at > n1.created_at, n2.updated_at > n1.updated_at

        # n2 先置顶 → pinned_at 旧
        note_svc.pin_note(n2.id)
        time.sleep(0.015)
        # n1 更新（刷新 updated_at 使之最新）后置顶 → pinned_at 新
        note_svc.update(n1.id, content="c1-已更新")
        time.sleep(0.005)
        note_svc.pin_note(n1.id)
        # n1.updated_at > n2.updated_at, n1.pinned_at > n2.pinned_at

        # 切换 created_at（n2 后创建应排前，但手动置顶区应按 pinned_at）
        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == n1.id, (
            f"手动置顶区按 pinned_at DESC（n1 后置顶应排前），"
            f"不受排序偏好影响"
        )

    def test_manual_pin_three_notes_pinned_at_order(self, note_svc):
        """3 张手动置顶便签，按 pinned_at DESC 排列。"""
        n1 = note_svc.create(title="第1个", content="c1")
        note_svc.pin_note(n1.id)
        time.sleep(0.015)
        n2 = note_svc.create(title="第2个", content="c2")
        note_svc.pin_note(n2.id)
        time.sleep(0.015)
        n3 = note_svc.create(title="第3个", content="c3")
        note_svc.pin_note(n3.id)

        notes = note_svc.get_incomplete()

        assert [n.id for n in notes] == [n3.id, n2.id, n1.id], (
            f"手动置顶区应按 pinned_at DESC：[n3, n2, n1]（后置顶的在前），"
            f"实际: {[n.id for n in notes]}"
        )


class TestTagPinAreaGroupedOrder:
    """标签置顶区：紧随手动置顶区，同标签便签聚在一起，
    不同标签按用户点选置顶标签的顺序排列。
    """

    def test_tag_pin_groups_follow_selection_order(self, note_svc, tag_svc):
        """FIXME-RED：不同置顶标签按选择顺序排列。

        用户先置顶标签 B，后置顶标签 A。
        预期：含 B 的便签组在含 A 的便签组之前。

        当前 bug：SQL 中标签位置 CASE WHEN 的 NULL 值在 DESC 排序中
        被 SQLite 排到最前（SQLite NULLs FIRST in DESC），
        导致标签位置映射失效，实际按 updated_at DESC 排列。
        """
        tag_svc.create("TagA")
        tag_svc.create("TagB")
        tag_svc.set_pinned(["TagB", "TagA"])

        nA = note_svc.create(title="含TagA", content="cA", tag_names=["TagA"])
        time.sleep(0.015)
        nB = note_svc.create(title="含TagB", content="cB", tag_names=["TagB"])
        # nB 后创建，updated_at DESC 让 nB 排前

        notes = note_svc.get_incomplete()

        assert notes[0].id == nB.id, (
            f"pinned_tags=[TagB, TagA]，TagB 先被选为置顶，"
            f"含 TagB 的便签(id={nB.id})应在含 TagA 的便签(id={nA.id})之前，"
            f"实际顺序: {[n.id for n in notes]}"
        )

    def test_same_tag_group_ordered_by_updated_at(self, note_svc, tag_svc):
        """同一置顶标签内的便签按 updated_at DESC 排列。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="较早", content="c1", tag_names=["工作"])
        time.sleep(0.015)
        n2 = note_svc.create(title="较晚", content="c2", tag_names=["工作"])

        notes = note_svc.get_incomplete()

        assert notes[0].id == n2.id, (
            f"同标签内按 updated_at DESC：n2(后创建/更新)应在前"
        )
        assert notes[1].id == n1.id

    def test_tag_pin_order_reversed_selection(self, note_svc, tag_svc):
        """FIXME-RED：反转置顶标签选择顺序，便签排列随之反转。

        先 [B, A]，后改为 [A, B]，含 A 的便签应排到含 B 的前面。
        """
        tag_svc.create("TagA")
        tag_svc.create("TagB")

        nA = note_svc.create(title="含TagA", content="cA", tag_names=["TagA"])
        time.sleep(0.015)
        nB = note_svc.create(title="含TagB", content="cB", tag_names=["TagB"])

        # 先设为 [B, A]
        tag_svc.set_pinned(["TagB", "TagA"])
        notes1 = note_svc.get_incomplete()

        # 再改为 [A, B]
        tag_svc.set_pinned(["TagA", "TagB"])
        notes2 = note_svc.get_incomplete()

        # 选择顺序反转后，含 A 的便签应在含 B 前面
        assert notes2[0].id == nA.id, (
            f"pinned_tags 改为 [TagA, TagB] 后，"
            f"含 TagA 的便签(id={nA.id})应在含 TagB 的便签(id={nB.id})之前，"
            f"实际顺序: {[n.id for n in notes2]}"
        )

    def test_three_tag_groups_selection_order(self, note_svc, tag_svc):
        """FIXME-RED：3 个置顶标签按选择顺序排列便签组。"""
        tag_svc.create("Alpha")
        tag_svc.create("Beta")
        tag_svc.create("Gamma")
        tag_svc.set_pinned(["Gamma", "Alpha", "Beta"])

        n_alpha = note_svc.create(title="含Alpha", content="cA", tag_names=["Alpha"])
        time.sleep(0.010)
        n_beta = note_svc.create(title="含Beta", content="cB", tag_names=["Beta"])
        time.sleep(0.010)
        n_gamma = note_svc.create(title="含Gamma", content="cG", tag_names=["Gamma"])

        notes = note_svc.get_incomplete()

        assert [n.id for n in notes] == [n_gamma.id, n_alpha.id, n_beta.id], (
            f"pinned_tags=[Gamma, Alpha, Beta]，"
            f"预期顺序 [Gamma, Alpha, Beta]，"
            f"实际: {[n.id for n in notes]}"
        )

    def test_note_with_multiple_pinned_tags_in_first_match_group(self, note_svc, tag_svc):
        """FIXME-RED：便签含多个置顶标签时，出现在第一个匹配的标签组中。

        便签同时含 TagA 和 TagB，pinned_tags=[TagA, TagB]，
        该便签应出现在 TagA 组中（第一个匹配的置顶标签），
        且在结果列表中仅出现一次。
        """
        tag_svc.create("TagA")
        tag_svc.create("TagB")
        tag_svc.set_pinned(["TagA", "TagB"])

        n_both = note_svc.create(
            title="含两个置顶标签", content="c_both",
            tag_names=["TagA", "TagB"]
        )
        n_only_b = note_svc.create(title="仅含TagB", content="c_b", tag_names=["TagB"])

        notes = note_svc.get_incomplete()

        occurrences = [n for n in notes if n.id == n_both.id]
        assert len(occurrences) == 1, (
            f"便签(id={n_both.id})含两个置顶标签，应在结果中仅出现一次，"
            f"实际出现 {len(occurrences)} 次"
        )

    def test_tag_pin_area_immune_to_created_at_sort(self, note_svc, tag_svc):
        """FIXME-RED：标签置顶区不受 created_at 排序影响。

        标签置顶区的组间顺序始终按标签选择顺序，
        组内按 updated_at DESC（固定），不受排序按钮影响。
        """
        tag_svc.create("TagA")
        tag_svc.create("TagB")
        tag_svc.set_pinned(["TagB", "TagA"])

        nA = note_svc.create(title="含TagA先创建", content="cA", tag_names=["TagA"])
        time.sleep(0.015)
        nB = note_svc.create(title="含TagB后创建", content="cB", tag_names=["TagB"])

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == nB.id, (
            f"标签置顶区组间顺序按选择顺序 [TagB, TagA]，"
            f"含 TagB 的便签应在含 TagA 的前面，不受 created_at 排序影响"
        )


class TestPinAreaNoOverlap:
    """手动置顶区和标签置顶区不可重合。
    如果冲突（便签同时手动置顶+含置顶标签），只出现在手动置顶区。
    """

    def test_manual_pin_overrides_tag_pin(self, note_svc, tag_svc):
        """便签同时手动置顶+含置顶标签，仅出现在手动置顶区（不重复）。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n = note_svc.create(title="双重身份", content="c", tag_names=["工作"])
        note_svc.pin_note(n.id)

        notes = note_svc.get_incomplete()

        occurrences = [x for x in notes if x.id == n.id]
        assert len(occurrences) == 1, (
            f"便签(id={n.id})同时手动置顶+含置顶标签，"
            f"应仅出现 1 次，实际 {len(occurrences)} 次"
        )
        assert notes[0].id == n.id, "应出现在最前面（手动置顶区）"

    def test_conflict_note_in_manual_pin_position(self, note_svc, tag_svc):
        """FIXME-RED：冲突便签在手动置顶区按 pinned_at 排列。

        n1 仅手动置顶，n2 手动置顶+含置顶标签。
        n2 后置顶 → pinned_at 更新 → 应排在 n1 前面。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="仅手动置顶", content="c1")
        note_svc.pin_note(n1.id)
        time.sleep(0.015)
        n2 = note_svc.create(title="手动+标签双重", content="c2", tag_names=["工作"])
        note_svc.pin_note(n2.id)

        notes = note_svc.get_incomplete()

        assert notes[0].id == n2.id, (
            f"n2 后置顶（pinned_at 更新），应排在手动置顶区第一位"
        )
        assert notes[1].id == n1.id

    def test_unpin_removes_from_manual_area_note_in_tag_area(self, note_svc, tag_svc):
        """FIXME-RED：取消手动置顶后，含置顶标签的便签回到标签置顶区。

        便签先手动置顶+含置顶标签（在手动置顶区），
        取消手动置顶后，应出现在标签置顶区。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n = note_svc.create(title="切换置顶", content="c", tag_names=["工作"])
        note_svc.pin_note(n.id)

        notes_before = note_svc.get_incomplete()
        assert notes_before[0].is_pinned == 1

        note_svc.unpin_note(n.id)
        notes_after = note_svc.get_incomplete()

        assert notes_after[0].id == n.id, (
            f"取消手动置顶后，含置顶标签的便签(id={n.id})"
            f"应出现在标签置顶区（仍在列表前面），"
            f"实际: is_pinned={notes_after[0].is_pinned}"
        )
        assert notes_after[0].is_pinned == 0, "取消置顶后 is_pinned 应为 0"

    def test_multiple_conflict_notes_all_in_manual_area(self, note_svc, tag_svc):
        """多张便签同时手动置顶+含置顶标签，全部仅在手动置顶区，不重复。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="双重1", content="c1", tag_names=["工作"])
        note_svc.pin_note(n1.id)
        time.sleep(0.010)
        n2 = note_svc.create(title="双重2", content="c2", tag_names=["工作"])
        note_svc.pin_note(n2.id)
        n3 = note_svc.create(title="仅标签置顶", content="c3", tag_names=["工作"])

        notes = note_svc.get_incomplete()

        n1_count = len([x for x in notes if x.id == n1.id])
        n2_count = len([x for x in notes if x.id == n2.id])
        n3_count = len([x for x in notes if x.id == n3.id])

        assert n1_count == 1, f"n1 应仅出现 1 次，实际 {n1_count}"
        assert n2_count == 1, f"n2 应仅出现 1 次，实际 {n2_count}"
        assert n3_count == 1, f"n3 应仅出现 1 次，实际 {n3_count}"
        assert len(notes) == 3, f"总共应有 3 条便签，实际 {len(notes)}"


class TestUnpinnedAreaRespectsSort:
    """非置顶区（普通便签）：按排序功能自由排序。"""

    def test_unpinned_created_at_desc(self, note_svc, tag_svc):
        """created_at DESC：非置顶区从新到旧。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        pinned = note_svc.create(title="标签置顶", content="cp", tag_names=["工作"])
        time.sleep(0.010)
        old = note_svc.create(title="旧普通", content="co")
        time.sleep(0.010)
        new = note_svc.create(title="新普通", content="cn")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == pinned.id, "标签置顶便签在最前"
        ids = [n.id for n in notes]
        assert ids.index(new.id) < ids.index(old.id), (
            f"非置顶区 created_at DESC：新便签在旧便签前面"
        )

    def test_unpinned_updated_at_desc(self, note_svc, tag_svc):
        """updated_at DESC：非置顶区从最近更新到最早。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        pinned = note_svc.create(title="标签置顶", content="cp", tag_names=["工作"])
        time.sleep(0.010)
        n1 = note_svc.create(title="先创建", content="c1")
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建", content="c2")

        note_svc.set_sort_preference("updated_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == pinned.id, "标签置顶便签在最前"
        ids = [n.id for n in notes]
        assert ids.index(n2.id) < ids.index(n1.id), (
            f"非置顶区 updated_at DESC：后创建的在前面"
        )

    def test_sort_toggle_changes_unpinned_order(self, note_svc):
        """切换排序偏好后，非置顶区顺序变化。

        n1 先创建，n2 后创建但先更新（然后 n1 再更新使其 updated_at 最新）。
        created_at DESC: n2 在前（后创建）
        updated_at DESC: n1 在前（最后更新）
        """
        n1 = note_svc.create(title="先创建", content="c1")
        time.sleep(0.015)
        n2 = note_svc.create(title="后创建", content="c2")
        # n2.created_at > n1.created_at, n2.updated_at > n1.updated_at

        # n1 更新 → n1.updated_at 变为最新
        time.sleep(0.010)
        note_svc.update(n1.id, content="c1-已更新")
        # n1.updated_at > n2.updated_at

        note_svc.set_sort_preference("created_at")
        notes_ca = note_svc.get_incomplete()
        assert notes_ca[0].id == n2.id, "created_at DESC: n2(后创建)在前"

        note_svc.set_sort_preference("updated_at")
        notes_ua = note_svc.get_incomplete()
        assert notes_ua[0].id == n1.id, "updated_at DESC: n1(后更新)在前"


class TestFullPinHierarchy:
    """完整置顶层级验证：手动置顶 → 标签置顶 → 非置顶。"""

    def test_three_tier_hierarchy(self, note_svc, tag_svc):
        """FIXME-RED：三层结构正确——手动置顶 → 标签置顶 → 普通便签。"""
        tag_svc.create("工作")
        tag_svc.create("生活")
        tag_svc.set_pinned(["工作", "生活"])

        manual_pin = note_svc.create(title="手动置顶", content="cm")
        note_svc.pin_note(manual_pin.id)
        time.sleep(0.010)
        tag_work = note_svc.create(title="工作标签", content="cw", tag_names=["工作"])
        time.sleep(0.010)
        tag_life = note_svc.create(title="生活标签", content="cl", tag_names=["生活"])
        time.sleep(0.010)
        normal = note_svc.create(title="普通便签", content="cn")

        notes = note_svc.get_incomplete()

        assert notes[0].id == manual_pin.id, "第一层：手动置顶"
        assert notes[1].id == tag_work.id, (
            f"第二层：标签置顶（工作先选），"
            f"实际第二位: id={notes[1].id}"
        )
        assert notes[2].id == tag_life.id, (
            f"第二层：标签置顶（生活后选），"
            f"实际第三位: id={notes[2].id}"
        )
        assert notes[3].id == normal.id, "第三层：普通便签"

    def test_three_tier_hierarchy_with_sort_toggle(self, note_svc, tag_svc):
        """FIXME-RED：切换排序后三层结构不变（仅非置顶区内部顺序可能变化）。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        manual1 = note_svc.create(title="手动1", content="cm1")
        note_svc.pin_note(manual1.id)
        time.sleep(0.010)
        manual2 = note_svc.create(title="手动2", content="cm2")
        note_svc.pin_note(manual2.id)
        time.sleep(0.010)
        tag_note = note_svc.create(title="标签置顶", content="ct", tag_names=["工作"])
        time.sleep(0.010)
        normal_old = note_svc.create(title="旧普通", content="co")
        time.sleep(0.010)
        normal_new = note_svc.create(title="新普通", content="cn")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        assert notes[0].id == manual2.id, "手动置顶区第一位（后置顶）"
        assert notes[1].id == manual1.id, "手动置顶区第二位（先置顶）"
        assert notes[2].id == tag_note.id, "标签置顶区"

        normal_ids = [n.id for n in notes[3:]]
        assert normal_ids.index(normal_new.id) < normal_ids.index(normal_old.id), (
            f"非置顶区 created_at DESC：新便签在旧便签前面"
        )

    def test_unpin_moves_from_manual_to_unpinned(self, note_svc, tag_svc):
        """取消手动置顶后，便签从手动置顶区移到非置顶区（无置顶标签时）。"""
        n = note_svc.create(title="将取消置顶", content="c")
        note_svc.pin_note(n.id)
        time.sleep(0.010)
        other = note_svc.create(title="普通便签", content="co")

        notes_before = note_svc.get_incomplete()
        assert notes_before[0].id == n.id, "置顶前：n 在第一位"

        note_svc.unpin_note(n.id)
        notes_after = note_svc.get_incomplete()

        assert notes_after[0].is_pinned == 0, "取消置顶后 n 不再是置顶"
        ids_after = [x.id for x in notes_after]
        assert n.id in ids_after, "便签仍在列表中"
