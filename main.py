"""便签应用入口。使用项目目录下的 Python 3.12 + KivyMD 运行。"""

import sys
import os

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app_tool.ui.app import NotesApp

if __name__ == "__main__":
    NotesApp().run()
