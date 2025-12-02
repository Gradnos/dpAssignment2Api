from __future__ import annotations

from datetime import date
from typing import Protocol

from app.core.models import Habit, LogEntry


class HabitRepository(Protocol):
    def add(self, habit: Habit) -> None: ...

    def get(self, habit_id: str) -> Habit | None: ...

    def list(self) -> list[Habit]: ...

    def update(self, habit: Habit) -> None: ...

    def delete(self, habit_id: str) -> None: ...


class LogRepository(Protocol):
    def add(self, log: LogEntry) -> None: ...

    def list_for_habit(
        self,
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[LogEntry]: ...

    def list_all(self) -> list[LogEntry]: ...
