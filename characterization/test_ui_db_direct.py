"""特征测试 — UI 层直接访问 db_conn 执行 SQL。

锁定现状：main_screen.py 中 6 处直接 app.db_conn.execute()，
绕过 Service 层。settings_screen.py 使用共享的 load_setting/save_setting。
"""

import inspect
import pytest


class TestUIDBDirectAccess:
    """UI 层直接访问数据库的调用点。"""

    def test_main_screen_db_direct_calls_exist(self):
        """现状：main_screen.py 中至少 6 处直接 app.db_conn.execute()。"""
        from app_tool.ui import main_screen

        source = inspect.getsource(main_screen)
        occurrences = source.count('app.db_conn.execute')

        # 现状：6 处
        assert occurrences >= 6, (
            f"main_screen.py 中应有至少 6 处 app.db_conn.execute()，"
            f"实际找到 {occurrences} 处"
        )

    def test_db_direct_methods_list(self):
        """现状：列出所有直接访问 DB 的方法名。"""
        import re
        from app_tool.ui import main_screen

        source = inspect.getsource(main_screen)

        # 提取所有包含 app.db_conn.execute 的方法
        # 找到每个 def 和所属的方法名
        lines = source.split('\n')
        current_method = '<module>'
        db_direct_methods = set()

        for line in lines:
            if line.strip().startswith('def '):
                match = re.match(r'\s*def\s+(\w+)', line)
                if match:
                    current_method = match.group(1)
            if 'app.db_conn.execute' in line:
                db_direct_methods.add(current_method)

        # 现状：这些方法直接访问 DB
        assert '_load_templates' in db_direct_methods, (
            f"_load_templates 应直接访问 DB，实际方法: {db_direct_methods}"
        )
        assert '_save_templates' in db_direct_methods, (
            f"_save_templates 应直接访问 DB"
        )
        assert '_load_username' in db_direct_methods, (
            f"_load_username 应直接访问 DB"
        )
        assert '_save_username' in db_direct_methods, (
            f"_save_username 应直接访问 DB"
        )
        assert '_load_username_style' in db_direct_methods, (
            f"_load_username_style 应直接访问 DB"
        )
        assert '_save_username_style' in db_direct_methods, (
            f"_save_username_style 应直接访问 DB"
        )

    def test_sql_statements_used(self):
        """现状：锁定所有直接执行的 SQL 语句类型。"""
        from app_tool.ui import main_screen

        source = inspect.getsource(main_screen)

        # 涉及的表
        assert 'UserSettings' in source, "所有直连 SQL 都操作 UserSettings 表"
        assert 'text_templates' in source, "_load_templates 查询 key='text_templates'"
        assert 'username' in source, "_load_username/_save_username 涉及 username"
        assert 'username_style' in source, "_load/_save_username_style 涉及 username_style"
        assert 'INSERT OR REPLACE' in source, "使用 INSERT OR REPLACE 语义"

    def test_no_db_direct_in_settings_screen(self):
        """现状：settings_screen.py 不直接 app.db_conn.execute。

        使用共享的 load_setting/save_setting 函数封装了 DB 访问。
        """
        from app_tool.ui import settings_screen

        source = inspect.getsource(settings_screen)
        # settings_screen 通过 load_setting/save_setting 访问 DB
        assert 'app.db_conn.execute' not in source, (
            "settings_screen.py 不应直接 app.db_conn.execute，"
            "应使用 load_setting/save_setting"
        )
