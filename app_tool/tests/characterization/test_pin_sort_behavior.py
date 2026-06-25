"""红灯测试 — 排序与置顶行为预期（预期行为 vs 现状 gap）。

这些测试验证 ui_spec.md §八 定义的预期行为。
当前代码不满足预期 → 红灯。修复后 → 绿灯。

对应 spec: ui_spec.md §八, spec.md §5.1, FEATURE_TESTS.md CT-P0-04/07/08/09
"""

import time
import pytest

from app_tool.model.database import init_db
from app_tool.controller.note_service import NoteService
from app_tool.controller.tag_service import TagService


@pytest.fixture
def note_svc(db_conn):
    init_db(db_conn)
    return NoteService(db_conn)


@pytest.fixture
def tag_svc(db_conn):
    init_db(db_conn)
    return TagService(db_conn)


# ═══════════════════════════════════════════════════════════
# 红灯-01：手动置顶区不受排序按钮影响
# ═══════════════════════════════════════════════════════════

class TestManualPinAreaImmuneToSort:
    """预期：手动置顶区始终按 pinned_at DESC，排序偏好只影响非置顶区。"""

    def test_manual_pin_order_unchanged_after_sort_toggle(self, note_svc):
        """预期(FIXME-RED)：切换排序偏好后，手动置顶便签保持 pinned_at 顺序不变。

        设计：n1 先创建但后置顶（pinned_at 更新 → 应排在前），
        n2 后创建但先置顶（created_at 更新但 pinned_at 更旧 → 应排在后）。
        created_at DESC 排序会让 n2 排前（创建时间新），
        但预期行为是 n1 排前（pinned_at 更新，手动置顶区免疫排序）。
        pin_note() 不更新 updated_at，因此需要 update() 来制造时间差。
        """
        n1 = note_svc.create(title="先创建后置顶", content="内容1")
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建先置顶", content="内容2")
        # n2.created_at > n1.created_at

        # n2 先置顶 → pinned_at 更旧
        note_svc.pin_note(n2.id)
        time.sleep(0.010)
        # n1 更新内容（刷新 updated_at）后置顶 → pinned_at 更新
        note_svc.update(n1.id, content="内容1-已更新")
        time.sleep(0.005)
        note_svc.pin_note(n1.id)
        # 此时 n1.pinned_at > n2.pinned_at，n1.updated_at > n2.updated_at

        # 刷新引用（create 返回的对象不会随 pin_note/update 自动更新）
        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)

        # 初始按 updated_at DESC：n1(updated_at 更新) → n2
        notes = note_svc.get_incomplete()
        assert notes[0].id == n1.id, f"updated_at DESC: n1 更新晚应排前，实际 {notes[0].id}"
        assert notes[1].id == n2.id

        # 切换到 created_at DESC
        note_svc.set_sort_preference("created_at")
        notes2 = note_svc.get_incomplete()

        # FIXME-RED 预期：n1 仍在前面（手动置顶区按 pinned_at，不受 created_at 影响）
        # 当前 bug：created_at DESC 会使 n2（后创建）排到 n1 前面
        assert notes2[0].id == n1.id, (
            f"手动置顶区应免疫排序偏好。n1(pinned_at={n1.pinned_at})应在前，"
            f"但 created_at DESC 让 n2(created_at={n2.created_at}) 排到了前面"
        )
        assert notes2[1].id == n2.id

    def test_unpinned_area_respects_sort_toggle(self, note_svc):
        """预期：排序偏好切换后，非置顶区顺序变化。"""
        n1 = note_svc.create(title="先创建", content="内容1")
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建", content="内容2")

        # 默认 updated_at DESC → n2 在前
        notes = note_svc.get_incomplete()
        assert notes[0].id == n2.id

        # 切换 created_at DESC → n2 仍在前（后创建）
        note_svc.set_sort_preference("created_at")
        notes2 = note_svc.get_incomplete()
        assert notes2[0].id == n2.id


# ═══════════════════════════════════════════════════════════
# 红灯-02：标签置顶区按标签选择顺序排列
# ═══════════════════════════════════════════════════════════

class TestTagPinAreaOrderBySelectionOrder:
    """预期：不同置顶标签的便签按标签选择顺序排列（pinned_tags 数组顺序）。"""

    def test_tag_pin_order_follows_selection_order(self, note_svc, tag_svc):
        """预期(FIXME-RED)：B→A 顺序置顶标签时，含 B 的便签排在含 A 的便签前面。

        设计：nB 先创建（含标签 B）、nA 后创建（含标签 A），
        时间偏好 updated_at DESC 会让 nA 排前（后创建），
        但预期行为是 nB 排前（B 被先选为置顶标签）。
        """
        tag_svc.create("A")
        tag_svc.create("B")

        # 按 B→A 顺序设置置顶标签
        tag_svc.set_pinned(["B", "A"])

        nB = note_svc.create(title="含标签B", content="内容B", tag_names=["B"])
        time.sleep(0.010)
        nA = note_svc.create(title="含标签A", content="内容A", tag_names=["A"])
        # nA 后创建，updated_at DESC → nA 在 nB 前面（当前行为，不对）
        # 预期：B 先被选为置顶 → 含 B 的便签排在前面

        notes = note_svc.get_incomplete()

        # FIXME-RED 预期：标签 B 先被选为置顶，含 B 的便签应排在含 A 之前
        # 当前 bug：updated_at DESC 让 nA（后创建/更新）排到了 nB 前面
        assert notes[0].id == nB.id, (
            f"标签 B 先被选为置顶（pinned_tags=[B, A]），"
            f"含 B 的便签(nB, id={nB.id})应在含 A 的便签(nA, id={nA.id})之前，"
            f"但时间偏好让后创建的 nA 排到了前面"
        )
        assert notes[1].id == nA.id

    def test_same_tag_notes_ordered_by_updated_at(self, note_svc, tag_svc):
        """同一置顶标签内的多张便签按 updated_at DESC。"""
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="较早更新", content="c1", tag_names=["工作"])
        time.sleep(0.010)
        n2 = note_svc.create(title="较晚更新", content="c2", tag_names=["工作"])

        notes = note_svc.get_incomplete()
        # 同标签内，updated_at DESC → n2 在前
        assert notes[0].id == n2.id
        assert notes[1].id == n1.id


# ═══════════════════════════════════════════════════════════
# 红灯-03：手动置顶 + 标签置顶冲突去重
# ═══════════════════════════════════════════════════════════

class TestPinConflictDedup:
    """预期：同时手动置顶+含置顶标签的便签仅出现在手动置顶区。"""

    def test_manual_pin_overrides_tag_pin_dedup(self, note_svc, tag_svc):
        """预期(FIXME-RED)：便签同时手动置顶+含置顶标签时，仅出现一次（手动置顶区）。

        现状(gap)：DISTINCT 可去重 row 级别的重复，
        但便签仍在两个 CASE WHEN 中都被匹配。
        如果 SQL 中两个 CASE 都是 0（最低优先级），
        则实际该便签只出现在手动置顶组中。
        本测试验证 get_incomplete() 返回列表中该便签仅出现一次。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="双重置顶", content="内容1", tag_names=["工作"])
        note_svc.pin_note(n1.id)

        notes = note_svc.get_incomplete()

        # FIXME-RED 预期：便签仅在手动置顶区出现一次
        occurrences = [n for n in notes if n.id == n1.id]
        assert len(occurrences) == 1, (
            f"便签 ID={n1.id} 同时手动置顶+含置顶标签，"
            f"应在结果中仅出现一次，实际出现 {len(occurrences)} 次"
        )
        # 且应排在第一位（手动置顶优先）
        assert notes[0].id == n1.id


# ═══════════════════════════════════════════════════════════
# 红灯-04：新便签在非置顶区最上方
# ═══════════════════════════════════════════════════════════

class TestNewNotePosition:
    """预期：新创建的未置顶便签在非置顶区最上方（置顶便签之下、旧便签之上）。"""

    def test_new_note_at_top_of_unpinned_sorted_by_created_at(self, note_svc):
        """预期(FIXME-RED)：created_at DESC 排序，新便签在非置顶区最前。

        服务层 get_incomplete() 返回 created_at DESC，新便签应排在首位。
        此测试验证服务层返回顺序正确——UI 层 add_widget 反转是另一个 bug。
        """
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.010)
        new = note_svc.create(title="新便签", content="新内容")

        note_svc.set_sort_preference("created_at")
        notes = note_svc.get_incomplete()

        # FIXME-RED 预期：新便签（后创建）排在前面
        assert notes[0].id == new.id, (
            f"created_at DESC 排序，新便签({new.id})应在旧便签({old.id})之前"
        )

    def test_new_note_at_top_of_unpinned_sorted_by_updated_at(self, note_svc):
        """预期(FIXME-RED)：updated_at DESC 排序，新便签在非置顶区最前。"""
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.010)
        new = note_svc.create(title="新便签", content="新内容")

        # 默认 updated_at DESC
        notes = note_svc.get_incomplete()

        # FIXME-RED 预期：新便签（最近更新）排在前面
        assert notes[0].id == new.id, (
            f"updated_at DESC 排序，新便签({new.id})应在旧便签({old.id})之前"
        )

    def test_new_note_below_pinned_notes(self, note_svc):
        """新便签在置顶便签之下、旧便签之上。"""
        pinned = note_svc.create(title="置顶便签", content="置顶")
        note_svc.pin_note(pinned.id)
        time.sleep(0.010)
        old = note_svc.create(title="旧便签", content="旧内容")
        time.sleep(0.010)
        new = note_svc.create(title="新便签", content="新内容")

        notes = note_svc.get_incomplete()

        # 置顶 → 新 → 旧
        assert notes[0].id == pinned.id
        assert notes[1].id == new.id, (
            f"新便签({new.id})应在旧便签({old.id})之上"
        )
        assert notes[2].id == old.id
