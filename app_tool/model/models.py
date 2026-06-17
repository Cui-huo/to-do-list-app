"""数据类定义：Note / Tag / NoteTag / Reminder。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Note:
    """便签数据类。"""

    title: str
    created_at: str
    updated_at: str
    id: Optional[int] = None
    content: str = ""
    completed_at: Optional[str] = None
    is_completed: int = 0
    position: float = 0.0
    is_pinned: int = 0
    pinned_at: Optional[str] = None


@dataclass
class Tag:
    """标签数据类。"""

    name: str
    id: Optional[int] = None


@dataclass
class NoteTag:
    """便签-标签关联（多对多）。"""

    note_id: int
    tag_id: int


@dataclass
class Reminder:
    """提醒数据类。"""

    note_id: int
    remind_at: str
    id: Optional[int] = None
    is_triggered: int = 0
