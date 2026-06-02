import os
from copy import deepcopy
from typing import Optional

from dotenv import load_dotenv

from schemas.cardio_schema import CardioPlanRequest
from schemas.plan_schema import PlanRequest


load_dotenv()


class SupabaseNotConfiguredError(Exception):
    """Raised when required Supabase environment variables are missing."""


def _model_to_dict(model):
    """Convert Pydantic models to plain dictionaries."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _get_supabase_package():
    """Import Supabase lazily so the backend can still start before install."""
    try:
        from supabase import create_client
    except ImportError as error:
        raise SupabaseNotConfiguredError(
            "Supabase package is not installed. Run: pip install supabase python-dotenv"
        ) from error

    return create_client


def _get_env_value(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SupabaseNotConfiguredError(f"Missing environment variable: {name}")
    return value


def get_supabase_admin_client():
    """Create a Supabase client for server-side database operations.

    Prefer the service role key on the backend because it should never be sent
    to the browser. The route verifies the user's access token before using it.
    """
    create_client = _get_supabase_package()
    url = _get_env_value("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or _get_env_value(
        "SUPABASE_ANON_KEY"
    )
    return create_client(url, key)


def get_supabase_auth_client():
    """Create a Supabase client using the anon key for auth verification."""
    create_client = _get_supabase_package()
    url = _get_env_value("SUPABASE_URL")
    anon_key = _get_env_value("SUPABASE_ANON_KEY")
    return create_client(url, anon_key)


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """Pull the access token out of an Authorization: Bearer header."""
    if not authorization_header:
        return None

    parts = authorization_header.split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]

    return None


def verify_user_access_token(access_token: Optional[str], expected_user_id: str) -> None:
    """Confirm the frontend session token belongs to the submitted user_id."""
    if not access_token:
        raise PermissionError("Missing Supabase access token")

    auth_client = get_supabase_auth_client()
    auth_response = auth_client.auth.get_user(access_token)
    user = getattr(auth_response, "user", None)

    if not user or user.id != expected_user_id:
        raise PermissionError("Supabase token does not match submitted user_id")


def save_plan_bundle(user_id: str, request: PlanRequest, plan: dict) -> str:
    """Save profile, stations, goal, and generated plan in Supabase."""
    supabase = get_supabase_admin_client()

    profile_data = _model_to_dict(request.fitness_profile)
    profile_data["user_id"] = user_id
    supabase.table("fitness_profiles").insert(profile_data).execute()

    station_rows = []
    for station in request.hyrox_assessment.stations:
        station_data = _model_to_dict(station)
        station_data["user_id"] = user_id
        station_rows.append(station_data)

    if station_rows:
        supabase.table("hyrox_assessments").insert(station_rows).execute()

    goal_data = _model_to_dict(request.goal)
    goal_data["user_id"] = user_id
    supabase.table("goals").insert(goal_data).execute()

    plan_row = {
        "user_id": user_id,
        "plan_type": plan["plan_type"],
        "summary": plan["summary"],
        "training_phase": plan["training_phase"],
        "plan_json": plan,
    }
    plan_response = supabase.table("workout_plans").insert(plan_row).execute()

    if not plan_response.data:
        raise RuntimeError("Plan was generated but Supabase did not return a plan id")

    return plan_response.data[0]["id"]


def fetch_latest_plan(user_id: str) -> Optional[dict]:
    """Fetch the latest saved workout plan for a user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("workout_plans")
        .select("id, created_at, plan_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]
    return {
        "plan_id": row["id"],
        "created_at": row.get("created_at"),
        "plan": row["plan_json"],
    }


def save_cardio_week_plan_bundle(
    user_id: str,
    request: CardioPlanRequest,
    plan: dict,
    cardio_profile_id: Optional[str] = None,
) -> str:
    """Save a Cardio Lab profile snapshot and generated one-week plan."""
    supabase = get_supabase_admin_client()

    if not cardio_profile_id:
        profile_data = _model_to_dict(request)
        profile_data.pop("week_number", None)
        profile_data["user_id"] = user_id
        profile_response = supabase.table("cardio_profiles").insert(profile_data).execute()

        if not profile_response.data:
            raise RuntimeError("Cardio profile was not saved")

        cardio_profile_id = profile_response.data[0]["id"]

    plan_row = {
        "user_id": user_id,
        "cardio_profile_id": cardio_profile_id,
        "week_number": plan["week_number"],
        "plan_json": plan,
        "ai_status": plan.get("ai_status", "rule_based"),
    }
    response = supabase.table("cardio_week_plans").insert(plan_row).execute()

    if not response.data:
        raise RuntimeError("Cardio plan was generated but Supabase did not return an id")

    return response.data[0]["id"]


def fetch_current_cardio_plan(user_id: str) -> Optional[dict]:
    """Fetch the latest saved Cardio Lab plan for a user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("cardio_week_plans")
        .select("id, cardio_profile_id, created_at, plan_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]
    return {
        "cardio_plan_id": row["id"],
        "cardio_profile_id": row.get("cardio_profile_id"),
        "created_at": row.get("created_at"),
        "plan": row["plan_json"],
    }


def fetch_cardio_plan_row(user_id: str, cardio_plan_id: str) -> Optional[dict]:
    """Fetch one Cardio Lab plan row owned by the user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("cardio_week_plans")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", cardio_plan_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def fetch_cardio_profile_row(user_id: str, cardio_profile_id: str) -> Optional[dict]:
    """Fetch one Cardio Lab profile row owned by the user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("cardio_profiles")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", cardio_profile_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def save_cardio_week_review(review) -> dict:
    """Save the user's weekly Cardio Lab review."""
    supabase = get_supabase_admin_client()
    review_data = _model_to_dict(review)
    response = supabase.table("cardio_week_reviews").insert(review_data).execute()

    if not response.data:
        raise RuntimeError("Cardio weekly review was not saved")

    return response.data[0]


def fetch_latest_cardio_review(user_id: str, cardio_plan_id: str) -> Optional[dict]:
    """Fetch the newest review for one Cardio Lab week plan."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("cardio_week_reviews")
        .select("*")
        .eq("user_id", user_id)
        .eq("cardio_plan_id", cardio_plan_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def build_next_cardio_request_from_saved(
    user_id: str, plan_row: dict, review: Optional[dict]
) -> CardioPlanRequest:
    """Recreate a CardioPlanRequest from saved profile data for next week."""
    profile = fetch_cardio_profile_row(user_id, plan_row["cardio_profile_id"])

    if not profile:
        raise RuntimeError("Cardio profile for previous plan was not found")

    next_week = int(plan_row.get("week_number") or 1) + 1
    profile_data = {
        "user_id": user_id,
        "cardio_goal": profile.get("cardio_goal"),
        "preferred_training_mode": profile.get("preferred_training_mode"),
        "experience_level": profile.get("experience_level"),
        "training_days_per_week": profile.get("training_days_per_week"),
        "current_1km_time": (review.get("updated_1km_time") if review else None)
        or profile.get("current_1km_time"),
        "current_5km_time": (review.get("updated_5km_time") if review else None)
        or profile.get("current_5km_time"),
        "current_long_run_distance": profile.get("current_long_run_distance"),
        "resting_heart_rate": profile.get("resting_heart_rate"),
        "max_heart_rate": profile.get("max_heart_rate"),
        "available_session_duration": profile.get("available_session_duration"),
        "injury_or_limitation": profile.get("injury_or_limitation") or "",
        "week_number": next_week,
    }
    return CardioPlanRequest.model_validate(profile_data)


def save_diet_suggestion(request, diet: dict) -> str:
    """Save a generated diet suggestion in Supabase."""
    supabase = get_supabase_admin_client()
    row = {
        "user_id": request.user_id,
        "goal_type": request.goal_type,
        "daily_calories": diet["daily_calories"],
        "protein_min": diet["protein_min"],
        "protein_max": diet["protein_max"],
        "hydration_advice": diet["hydration"],
        "carb_strategy": diet["carb_strategy"],
        "fat_strategy": diet["fat_strategy"],
        "pre_workout_meal": diet["pre_workout_meal"],
        "post_workout_meal": diet["post_workout_meal"],
        "general_tips": diet["general_tips"],
        "disclaimer": diet["disclaimer"],
    }
    response = supabase.table("diet_suggestions").insert(row).execute()

    if not response.data:
        raise RuntimeError("Diet suggestion was generated but Supabase did not return an id")

    return response.data[0]["id"]


def fetch_latest_diet_suggestion(user_id: str) -> Optional[dict]:
    """Fetch the latest saved diet suggestion for a user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("diet_suggestions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]
    return {
        "diet_id": row["id"],
        "created_at": row.get("created_at"),
        "diet": format_saved_diet_suggestion(row),
    }


def format_saved_diet_suggestion(row: dict) -> dict:
    """Convert a Supabase diet row into the frontend response shape."""
    protein_min = round(float(row.get("protein_min") or 0))
    protein_max = round(float(row.get("protein_max") or 0))

    return {
        "daily_calories": row.get("daily_calories"),
        "protein_range": f"{protein_min}-{protein_max} g/day",
        "hydration": row.get("hydration_advice"),
        "carb_strategy": row.get("carb_strategy"),
        "fat_strategy": row.get("fat_strategy"),
        "pre_workout_meal": row.get("pre_workout_meal"),
        "post_workout_meal": row.get("post_workout_meal"),
        "general_tips": row.get("general_tips") or [],
        "disclaimer": row.get("disclaimer"),
    }


def fetch_ai_context(user_id: str, plan_id: Optional[str] = None) -> dict:
    """Collect profile, plan, progress, goal, assessment, and diet for AI coach."""
    supabase = get_supabase_admin_client()
    plan_row = fetch_workout_plan_row(user_id, plan_id) if plan_id else None

    if not plan_row:
        latest_plan = fetch_latest_plan(user_id)
        if latest_plan:
            plan_row = fetch_workout_plan_row(user_id, latest_plan["plan_id"])

    profile = fetch_latest_user_row(supabase, "fitness_profiles", user_id)
    goal = fetch_latest_user_row(supabase, "goals", user_id)
    assessments = fetch_latest_assessments(supabase, user_id)
    progress_entries = []

    if plan_row:
        progress_entries = fetch_workout_progress(user_id, plan_row["id"])

    try:
        latest_diet = fetch_latest_diet_suggestion(user_id)
    except Exception:
        latest_diet = None

    plan = plan_row.get("plan_json") if plan_row else None

    return {
        "user_id": user_id,
        "plan_id": plan_row.get("id") if plan_row else None,
        "profile": profile,
        "goal": goal,
        "hyrox_assessment": assessments,
        "plan": plan,
        "available_workouts": build_available_workouts(plan or {}),
        "progress_entries": progress_entries[:20],
        "weak_areas": extract_weak_areas(plan or {}),
        "diet_suggestion": latest_diet,
    }


def fetch_latest_user_row(supabase, table_name: str, user_id: str) -> Optional[dict]:
    """Fetch the newest row from a user-owned table."""
    response = (
        supabase.table(table_name)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def fetch_latest_assessments(supabase, user_id: str) -> list[dict]:
    """Fetch the most recent station assessment rows for AI context."""
    response = (
        supabase.table("hyrox_assessments")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(9)
        .execute()
    )
    return response.data or []


def fetch_workout_plan_row(user_id: str, plan_id: str) -> Optional[dict]:
    """Fetch one workout plan row owned by the user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("workout_plans")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", plan_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def build_available_workouts(plan: dict) -> list[dict]:
    """Build stable workout ids so AI can reference exact plan days."""
    workouts = []
    for week in plan.get("weeks", []):
        for day in week.get("days", []):
            workouts.append(
                {
                    "workout_id": build_workout_id(week.get("week"), day.get("day")),
                    "week": week.get("week"),
                    "day": day.get("day"),
                    "workout_title": day.get("workout_title"),
                    "details": day.get("details"),
                    "intensity": day.get("intensity"),
                    "duration": day.get("duration"),
                }
            )
    return workouts


def build_workout_id(week_number: int, day_name: str) -> str:
    """Match the stable workout_id used on the frontend."""
    day_slug = "".join(
        character.lower() if character.isalnum() else "-"
        for character in str(day_name)
    )
    day_slug = "-".join(part for part in day_slug.split("-") if part)
    return f"week-{week_number}-day-{day_slug}"


def save_ai_recommendation(
    user_id: str,
    recommendation_type: str,
    ai_response: dict,
    plan_id: Optional[str] = None,
    user_message: Optional[str] = None,
) -> str:
    """Save AI coach output so the user can review or apply it later."""
    supabase = get_supabase_admin_client()
    row = {
        "user_id": user_id,
        "plan_id": plan_id,
        "recommendation_type": recommendation_type,
        "user_message": user_message,
        "ai_response": ai_response,
        "status": "pending",
    }
    response = supabase.table("ai_recommendations").insert(row).execute()

    if not response.data:
        raise RuntimeError("AI recommendation was generated but Supabase did not return an id")

    return response.data[0]["id"]


def fetch_ai_recommendation(user_id: str, recommendation_id: str) -> Optional[dict]:
    """Fetch one AI recommendation owned by a user."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("ai_recommendations")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", recommendation_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def update_ai_recommendation_status(recommendation_id: str, status: str) -> None:
    """Mark an AI recommendation as pending, applied, or dismissed."""
    supabase = get_supabase_admin_client()
    supabase.table("ai_recommendations").update({"status": status}).eq(
        "id", recommendation_id
    ).execute()


def apply_ai_plan_changes(
    user_id: str, plan_id: str, recommendation_id: str
) -> dict:
    """Apply approved AI workout edits as a new workout plan version."""
    recommendation = fetch_ai_recommendation(user_id, recommendation_id)

    if not recommendation:
        raise RuntimeError("AI recommendation was not found")

    if recommendation.get("status") == "applied":
        raise RuntimeError("AI recommendation has already been applied")

    if recommendation.get("recommendation_type") != "plan_adjustment":
        raise RuntimeError("Only plan adjustment recommendations can be applied")

    if recommendation.get("plan_id") != plan_id:
        raise RuntimeError("AI recommendation does not belong to this plan")

    plan_row = fetch_workout_plan_row(user_id, plan_id)

    if not plan_row:
        raise RuntimeError("Workout plan was not found")

    updated_plan = deepcopy(plan_row["plan_json"])
    modified_count = apply_modified_workouts_to_plan(
        updated_plan,
        recommendation.get("ai_response", {})
        .get("updated_plan_preview", {})
        .get("modified_workouts", []),
    )

    if modified_count == 0:
        raise RuntimeError("AI recommendation did not include valid workout changes")

    if "AI Adjusted" not in updated_plan.get("plan_type", ""):
        updated_plan["plan_type"] = f"{updated_plan.get('plan_type')} (AI Adjusted)"

    updated_plan["summary"] = (
        f"{updated_plan.get('summary')} This version includes approved AI coach "
        "adjustments based on your feedback."
    )

    current_version = int(plan_row.get("version_number") or 1)
    new_plan_row = {
        "user_id": user_id,
        "plan_type": updated_plan["plan_type"],
        "summary": updated_plan["summary"],
        "training_phase": updated_plan.get("training_phase"),
        "plan_json": updated_plan,
        "parent_plan_id": plan_id,
        "version_number": current_version + 1,
        "source": "ai_adjusted",
        "ai_recommendation_id": recommendation_id,
    }
    supabase = get_supabase_admin_client()
    response = supabase.table("workout_plans").insert(new_plan_row).execute()

    if not response.data:
        raise RuntimeError("Updated plan was not saved")

    update_ai_recommendation_status(recommendation_id, "applied")

    return {
        "plan_id": response.data[0]["id"],
        "parent_plan_id": plan_id,
        "version_number": new_plan_row["version_number"],
        "plan": updated_plan,
    }


def apply_modified_workouts_to_plan(plan: dict, modified_workouts: list[dict]) -> int:
    """Patch workout fields that AI preview explicitly changed."""
    modified_by_id = {
        item.get("workout_id"): item
        for item in modified_workouts
        if item.get("workout_id")
    }
    modified_count = 0

    for week in plan.get("weeks", []):
        for day in week.get("days", []):
            workout_id = build_workout_id(week.get("week"), day.get("day"))
            change = modified_by_id.get(workout_id)

            if not change:
                continue

            day["workout_title"] = change.get("new_workout_title") or day.get(
                "workout_title"
            )
            day["details"] = change.get("new_details") or day.get("details")
            day["intensity"] = change.get("new_intensity") or day.get("intensity")
            day["duration"] = change.get("new_duration") or day.get("duration")
            modified_count += 1

    return modified_count


def save_or_update_workout_progress(progress_data: dict) -> dict:
    """Save progress for one workout, updating it if it already exists."""
    supabase = get_supabase_admin_client()

    existing_response = (
        supabase.table("workout_progress")
        .select("*")
        .eq("user_id", progress_data["user_id"])
        .eq("workout_plan_id", progress_data["workout_plan_id"])
        .eq("workout_id", progress_data["workout_id"])
        .limit(1)
        .execute()
    )

    if existing_response.data:
        progress_id = existing_response.data[0]["id"]
        response = (
            supabase.table("workout_progress")
            .update(progress_data)
            .eq("id", progress_id)
            .execute()
        )
    else:
        response = supabase.table("workout_progress").insert(progress_data).execute()

    if not response.data:
        raise RuntimeError("Supabase did not return the saved progress row")

    return response.data[0]


def fetch_workout_progress(user_id: str, workout_plan_id: str) -> list[dict]:
    """Fetch all progress entries for a user's saved plan."""
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("workout_progress")
        .select("*")
        .eq("user_id", user_id)
        .eq("workout_plan_id", workout_plan_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def fetch_dashboard_data(user_id: str) -> dict:
    """Calculate dashboard values from the latest plan and progress rows."""
    latest_plan = fetch_latest_plan(user_id)

    if not latest_plan:
        return build_empty_dashboard(user_id)

    plan = latest_plan["plan"]
    plan_id = latest_plan["plan_id"]
    progress_entries = fetch_workout_progress(user_id, plan_id)
    total_workouts = count_plan_workouts(plan)
    completed_workouts = sum(1 for item in progress_entries if item.get("completed"))
    completion_percentage = calculate_percentage(completed_workouts, total_workouts)
    consistency_score = calculate_consistency_score(completion_percentage)
    weak_areas = extract_weak_areas(plan)
    race_readiness_score = calculate_dashboard_readiness(
        completion_percentage=completion_percentage,
        consistency_score=consistency_score,
        weak_areas=weak_areas,
        progress_entries=progress_entries,
    )
    cardio_summary = build_cardio_lab_summary(user_id)
    performance_scores = build_performance_scores(
        race_readiness_score=race_readiness_score,
        completion_percentage=completion_percentage,
        progress_entries=progress_entries,
        cardio_summary=cardio_summary,
    )
    current_week = find_current_week_focus(plan, progress_entries)
    weakness_analysis = build_weakness_analysis(
        plan=plan,
        weak_areas=weak_areas,
        cardio_summary=cardio_summary,
    )
    progress_trends = build_progress_trends(
        completion_percentage=completion_percentage,
        completed_workouts=completed_workouts,
        total_workouts=total_workouts,
        race_readiness_score=race_readiness_score,
        cardio_summary=cardio_summary,
        performance_scores=performance_scores,
    )
    latest_ai_advice = fetch_latest_ai_coach_advice(user_id)
    recovery_recommendation = build_weekly_recovery_recommendation(
        progress_entries, cardio_summary
    )
    coaching_insights = build_adaptive_coaching_insights(
        completion_percentage=completion_percentage,
        weak_areas=weak_areas,
        progress_entries=progress_entries,
        cardio_summary=cardio_summary,
        readiness_score=race_readiness_score,
        recovery_recommendation=recovery_recommendation,
    )

    return {
        "total_workouts": total_workouts,
        "completed_workouts": completed_workouts,
        "completion_percentage": completion_percentage,
        "consistency_score": consistency_score,
        "latest_plan_type": plan.get("plan_type"),
        "current_training_phase": plan.get("training_phase"),
        "weak_areas": weak_areas,
        "race_readiness_score": race_readiness_score,
        "recent_notes": get_recent_notes(progress_entries),
        "performance_scores": performance_scores,
        "weakness_analysis": weakness_analysis,
        "progress_trends": progress_trends,
        "adaptive_coaching_insights": coaching_insights,
        "current_week_number": current_week.get("week"),
        "current_week_focus": current_week.get("focus"),
        "latest_ai_coach_advice": latest_ai_advice,
        "cardio_lab_summary": cardio_summary,
        "weekly_recovery_recommendation": recovery_recommendation,
    }


def build_empty_dashboard(user_id: Optional[str] = None) -> dict:
    """Return useful dashboard defaults before a user has a saved plan."""
    cardio_summary = build_cardio_lab_summary(user_id) if user_id else None
    return {
        "total_workouts": 0,
        "completed_workouts": 0,
        "completion_percentage": 0,
        "consistency_score": 0,
        "latest_plan_type": None,
        "current_training_phase": None,
        "weak_areas": [],
        "race_readiness_score": {
            "total_score": 0,
            "status": "Generate a plan and save workout progress to calculate readiness",
            "breakdown": {
                "running": 0,
                "strength": 0,
                "hyrox_skill": 0,
                "consistency": 0,
                "recovery_diet": 0,
            },
        },
        "recent_notes": [],
        "performance_scores": {
            "hyrox_readiness": 0,
            "endurance": 0,
            "running": 0,
            "recovery": 0,
            "consistency": 0,
            "zone_balance": cardio_summary.get("zone_balance_score", 0)
            if cardio_summary
            else 0,
        },
        "weakness_analysis": [],
        "progress_trends": [],
        "adaptive_coaching_insights": [
            "Generate a HYROX plan and save workout progress to unlock coaching insights."
        ],
        "current_week_number": None,
        "current_week_focus": None,
        "latest_ai_coach_advice": fetch_latest_ai_coach_advice(user_id)
        if user_id
        else None,
        "cardio_lab_summary": cardio_summary,
        "weekly_recovery_recommendation": "Start logging workouts so recovery guidance can adapt to your feedback.",
    }


def count_plan_workouts(plan: dict) -> int:
    """Count workout day cards across all weeks, excluding rest days."""
    total = 0
    for week in plan.get("weeks", []):
        for day in week.get("days", []):
            if day.get("workout_type") != "Rest":
                total += 1
    return total


def calculate_percentage(completed: int, total: int) -> int:
    """Convert completed workouts into a whole-number percentage."""
    if total == 0:
        return 0
    return round((completed / total) * 100)


def calculate_consistency_score(completion_percentage: int) -> int:
    """Map completion percentage to the 15-point consistency score."""
    return round((completion_percentage / 100) * 15)


def extract_weak_areas(plan: dict) -> list[str]:
    """Extract readable weak areas from the generated plan notes."""
    weak_areas = []
    for item in plan.get("weakness_focus", []):
        lowered = item.lower()
        for keyword in [
            "running",
            "sled",
            "wall balls",
            "rowing",
            "skierg",
            "burpee",
            "farmer",
            "sandbag",
        ]:
            if keyword in lowered and keyword not in weak_areas:
                weak_areas.append(keyword)
    return weak_areas


def calculate_dashboard_readiness(
    completion_percentage: int,
    consistency_score: int,
    weak_areas: list[str],
    progress_entries: list[dict],
) -> dict:
    """Create a simple readiness score from completion and workout feedback."""
    hard_sessions = sum(
        1 for item in progress_entries if item.get("difficulty_level") == "hard"
    )
    low_energy_sessions = sum(
        1 for item in progress_entries if item.get("energy_level") == "low"
    )

    running = min(25, round(completion_percentage * 0.22))
    strength = min(25, round(completion_percentage * 0.22))
    hyrox_skill = min(25, round(completion_percentage * 0.21))
    recovery_diet = max(3, min(10, 10 - low_energy_sessions))

    if "running" in weak_areas:
        running = max(0, running - 3)
    if "sled" in weak_areas or "farmer" in weak_areas or "sandbag" in weak_areas:
        strength = max(0, strength - 3)
    if "wall balls" in weak_areas or "rowing" in weak_areas or "skierg" in weak_areas:
        hyrox_skill = max(0, hyrox_skill - 3)
    if hard_sessions >= 3:
        recovery_diet = max(3, recovery_diet - 1)

    total_score = running + strength + hyrox_skill + consistency_score + recovery_diet

    return {
        "total_score": total_score,
        "status": build_readiness_status(total_score, weak_areas),
        "breakdown": {
            "running": running,
            "strength": strength,
            "hyrox_skill": hyrox_skill,
            "consistency": consistency_score,
            "recovery_diet": recovery_diet,
        },
    }


def build_readiness_status(total_score: int, weak_areas: list[str]) -> str:
    """Turn a score into direct coaching feedback."""
    weakness_text = " and ".join(weak_areas[:2])

    if total_score >= 80:
        return "Excellent progress. Keep sharpening race simulation and recovery"
    if total_score >= 65:
        if weakness_text:
            return f"Good progress, but improve {weakness_text} consistency"
        return "Good progress. Keep building consistency"
    if total_score >= 45:
        if weakness_text:
            return f"Building readiness. Focus on {weakness_text} and weekly consistency"
        return "Building readiness. Complete more weekly sessions"
    return "Early progress. Complete more workouts to build race readiness"


def get_recent_notes(progress_entries: list[dict]) -> list[dict]:
    """Return the latest notes users wrote after workouts."""
    notes = []
    for item in progress_entries:
        if item.get("notes"):
            notes.append(
                {
                    "workout_id": item.get("workout_id"),
                    "notes": item.get("notes"),
                    "created_at": item.get("created_at"),
                }
            )
    return notes[:5]


def build_cardio_lab_summary(user_id: str) -> Optional[dict]:
    """Summarize the latest Cardio Lab plan and review for dashboard coaching."""
    try:
        current_cardio = fetch_current_cardio_plan(user_id)
    except Exception:
        return None

    if not current_cardio:
        return None

    plan = current_cardio.get("plan") or {}
    review = fetch_latest_cardio_review_for_user(user_id)
    zone_distribution = plan.get("zone_distribution") or {}
    days = plan.get("days") or []
    total_cardio_workouts = sum(
        1 for day in days if str(day.get("workout_type", "")).lower() != "rest"
    )
    zone_balance_score = calculate_zone_balance_score(zone_distribution, days)

    review_completion = 0
    if review:
        review_completion = calculate_percentage(
            int(review.get("workouts_completed") or 0),
            int(review.get("total_workouts") or 0),
        )

    weak_cardio_areas = detect_weak_cardio_areas(
        zone_distribution=zone_distribution,
        review=review,
        zone_balance_score=zone_balance_score,
    )

    return {
        "cardio_plan_id": current_cardio.get("cardio_plan_id"),
        "week_number": plan.get("week_number"),
        "cardio_goal": plan.get("cardio_goal"),
        "training_mode": plan.get("preferred_training_mode"),
        "week_summary": plan.get("week_summary"),
        "current_week_focus": plan.get("progression_advice"),
        "total_cardio_workouts": total_cardio_workouts,
        "zone_distribution": zone_distribution,
        "zone_balance_score": zone_balance_score,
        "latest_review": review,
        "review_completion_percentage": review_completion,
        "weak_cardio_areas": weak_cardio_areas,
    }


def fetch_latest_cardio_review_for_user(user_id: str) -> Optional[dict]:
    """Fetch the newest Cardio Lab review across all saved cardio plans."""
    try:
        supabase = get_supabase_admin_client()
        response = (
            supabase.table("cardio_week_reviews")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception:
        return None


def fetch_latest_ai_coach_advice(user_id: Optional[str]) -> Optional[dict]:
    """Fetch the latest saved AI Coach recommendation in a compact dashboard shape."""
    if not user_id:
        return None

    try:
        supabase = get_supabase_admin_client()
        response = (
            supabase.table("ai_recommendations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        return None

    if not response.data:
        return None

    row = response.data[0]
    ai_response = row.get("ai_response") or {}
    recommendation_type = row.get("recommendation_type") or "ai_coach"

    summary = (
        ai_response.get("coach_response")
        or ai_response.get("personalized_summary")
        or ai_response.get("recovery_advice")
        or "AI Coach advice is saved and ready to review."
    )
    issue = ai_response.get("issue_detected") or recommendation_type.replace("_", " ")

    return {
        "recommendation_type": recommendation_type,
        "status": row.get("status"),
        "issue": issue,
        "summary": summary,
        "created_at": row.get("created_at"),
    }


def calculate_zone_balance_score(zone_distribution: dict, days: list[dict]) -> int:
    """Score whether Cardio Lab has a safe endurance/intensity balance."""
    if not zone_distribution and not days:
        return 0

    zone_1 = int(zone_distribution.get("zone_1") or 0)
    zone_2 = int(zone_distribution.get("zone_2") or 0)
    zone_3 = int(zone_distribution.get("zone_3") or 0)
    zone_4 = int(zone_distribution.get("zone_4") or 0)
    zone_5 = int(zone_distribution.get("zone_5") or 0)
    training_days = max(1, zone_1 + zone_2 + zone_3 + zone_4 + zone_5)

    score = 70
    if zone_2 >= 2:
        score += 12
    if zone_1 >= 1:
        score += 6
    if zone_5 == 1:
        score += 8
    if zone_5 > 1:
        score -= (zone_5 - 1) * 12
    if zone_5 / training_days > 0.35:
        score -= 12
    if zone_2 == 0:
        score -= 18

    sunday_rest = any(
        day.get("day") == "Sunday"
        and str(day.get("workout_type", "")).lower() == "rest"
        for day in days
    )
    if sunday_rest:
        score += 4

    return max(0, min(100, score))


def detect_weak_cardio_areas(
    zone_distribution: dict, review: Optional[dict], zone_balance_score: int
) -> list[str]:
    """Find the Cardio Lab limiters that should be surfaced on the dashboard."""
    weak_areas = []
    zone_2 = int(zone_distribution.get("zone_2") or 0)
    zone_5 = int(zone_distribution.get("zone_5") or 0)
    total_zones = max(1, sum(int(value or 0) for value in zone_distribution.values()))

    if zone_balance_score < 65:
        weak_areas.append("zone balance")
    if zone_2 == 0:
        weak_areas.append("aerobic base")
    if zone_5 / total_zones > 0.35:
        weak_areas.append("too much Zone 5")

    if review:
        completion = calculate_percentage(
            int(review.get("workouts_completed") or 0),
            int(review.get("total_workouts") or 0),
        )
        if completion < 60:
            weak_areas.append("cardio consistency")
        if review.get("average_energy_level") == "low":
            weak_areas.append("cardio recovery")
        if review.get("average_difficulty") == "hard":
            weak_areas.append("intensity control")

    return list(dict.fromkeys(weak_areas))[:4]


def build_performance_scores(
    race_readiness_score: dict,
    completion_percentage: int,
    progress_entries: list[dict],
    cardio_summary: Optional[dict],
) -> dict:
    """Build 0-100 dashboard scores from HYROX progress and Cardio Lab data."""
    readiness_total = int(race_readiness_score.get("total_score") or 0)
    breakdown = race_readiness_score.get("breakdown") or {}
    running_score = min(100, int(breakdown.get("running") or 0) * 4)
    recovery_score = calculate_recovery_score(progress_entries, cardio_summary)
    zone_balance_score = (
        int(cardio_summary.get("zone_balance_score") or 0) if cardio_summary else 0
    )

    if cardio_summary:
        cardio_completion = int(
            cardio_summary.get("review_completion_percentage")
            or completion_percentage
            or 0
        )
        endurance_score = round(
            (running_score * 0.35)
            + (zone_balance_score * 0.35)
            + (cardio_completion * 0.30)
        )
    else:
        endurance_score = round((running_score * 0.60) + (completion_percentage * 0.40))

    return {
        "hyrox_readiness": readiness_total,
        "endurance": max(0, min(100, endurance_score)),
        "running": running_score,
        "recovery": recovery_score,
        "consistency": completion_percentage,
        "zone_balance": zone_balance_score,
    }


def calculate_recovery_score(
    progress_entries: list[dict], cardio_summary: Optional[dict]
) -> int:
    """Estimate recovery from energy, difficulty, and Cardio Lab review feedback."""
    if not progress_entries and not cardio_summary:
        return 70

    low_energy_sessions = sum(
        1 for item in progress_entries if item.get("energy_level") == "low"
    )
    hard_sessions = sum(
        1 for item in progress_entries if item.get("difficulty_level") == "hard"
    )
    score = 90 - (low_energy_sessions * 10) - (hard_sessions * 4)

    review = (cardio_summary or {}).get("latest_review")
    if review:
        if review.get("average_energy_level") == "low":
            score -= 15
        if review.get("average_difficulty") == "hard":
            score -= 10
        if review.get("average_energy_level") == "high":
            score += 5

    return max(0, min(100, score))


def find_current_week_focus(plan: dict, progress_entries: list[dict]) -> dict:
    """Pick the first week that still has incomplete workouts."""
    completed_ids = {
        item.get("workout_id") for item in progress_entries if item.get("completed")
    }
    weeks = plan.get("weeks") or []

    for week in weeks:
        workout_ids = [
            build_workout_id(week.get("week"), day.get("day"))
            for day in week.get("days", [])
            if day.get("workout_type") != "Rest"
        ]

        if workout_ids and any(workout_id not in completed_ids for workout_id in workout_ids):
            return {"week": week.get("week"), "focus": week.get("focus")}

    if weeks:
        last_week = weeks[-1]
        return {"week": last_week.get("week"), "focus": last_week.get("focus")}

    return {"week": None, "focus": None}


def build_weakness_analysis(
    plan: dict, weak_areas: list[str], cardio_summary: Optional[dict]
) -> list[dict]:
    """Create short actionable HYROX and cardio weakness insights."""
    insights = []

    for station in plan.get("station_analysis", []):
        classification = station.get("classification")
        if classification != "weak":
            continue

        station_name = station.get("station_name", "Station")
        training_focus = station.get("training_focus") or "Targeted station practice"
        insights.append(
            {
                "area": station_name,
                "type": "HYROX",
                "severity": "High",
                "insight": build_station_insight(station_name),
                "action": training_focus,
            }
        )

    if not insights:
        for area in weak_areas[:3]:
            insights.append(
                {
                    "area": area,
                    "type": "HYROX",
                    "severity": "Medium",
                    "insight": f"{area.title()} is limiting your race readiness.",
                    "action": "Keep logging sessions and follow the weakness-focused workouts.",
                }
            )

    for area in (cardio_summary or {}).get("weak_cardio_areas", []):
        insights.append(
            {
                "area": area,
                "type": "Cardio",
                "severity": "High" if "Zone 5" in area or "recovery" in area else "Medium",
                "insight": build_cardio_insight(area),
                "action": build_cardio_action(area),
            }
        )

    return insights[:6]


def build_station_insight(station_name: str) -> str:
    """Return direct station-specific coaching language."""
    lowered = station_name.lower()
    if "run" in lowered:
        return "Running endurance is limiting your race readiness."
    if "wall" in lowered:
        return "Wall ball endurance needs improvement."
    if "sled" in lowered:
        return "Sled power is a race-specific limiter."
    if "row" in lowered:
        return "Rowing pace control needs more attention."
    if "skierg" in lowered:
        return "SkiErg pulling endurance can improve."
    if "farmer" in lowered:
        return "Grip and loaded carry capacity need work."
    if "sandbag" in lowered:
        return "Lunge endurance and trunk stability need work."
    if "burpee" in lowered:
        return "Burpee broad jump rhythm is costing efficiency."
    return f"{station_name} needs focused practice."


def build_cardio_insight(area: str) -> str:
    """Return short cardio weakness insight text."""
    if area == "too much Zone 5":
        return "Too much Zone 5 work detected. Recovery may limit progress."
    if area == "aerobic base":
        return "Aerobic base work is too low for endurance development."
    if area == "cardio consistency":
        return "Cardio consistency is limiting your endurance trend."
    if area == "cardio recovery":
        return "Low energy in cardio reviews suggests recovery pressure."
    if area == "intensity control":
        return "Cardio sessions are trending too hard."
    return "Cardio balance needs attention."


def build_cardio_action(area: str) -> str:
    """Return one practical next action for a cardio weakness."""
    if area == "too much Zone 5":
        return "Add more Zone 1-2 recovery and keep Zone 5 to focused sessions."
    if area == "aerobic base":
        return "Add steady Zone 2 work before increasing interval volume."
    if area == "cardio consistency":
        return "Reduce session complexity and complete the planned weekly basics."
    if area == "cardio recovery":
        return "Lower interval volume and prioritize sleep, hydration, and easy days."
    if area == "intensity control":
        return "Keep threshold and Zone 5 controlled instead of all-out."
    return "Rebalance the week around Zone 2, recovery, and one quality intensity day."


def build_progress_trends(
    completion_percentage: int,
    completed_workouts: int,
    total_workouts: int,
    race_readiness_score: dict,
    cardio_summary: Optional[dict],
    performance_scores: dict,
) -> list[dict]:
    """Create compact trend rows that the frontend can render as coaching cards."""
    cardio_review = (cardio_summary or {}).get("latest_review")
    cardio_completion = (
        cardio_summary.get("review_completion_percentage") if cardio_summary else 0
    )
    running_value = performance_scores.get("running", 0)

    trends = [
        {
            "label": "Workout completion trend",
            "value": f"{completion_percentage}%",
            "direction": "up" if completion_percentage >= 70 else "needs_work",
            "detail": f"{completed_workouts} of {total_workouts} HYROX workouts complete.",
        },
        {
            "label": "Running improvement trend",
            "value": f"{running_value}/100",
            "direction": "up" if running_value >= 70 else "needs_work",
            "detail": "Running score is based on HYROX readiness and logged progress.",
        },
        {
            "label": "Weekly consistency trend",
            "value": f"{completion_percentage}%",
            "direction": "up" if completion_percentage >= 75 else "steady",
            "detail": "Consistency improves as more planned sessions are completed.",
        },
    ]

    if cardio_summary:
        trends.insert(
            1,
            {
                "label": "Cardio improvement trend",
                "value": f"{cardio_completion or 0}%",
                "direction": "up"
                if cardio_completion and cardio_completion >= 70
                else "steady",
                "detail": build_cardio_trend_detail(cardio_review),
            },
        )

    return trends


def build_cardio_trend_detail(review: Optional[dict]) -> str:
    """Explain the latest Cardio Lab trend in one sentence."""
    if not review:
        return "Submit a Cardio Lab review to track endurance changes week by week."

    improved_times = []
    if review.get("updated_1km_time"):
        improved_times.append(f"1km: {review.get('updated_1km_time')}")
    if review.get("updated_5km_time"):
        improved_times.append(f"5km: {review.get('updated_5km_time')}")

    if improved_times:
        return f"Latest review logged updated running markers: {', '.join(improved_times)}."

    return "Latest Cardio Lab review is saved; keep updating 1km or 5km markers."


def build_weekly_recovery_recommendation(
    progress_entries: list[dict], cardio_summary: Optional[dict]
) -> str:
    """Give one recovery recommendation from workout and cardio feedback."""
    low_energy_sessions = sum(
        1 for item in progress_entries if item.get("energy_level") == "low"
    )
    hard_sessions = sum(
        1 for item in progress_entries if item.get("difficulty_level") == "hard"
    )
    cardio_review = (cardio_summary or {}).get("latest_review")

    if cardio_review and cardio_review.get("average_energy_level") == "low":
        return "Keep the next cardio session easy and add sleep, hydration, and mobility focus."
    if low_energy_sessions >= 2:
        return "Energy is trending low. Reduce one high-intensity session and protect recovery."
    if hard_sessions >= 4:
        return "Several sessions feel hard. Add an easier aerobic or mobility day this week."
    if cardio_summary and cardio_summary.get("zone_balance_score", 0) < 65:
        return "Rebalance cardio with more Zone 2 and less high-intensity work."
    return "Recovery looks manageable. Keep one full rest day, hydrate well, and avoid adding extra volume."


def build_adaptive_coaching_insights(
    completion_percentage: int,
    weak_areas: list[str],
    progress_entries: list[dict],
    cardio_summary: Optional[dict],
    readiness_score: dict,
    recovery_recommendation: str,
) -> list[str]:
    """Generate short rule-based coaching feedback for the dashboard."""
    insights = []
    readiness_total = int(readiness_score.get("total_score") or 0)

    if completion_percentage < 50:
        insights.append("Your biggest unlock is completing more planned sessions before adding intensity.")
    elif completion_percentage >= 80:
        insights.append("Consistency is strong. Start focusing on session quality and race-specific pacing.")
    else:
        insights.append("You are building momentum. Keep the weekly split steady before increasing volume.")

    if weak_areas:
        insights.append(f"Priority HYROX limiter: {weak_areas[0]}. Keep this in the main training focus.")

    if readiness_total < 65:
        insights.append("Race readiness is still building, so avoid aggressive jumps in volume.")
    elif readiness_total >= 80:
        insights.append("Readiness is strong. Sharpen transitions, pacing, and recovery.")

    cardio_areas = (cardio_summary or {}).get("weak_cardio_areas", [])
    if cardio_areas:
        insights.append(build_cardio_insight(cardio_areas[0]))

    if any(item.get("notes") for item in progress_entries):
        insights.append("Recent workout notes are being factored into your recovery and weakness guidance.")

    insights.append(recovery_recommendation)
    return list(dict.fromkeys(insights))[:5]
