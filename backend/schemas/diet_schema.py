from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DietSuggestionRequest(BaseModel):
    """User data needed for a simple rule-based nutrition suggestion."""

    user_id: str = Field(..., example="supabase-user-id")
    weight: float = Field(..., gt=0, example=75)
    goal_type: str = Field(..., example="finish")
    category: Literal["Open", "Pro"] = Field(..., example="Open")
    training_days_per_week: int = Field(..., ge=1, le=7, example=5)
    preparation_weeks: int = Field(..., ge=1, example=12)


class DietSuggestion(BaseModel):
    """Nutrition guidance returned to the frontend."""

    daily_calories: int
    protein_range: str
    hydration: str
    carb_strategy: str
    fat_strategy: str
    pre_workout_meal: str
    post_workout_meal: str
    general_tips: List[str]
    disclaimer: str


class DietSuggestionResponse(BaseModel):
    """Response after generating and saving a diet suggestion."""

    message: str
    diet_id: Optional[str] = None
    diet: DietSuggestion


class LatestDietSuggestionResponse(BaseModel):
    """Latest saved diet suggestion returned from Supabase."""

    diet_id: str
    created_at: Optional[str] = None
    diet: DietSuggestion
