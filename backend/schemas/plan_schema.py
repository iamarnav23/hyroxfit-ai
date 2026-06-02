from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from schemas.goal_schema import Goal
from schemas.profile_schema import (
    FitnessProfile,
    HyroxAssessment,
    HyroxStationAssessment,
)


class WorkoutDay(BaseModel):
    """One training day inside a weekly plan."""

    day: str
    workout_type: str
    workout_title: str
    details: str
    hyrox_focus: str
    intensity: str
    duration: str


class TrainingWeek(BaseModel):
    """A week of HYROX training."""

    week: int
    focus: str
    progression_note: str = ""
    weekly_recommendations: List[str] = Field(default_factory=list)
    days: List[WorkoutDay]


class TrainingPlan(BaseModel):
    """Full training plan returned by the plan generator."""

    plan_type: str
    summary: str
    training_phase: str
    station_analysis: List[dict] = Field(default_factory=list)
    weekly_schedule_rules: dict = Field(default_factory=dict)
    weeks: List[TrainingWeek]
    weakness_focus: List[str]
    body_type_adjustments: List[str] = Field(default_factory=list)
    recommendations: List[str]


class PlanRequest(BaseModel):
    """All information needed to generate a HYROX plan."""

    user_id: Optional[str] = None
    fitness_profile: FitnessProfile
    hyrox_assessment: Union[HyroxAssessment, List[HyroxStationAssessment]]
    goal: Goal

    @field_validator("hyrox_assessment", mode="before")
    @classmethod
    def normalize_hyrox_assessment(cls, value):
        """Accept both the old object shape and the new list shape."""
        if isinstance(value, list):
            return {"stations": value}
        return value


class PlanSaveResponse(BaseModel):
    """Response returned by /generate-plan after Stage 6."""

    message: str
    plan_id: Optional[str] = None
    plan: TrainingPlan


class LatestPlanResponse(BaseModel):
    """Latest saved plan returned from Supabase."""

    plan_id: str
    created_at: Optional[str] = None
    plan: TrainingPlan
