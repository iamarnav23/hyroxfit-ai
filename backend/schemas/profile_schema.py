from typing import List, Literal

from pydantic import BaseModel, Field


class FitnessProfile(BaseModel):
    """User's general fitness and training background."""

    age: int = Field(..., example=24)
    gender: str = Field(..., example="male")
    height: float = Field(..., example=175.0)
    weight: float = Field(..., example=72.0)
    body_type: str = Field(..., example="athletic")
    training_experience: Literal["beginner", "intermediate", "advanced"]
    training_days_per_week: int = Field(..., ge=1, le=7, example=4)
    injury_history: str = Field(..., example="No major injuries")


class HyroxStationAssessment(BaseModel):
    """Performance data for one HYROX station."""

    station_name: str = Field(..., example="Sled push")
    level: Literal["beginner", "intermediate", "advanced"]
    current_value: str = Field(..., example="50 kg for 20 meters")
    difficulty: Literal["easy", "medium", "hard"]


class HyroxAssessment(BaseModel):
    """Collection of HYROX station assessments."""

    stations: List[HyroxStationAssessment]
