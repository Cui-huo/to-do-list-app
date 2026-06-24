"""特征测试 fixtures — 复用现有 conftest 的 db_conn、kivy_app_instance。"""

import pytest

# 复用父级 conftest.py 的 fixtures（db_conn、kivy_app、kivy_app_instance）
# 通过 conftest 链自动发现机制，无需显式导入
