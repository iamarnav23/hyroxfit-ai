from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


CardioGoal = Literal[
    "HYROX endurance",
    "Marathon preparation",
    "General cardiovascular health",
    "Zone 5 / VO2 max improvement",
    "Fat loss endurance",
    "Mixed endurance performance",
]

TrainingMode = Literal["Running", "Cycling", "Swimming", "Mixed"]
ExperienceLevel = Literal["beginner", "intermediate", "advanced"]
EnergyLevel = Literal["low", "medium", "high"]
DifficultyLevel = Literal["easy", "medium", "hard"]


class CardioPlanRequest(BaseModel):
    """Input needed to build a one-week Cardio Lab plan."""

    user_id: str = Field(..., example="supabase-user-id")
    cardio_goal: CardioGoal
    preferred_training_mode: TrainingMode
    experience_level: ExperienceLevel
    training_days_per_week: int = Field(..., ge=2, le=6, example=4)
    current_1km_time: Optional[str] = None
    current_5km_time: Optional[str] = None
    current_long_run_distance: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    available_session_duration: str = Field(..., example="30-45 min")
    injury_or_limitation: Optional[str] = ""
    week_number: int = Field(default=1, ge=1)


class CardioTrainingZone(BaseModel):
    """One heart-rate/RPE training zone."""

    zone: str
    purpose: str
    percent_max_hr: str
    rpe: str
    heart_rate_range: Optional[str] = None


class CardioWorkoutDay(BaseModel):
    """One day in a Cardio Lab week plan."""

    day: str
    workout_type: str
    training_mode: str
    zone: str
    workout_title: str
    details: str
    intensity: str
    duration: str
    rpe: str
    coaching_tip: str
    safety_note: str


class CardioWeekPlan(BaseModel):
    """One complete one-week cardio plan."""

    week_number: int
    cardio_goal: Optional[str] = None
    preferred_training_mode: Optional[str] = None
    experience_level: Optional[str] = None
    training_days_per_week: Optional[int] = None
    week_summary: str
    plan_reasoning: str
    training_zones: List[CardioTrainingZone]
    days: List[CardioWorkoutDay]
    zone_distribution: Dict[str, int]
    progression_advice: str
    recovery_advice: str
    safety_disclaimer: str
    ai_status: str = "rule_based"


class CardioAIPlanOutput(BaseModel):
    """Structured output requested from OpenAI for Cardio Lab refinement."""

    week_summary: str
    plan_reasoning: str
    days: List[CardioWorkoutDay]
    zone_distribution: Dict[str, int]
    progression_advice: str
    recovery_advice: str
    safety_disclaimer: str


class CardioPlanResponse(BaseModel):
    """Response returned after generating and saving a cardio plan."""

    message: str
    cardio_plan_id: Optional[str] = None
    plan: CardioWeekPlan


class CurrentCardioPlanResponse(BaseModel):
    """Latest saved Cardio Lab plan for a user."""

    cardio_plan_id: str
    cardio_profile_id: Optional[str] = None
    created_at: Optional[str] = None
    plan: CardioWeekPlan


class CardioWeeklyReview(BaseModel):
    """Weekly review submitted by the user after trying a cardio plan."""

    user_id: str
    cardio_plan_id: str
    week_number: int = Field(..., ge=1)
    workouts_completed: int = Field(..., ge=0)
    total_workouts: int = Field(..., ge=0)
    average_energy_level: EnergyLevel
    average_difficulty: DifficultyLevel
    hardest_session: str
    updated_1km_time: Optional[str] = None
    updated_5km_time: Optional[str] = None
    notes: Optional[str] = ""


class CardioReviewResponse(BaseModel):
    """Response after saving a weekly review."""

    message: str
    review: dict
    next_week_adjustment: dict


class GenerateNextCardioWeekRequest(BaseModel):
    """Request for generating the next adaptive cardio week."""

    user_id: str
    previous_cardio_plan_id: str
