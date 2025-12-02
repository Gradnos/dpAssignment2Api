"""Unit tests for services."""

import uuid
from datetime import date, timedelta

import pytest

from app.api.schemas import HabitUpdate
from app.core.models import Habit, HabitType
from app.core.services import HabitService
from app.db.in_memory import InMemoryHabitRepository, InMemoryLogRepository


@pytest.fixture
def habit_service() -> HabitService:
    return HabitService(
        habit_repo=InMemoryHabitRepository(),
        log_repo=InMemoryLogRepository(),
    )


@pytest.fixture
def sample_habit() -> Habit:
    return Habit(
        id=str(uuid.uuid4()),
        name="Exercise",
        description="Daily workout",
        category="Health",
        type=HabitType.BOOLEAN,
        goal=None,
    )


class TestHabitCRUD:
    def test_create_habit(
        self, habit_service: HabitService, sample_habit: Habit
    ) -> None:
        habit_service.create_habit(sample_habit)

        retrieved = habit_service.get_habit(sample_habit.id)
        assert retrieved is not None
        assert retrieved.name == sample_habit.name

    def test_get_nonexistent_habit(self, habit_service: HabitService) -> None:
        result = habit_service.get_habit("nonexistent-id")
        assert result is None

    def test_list_habits(self, habit_service: HabitService) -> None:
        habit1 = Habit(
            id=str(uuid.uuid4()),
            name="Habit 1",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )
        habit2 = Habit(
            id=str(uuid.uuid4()),
            name="Habit 2",
            description=None,
            category=None,
            type=HabitType.NUMERIC,
            goal=5.0,
        )

        habit_service.create_habit(habit1)
        habit_service.create_habit(habit2)

        habits = habit_service.list_habits()
        assert len(habits) == 2

    def test_update_habit(
        self, habit_service: HabitService, sample_habit: Habit
    ) -> None:
        habit_service.create_habit(sample_habit)

        update = HabitUpdate(
            name="Updated Exercise",
            description="New description",
            category="Fitness",
            goal=10.0,
        )

        updated = habit_service.update_habit(sample_habit.id, update)

        assert updated.name == "Updated Exercise"
        assert updated.description == "New description"
        assert updated.category == "Fitness"
        assert updated.goal == 10.0

    def test_update_nonexistent_habit(self, habit_service: HabitService) -> None:
        update = HabitUpdate(name="Test")

        with pytest.raises(ValueError, match="Habit not found"):
            habit_service.update_habit("nonexistent-id", update)

    def test_delete_habit(
        self, habit_service: HabitService, sample_habit: Habit
    ) -> None:
        habit_service.create_habit(sample_habit)
        habit_service.delete_habit(sample_habit.id)

        result = habit_service.get_habit(sample_habit.id)
        assert result is None

    def test_delete_nonexistent_habit(self, habit_service: HabitService) -> None:
        with pytest.raises(ValueError, match="Habit not found"):
            habit_service.delete_habit("nonexistent-id")


class TestSubhabits:
    def test_add_subhabit(self, habit_service: HabitService) -> None:
        parent = Habit(
            id=str(uuid.uuid4()),
            name="Morning Routine",
            description=None,
            category="Routines",
            type=HabitType.BOOLEAN,
            goal=None,
        )

        subhabit = Habit(
            id=str(uuid.uuid4()),
            name="Meditate",
            description=None,
            category="Health",
            type=HabitType.BOOLEAN,
            goal=None,
        )

        habit_service.create_habit(parent)
        habit_service.add_subhabit(parent.id, subhabit)

        retrieved_parent = habit_service.get_habit(parent.id)
        retrieved_sub = habit_service.get_habit(subhabit.id)

        assert retrieved_parent is not None
        assert subhabit.id in retrieved_parent.subhabit_ids
        assert retrieved_sub is not None
        assert retrieved_sub.parent_id == parent.id

    def test_add_subhabit_to_nonexistent_parent(
        self,
        habit_service: HabitService,
    ) -> None:
        subhabit = Habit(
            id=str(uuid.uuid4()),
            name="Test",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        with pytest.raises(ValueError, match="Parent habit not found"):
            habit_service.add_subhabit("nonexistent-id", subhabit)

    def test_delete_habit_with_subhabits(self, habit_service: HabitService) -> None:
        parent = Habit(
            id=str(uuid.uuid4()),
            name="Parent",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        sub = Habit(
            id=str(uuid.uuid4()),
            name="Sub",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        habit_service.create_habit(parent)
        habit_service.add_subhabit(parent.id, sub)

        habit_service.delete_habit(parent.id)

        assert habit_service.get_habit(parent.id) is None
        assert habit_service.get_habit(sub.id) is None


class TestLogging:
    def test_record_log(self, habit_service: HabitService, sample_habit: Habit) -> None:
        habit_service.create_habit(sample_habit)

        log = habit_service.record_log(
            habit_id=sample_habit.id,
            date_=date.today(),
            value=1.0,
        )

        assert log.habit_id == sample_habit.id
        assert log.date == date.today()
        assert log.value == 1.0

    def test_record_log_for_nonexistent_habit(
        self,
        habit_service: HabitService,
    ) -> None:
        with pytest.raises(ValueError, match="Habit not found"):
            habit_service.record_log("nonexistent-id", date.today(), 1.0)

    def test_get_logs(self, habit_service: HabitService, sample_habit: Habit) -> None:
        habit_service.create_habit(sample_habit)

        log1 = habit_service.record_log(sample_habit.id, date.today(), 1.0)
        log2 = habit_service.record_log(
            sample_habit.id,
            date.today() - timedelta(days=1),
            1.0,
        )

        logs = habit_service.get_logs(sample_habit.id)

        assert len(logs) == 2
        assert logs[0].id in [log1.id, log2.id]

    def test_get_logs_with_date_range(
        self,
        habit_service: HabitService,
        sample_habit: Habit,
    ) -> None:
        habit_service.create_habit(sample_habit)

        today = date.today()
        habit_service.record_log(sample_habit.id, today, 1.0)
        habit_service.record_log(sample_habit.id, today - timedelta(days=5), 1.0)
        habit_service.record_log(sample_habit.id, today - timedelta(days=10), 1.0)

        logs = habit_service.get_logs(
            sample_habit.id,
            start=today - timedelta(days=7),
        )

        assert len(logs) == 2

    def test_get_logs_for_nonexistent_habit(
        self,
        habit_service: HabitService,
    ) -> None:
        with pytest.raises(ValueError, match="Habit not found"):
            habit_service.get_logs("nonexistent-id")


class TestStatistics:
    def test_boolean_habit_statistics(
        self,
        habit_service: HabitService,
    ) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Exercise",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        habit_service.create_habit(habit)

        # Create a streak
        today = date.today()
        for i in range(5):
            habit_service.record_log(
                habit.id,
                today - timedelta(days=i),
                1.0,
            )

        stats = habit_service.get_statistics(habit.id)

        assert stats["current_streak"] == 5
        assert stats["total_completions"] == 5
        assert stats["completion_rate"] == 1.0

    def test_numeric_habit_statistics(
        self,
        habit_service: HabitService,
    ) -> None:
        habit = Habit(
            id=str(uuid.uuid4()),
            name="Read Pages",
            description=None,
            category=None,
            type=HabitType.NUMERIC,
            goal=10.0,
        )

        habit_service.create_habit(habit)

        today = date.today()
        habit_service.record_log(habit.id, today, 15.0)
        habit_service.record_log(habit.id, today - timedelta(days=1), 12.0)
        habit_service.record_log(habit.id, today - timedelta(days=2), 5.0)

        stats = habit_service.get_statistics(habit.id)

        assert stats["total_completions"] == 2  # Only 15 and 12 meet goal
        assert stats["average_value"] == (15.0 + 12.0 + 5.0) / 3

    def test_statistics_for_nonexistent_habit(
        self,
        habit_service: HabitService,
    ) -> None:
        with pytest.raises(ValueError, match="Habit not found"):
            habit_service.get_statistics("nonexistent-id")
