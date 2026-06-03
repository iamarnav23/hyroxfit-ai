import json
import os
from typing import Type

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from schemas.ai_schema import (
    DietAdjustmentOutput,
    PlanAdjustmentOutput,
    PlanPersonalizationOutput,
)


load_dotenv()


DEFAULT_MODEL = "gpt-4.1-mini"
AI_UNAVAILABLE_MESSAGE = (
    "AI coach is temporarily unavailable. Your rule-based plan is still safe to use."
)


class AICoachUnavailableError(Exception):
    """Raised when the OpenAI API cannot be reached or configured."""


class AIResponseValidationError(Exception):
    """Raised when AI output does not match the expected JSON structure."""


def get_openai_client():
    """Create an OpenAI client using only backend environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise AICoachUnavailableError(AI_UNAVAILABLE_MESSAGE)

    try:
        from openai import OpenAI
    except ImportError as error:
        raise AICoachUnavailableError(
            "OpenAI package is not installed. Run: pip install openai"
        ) from error

    return OpenAI(api_key=api_key)


def get_model_name() -> str:
    """Use OPENAI_MODEL when set, otherwise default to a small coaching model."""
    return os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


def base_system_prompt() -> str:
    """Safety rules shared by all AI coach calls."""
    return (
        "You are Rox Zone AI Coach, a careful HYROX race preparation assistant. "
        "Use the user's rule-based plan, profile, goal, workout progress, and "
        "diet context to give practical coaching. Do not replace the safe base "
        "plan unless the user later approves changes. Do not diagnose injuries "
        "or medical conditions. If the user mentions pain, injury, dizziness, "
        "chest pain, fainting, severe discomfort, or a medical condition, reduce "
        "intensity and recommend qualified medical or physiotherapy guidance. "
        "Do not suggest extreme calorie cuts, unsafe volume jumps, removing all "
        "rest days, or guaranteed race results. Keep the answer specific, concise, "
        "and safe."
    )


def call_ai_with_schema(
    user_prompt: str,
    output_schema: Type[BaseModel],
    temperature: float = 0.25,
) -> dict:
    """Ask OpenAI for a structured response and validate it with Pydantic."""
    try:
        client = get_openai_client()
        completion = client.chat.completions.parse(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": base_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
            response_format=output_schema,
            temperature=temperature,
        )
        parsed = completion.choices[0].message.parsed
    except AICoachUnavailableError:
        raise
    except ValidationError as error:
        raise AIResponseValidationError(
            "AI response did not match the required structured format."
        ) from error
    except Exception as error:
        raise AICoachUnavailableError(AI_UNAVAILABLE_MESSAGE) from error

    if not parsed:
        raise AIResponseValidationError(
            "AI response did not match the required structured format."
        )

    return parsed.model_dump()


def context_to_json(context: dict) -> str:
    """Turn Supabase context into a compact JSON string for the model."""
    return json.dumps(context, ensure_ascii=True, default=str)


def personalize_plan(context: dict) -> dict:
    """Generate coaching notes for an existing rule-based plan."""
    prompt = f"""
Create personalized coaching notes for this HYROX plan.

Return structured JSON only in the required schema.

Context:
{context_to_json(context)}

Instructions:
- Explain why the current rule-based plan fits the user.
- Add one practical note per week in the plan.
- Add weakness-specific strategy based on goal, assessment, and progress.
- Include recovery advice and a clear safety note.
- Do not rewrite the plan.
"""
    return call_ai_with_schema(prompt, PlanPersonalizationOutput)


def adjust_plan(context: dict, user_message: str) -> dict:
    """Suggest safe plan changes without applying them automatically."""
    prompt = f"""
The user has a problem with their HYROX plan.

User message:
{user_message}

Context:
{context_to_json(context)}

Instructions:
- Identify the issue.
- Suggest safe changes only.
- If pain, injury, dizziness, chest pain, fainting, severe discomfort, or a
  medical condition is mentioned, reduce training impact/intensity and suggest
  qualified professional guidance.
- Use workout_id values from context.available_workouts when creating
  updated_plan_preview.modified_workouts.
- Do not remove all rest/recovery.
- Do not create unsafe volume jumps.
- Set requires_user_approval to true.
- Do not claim guaranteed HYROX results.
"""
    return call_ai_with_schema(prompt, PlanAdjustmentOutput)


def adjust_diet(context: dict, user_message: str) -> dict:
    """Suggest safe nutrition adjustments without overwriting the diet record."""
    prompt = f"""
The user has a nutrition problem during HYROX training.

User message:
{user_message}

Context:
{context_to_json(context)}

Instructions:
- Identify the nutrition issue.
- Suggest practical, moderate diet changes.
- Do not suggest extreme calorie cuts.
- Use small calorie changes when needed.
- Include meal timing and hydration advice.
- Include a general nutrition safety note, not medical claims.
- Set requires_user_approval to true.
"""
    return call_ai_with_schema(prompt, DietAdjustmentOutput)
