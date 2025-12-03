import json
import sqlite3
from datetime import date, datetime
from typing import Any

from app.core.models import Habit, HabitType, LogEntry
from app.db.repository import HabitRepository, LogRepository


class SQLiteHabitRepository(HabitRepository):
    def __init__(self, db_path: str = "habits.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    type TEXT NOT NULL,
                    goal REAL,
                    created_at TEXT NOT NULL,
                    parent_id TEXT,
                    subhabit_ids TEXT NOT NULL
                )
            """)
            conn.commit()

    def _habit_from_row(self, row: tuple[Any, ...]) -> Habit:
        return Habit(
            id=row[0],
            name=row[1],
            description=row[2],
            category=row[3],
            type=HabitType(row[4]),
            goal=row[5],
            created_at=datetime.fromisoformat(row[6]),
            parent_id=row[7],
            subhabit_ids=json.loads(row[8]),
        )

    def add(self, habit: Habit) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO habits
                (id, name, description, category, type, goal,
                created_at, parent_id, subhabit_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    habit.id,
                    habit.name,
                    habit.description,
                    habit.category,
                    habit.type.value,
                    habit.goal,
                    habit.created_at.isoformat(),
                    habit.parent_id,
                    json.dumps(habit.subhabit_ids),
                ),
            )
            conn.commit()

    def get(self, habit_id: str) -> Habit | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM habits WHERE id = ?",
                (habit_id,),
            )
            row = cursor.fetchone()
            return self._habit_from_row(row) if row else None

    def list(self) -> list[Habit]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM habits")
            return [self._habit_from_row(row) for row in cursor.fetchall()]

    def update(self, habit: Habit) -> None:
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE habits
                SET name = ?, description = ?, category = ?,
                    goal = ?, subhabit_ids = ?
                WHERE id = ?
                """,
                (
                    habit.name,
                    habit.description,
                    habit.category,
                    habit.goal,
                    json.dumps(habit.subhabit_ids),
                    habit.id,
                ),
            )
            if result.rowcount == 0:
                raise KeyError("Habit not found")
            conn.commit()

    def delete(self, habit_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            conn.commit()


class SQLiteLogRepository(LogRepository):
    def __init__(self, db_path: str = "habits.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    habit_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    value REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_habit_id
                ON logs(habit_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_date
                ON logs(date)
            """)
            conn.commit()

    def _log_from_row(self, row: tuple[Any, ...]) -> LogEntry:
        return LogEntry(
            id=row[0],
            habit_id=row[1],
            date=date.fromisoformat(row[2]),
            value=row[3],
            created_at=datetime.fromisoformat(row[4]),
        )

    def add(self, log: LogEntry) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO logs (id, habit_id, date, value, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.habit_id,
                    log.date.isoformat(),
                    log.value,
                    log.created_at.isoformat(),
                ),
            )
            conn.commit()

    def list_for_habit(
        self,
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[LogEntry]:
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM logs WHERE habit_id = ?"
            params: list[Any] = [habit_id]

            if start is not None:
                query += " AND date >= ?"
                params.append(start.isoformat())

            if end is not None:
                query += " AND date <= ?"
                params.append(end.isoformat())

            query += " ORDER BY date"

            cursor = conn.execute(query, params)
            return [self._log_from_row(row) for row in cursor.fetchall()]

    def list_all(self) -> list[LogEntry]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM logs")
            return [self._log_from_row(row) for row in cursor.fetchall()]
