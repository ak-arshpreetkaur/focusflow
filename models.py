# models.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class Task:
    id: int
    title: str
    notes: str
    due_date: Optional[date]
    priority: str
    is_done: bool

@dataclass
class FocusSession:
    id: int
    task_id: Optional[int]
    started_at: datetime
    ended_at: datetime
    duration_minutes: int
