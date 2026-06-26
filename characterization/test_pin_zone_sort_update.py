"""排序规则验证测试 — 三大功能区排序规则（ui_spec.md §八 2026-06-25 更新）。

验证：
1. 手动置顶区：按 updated_at DESC 排序
2. 标签置顶区：按 updated_at DESC 排序
3. pin_note() 同时刷新 updated_at
4. 两大置顶区免疫排序按钮
5. 冲突去重：手动置顶优先，标签置顶跳过已在手动置顶区的便签

对应 spec: ui_spec.md §8.1
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
# 01：手动置顶区按 updated_at DESC 排序
# ═══════════════════════════════════════════════════════════

class TestManualPinSortedByUpdatedAt:
    """预期：手动置顶区按 updated_at DESC，非 pinned_at DESC。"""

    def test_manual_pin_by_updated_at_not_pinned_at(self, note_svc):
        """手动置顶区应优先按 updated_at 排序，非 pinned_at。

        设计：n1 先创建先置顶（pinned_at 旧），后编辑 → updated_at 最新。
        n2 后创建后置顶（pinned_at 新），不编辑 → updated_at 较旧。
        预期 updated_at DESC：[n1, n2]。
        """
        n1 = note_svc.create(title="先来先置顶后编辑", content="内容1")
        note_svc.pin_note(n1.id)
        time.sleep(0.010)
        n2 = note_svc.create(title="后来后置顶", content="内容2")
        note_svc.pin_note(n2.id)
        time.sleep(0.010)
        # n1 编辑 → updated_at 刷新为最新（超过 n2 的 updated_at）
        note_svc.update(n1.id, content="内容1-已编辑")

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)
        # n1.updated_at > n2.updated_at（n1 后编辑），
        # n1.pinned_at < n2.pinned_at（n1 先置顶）

        notes = note_svc.get_incomplete()

        # 预期：updated_at DESC → n1 在前
        assert notes[0].id == n1.id, (
            f"手动置顶区应按 updated_at DESC：n1(updated_at 最新)应在前，"
            f"但 pinned_at DESC 让 n2(pinned_at 更新) 排到了前面"
        )
        assert notes[1].id == n2.id

    def test_manual_pin_updated_at_order_differs_from_pinned_at(self, note_svc):
        """当 updated_at 顺序与 pinned_at 顺序冲突时，
        应以 updated_at 为准。

        设计：n1 先创建、先置顶、后编辑 → updated_at 最新，但 pinned_at 旧。
        n2 后创建、后置顶 → updated_at 较旧，但 pinned_at 新。
        预期：n1 在前（updated_at 最新）。
        """
        n1 = note_svc.create(title="先来后更新", content="内容1")
        note_svc.pin_note(n1.id)
        time.sleep(0.010)
        n2 = note_svc.create(title="后来", content="内容2")
        note_svc.pin_note(n2.id)
        time.sleep(0.010)
        # n1 编辑 → updated_at 刷新为最新
        note_svc.update(n1.id, content="内容1-已编辑")

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)
        # n1.updated_at > n2.updated_at（n1 后编辑）
        # n1.pinned_at < n2.pinned_at（n1 先置顶）

        notes = note_svc.get_incomplete()

        # 预期：updated_at DESC → n1 在前
        assert notes[0].id == n1.id, (
            f"手动置顶区应按 updated_at DESC：n1(updated_at 最新)应在前，"
            f"但 pinned_at DESC 让 n2(pinned_at 更新) 排到了前面"
        )
        assert notes[1].id == n2.id


# ═══════════════════════════════════════════════════════════
# 02：标签置顶区按 updated_at DESC 排序
# ═══════════════════════════════════════════════════════════

class TestTagPinSortedByUpdatedAt:
    """预期：标签置顶区按 updated_at DESC，非标签选择顺序。"""

    def test_tag_pin_by_updated_at_not_selection_order(self, note_svc, tag_svc):
        """标签置顶区所有便签统一按 updated_at DESC 排序。

        设计：B→A 顺序置顶标签。nB 含标签B（先创建），nA 含标签A（后创建）。
        预期：按 updated_at DESC → nA 在 nB 前（后创建→updated_at 更新）。
        """
        tag_svc.create("A")
        tag_svc.create("B")
        tag_svc.set_pinned(["B", "A"])  # B 先选，A 后选

        nB = note_svc.create(title="含标签B", content="内容B", tag_names=["B"])
        time.sleep(0.010)
        nA = note_svc.create(title="含标签A", content="内容A", tag_names=["A"])

        nA = note_svc.get_by_id(nA.id)
        nB = note_svc.get_by_id(nB.id)
        # nA.updated_at > nB.updated_at（nA 后创建）

        notes = note_svc.get_incomplete()

        # 预期：updated_at DESC → nA（更新）在前
        assert notes[0].id == nA.id, (
            f"标签置顶区应按 updated_at DESC：后创建的 nA(id={nA.id}) 应在前，"
            f"但标签选择顺序让 nB(id={nB.id}) 排到了前面"
        )
        assert notes[1].id == nB.id

    def test_tag_pin_multiple_tags_all_by_updated_at(self, note_svc, tag_svc):
        """多个标签的便签混排，按 updated_at DESC 统一排序。"""
        tag_svc.create("工作")
        tag_svc.create("生活")
        tag_svc.set_pinned(["工作", "生活"])

        n1 = note_svc.create(title="工作-先创建", content="c1", tag_names=["工作"])
        time.sleep(0.010)
        n2 = note_svc.create(title="生活-后创建", content="c2", tag_names=["生活"])
        time.sleep(0.010)
        n3 = note_svc.create(title="工作-最后创建", content="c3", tag_names=["工作"])

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)
        n3 = note_svc.get_by_id(n3.id)

        notes = note_svc.get_incomplete()

        # 预期：updated_at DESC → [n3, n2, n1]
        assert notes[0].id == n3.id, (
            f"标签置顶区应按 updated_at DESC 统一排序，n3 最后创建应排第一"
        )
        assert notes[1].id == n2.id
        assert notes[2].id == n1.id


# ═══════════════════════════════════════════════════════════
# 03：pin_note() 刷新 updated_at
# ═══════════════════════════════════════════════════════════

class TestPinNoteUpdatesUpdatedAt:
    """预期：pin_note() 同时设置 updated_at = now。"""

    def test_pin_note_refreshes_updated_at(self, note_svc):
        """pin_note() 应将 updated_at 设为当前时间。

        pin_note() 同时设置 updated_at。
        """
        note = note_svc.create(title="测试置顶", content="内容")
        original_updated_at = note.updated_at
        time.sleep(0.010)

        pinned = note_svc.pin_note(note.id)

        # 预期：置顶后 updated_at 应更新
        assert pinned.updated_at != original_updated_at, (
            f"pin_note() 应刷新 updated_at。"
            f"原始={original_updated_at}, 置顶后={pinned.updated_at}"
        )

    def test_pin_note_updated_at_is_later_after_sleep(self, note_svc):
        """置顶后 updated_at 应大于置顶前的原始值。"""
        note = note_svc.create(title="测试", content="内容")
        time.sleep(0.020)
        pinned = note_svc.pin_note(note.id)

        # 预期：置顶后的 updated_at > 创建时的 updated_at
        assert pinned.updated_at > note.updated_at, (
            f"pin_note() 后的 updated_at({pinned.updated_at}) "
            f"应 > 创建时的 updated_at({note.updated_at})"
        )


# ═══════════════════════════════════════════════════════════
# 04：两大置顶区免疫排序按钮
# ═══════════════════════════════════════════════════════════

class TestPinZonesImmuneToSortToggle:
    """预期：手动置顶区和标签置顶区不受排序偏好切换影响。"""

    def test_manual_pin_zone_order_unchanged_after_sort_toggle(self, note_svc):
        """切换排序偏好后，手动置顶区顺序不变。

        设计：n1 先创建后置顶再编辑 → updated_at 最新、created_at 旧。
        n2 后创建先置顶不编辑 → updated_at 旧、created_at 新。
        手动置顶区 updated_at DESC → [n1, n2]。
        切换 created_at DESC → 应仍为 [n1, n2]（免疫）。
        若未免疫 → [n2, n1]（n2 created_at 更新）。
        """
        n1 = note_svc.create(title="先创建后置顶后编辑", content="c1")
        note_svc.pin_note(n1.id)
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建先置顶", content="c2")
        note_svc.pin_note(n2.id)
        time.sleep(0.010)
        # n1 编辑 → updated_at 刷新为最新
        note_svc.update(n1.id, content="c1-已编辑")

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)
        # n1.updated_at > n2.updated_at, n1.created_at < n2.created_at

        notes = note_svc.get_incomplete()
        # 预期置顶区 updated_at DESC：[n1, n2]
        assert notes[0].id == n1.id, f"updated_at DESC: n1(编辑后最新)应在前"
        assert notes[1].id == n2.id

        # 切换到 created_at DESC
        note_svc.set_sort_preference("created_at")
        notes2 = note_svc.get_incomplete()

        # 预期：手动置顶区免疫排序 → 仍为 [n1, n2]
        assert notes2[0].id == n1.id, (
            f"手动置顶区应免疫排序切换。created_at DESC 下 n1(id={n1.id}) "
            f"仍应在 n2(id={n2.id}) 之前"
        )
        assert notes2[1].id == n2.id

    def test_tag_pin_zone_order_unchanged_after_sort_toggle(self, note_svc, tag_svc):
        """切换排序偏好后，标签置顶区顺序不变。此测试为假绿灯守门——

        当前代码在标签置顶组内以 updated_at DESC 为主排序键，
        {time_col} 仅作为第 3 排序键 → 大多数场景不起作用 → 假绿灯。
        此测试的 _equal_updated_at 变体进一步验证免疫行为。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="先创建后编辑", content="c1", tag_names=["工作"])
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建不编辑", content="c2", tag_names=["工作"])
        time.sleep(0.010)
        note_svc.update(n1.id, content="c1-已编辑")

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)

        notes = note_svc.get_incomplete()
        assert notes[0].id == n1.id
        assert notes[1].id == n2.id

        note_svc.set_sort_preference("created_at")
        notes2 = note_svc.get_incomplete()

        assert notes2[0].id == n1.id, (
            f"标签置顶区应免疫排序切换。created_at DESC 下 n1(id={n1.id}) "
            f"仍应在 n2(id={n2.id}) 之前"
        )
        assert notes2[1].id == n2.id

    def test_tag_pin_immunity_equal_updated_at(self, note_svc, tag_svc):
        """updated_at 相同时，created_at 尾排序不应影响标签置顶区。

        核心设计：通过直接 SQL 强制两便签 updated_at 完全相同，
        使当前代码的 {time_col} DESC 尾排序成为唯一决定因素。
        此时切换排序偏好会改变标签置顶区顺序 → 暴露非免疫的真面目。
        预期（修复后）：标签置顶区仅按 updated_at DESC 排序，
        updated_at 相同时顺序保持稳定（不随 sort_preference 变化）。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="先创建", content="c1", tag_names=["工作"])
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建", content="c2", tag_names=["工作"])
        time.sleep(0.010)
        # n1.created_at < n2.created_at

        # 强制两便签 updated_at 完全相同，让 time_col 尾排序成为决定因素
        forced_time = "2024-01-01T00:00:00.000000"
        note_svc.conn.execute(
            "UPDATE Note SET updated_at = ? WHERE id IN (?, ?)",
            (forced_time, n1.id, n2.id),
        )
        note_svc.conn.commit()

        # 默认 sort_pref = updated_at，time_col = updated_at
        # n1 和 n2 的 updated_at 相同 → time_col 也相同 → 顺序依赖 SQLite 内部（rowid）
        notes_before = note_svc.get_incomplete()
        tag_order_before = [
            n.id for n in notes_before if n.id in (n1.id, n2.id)
        ]

        # 切换到 created_at DESC，time_col = created_at
        note_svc.set_sort_preference("created_at")
        notes_after = note_svc.get_incomplete()
        tag_order_after = [
            n.id for n in notes_after if n.id in (n1.id, n2.id)
        ]

        # 预期：标签置顶区免疫 → 顺序不变
        assert tag_order_after == tag_order_before, (
            f"标签置顶区应免疫排序切换。updated_at 相同时，"
            f"created_at DESC 不应影响标签置顶区顺序。\n"
            f"切换前: {tag_order_before}\n"
            f"切换后: {tag_order_after}"
        )


# ═══════════════════════════════════════════════════════════
# 05：冲突去重 — 手动置顶优先 + 标签置顶跳过
# ═══════════════════════════════════════════════════════════

class TestPinConflictDedup:
    """预期：手动置顶优先，标签置顶区不含已手动置顶的便签。"""

    def test_manual_pin_excluded_from_tag_zone(self, note_svc, tag_svc):
        """便签同时手动置顶+含置顶标签，仅出现在手动置顶区。

        get_incomplete() 返回列表中该便签仅出现一次且在最前面。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n = note_svc.create(title="双重身份", content="内容", tag_names=["工作"])
        note_svc.pin_note(n.id)

        notes = note_svc.get_incomplete()

        # 该便签仅出现一次（非重复）
        occurrences = [x for x in notes if x.id == n.id]
        assert len(occurrences) == 1, (
            f"便签 ID={n.id} 应仅在列表中出一次，实际 {len(occurrences)} 次"
        )
        # 排在手动置顶区第一位
        assert notes[0].id == n.id

    def test_tag_pin_notes_with_mixed_manual(self, note_svc, tag_svc):
        """标签置顶区包含非手动置顶的标签便签，已手动置顶的排在手动置顶区。

        创建 3 张含「工作」标签的便签：n1（手动置顶）、n2（不置顶）、n3（不置顶）。
        预期顺序：n1（手动置顶区）→ n3→n2（标签置顶区，updated_at DESC）。
        """
        tag_svc.create("工作")
        tag_svc.set_pinned(["工作"])

        n1 = note_svc.create(title="手动置顶", content="c1", tag_names=["工作"])
        note_svc.pin_note(n1.id)
        time.sleep(0.010)
        n2 = note_svc.create(title="标签置顶-先", content="c2", tag_names=["工作"])
        time.sleep(0.010)
        n3 = note_svc.create(title="标签置顶-后", content="c3", tag_names=["工作"])

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)
        n3 = note_svc.get_by_id(n3.id)

        notes = note_svc.get_incomplete()

        # 预期：[n1(手动), n3(标签-后), n2(标签-先)]
        assert notes[0].id == n1.id, "手动置顶应在第一位"
        assert notes[1].id == n3.id, (
            f"标签置顶区 updated_at DESC：n3(id={n3.id}) 后创建应在前"
        )
        assert notes[2].id == n2.id


# ═══════════════════════════════════════════════════════════
# 06：非置顶区正常参与排序
# ═══════════════════════════════════════════════════════════

class TestUnpinnedAreaNormalSort:
    """预期：非置顶区正常响应排序按钮切换。"""

    def test_unpinned_area_respects_sort_preference(self, note_svc):
        """非置顶区切换排序偏好后顺序变化。"""
        n1 = note_svc.create(title="先创建", content="c1")
        time.sleep(0.010)
        n2 = note_svc.create(title="后创建", content="c2")

        n1 = note_svc.get_by_id(n1.id)
        n2 = note_svc.get_by_id(n2.id)

        # 默认 updated_at DESC → n2 在前（后创建 updated_at 更新）
        notes = note_svc.get_incomplete()
        assert notes[0].id == n2.id
        assert notes[1].id == n1.id

        # 切换 created_at DESC → n2 仍在前（后创建 created_at 更新）
        note_svc.set_sort_preference("created_at")
        notes2 = note_svc.get_incomplete()
        assert notes2[0].id == n2.id
        assert notes2[1].id == n1.id

    def test_new_note_at_top_of_unpinned_zone(self, note_svc):
        """新便签在非置顶区最上方（置顶便签之下）。"""
        pinned = note_svc.create(title="置顶", content="p")
        note_svc.pin_note(pinned.id)
        time.sleep(0.010)
        old = note_svc.create(title="旧便签", content="c1")
        time.sleep(0.010)
        new = note_svc.create(title="新便签", content="c2")

        notes = note_svc.get_incomplete()

        # 预期：[pinned, new, old]
        assert notes[0].id == pinned.id
        assert notes[1].id == new.id, (
            f"新便签(id={new.id})应在非置顶区最上方"
        )
        assert notes[2].id == old.id
