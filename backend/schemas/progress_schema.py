from typing import List, Optional

from pydantic import BaseModel, Field


class WorkoutProgress(BaseModel):
    """User feedback after completing a workout."""

    user_id: str = Field(..., example="supabase-user-id")
    workout_plan_id: str = Field(..., example="saved-plan-id")
    workout_id: str = Field(..., example="week-1-day-monday")
    completed: bool = Field(..., example=True)
    time_taken: str = Field(..., example="35 minutes")
    energy_level: str = Field(..., example="high")
    difficulty_level: str = Field(..., example="medium")
    notes: str = Field(..., example="Felt good but sled push was hard")


class WorkoutProgressResponse(BaseModel):
    """Response returned after saving a workout progress entry."""

    message: str
    progress: dict


class WorkoutProgressListResponse(BaseModel):
    """All progress entries for one saved workout plan."""

    progress: List[dict]


class ReadinessScoreBreakdown(BaseModel):
    """Score categories that add up to 100."""

    running: int
    strength: int
    hyrox_skill: int
    consistency: int
    recovery_diet: int


class ReadinessScoreResponse(BaseModel):
    """Race readiness score response."""

    total_score: int
    status: str
    breakdown: ReadinessScoreBreakdown


class DashboardResponse(BaseModel):
    """Progress dashboard data for the logged-in user."""

    total_workouts: int
    completed_workouts: int
    completion_percentage: int
    consistency_score: int
    latest_plan_type: Optional[str]
    current_training_phase: Optional[str]
    weak_areas: List[str]
    race_readiness_score: ReadinessScoreResponse
    recent_notes: List[dict]
    performance_scores: dict = Field(default_factory=dict)
    weakness_analysis: List[dict] = Field(default_factory=list)
    progress_trends: List[dict] = Field(default_factory=list)
    adaptive_coaching_insights: List[str] = Field(default_factory=list)
    current_week_number: Optional[int] = None
    current_week_focus: Optional[str] = None
    latest_ai_coach_advice: Optional[dict] = None
    cardio_lab_summary: Optional[dict] = None
    weekly_recovery_recommendation: str = ""
