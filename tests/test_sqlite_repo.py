import os
import tempfile
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Generator  # noqa: UP035

import pytest

from app.core.models import Habit, HabitType, LogEntry
from app.db.sqlite import SQLiteHabitRepository, SQLiteLogRepository


@pytest.fixture
def temp_db() -> Generator[str]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def habit_repo(temp_db: str) -> SQLiteHabitRepository:
    return SQLiteHabitRepository(temp_db)


@pytest.fixture
def log_repo(temp_db: str) -> SQLiteLogRepository:
    return SQLiteLogRepository(temp_db)


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


class TestSQLiteHabitRepository:
    def test_add_and_get(
        self,
        habit_repo: SQLiteHabitRepository,
        sample_habit: Habit,
    ) -> None:
        habit_repo.add(sample_habit)
        retrieved = habit_repo.get(sample_habit.id)

        assert retrieved is not None
        assert retrieved.id == sample_habit.id
        assert retrieved.name == sample_habit.name
        assert retrieved.type == sample_habit.type

    def test_get_nonexistent(self, habit_repo: SQLiteHabitRepository) -> None:
        result = habit_repo.get("nonexistent-id")
        assert result is None

    def test_list(self, habit_repo: SQLiteHabitRepository) -> None:
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
            goal=10.0,
        )

        habit_repo.add(habit1)
        habit_repo.add(habit2)

        habits = habit_repo.list()
        assert len(habits) == 2
        assert any(h.id == habit1.id for h in habits)
        assert any(h.id == habit2.id for h in habits)

    def test_update(
        self,
        habit_repo: SQLiteHabitRepository,
        sample_habit: Habit,
    ) -> None:
        habit_repo.add(sample_habit)

        sample_habit.name = "Updated Name"
        sample_habit.description = "Updated description"
        habit_repo.update(sample_habit)

        retrieved = habit_repo.get(sample_habit.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Name"
        assert retrieved.description == "Updated description"

    def test_update_nonexistent(
        self,
        habit_repo: SQLiteHabitRepository,
        sample_habit: Habit,
    ) -> None:
        with pytest.raises(KeyError, match="Habit not found"):
            habit_repo.update(sample_habit)

    def test_delete(
        self,
        habit_repo: SQLiteHabitRepository,
        sample_habit: Habit,
    ) -> None:
        habit_repo.add(sample_habit)
        habit_repo.delete(sample_habit.id)

        result = habit_repo.get(sample_habit.id)
        assert result is None

    def test_subhabit_ids_persistence(
        self,
        habit_repo: SQLiteHabitRepository,
    ) -> None:
        parent = Habit(
            id=str(uuid.uuid4()),
            name="Parent",
            description=None,
            category=None,
            type=HabitType.BOOLEAN,
            goal=None,
        )

        sub_id = str(uuid.uuid4())
        parent.subhabit_ids.append(sub_id)

        habit_repo.add(parent)
        retrieved = habit_repo.get(parent.id)

        assert retrieved is not None
        assert sub_id in retrieved.subhabit_ids


class TestSQLiteLogRepository:
    def test_add_and_list(
        self,
        log_repo: SQLiteLogRepository,
        sample_habit: Habit,
    ) -> None:
        log = LogEntry.create(
            habit_id=sample_habit.id,
            date_=date.today(),
            value=1.0,
        )

        log_repo.add(log)
        logs = log_repo.list_for_habit(sample_habit.id)

        assert len(logs) == 1
        assert logs[0].id == log.id
        assert logs[0].value == 1.0

    def test_list_for_habit_filters_by_habit(
        self,
        log_repo: SQLiteLogRepository,
    ) -> None:
        habit1_id = str(uuid.uuid4())
        habit2_id = str(uuid.uuid4())

        log1 = LogEntry.create(habit1_id, date.today(), 1.0)
        log2 = LogEntry.create(habit2_id, date.today(), 1.0)

        log_repo.add(log1)
        log_repo.add(log2)

        logs = log_repo.list_for_habit(habit1_id)

        assert len(logs) == 1
        assert logs[0].habit_id == habit1_id

    def test_list_for_habit_with_date_range(
        self,
        log_repo: SQLiteLogRepository,
    ) -> None:
        habit_id = str(uuid.uuid4())
        today = date.today()

        log1 = LogEntry.create(habit_id, today, 1.0)
        log2 = LogEntry.create(habit_id, today - timedelta(days=5), 1.0)
        log3 = LogEntry.create(habit_id, today - timedelta(days=10), 1.0)

        log_repo.add(log1)
        log_repo.add(log2)
        log_repo.add(log3)

        logs = log_repo.list_for_habit(
            habit_id,
            start=today - timedelta(days=7),
        )

        assert len(logs) == 2
        assert all(log.date >= today - timedelta(days=7) for log in logs)

    def test_list_all(self, log_repo: SQLiteLogRepository) -> None:
        habit1_id = str(uuid.uuid4())
        habit2_id = str(uuid.uuid4())

        log1 = LogEntry.create(habit1_id, date.today(), 1.0)
        log2 = LogEntry.create(habit2_id, date.today(), 1.0)

        log_repo.add(log1)
        log_repo.add(log2)

        all_logs = log_repo.list_all()
        assert len(all_logs) == 2

    def test_logs_sorted_by_date(
        self,
        log_repo: SQLiteLogRepository,
    ) -> None:
        habit_id = str(uuid.uuid4())
        today = date.today()

        log1 = LogEntry.create(habit_id, today - timedelta(days=2), 1.0)
        log2 = LogEntry.create(habit_id, today, 1.0)
        log3 = LogEntry.create(habit_id, today - timedelta(days=1), 1.0)

        log_repo.add(log1)
        log_repo.add(log2)
        log_repo.add(log3)

        logs = log_repo.list_for_habit(habit_id)

        assert logs[0].date == today - timedelta(days=2)
        assert logs[1].date == today - timedelta(days=1)
        assert logs[2].date == today
