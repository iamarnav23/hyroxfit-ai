from typing import Literal

from pydantic import BaseModel, Field


class Goal(BaseModel):
    """The user's race goal and preparation target."""

    preparation_reason: str = Field(..., example="Preparing for my first HYROX race")
    category: Literal["Open", "Pro"]
    target_time: str = Field(..., example="1:30:00")
    preparation_weeks: int = Field(..., ge=1, example=12)
    main_weakness: str = Field(..., example="Sled push")
    goal_type: Literal["finish", "improve", "compete"]
