from datetime import date

from pydantic import BaseModel, Field

from app.core.models import HabitType


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, max_length=100)
    type: HabitType = HabitType.BOOLEAN
    goal: float | None = Field(None, gt=0)
    parent_id: str | None = None


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=100)
    goal: float | None = Field(default=None, gt=0)


class HabitRead(BaseModel):
    id: str
    name: str
    description: str | None
    category: str | None
    type: HabitType
    goal: float | None
    parent_id: str | None


class LogCreate(BaseModel):
    date: date
    value: float | None = None


class LogRead(BaseModel):
    id: str
    habit_id: str
    date: date
    value: float | None


class HabitStats(BaseModel):
    habit_id: str
    current_streak: int
    longest_streak: int
    total_completions: int
    completion_rate: float
    average_value: float | None
    total_days_tracked: int
