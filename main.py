import os

from fastapi import FastAPI

from app.api.controllers import create_router
from app.core.services import HabitService
from app.db.in_memory import InMemoryHabitRepository, InMemoryLogRepository
from app.db.repository import HabitRepository, LogRepository
from app.db.sqlite import SQLiteHabitRepository, SQLiteLogRepository


def build_app() -> FastAPI:
    # default is in memory
    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"

    habit_repo: HabitRepository
    log_repo: LogRepository

    if use_sqlite:
        db_path = os.getenv("DB_PATH", "habits.db")  # default base is habits.db
        habit_repo = SQLiteHabitRepository(db_path)
        log_repo = SQLiteLogRepository(db_path)
    else:
        habit_repo = InMemoryHabitRepository()
        log_repo = InMemoryLogRepository()

    habit_service = HabitService(
        habit_repo=habit_repo,
        log_repo=log_repo,
    )

    app = FastAPI()
    app.include_router(create_router(habit_service))

    return app


app = build_app()
