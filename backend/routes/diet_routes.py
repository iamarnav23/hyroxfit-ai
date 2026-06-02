from fastapi import APIRouter, Header, HTTPException

from database.supabase_client import (
    SupabaseNotConfiguredError,
    extract_bearer_token,
    fetch_latest_diet_suggestion,
    save_diet_suggestion,
    verify_user_access_token,
)
from schemas.diet_schema import (
    DietSuggestionRequest,
    DietSuggestionResponse,
    LatestDietSuggestionResponse,
)
from services.diet_generator import generate_diet_suggestion


router = APIRouter(tags=["Diet"])


@router.post("/diet-suggestion", response_model=DietSuggestionResponse)
def create_diet_suggestion(
    request: DietSuggestionRequest, authorization: str | None = Header(None)
):
    """Generate a rule-based diet suggestion and save it for the user."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, request.user_id)
        diet = generate_diet_suggestion(request)
        diet_id = save_diet_suggestion(request, diet)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Diet suggestion generated but could not be saved: {error}",
        ) from error

    return {
        "message": "Diet suggestion generated successfully",
        "diet_id": diet_id,
        "diet": diet,
    }


@router.get(
    "/diet-suggestion/latest/{user_id}",
    response_model=LatestDietSuggestionResponse,
)
def get_latest_diet_suggestion(
    user_id: str, authorization: str | None = Header(None)
):
    """Return the latest saved diet suggestion for the logged-in user."""
    try:
        access_token = extract_bearer_token(authorization)
        verify_user_access_token(access_token, user_id)
        latest_diet = fetch_latest_diet_suggestion(user_id)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if not latest_diet:
        raise HTTPException(status_code=404, detail="No saved diet suggestion found")

    return latest_diet
