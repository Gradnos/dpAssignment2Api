"""Unit tests for statistics calculators."""

import uuid
from datetime import date, timedelta

from app.core.models import Habit, HabitType, LogEntry
from app.core.statistics import (
    BooleanStatisticsCalculator,
    NumericStatisticsCalculator,
    StatisticsCalculatorFactory,
)


class TestBooleanStatisticsCalculator:
    def test_empty_logs(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        calculator = BooleanStatisticsCalculator()
        result = calculator.calculate(habit, [])

        assert result.current_streak == 0
        assert result.longest_streak == 0
        assert result.total_completions == 0
        assert result.completion_rate == 0.0

    def test_single_completion(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        logs = [
            LogEntry.create(habit.id, date.today(), 1.0),
        ]

        calculator = BooleanStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.current_streak == 1
        assert result.total_completions == 1
        assert result.completion_rate == 1.0

    def test_consecutive_streak(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 1.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 1.0),
            LogEntry.create(habit.id, today - timedelta(days=2), 1.0),
        ]

        calculator = BooleanStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.current_streak == 3
        assert result.longest_streak == 3

    def test_broken_streak(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 1.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 1.0),
            LogEntry.create(habit.id, today - timedelta(days=5), 1.0),
            LogEntry.create(habit.id, today - timedelta(days=6), 1.0),
        ]

        calculator = BooleanStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.current_streak == 2
        assert result.longest_streak == 2

    def test_incomplete_logs(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 1.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 0.0),
            LogEntry.create(habit.id, today - timedelta(days=2), 1.0),
        ]

        calculator = BooleanStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.total_completions == 2
        assert result.completion_rate == 2 / 3


class TestNumericStatisticsCalculator:
    def test_with_goal(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Read Pages",
            description=None,
            category=None,
            type=HabitType.NUMERIC,
            goal=10.0,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 15.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 12.0),
            LogEntry.create(habit.id, today - timedelta(days=2), 5.0),
        ]

        calculator = NumericStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.total_completions == 2
        assert result.average_value == (15.0 + 12.0 + 5.0) / 3

    def test_without_goal(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Steps",
            description=None,
            category=None,
            type=HabitType.NUMERIC,
            goal=None,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 5000.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 7000.0),
        ]

        calculator = NumericStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.total_completions == 2
        assert result.average_value == 6000.0

    def test_numeric_streak(self) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.NUMERIC,
            goal=10.0,
        )

        today = date.today()
        logs = [
            LogEntry.create(habit.id, today, 15.0),
            LogEntry.create(habit.id, today - timedelta(days=1), 12.0),
            LogEntry.create(habit.id, today - timedelta(days=2), 11.0),
        ]

        calculator = NumericStatisticsCalculator()
        result = calculator.calculate(habit, logs)

        assert result.current_streak == 3


class TestStatisticsCalculatorFactory:
    def test_get_boolean_calculator(self) -> None:
        calculator = StatisticsCalculatorFactory.get_calculator(HabitType.BOOLEAN)
        assert isinstance(calculator, BooleanStatisticsCalculator)

    def test_get_numeric_calculator(self) -> None:
        calculator = StatisticsCalculatorFactory.get_calculator(HabitType.NUMERIC)
        assert isinstance(calculator, NumericStatisticsCalculator)

    def test_register_new_calculator(self) -> None:
        class CustomCalculator(BooleanStatisticsCalculator):
            pass

        custom_type = HabitType.BOOLEAN
        custom_calculator = CustomCalculator()

        StatisticsCalculatorFactory.register_calculator(
            custom_type,
            custom_calculator,
        )

        retrieved = StatisticsCalculatorFactory.get_calculator(custom_type)
        assert isinstance(retrieved, CustomCalculator)
