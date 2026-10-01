from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.now(UTC)


FLOW_LEVELS = ("spotting", "light", "medium", "heavy")
BLEEDING = ("light", "medium", "heavy")  # spotting does not start/extend a period


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    display_name: str = ""
    created_at: datetime = Field(default_factory=now)
    onboarded: bool = False
    # cycle defaults used until enough history exists
    cycle_length: int = 28
    period_length: int = 5
    luteal_length: int = 14
    goal: str = "track"  # track | conceive | avoid
    birth_year: int | None = None
    temp_unit: str = "C"
    weight_unit: str = "kg"


class DayLog(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    day: date = Field(index=True)
    flow: str | None = None  # None | spotting | light | medium | heavy
    tags: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    temperature: float | None = None  # basal body temp, always °C
    weight: float | None = None  # always kg
    water_ml: int | None = None
    sleep_hours: float | None = None
    notes: str = ""
    updated_at: datetime = Field(default_factory=now)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    role: str  # user | assistant
    content: str
    created_at: datetime = Field(default_factory=now)


class InsightCache(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    day: date
    content: str
    created_at: datetime = Field(default_factory=now)


class Setting(SQLModel, table=True):
    """Server-wide key/value settings (e.g. AI provider), editable in-app by the admin."""

    key: str = Field(primary_key=True)
    value: str = ""
