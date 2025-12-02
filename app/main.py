from fastapi import FastAPI

from app.api.controllers import create_router
from app.core.services import HabitService
from app.db.in_memory import InMemoryHabitRepository, InMemoryLogRepository


def build_app() -> FastAPI:
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
