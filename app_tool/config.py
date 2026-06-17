"""应用配置常量与种子数据。"""

DB_FILENAME = "notes.db"

SEED_TAGS = [
    "紧急重要",
    "紧急",
    "重要不紧急",
    "P1",
    "P2",
    "P3",
]

MAX_REMINDERS_PER_NOTE = 3
MAX_PINNED_TAGS = 3
EXPORT_FORMATS = ["json", "text"]
FTS_MIN_KEYWORD_LENGTH = 1
UNDO_TIMEOUT_SECONDS = 12 * 3600  # 撤销箭头 12 小时有效
MAX_TITLE_LENGTH = 50
MAX_CONTENT_LENGTH = 5000
MAX_TAG_NAME_LENGTH = 10
