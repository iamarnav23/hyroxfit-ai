from fastapi import APIRouter, Header, HTTPException

from database.supabase_client import (
    SupabaseNotConfiguredError,
    apply_ai_plan_changes,
    extract_bearer_token,
    fetch_ai_context,
    save_ai_recommendation,
    verify_user_access_token,
)
from schemas.ai_schema import (
    AIRecommendationResponse,
    ApplyPlanChangesRequest,
    ApplyPlanChangesResponse,
    DietAdjustmentRequest,
    PlanAdjustmentRequest,
    PlanPersonalizationRequest,
)
from services.ai_coach import (
    AICoachUnavailableError,
    AIResponseValidationError,
    adjust_diet,
    adjust_plan,
    personalize_plan,
)


router = APIRouter(prefix="/ai", tags=["AI Coach"])


def verify_request_user(user_id: str, authorization: str | None) -> None:
    """Validate that the frontend token belongs to the submitted user."""
    access_token = extract_bearer_token(authorization)
    verify_user_access_token(access_token, user_id)


def ai_unavailable_error() -> HTTPException:
    """Return the standard Stage 9 fallback error."""
    return HTTPException(
        status_code=503,
        detail={
            "error": "AI coach is temporarily unavailable. Your rule-based plan is still safe to use."
        },
    )


@router.post("/personalize-plan", response_model=AIRecommendationResponse)
def personalize_existing_plan(
    request: PlanPersonalizationRequest,
    authorization: str | None = Header(None),
):
    """Add AI coaching notes to an existing rule-based plan."""
    try:
        verify_request_user(request.user_id, authorization)
        context = fetch_ai_context(request.user_id, request.plan_id)
        if context.get("plan_id") != request.plan_id:
            raise HTTPException(status_code=404, detail="Saved plan was not found")
        result = personalize_plan(context)
        recommendation_id = save_ai_recommendation(
            user_id=request.user_id,
            plan_id=request.plan_id,
            recommendation_type="plan_personalization",
            ai_response=result,
        )
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except AICoachUnavailableError as error:
        raise ai_unavailable_error() from error
    except AIResponseValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="AI response could not be validated. Please try again.",
        ) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "message": "AI plan personalization generated successfully",
        "ai_recommendation_id": recommendation_id,
        "recommendation_type": "plan_personalization",
        "result": result,
    }


@router.post("/adjust-plan", response_model=AIRecommendationResponse)
def create_plan_adjustment(
    request: PlanAdjustmentRequest,
    authorization: str | None = Header(None),
):
    """Suggest safe plan changes without applying them automatically."""
    try:
        verify_request_user(request.user_id, authorization)
        context = fetch_ai_context(request.user_id, request.plan_id)
        if context.get("plan_id") != request.plan_id:
            raise HTTPException(status_code=404, detail="Saved plan was not found")
        result = adjust_plan(context, request.user_message)
        recommendation_id = save_ai_recommendation(
            user_id=request.user_id,
            plan_id=request.plan_id,
            recommendation_type="plan_adjustment",
            user_message=request.user_message,
            ai_response=result,
        )
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except AICoachUnavailableError as error:
        raise ai_unavailable_error() from error
    except AIResponseValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="AI response could not be validated. Please try again.",
        ) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "message": "AI plan adjustment generated successfully",
        "ai_recommendation_id": recommendation_id,
        "recommendation_type": "plan_adjustment",
        "result": result,
    }


@router.post("/adjust-diet", response_model=AIRecommendationResponse)
def create_diet_adjustment(
    request: DietAdjustmentRequest,
    authorization: str | None = Header(None),
):
    """Suggest safe diet adjustments without overwriting saved diet guidance."""
    try:
        verify_request_user(request.user_id, authorization)
        context = fetch_ai_context(request.user_id)
        result = adjust_diet(context, request.user_message)
        recommendation_id = save_ai_recommendation(
            user_id=request.user_id,
            plan_id=context.get("plan_id"),
            recommendation_type="diet_adjustment",
            user_message=request.user_message,
            ai_response=result,
        )
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except AICoachUnavailableError as error:
        raise ai_unavailable_error() from error
    except AIResponseValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="AI response could not be validated. Please try again.",
        ) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "message": "AI diet adjustment generated successfully",
        "ai_recommendation_id": recommendation_id,
        "recommendation_type": "diet_adjustment",
        "result": result,
    }


@router.post("/apply-plan-changes", response_model=ApplyPlanChangesResponse)
def apply_plan_changes(
    request: ApplyPlanChangesRequest,
    authorization: str | None = Header(None),
):
    """Apply approved AI plan changes as a new plan version."""
    try:
        verify_request_user(request.user_id, authorization)
        updated_plan = apply_ai_plan_changes(
            user_id=request.user_id,
            plan_id=request.plan_id,
            recommendation_id=request.ai_recommendation_id,
        )
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except SupabaseNotConfiguredError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "message": "AI plan changes applied as a new plan version",
        **updated_plan,
    }
