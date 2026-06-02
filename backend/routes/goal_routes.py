from fastapi import APIRouter

from schemas.goal_schema import Goal


router = APIRouter(tags=["Goal"])


@router.post("/goal")
def save_goal(goal: Goal):
    """Validate the user's HYROX goal.

    For this MVP, the route only returns the submitted data.
    """
    return {
        "message": "Goal received",
        "goal": goal,
    }
