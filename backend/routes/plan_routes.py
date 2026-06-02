from fastapi import APIRouter, Header, HTTPException

from database.supabase_client import (
    SupabaseNotConfiguredError,
    extract_bearer_token,
    fetch_latest_plan,
    save_plan_bundle,
    verify_user_access_token,
)
from schemas.plan_schema import LatestPlanResponse, PlanRequest, PlanSaveResponse
from services.plan_generator import generate_training_plan


router = APIRouter(tags=["Training Plan"])


@router.post("/generate-plan", response_model=PlanSaveResponse)
def generate_plan(request: PlanRequest, authorization: str | None = Header(None)):
    """Generate a HYROX plan and save it when a Supabase user is present."""
    plan = generate_training_plan(request)

    if not request.user_id:
        return {
            "message": "Plan generated successfully but was not saved because no user_id was provided",
            "plan_id": None,
            "plan": plan,
        }

    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, request.user_id)
        plan_id = save_plan_bundle(request.user_id, request, plan)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Plan generated but could not be saved: {error}",
        ) from error

    return {
        "message": "Plan generated and saved successfully",
        "plan_id": plan_id,
        "plan": plan,
    }


@router.get("/plans/latest/{user_id}", response_model=LatestPlanResponse)
def get_latest_plan(user_id: str, authorization: str | None = Header(None)):
    """Return the latest saved workout plan for the logged-in user."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, user_id)
        latest_plan = fetch_latest_plan(user_id)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if not latest_plan:
        raise HTTPException(status_code=404, detail="No saved plan found")

    return latest_plan
