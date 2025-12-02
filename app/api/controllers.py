import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status

from app.api import schemas
from app.core.models import Habit
from app.core.services import HabitService


def create_router(habit_service: HabitService) -> APIRouter:
    router = APIRouter(prefix="/habits", tags=["habits"])

    @router.post(
        "", response_model=schemas.HabitRead, status_code=status.HTTP_201_CREATED
    )
    def create_habit(payload: schemas.HabitCreate) -> schemas.HabitRead:
        habit = Habit(
            id=str(uuid.uuid4()),
            name=payload.name,
            description=payload.description,
            category=payload.category,
            type=payload.type,
            goal=payload.goal,
            parent_id=payload.parent_id,
        )

        habit_service.create_habit(habit)
        return schemas.HabitRead(**habit.__dict__)

    @router.get("", response_model=list[schemas.HabitRead])
    def list_habits() -> list[schemas.HabitRead]:
        habits = habit_service.list_habits()
        return [schemas.HabitRead(**h.__dict__) for h in habits]

    @router.get("/{habit_id}", response_model=schemas.HabitRead)
    def get_habit(habit_id: str) -> schemas.HabitRead:
        habit = habit_service.get_habit(habit_id)
        if habit is None:
            raise HTTPException(status_code=404, detail="Habit not found")

        return schemas.HabitRead(**habit.__dict__)

    @router.put("/{habit_id}", response_model=schemas.HabitRead)
    def update_habit(
        habit_id: str,
        payload: schemas.HabitUpdate,
    ) -> schemas.HabitRead:
        try:
            habit = habit_service.update_habit(habit_id, payload)
            return schemas.HabitRead(**habit.__dict__)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_habit(habit_id: str) -> None:
        try:
            habit_service.delete_habit(habit_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post(
        "/{habit_id}/subhabits",
        response_model=schemas.HabitRead,
        status_code=status.HTTP_201_CREATED,
    )
    def add_subhabit(
        habit_id: str,
        payload: schemas.HabitCreate,
    ) -> schemas.HabitRead:
        sub = Habit(
            id=str(uuid.uuid4()),
            name=payload.name,
            description=payload.description,
            category=payload.category,
            type=payload.type,
            goal=payload.goal,
            parent_id=habit_id,
        )

        try:
            habit_service.add_subhabit(habit_id, sub)
            return schemas.HabitRead(**sub.__dict__)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post(
        "/{habit_id}/logs",
        response_model=schemas.LogRead,
        status_code=status.HTTP_201_CREATED,
    )
    def record_log(
        habit_id: str,
        payload: schemas.LogCreate,
    ) -> schemas.LogRead:
        try:
            log = habit_service.record_log(
                habit_id=habit_id,
                date_=payload.date,
                value=payload.value,
            )
            return schemas.LogRead(**log.__dict__)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/{habit_id}/logs", response_model=list[schemas.LogRead])
    def get_logs(
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[schemas.LogRead]:
        try:
            logs = habit_service.get_logs(habit_id, start, end)
            return [schemas.LogRead(**log.__dict__) for log in logs]
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/{habit_id}/stats", response_model=schemas.HabitStats)
    def get_stats(
        habit_id: str,
        start: date | None = None,
        end: date | None = None,
    ) -> schemas.HabitStats:
        try:
            stats = habit_service.get_statistics(habit_id, start, end)
            return schemas.HabitStats(**stats)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return router
