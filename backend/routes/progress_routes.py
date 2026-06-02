from fastapi import APIRouter, Header, HTTPException

from database.supabase_client import (
    SupabaseNotConfiguredError,
    extract_bearer_token,
    fetch_dashboard_data,
    fetch_workout_progress,
    save_or_update_workout_progress,
    verify_user_access_token,
)
from schemas.plan_schema import PlanRequest
from schemas.progress_schema import (
    DashboardResponse,
    ReadinessScoreResponse,
    WorkoutProgress,
    WorkoutProgressListResponse,
    WorkoutProgressResponse,
)
from services.readiness_score import calculate_readiness_score


router = APIRouter(tags=["Progress"])


@router.post("/progress")
def save_workout_progress(progress: WorkoutProgress):
    """Validate workout progress data.

    Database saving will be added in a later stage.
    """
    return {
        "message": "Workout progress received",
        "progress": progress,
    }


@router.post("/workout-progress", response_model=WorkoutProgressResponse)
def save_or_update_progress(
    progress: WorkoutProgress, authorization: str | None = Header(None)
):
    """Save or update progress for one workout day."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, progress.user_id)
        saved_progress = save_or_update_workout_progress(progress.model_dump())
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save workout progress: {error}",
        ) from error

    return {
        "message": "Workout progress saved successfully",
        "progress": saved_progress,
    }


@router.get(
    "/workout-progress/{user_id}/{workout_plan_id}",
    response_model=WorkoutProgressListResponse,
)
def get_progress_entries(
    user_id: str,
    workout_plan_id: str,
    authorization: str | None = Header(None),
):
    """Fetch all progress rows for a saved workout plan."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, user_id)
        progress_entries = fetch_workout_progress(user_id, workout_plan_id)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {"progress": progress_entries}


@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
def get_dashboard(user_id: str, authorization: str | None = Header(None)):
    """Return the logged-in user's workout progress dashboard."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, user_id)
        dashboard_data = fetch_dashboard_data(user_id)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return dashboard_data


@router.post("/calculate-readiness-score", response_model=ReadinessScoreResponse)
def get_readiness_score(request: PlanRequest):
    """Calculate a basic race readiness score out of 100."""
    return calculate_readiness_score(request)
