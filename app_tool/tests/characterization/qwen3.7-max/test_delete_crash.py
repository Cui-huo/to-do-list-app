"""红灯测试 — 删除便签后应用闪退 (ValueError: 便签 ID=N 不存在)。

问题行为：删除便签确认后应用闪退，报错 ValueError: 便签 ID=34 不存在。
根因：_handle_delete 的 on_confirm 回调没有 try/except，
当 note_svc.delete() 抛出 ValueError 时异常未捕获，直接崩溃。
对比 _handle_complete_toggle 和 _handle_pin_toggle 都有 try/except 防御。

期望行为：删除失败时不崩溃，弹 Toast 提示并刷新列表。

运行命令：
  pytest app_tool/tests/characterization/qwen3.7-max/test_delete_crash.py -v
"""

import inspect
import pytest


class TestDeleteCallbackErrorHandling:
    """_handle_delete 的 on_confirm 回调必须有 try/except 防御。"""

    def test_on_confirm_has_try_except(self):
        """FIXME-RED：on_confirm 回调必须捕获 ValueError。

        当便签已被其他操作删除（或 note_id 过期），
        note_svc.delete() 抛 ValueError，不捕获则闪退。
        对比 _handle_complete_toggle / _handle_pin_toggle 都有 try/except。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._handle_delete)

        assert 'try' in source, (
            "_handle_delete 的 on_confirm 回调缺少 try/except，"
            "note_svc.delete() 抛 ValueError 时直接崩溃"
        )
        assert 'except' in source, (
            "_handle_delete 必须有 except 分支处理 ValueError"
        )

    def test_on_confirm_catches_value_error(self):
        """on_confirm 必须专门捕获 ValueError（不能只 catch Exception）。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._handle_delete)

        assert 'ValueError' in source, (
            "_handle_delete 应显式捕获 ValueError，"
            "与 _handle_complete_toggle / _handle_pin_toggle 保持一致"
        )

    def test_on_confirm_shows_toast_on_error(self):
        """删除失败时应弹 Toast 提示用户，而非静默失败。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen._handle_delete)

        # except 块中必须有 _toast 调用
        lines = source.split('\n')
        in_except = False
        has_toast_in_except = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('except'):
                in_except = True
            elif in_except and '_toast' in stripped:
                has_toast_in_except = True
                break
            elif in_except and stripped and not stripped.startswith('#') and not stripped.startswith('self._toast'):
                # 如果遇到非 toast、非注释的新语句（非缩进延续），退出 except 块
                if not line.startswith('            ') and not line.startswith('                '):
                    in_except = False

        assert has_toast_in_except, (
            "_handle_delete 的 except 块中必须调用 _toast() 提示用户"
        )


class TestDeleteWithNonexistentNote:
    """服务层验证：删除不存在的便签抛 ValueError。"""

    def test_delete_nonexistent_raises(self, note_svc):
        """回归保护：delete() 对不存在的 ID 必须抛 ValueError。"""
        from app_tool.model.database import init_db

        with pytest.raises(ValueError, match="不存在"):
            note_svc.delete(99999)

    def test_double_delete_second_raises(self, note_svc):
        """回归保护：同一便签删除两次，第二次必须抛 ValueError。"""
        from app_tool.model.database import init_db

        note = note_svc.create(title="将删除", content="c")
        note_svc.delete(note.id)

        with pytest.raises(ValueError, match="不存在"):
            note_svc.delete(note.id)


class TestRefreshListLayoutFreeze:
    """refresh_list() 也应有布局冻结，避免全量重建时的 O(N²) 卡顿。"""

    def test_refresh_list_freezes_adaptive_height(self):
        """FIXME-RED：refresh_list() 在 clear+add 循环期间应冻结 minimum_height。

        refresh_list() 做 clear_widgets + 逐条 add_widget，
        每次 add_widget 触发 minimum_height 重算 → O(N²) 布局开销。
        应与 _reorder_cards() 一致，unbind → 操作 → bind。
        """
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.refresh_list)

        assert 'unbind' in source, (
            "refresh_list() 应在 clear_widgets 前 unbind minimum_height，"
            "避免 O(N²) 布局重算"
        )

    def test_refresh_list_restores_adaptive_height(self):
        """refresh_list() 应在操作完成后 bind 恢复 minimum_height。"""
        from app_tool.ui.main_screen import MainScreen
        source = inspect.getsource(MainScreen.refresh_list)

        assert 'minimum_height' in source and 'bind' in source, (
            "refresh_list() 应在 add_widget 完成后 bind minimum_height 恢复自适应"
        )


@pytest.fixture
def note_svc(db_conn):
    from app_tool.model.database import init_db
    init_db(db_conn)
    from app_tool.controller.note_service import NoteService
    return NoteService(db_conn)
