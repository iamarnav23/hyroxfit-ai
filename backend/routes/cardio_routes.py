from fastapi import APIRouter, Header, HTTPException

from database.supabase_client import (
    SupabaseNotConfiguredError,
    build_next_cardio_request_from_saved,
    extract_bearer_token,
    fetch_cardio_plan_row,
    fetch_current_cardio_plan,
    fetch_latest_cardio_review,
    save_cardio_week_plan_bundle,
    save_cardio_week_review,
    verify_user_access_token,
)
from schemas.cardio_schema import (
    CardioPlanRequest,
    CardioPlanResponse,
    CardioReviewResponse,
    CardioWeeklyReview,
    CurrentCardioPlanResponse,
    GenerateNextCardioWeekRequest,
)
from services.cardio_ai import personalize_cardio_plan_with_ai
from services.cardio_generator import generate_base_cardio_plan, get_next_week_adjustment


router = APIRouter(prefix="/cardio", tags=["Cardio Lab"])


@router.post("/generate-week-plan", response_model=CardioPlanResponse)
def generate_cardio_week_plan(
    request: CardioPlanRequest, authorization: str | None = Header(None)
):
    """Generate, AI-refine when possible, and save a one-week Cardio Lab plan."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, request.user_id)

        base_plan = generate_base_cardio_plan(request)
        plan = personalize_cardio_plan_with_ai(request.model_dump(), base_plan)
        cardio_plan_id = save_cardio_week_plan_bundle(request.user_id, request, plan)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate Cardio Lab plan: {error}",
        ) from error

    return {
        "message": "Cardio week plan generated successfully",
        "cardio_plan_id": cardio_plan_id,
        "plan": plan,
    }


@router.get("/current-plan/{user_id}", response_model=CurrentCardioPlanResponse)
def get_current_cardio_plan(user_id: str, authorization: str | None = Header(None)):
    """Return the latest saved Cardio Lab plan for the logged-in user."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, user_id)
        current_plan = fetch_current_cardio_plan(user_id)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if not current_plan:
        raise HTTPException(status_code=404, detail="No Cardio Lab plan found")

    return current_plan


@router.post("/weekly-review", response_model=CardioReviewResponse)
def save_weekly_review(
    review: CardioWeeklyReview, authorization: str | None = Header(None)
):
    """Save a weekly review and return the next-week adjustment recommendation."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, review.user_id)

        plan_row = fetch_cardio_plan_row(review.user_id, review.cardio_plan_id)
        if not plan_row:
            raise RuntimeError("Cardio plan was not found")

        saved_review = save_cardio_week_review(review)
        adjustment = get_next_week_adjustment(review)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save Cardio Lab review: {error}",
        ) from error

    return {
        "message": "Cardio weekly review saved successfully",
        "review": saved_review,
        "next_week_adjustment": adjustment,
    }


@router.post("/generate-next-week-plan", response_model=CardioPlanResponse)
def generate_next_cardio_week_plan(
    request: GenerateNextCardioWeekRequest,
    authorization: str | None = Header(None),
):
    """Generate next week's Cardio Lab plan from the latest review feedback."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, request.user_id)

        previous_plan = fetch_cardio_plan_row(
            request.user_id, request.previous_cardio_plan_id
        )
        if not previous_plan:
            raise RuntimeError("Previous Cardio Lab plan was not found")

        review = fetch_latest_cardio_review(
            request.user_id, request.previous_cardio_plan_id
        )
        next_request = build_next_cardio_request_from_saved(
            request.user_id, previous_plan, review
        )
        base_plan = generate_base_cardio_plan(next_request, review)
        plan = personalize_cardio_plan_with_ai(
            next_request.model_dump(), base_plan, review
        )
        cardio_plan_id = save_cardio_week_plan_bundle(
            request.user_id,
            next_request,
            plan,
            cardio_profile_id=previous_plan.get("cardio_profile_id"),
        )
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate next Cardio Lab week: {error}",
        ) from error

    return {
        "message": "Next cardio week plan generated successfully",
        "cardio_plan_id": cardio_plan_id,
        "plan": plan,
    }
