"""红灯测试 — add_widget(index=0) 导致列表顺序反转。

验证：Kivy add_widget 默认 index=0 会使 UI 列表顺序与服务层返回顺序完全反转。
此 bug 导致"新便签出现在最下方"等问题。

对应 spec: FEATURE_TESTS.md CT-P0-09, ui_spec.md §8.2
"""

import pytest


class TestAddWidgetReversal:
    """Kivy add_widget(widget) 默认 index=0 反转顺序。"""

    def test_add_widget_default_index_reverses_order(self):
        """FIXME-RED：BoxLayout vertical 中 add_widget 默认 index=0 反转顺序。

        服务层返回 [newest, mid, oldest]，UI add_widget 逐条插入导致
        children[0]=oldest（视觉底部），children[-1]=newest（视觉顶部）。
        预期：children[0] 应为 newest（视觉顶部）。
        """
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        box = BoxLayout(orientation='vertical')
        l1 = Label(text='first')   # 应排最前
        l2 = Label(text='second')
        l3 = Label(text='third')   # 应排最后

        box.add_widget(l1)
        box.add_widget(l2)
        box.add_widget(l3)

        # Kivy BoxLayout vertical: children[0]=视觉顶部, children[-1]=视觉底部
        # 默认 index=0 意味着最后 add 的在 children[0]（顶部）
        # 所以 children = [l3, l2, l1] → 视觉: l3顶部, l1底部

        # FIXME-RED：预期 l1 在顶部
        assert box.children[0].text == 'first', (
            f"add_widget 默认 index=0 反转顺序: "
            f"期望 children[0]='first'(顶部)，实际 children[0]='{box.children[0].text}'，"
            f"children[-1]='{box.children[-1].text}'"
        )

    def test_add_widget_with_explicit_index_preserves_order(self):
        """正确方式：add_widget(w, index=len(children)) 保持顺序。"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        box = BoxLayout(orientation='vertical')
        l1 = Label(text='first')
        l2 = Label(text='second')
        l3 = Label(text='third')

        # 正确：用 index=len(children) 追加到末尾
        box.add_widget(l1, index=len(box.children))
        box.add_widget(l2, index=len(box.children))
        box.add_widget(l3, index=len(box.children))

        # children[0] = 最后加入的 = 视觉顶部；children[-1] = 最先加入的 = 视觉底部
        # 视觉: l1(top), l2, l3(bottom) — 与服务层顺序一致
        assert box.children[0].text == 'first'
        assert box.children[-1].text == 'third'


class TestAffectedLocations:
    """CT-P0-09 全局排查中发现的受影响位置。"""

    def test_refresh_list_lines_missing_index(self):
        """验证 main_screen.py refresh_list 中 add_widget 缺少 index 参数。

        受影响行：L865, L871, L876
        """
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen.refresh_list)
        # 预期修复后，incomplete_box.add_widget 和 completed_box.add_widget 应带 index=
        # 当前：add_widget(card) 或 add_widget(empty_label)，缺少 index 参数
        lines_with_add_widget = [
            line.strip()
            for line in source.split('\n')
            if 'add_widget(' in line and 'box' in line.lower()
        ]

        # FIXME-RED：每条 add_widget 应有 index= 参数
        for line in lines_with_add_widget:
            if 'incomplete_box' in line or 'completed_box' in line:
                assert 'index=' in line, (
                    f"refresh_list 中 add_widget 缺少 index 参数: {line}"
                )

    def test_reorder_cards_lines_missing_index(self):
        """验证 main_screen.py _reorder_cards 中 add_widget 缺少 index 参数。

        受影响行：L1100, L1105
        """
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._reorder_cards)
        lines_with_add_widget = [
            line.strip()
            for line in source.split('\n')
            if 'add_widget(' in line and 'box' in line.lower()
        ]

        # FIXME-RED：每条 add_widget 应有 index= 参数
        for line in lines_with_add_widget:
            if 'incomplete_box' in line or 'completed_box' in line:
                assert 'index=' in line, (
                    f"_reorder_cards 中 add_widget 缺少 index 参数: {line}"
                )
