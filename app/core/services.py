from dataclasses import dataclass
from datetime import date
from typing import Any

from app.api.schemas import HabitUpdate
from app.core.models import Habit, LogEntry
from app.core.statistics import StatisticsCalculatorFactory, StatisticsResult
from app.db.repository import HabitRepository, LogRepository


@dataclass
class HabitService:
    habit_repo: HabitRepository
    log_repo: LogRepository

    def create_habit(self, habit: Habit) -> None:
        self.habit_repo.add(habit)

    def get_habit(self, habit_id: str) -> Habit | None:
        return self.habit_repo.get(habit_id)

    def list_habits(self) -> list[Habit]:
        return self.habit_repo.list()

    def update_habit(self, habit_id: str, update: HabitUpdate) -> Habit:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise ValueError("Habit not found")

        if update.name is not None:
            habit.name = update.name
        if update.description is not None:
            habit.description = update.description
        if update.category is not None:
            habit.category = update.category
        if update.goal is not None:
            habit.goal = update.goal

        self.habit_repo.update(habit)
        return habit

    def delete_habit(self, habit_id: str) -> None:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise ValueError("Habit not found")

        for subhabit_id in habit.subhabit_ids:
            self.delete_habit(subhabit_id)

        self.habit_repo.delete(habit_id)

    def add_subhabit(self, parent_id: str, subhabit: Habit) -> None:
        parent = self.habit_repo.get(parent_id)
        if parent is None:
            raise ValueError("Parent habit not found")

        subhabit.parent_id = parent_id
        parent.subhabit_ids.append(subhabit.id)

        self.habit_repo.add(subhabit)
        self.habit_repo.update(parent)

    def record_log(
        self,
        habit_id: str,
        date_: date,
        value: float | None,
    ) -> LogEntry:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise ValueError("Habit not found")

        log = LogEntry.create(
            habit_id=habit_id,
            date_=date_,
            value=value,
        )
        self.log_repo.add(log)
        return log

    def get_logs(
        self,
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[LogEntry]:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise ValueError("Habit not found")

        return self.log_repo.list_for_habit(
            habit_id=habit_id,
            start=start,
            end=end,
        )

    def get_statistics(
        self,
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, Any]:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise ValueError("Habit not found")

        logs = self.log_repo.list_for_habit(habit_id, start, end)

        calculator = StatisticsCalculatorFactory.get_calculator(habit.type)
        result: StatisticsResult = calculator.calculate(habit, logs, start, end)

        return {
            "habit_id": habit_id,
            "current_streak": result.current_streak,
            "longest_streak": result.longest_streak,
            "total_completions": result.total_completions,
            "completion_rate": result.completion_rate,
            "average_value": result.average_value,
            "total_days_tracked": result.total_days_tracked,
        }
