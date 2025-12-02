from datetime import date

from app.core.models import Habit, LogEntry
from app.db.repository import HabitRepository, LogRepository


class InMemoryHabitRepository(HabitRepository):
    def __init__(self) -> None:
        self._storage: dict[str, Habit] = {}

    def add(self, habit: Habit) -> None:
        self._storage[habit.id] = habit

    def get(self, habit_id: str) -> Habit | None:
        return self._storage.get(habit_id)

    def list(self) -> list[Habit]:
        return list(self._storage.values())

    def update(self, habit: Habit) -> None:
        if habit.id not in self._storage:
            raise KeyError("Habit not found")
        self._storage[habit.id] = habit

    def delete(self, habit_id: str) -> None:
        self._storage.pop(habit_id, None)


class InMemoryLogRepository(LogRepository):
    def __init__(self) -> None:
        self._storage: list[LogEntry] = []

    def add(self, log: LogEntry) -> None:
        self._storage.append(log)

    def list_for_habit(
        self,
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[LogEntry]:
        logs = [log for log in self._storage if log.habit_id == habit_id]

        if start is not None:
            logs = [log for log in logs if log.date >= start]

        if end is not None:
            logs = [log for log in logs if log.date <= end]

        return sorted(logs, key=lambda log: log.date)

    def list_all(self) -> list[LogEntry]:
        return list(self._storage)
