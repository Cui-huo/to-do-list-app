"""特征测试 — Kivy BoxLayout vertical 的 children 顺序行为。

Kivy 源码 _iterate_layout (boxlayout.py L285):
  y = padding_bottom + selfy     # ← 从底部开始
  for i, ... in enumerate(...):  # ← 正序遍历 children
      yield i, cx, y, w, h
      y += h + spacing            # ← 向上叠加

结论：vertical BoxLayout 中 children[0]=视觉底部, children[-1]=视觉顶部。

对应 spec: ui_spec.md §8.2
"""

import pytest


class TestAddWidgetPreservesOrder:
    """Kivy add_widget(widget) 默认 index=0 保持 Service 层顺序。"""

    def test_add_widget_default_preserves_service_order(self):
        """验证：add_widget(widget) 默认 index=0 保持 Service 层 DESC 顺序。

        Service 返回 [first, second, third]（DESC: first 最新应排最上）。
        add_widget(w) 默认 index=0 将每个 widget prepend：
          add first  → children = [first]          → children[0]=BOTTOM
          add second → children = [second, first]  → children[1]=TOP=first ✓
          add third  → children = [third, second, first] → children[2]=TOP=first ✓
        视觉（TOP→BOTTOM）：first, second, third ✓
        """
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        box = BoxLayout(orientation='vertical')
        l1 = Label(text='first')
        l2 = Label(text='second')
        l3 = Label(text='third')

        box.add_widget(l1)
        box.add_widget(l2)
        box.add_widget(l3)

        # Kivy vertical: children[0]=视觉底部, children[-1]=视觉顶部
        # children = [l3, l2, l1]
        # children[-1] = l1 = 'first' = TOP ✓
        assert box.children[-1].text == 'first', (
            f"期望 children[-1]='first'(顶部)，实际 children[-1]='{box.children[-1].text}'"
        )
        assert box.children[0].text == 'third', (
            f"期望 children[0]='third'(底部)，实际 children[0]='{box.children[0].text}'"
        )

    def test_add_widget_with_index_len_reverses_order(self):
        """验证：add_widget(w, index=len(children)) 反转顺序。

        Service 返回 [first, second, third]（DESC）。
        index=len(children) 追加到末尾：
          add first (idx=0) → children=[first]           → children[0]=BOTTOM
          add second (idx=1) → children=[first,second]   → children[1]=TOP=second ❌
          add third (idx=2) → children=[first,second,third] → children[2]=TOP=third ❌
        视觉（TOP→BOTTOM）：third, second, first ❌ 完全反转！
        """
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        box = BoxLayout(orientation='vertical')
        l1 = Label(text='first')
        l2 = Label(text='second')
        l3 = Label(text='third')

        box.add_widget(l1, index=len(box.children))
        box.add_widget(l2, index=len(box.children))
        box.add_widget(l3, index=len(box.children))

        # children = [l1, l2, l3]
        # children[0] = l1 = 'first' = BOTTOM ❌（first 应该在顶部）
        # children[-1] = l3 = 'third' = TOP ❌（third 应该在底部）
        assert box.children[-1].text == 'third', (
            f"index=len 反转: 期望 children[-1]='third'(顶部，反转结果)，"
            f"实际 children[-1]='{box.children[-1].text}'"
        )
        assert box.children[0].text == 'first', (
            f"index=len 反转: 期望 children[0]='first'(底部，反转结果)，"
            f"实际 children[0]='{box.children[0].text}'"
        )


class TestRefreshListUsesDefaultAddWidget:
    """修复后 refresh_list 和 _reorder_cards 应使用默认 add_widget（无 index=）。"""

    def test_refresh_list_uses_default_add_widget(self):
        """验证 refresh_list 中 add_widget 使用默认 index（无 index= 参数）。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen.refresh_list)
        lines_with_add_widget = [
            line.strip()
            for line in source.split('\n')
            if 'add_widget(' in line and ('inc_box' in line or 'cmp_box' in line)
        ]

        for line in lines_with_add_widget:
            assert 'index=' not in line, (
                f"refresh_list 中 add_widget 不应有 index= 参数（应使用默认 index=0）: {line}"
            )

    def test_reorder_cards_uses_default_add_widget(self):
        """验证 _reorder_cards 中 add_widget 使用默认 index（无 index= 参数）。"""
        import inspect
        from app_tool.ui.main_screen import MainScreen

        source = inspect.getsource(MainScreen._reorder_cards)
        lines_with_add_widget = [
            line.strip()
            for line in source.split('\n')
            if 'add_widget(' in line and ('inc_box' in line or 'cmp_box' in line)
        ]

        for line in lines_with_add_widget:
            assert 'index=' not in line, (
                f"_reorder_cards 中 add_widget 不应有 index= 参数（应使用默认 index=0）: {line}"
            )
