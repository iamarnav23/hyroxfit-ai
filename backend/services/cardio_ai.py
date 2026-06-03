import json
import os

from dotenv import load_dotenv

from schemas.cardio_schema import CardioAIPlanOutput


load_dotenv()

DEFAULT_MODEL = "gpt-4.1-mini"


def personalize_cardio_plan_with_ai(
    user_profile: dict, base_plan: dict, previous_review: dict | None = None
) -> dict:
    """Refine a safe rule-based cardio plan with AI, falling back safely on failure."""
    try:
        refined = call_cardio_ai(user_profile, base_plan, previous_review)
        refined["training_zones"] = base_plan["training_zones"]
        refined["week_number"] = base_plan["week_number"]
        refined["cardio_goal"] = base_plan.get("cardio_goal")
        refined["preferred_training_mode"] = base_plan.get("preferred_training_mode")
        refined["experience_level"] = base_plan.get("experience_level")
        refined["training_days_per_week"] = base_plan.get("training_days_per_week")
        refined["ai_status"] = "personalized"

        if not is_safe_ai_plan(base_plan, refined):
            return with_fallback_status(base_plan)

        return refined
    except Exception:
        return with_fallback_status(base_plan)


def call_cardio_ai(
    user_profile: dict, base_plan: dict, previous_review: dict | None = None
) -> dict:
    """Call OpenAI with a structured Pydantic output schema."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.parse(
        model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Cardio Lab, a careful endurance coach inside Rox Zone. "
                    "Refine the provided rule-based cardio plan without changing the safe structure. "
                    "Keep the same number of days, keep Sunday as rest/recovery, do not make every "
                    "session Zone 5, do not diagnose injuries, and do not prescribe unsafe volume jumps. "
                    "If pain or injury appears, reduce impact and include professional guidance. "
                    "Return only the requested structured JSON."
                ),
            },
            {
                "role": "user",
                "content": build_prompt(user_profile, base_plan, previous_review),
            },
        ],
        response_format=CardioAIPlanOutput,
        temperature=0.25,
    )

    parsed = completion.choices[0].message.parsed
    if not parsed:
        raise RuntimeError("OpenAI returned an empty structured response")
    return parsed.model_dump()


def build_prompt(user_profile: dict, base_plan: dict, previous_review: dict | None) -> str:
    """Build compact JSON context for the AI refinement layer."""
    return f"""
Refine this one-week cardio plan.

Rules:
- Do not create a new plan from scratch.
- Keep the same number of day objects as the base plan.
- Keep Sunday as Rest / Recovery.
- Keep the same broad intensity distribution and avoid excessive Zone 5.
- Improve wording, sport-specific coaching tips, recovery advice, and safety notes.
- Keep all guidance general fitness guidance, not medical advice.

User profile:
{json.dumps(user_profile, ensure_ascii=True, default=str)}

Previous review:
{json.dumps(previous_review or {}, ensure_ascii=True, default=str)}

Base rule-based plan:
{json.dumps(base_plan, ensure_ascii=True, default=str)}
"""


def is_safe_ai_plan(base_plan: dict, refined_plan: dict) -> bool:
    """Validate safety-critical structure before saving AI output."""
    base_days = base_plan.get("days", [])
    refined_days = refined_plan.get("days", [])

    if len(base_days) != len(refined_days):
        return False

    if not refined_days or refined_days[-1].get("day") != "Sunday":
        return False

    sunday = refined_days[-1]
    if "Rest" not in sunday.get("workout_type", ""):
        return False

    zone_5_days = [
        day for day in refined_days if "Zone 5" in str(day.get("zone", ""))
    ]
    training_days = [
        day for day in refined_days if "Rest" not in str(day.get("workout_type", ""))
    ]

    if training_days and len(zone_5_days) > 2:
        return False

    return True


def with_fallback_status(base_plan: dict) -> dict:
    """Return the rule-based plan when AI is unavailable or invalid."""
    fallback = dict(base_plan)
    fallback["ai_status"] = "fallback_used"
    fallback["week_summary"] = (
        f"{fallback.get('week_summary', '')} AI personalization was unavailable, "
        "so this safe rule-based plan is shown."
    ).strip()
    return fallback
