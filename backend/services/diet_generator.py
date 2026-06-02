from schemas.diet_schema import DietSuggestionRequest


DISCLAIMER = "This is general fitness nutrition guidance and not medical advice."


def normalize_goal(goal_type: str) -> str:
    """Make goal matching consistent even if labels change later."""
    return goal_type.strip().lower()


def calculate_calories(weight: float, goal_type: str, category: str) -> int:
    """Estimate daily calories using simple body-weight multipliers."""
    normalized_goal = normalize_goal(goal_type)
    is_cut_goal = (
        normalized_goal == "cut"
        or "fat" in normalized_goal
        or "weight loss" in normalized_goal
    )

    if is_cut_goal:
        multiplier = 25
    elif normalized_goal in ["bulk", "strength", "compete"] or category == "Pro":
        multiplier = 36
    else:
        multiplier = 30

    return round(weight * multiplier)


def calculate_protein(weight: float) -> tuple[int, int]:
    """Return a daily protein range in grams."""
    protein_min = round(weight * 1.5)
    protein_max = round(weight * 2.0)
    return protein_min, protein_max


def get_hydration_advice(training_days_per_week: int) -> str:
    """Add extra hydration advice for higher training volume."""
    hydration = "3-4 liters/day"

    if training_days_per_week >= 5:
        hydration += ". Add extra 500-1000 ml around intense training sessions."

    return hydration


def get_carb_strategy(goal_type: str, category: str) -> str:
    """Choose a carb strategy based on the user's goal and race category."""
    normalized_goal = normalize_goal(goal_type)

    if normalized_goal == "cut" or "fat" in normalized_goal:
        return (
            "Use controlled carbs and place most carbs around training. Keep "
            "vegetables, lean protein, and steady portions as the base."
        )

    if normalized_goal in ["bulk", "strength", "compete"] or category == "Pro":
        return (
            "Use higher carbs to support hard intervals, sled work, and race "
            "simulation. Prioritize carbs before and after training."
        )

    return (
        "Use moderate carbs with balanced meals. Include carbs at breakfast, "
        "pre-workout, or post-workout to support consistent training."
    )


def get_fat_strategy() -> str:
    """Give simple fat guidance without making medical claims."""
    return (
        "Include healthy fats from nuts, olive oil, eggs, avocado, dairy, and "
        "fatty fish. Avoid very low-fat dieting during intense HYROX training."
    )


def get_general_tips(request: DietSuggestionRequest) -> list[str]:
    """Create a few practical tips based on training load and timeline."""
    tips = [
        "Build each meal around protein, carbs, vegetables, and a small fat source.",
        "Keep meal timing consistent on hard training days.",
        "Use simple foods you can repeat instead of chasing a perfect diet plan.",
    ]

    if request.training_days_per_week >= 5:
        tips.append("Add a carb-focused snack on interval, simulation, and sled days.")

    if request.preparation_weeks < 8:
        tips.append("Do not cut calories aggressively during a compressed race build.")
    elif request.preparation_weeks > 12:
        tips.append("Use the longer timeline to adjust calories gradually every few weeks.")

    if request.category == "Pro":
        tips.append("Fuel Pro sessions like performance work, especially before simulations.")

    return tips


def generate_diet_suggestion(request: DietSuggestionRequest) -> dict:
    """Build the full rule-based diet suggestion used by POST /diet-suggestion."""
    protein_min, protein_max = calculate_protein(request.weight)

    return {
        "daily_calories": calculate_calories(
            request.weight, request.goal_type, request.category
        ),
        "protein_min": protein_min,
        "protein_max": protein_max,
        "protein_range": f"{protein_min}-{protein_max} g/day",
        "hydration": get_hydration_advice(request.training_days_per_week),
        "carb_strategy": get_carb_strategy(request.goal_type, request.category),
        "fat_strategy": get_fat_strategy(),
        "pre_workout_meal": (
            "Eat a light meal 60-120 minutes before training: oats with banana, "
            "rice with eggs, yogurt with fruit, or toast with peanut butter."
        ),
        "post_workout_meal": (
            "Within 1-2 hours after training, aim for protein plus carbs: chicken "
            "and rice, eggs and potatoes, paneer with roti, or a smoothie with fruit."
        ),
        "general_tips": get_general_tips(request),
        "disclaimer": DISCLAIMER,
    }
