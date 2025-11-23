# models/log.py
from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class LogBase(BaseModel):
    user_id: UUID = Field(
        ...,
        description="UUID of the user who performed the action.",
        json_schema_extra={"example": "11111111-2222-4333-8444-555555555555"}
    )
    user_name: str = Field(
        ...,
        description="User's display name.",
        json_schema_extra={"example": "Jane Doe"}
    )
    place_name: str = Field(
        ...,
        description="Place related to the action.",
        json_schema_extra={"example": "Tokyo"}
    )
    rating: Optional[float] = Field(
        None,
        ge=1,
        le=5,
        description="Optional user rating.",
        json_schema_extra={"example": 5}
    )
    feedback: Optional[str] = Field(
        None,
        description="Optional feedback text.",
        json_schema_extra={"example": "Loved the sushi and alley restaurants!"}
    )
    action: str = Field(
        ...,
        description="Action performed by the user.",
        json_schema_extra={"example": "visited_place"}
    )


class LogCreate(LogBase):
    pass


class LogRead(LogBase):
    id: int = Field(
        ...,
        description="Numeric ID assigned by the server.",
        json_schema_extra={"example": 42}
    )
    created_at: datetime = Field(
        ...,
        description="When the log was created.",
        json_schema_extra={"example": "2025-11-18T18:23:45Z"}
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 42,
                "user_id": "11111111-2222-4333-8444-555555555555",
                "user_name": "Jane Doe",
                "place_name": "Tokyo",
                "rating": 5,
                "feedback": "Amazing!",
                "action": "visited_place",
                "created_at": "2025-11-18T18:23:45Z"
            }
        }
    }

