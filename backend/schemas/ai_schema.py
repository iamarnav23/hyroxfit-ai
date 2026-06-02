from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.plan_schema import TrainingPlan


class PlanPersonalizationRequest(BaseModel):
    """Request for AI coaching notes on an existing rule-based plan."""

    user_id: str = Field(..., example="supabase-user-id")
    plan_id: str = Field(..., example="saved-plan-id")


class PlanAdjustmentRequest(BaseModel):
    """Request where the user describes a problem with their training plan."""

    user_id: str = Field(..., example="supabase-user-id")
    plan_id: str = Field(..., example="saved-plan-id")
    user_message: str = Field(..., example="This plan is too hard.")


class DietAdjustmentRequest(BaseModel):
    """Request where the user describes a nutrition problem."""

    user_id: str = Field(..., example="supabase-user-id")
    user_message: str = Field(..., example="I feel low energy during workouts.")


class ApplyPlanChangesRequest(BaseModel):
    """Request to apply AI plan changes after the user approves them."""

    user_id: str = Field(..., example="supabase-user-id")
    plan_id: str = Field(..., example="saved-plan-id")
    ai_recommendation_id: str = Field(..., example="ai-recommendation-id")


class WeeklyCoachingNote(BaseModel):
    week: int
    note: str


class WeaknessStrategy(BaseModel):
    weakness: str
    strategy: str


class PlanPersonalizationOutput(BaseModel):
    personalized_summary: str
    why_this_plan_fits: str
    weekly_coaching_notes: List[WeeklyCoachingNote]
    weakness_strategy: List[WeaknessStrategy]
    recovery_advice: str
    safety_note: str


class RecommendedChange(BaseModel):
    change_type: str
    reason: str
    details: str


class ModifiedWorkout(BaseModel):
    workout_id: str
    old_workout_title: str
    new_workout_title: str
    new_details: str
    new_intensity: str
    new_duration: str


class UpdatedPlanPreview(BaseModel):
    weeks_to_modify: List[int]
    modified_workouts: List[ModifiedWorkout]


class PlanAdjustmentOutput(BaseModel):
    issue_detected: str
    coach_response: str
    recommended_changes: List[RecommendedChange]
    updated_plan_preview: UpdatedPlanPreview
    safety_note: str
    requires_user_approval: bool


class DietAdjustment(BaseModel):
    adjustment_type: str
    details: str


class CalorieAdjustment(BaseModel):
    suggested_change: str
    reason: str


class DietAdjustmentOutput(BaseModel):
    issue_detected: str
    coach_response: str
    diet_adjustments: List[DietAdjustment]
    calorie_adjustment: CalorieAdjustment
    meal_timing_advice: str
    hydration_advice: str
    safety_note: str
    requires_user_approval: bool


class AIRecommendationResponse(BaseModel):
    """Generic response after AI output is generated and saved."""

    message: str
    ai_recommendation_id: str
    recommendation_type: str
    result: dict


class ApplyPlanChangesResponse(BaseModel):
    """Response after AI changes are applied as a new plan version."""

    message: str
    plan_id: str
    parent_plan_id: Optional[str] = None
    version_number: int
    plan: TrainingPlan
