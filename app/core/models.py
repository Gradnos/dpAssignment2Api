from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum


class HabitType(str, Enum):
    BOOLEAN = "boolean"
    NUMERIC = "numeric"


@dataclass
class LogEntry:
    id: str
    habit_id: str
    date: datetime.date
    value: float | None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )

    @staticmethod
    def create(habit_id: str, date_: datetime.date, value: float | None) -> LogEntry:
        return LogEntry(
            id=str(uuid.uuid4()),
            habit_id=habit_id,
            date=date_,
            value=value,
        )


@dataclass
class Habit:
    id: str
    name: str
    description: str | None
    category: str | None
    type: HabitType
    goal: float | None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    parent_id: str | None = None
    subhabit_ids: list[str] = field(default_factory=list)
