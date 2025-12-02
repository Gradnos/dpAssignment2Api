from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.models import Habit, HabitType, LogEntry


@dataclass
class StatisticsResult:
    current_streak: int
    longest_streak: int
    total_completions: int
    completion_rate: float
    average_value: float | None
    total_days_tracked: int


class StatisticsCalculator(ABC):
    @abstractmethod
    def calculate(
        self,
        habit: Habit,
        logs: list[LogEntry],
        start: date | None = None,
        end: date | None = None,
    ) -> StatisticsResult:
        pass

    def _filter_logs_by_date(
        self,
        logs: list[LogEntry],
        start: date | None,
        end: date | None,
    ) -> list[LogEntry]:
        filtered = logs
        if start:
            filtered = [log for log in filtered if log.date >= start]
        if end:
            filtered = [log for log in filtered if log.date <= end]
        return filtered

    def _calculate_streaks(self, completed_dates: set[date]) -> tuple[int, int]:
        if not completed_dates:
            return 0, 0

        sorted_dates = sorted(completed_dates)

        # Calculate current streak
        current_streak = 0
        cursor = date.today()
        while cursor in completed_dates:
            current_streak += 1
            cursor -= timedelta(days=1)

        # Calculate longest streak
        longest_streak = 0
        current = 0

        for i in range(len(sorted_dates)):
            if i == 0:
                current = 1
            else:
                diff = (sorted_dates[i] - sorted_dates[i - 1]).days
                if diff == 1:
                    current += 1
                else:
                    current = 1
            longest_streak = max(longest_streak, current)

        return current_streak, longest_streak


class BooleanStatisticsCalculator(StatisticsCalculator):
    def calculate(
        self,
        habit: Habit,  # noqa: ARG002
        logs: list[LogEntry],
        start: date | None = None,
        end: date | None = None,
    ) -> StatisticsResult:
        filtered_logs = self._filter_logs_by_date(logs, start, end)

        completed_dates: set[date] = set()
        for log in filtered_logs:
            if log.value is not None and log.value >= 1.0:
                completed_dates.add(log.date)

        current_streak, longest_streak = self._calculate_streaks(completed_dates)

        total_completions = len(completed_dates)
        total_days = len(filtered_logs) if filtered_logs else 0
        completion_rate = total_completions / total_days if total_days > 0 else 0.0

        return StatisticsResult(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_completions=total_completions,
            completion_rate=completion_rate,
            average_value=None,
            total_days_tracked=total_days,
        )


class NumericStatisticsCalculator(StatisticsCalculator):
    def calculate(
        self,
        habit: Habit,
        logs: list[LogEntry],
        start: date | None = None,
        end: date | None = None,
    ) -> StatisticsResult:
        filtered_logs = self._filter_logs_by_date(logs, start, end)

        completed_dates: set[date] = set()
        values: list[float] = []

        for log in filtered_logs:
            if log.value is not None:
                values.append(log.value)

                if habit.goal is not None:
                    if log.value >= habit.goal:
                        completed_dates.add(log.date)
                elif log.value > 0:
                    completed_dates.add(log.date)

        current_streak, longest_streak = self._calculate_streaks(completed_dates)

        total_completions = len(completed_dates)
        total_days = len(filtered_logs) if filtered_logs else 0
        completion_rate = total_completions / total_days if total_days > 0 else 0.0
        average_value = sum(values) / len(values) if values else None

        return StatisticsResult(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_completions=total_completions,
            completion_rate=completion_rate,
            average_value=average_value,
            total_days_tracked=total_days,
        )


class StatisticsCalculatorFactory:
    _calculators: dict[HabitType, StatisticsCalculator] = {
        HabitType.BOOLEAN: BooleanStatisticsCalculator(),
        HabitType.NUMERIC: NumericStatisticsCalculator(),
    }

    @classmethod
    def get_calculator(cls, habit_type: HabitType) -> StatisticsCalculator:
        calculator = cls._calculators.get(habit_type)
        if calculator is None:
            raise ValueError(f"No calculator found for habit type: {habit_type}")
        return calculator

    @classmethod
    def register_calculator(
        cls,
        habit_type: HabitType,
        calculator: StatisticsCalculator,
    ) -> None:
        cls._calculators[habit_type] = calculator
