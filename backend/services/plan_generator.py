from schemas.plan_schema import PlanRequest
from services.hyrox_benchmarks import (
    STATION_TRAINING_FOCUS,
    classify_station_performance,
    get_station_specific_addons,
)


DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

STATION_KEYWORDS = {
    "1 km run": ["running", "run", "1 km", "1km"],
    "SkiErg": ["skierg", "ski erg", "ski"],
    "Sled push": ["sled push"],
    "Sled pull": ["sled pull"],
    "Burpee broad jumps": ["burpee broad jumps", "burpee"],
    "Rowing": ["rowing", "row"],
    "Farmer's carry": ["farmer carry", "farmer's carry", "farmers carry"],
    "Sandbag lunges": ["sandbag lunges", "sandbag lunge"],
    "Wall balls": ["wall balls", "wall ball"],
}


REST_DAY = {
    "workout_type": "Rest",
    "workout_title": "Complete Rest Day",
    "details": "Focus on recovery, hydration, light walking, mobility, and quality sleep.",
    "hyrox_focus": "Recovery",
    "intensity": "None",
    "duration": "Rest day",
}


def generate_training_plan(request: PlanRequest) -> dict:
    """Create a personalized rule-based HYROX training plan."""
    profile = request.fitness_profile
    goal = request.goal
    experience = profile.training_experience.lower()
    category = goal.category
    preparation_weeks = goal.preparation_weeks
    training_days = profile.training_days_per_week
    training_phase = determine_training_phase(preparation_weeks)
    station_analysis = analyze_stations(request)
    weak_station_names = get_weak_station_names(station_analysis, goal.main_weakness)
    station_addons = get_station_specific_addons(station_analysis)
    body_type_adjustments = get_body_type_adjustments(profile)
    weekly_schedule_rules = build_weekly_schedule_rules(training_days)

    weeks = []
    for week_number in range(1, preparation_weeks + 1):
        progression = get_week_progression_factor(week_number, preparation_weeks)
        weeks.append(
            {
                "week": week_number,
                "focus": get_week_focus_label(
                    week_number, preparation_weeks, progression
                ),
                "progression_note": get_progression_note(progression),
                "weekly_recommendations": get_weekly_recommendations(
                    week_number, progression, weak_station_names
                ),
                "days": build_week_plan(
                    week_number=week_number,
                    progression=progression,
                    experience=experience,
                    category=category,
                    goal_type=goal.goal_type,
                    training_days_per_week=training_days,
                    weak_station_names=weak_station_names,
                    station_addons=station_addons,
                    body_type_adjustments=body_type_adjustments,
                ),
            }
        )

    return {
        "plan_type": (
            f"{experience.title()} {category} {preparation_weeks}-week HYROX Plan"
        ),
        "summary": build_summary(
            experience=experience,
            category=category,
            training_phase=training_phase,
            training_days_per_week=training_days,
            weak_station_names=weak_station_names,
            body_type_adjustments=body_type_adjustments,
        ),
        "training_phase": training_phase,
        "station_analysis": station_analysis,
        "weekly_schedule_rules": weekly_schedule_rules,
        "weeks": weeks,
        "weakness_focus": build_weakness_focus(weak_station_names, station_addons),
        "body_type_adjustments": body_type_adjustments,
        "recommendations": build_recommendations(
            experience=experience,
            category=category,
            training_phase=training_phase,
            weak_station_names=weak_station_names,
            body_type_adjustments=body_type_adjustments,
        ),
    }


def determine_training_phase(preparation_weeks: int) -> str:
    """Describe the overall timeline structure."""
    if preparation_weeks < 8:
        return "Compressed preparation plan"
    if preparation_weeks <= 12:
        return "Balanced preparation plan"
    return "Progressive preparation plan"


def get_week_phase(week_number: int, preparation_weeks: int) -> str:
    """Choose the week phase from the user's total preparation timeline."""
    if preparation_weeks < 8:
        if week_number == preparation_weeks:
            return "Taper"
        if week_number <= max(1, round(preparation_weeks * 0.4)):
            return "Build"
        return "Race Specific"

    if preparation_weeks <= 12:
        if week_number > preparation_weeks - 2:
            return "Taper"
        if week_number <= 3:
            return "Foundation"
        if week_number <= 7:
            return "Build"
        return "Race Specific"

    foundation_end = round(preparation_weeks * 0.25)
    build_end = foundation_end + round(preparation_weeks * 0.35)
    race_end = build_end + round(preparation_weeks * 0.25)

    if week_number <= foundation_end:
        return "Foundation"
    if week_number <= build_end:
        return "Strength + Endurance Build"
    if week_number <= race_end:
        return "Race Specific"
    return "Simulation + Taper"


def get_week_progression_factor(week_number: int, preparation_weeks: int) -> dict:
    """Return deterministic week-by-week progression controls."""
    phase = get_week_phase(week_number, preparation_weeks)
    is_final_week = week_number == preparation_weeks
    is_taper = is_final_week or (preparation_weeks >= 10 and week_number >= preparation_weeks - 1)
    is_deload = week_number % 4 == 0 and not is_taper

    if is_taper:
        volume_multiplier = 0.55 if is_final_week else 0.7
        intensity_modifier = "Light"
    elif is_deload:
        volume_multiplier = 0.7
        intensity_modifier = "Deload"
    else:
        build_step = (week_number - 1) % 4
        block_bonus = min(0.3, ((week_number - 1) // 4) * 0.1)
        volume_multiplier = round(1.0 + (build_step * 0.1) + block_bonus, 2)
        intensity_modifier = "Low to Moderate" if week_number <= 2 else "Progressive"

    return {
        "phase": phase,
        "volume_multiplier": volume_multiplier,
        "intensity_modifier": intensity_modifier,
        "is_deload": is_deload,
        "is_taper": is_taper,
    }


def get_progression_note(progression: dict) -> str:
    """Explain what changes this week compared with prior weeks."""
    if progression["is_taper"]:
        return "Taper week: volume drops, intensity stays light, and the focus is recovery, mobility, and confidence."
    if progression["is_deload"]:
        return "Deload week: volume drops by about 25-35% while movement quality and technique stay sharp."
    if progression["volume_multiplier"] <= 1.05:
        return "Foundation week: establish repeatable pacing and clean station technique before adding volume."
    if progression["volume_multiplier"] <= 1.25:
        return "This week increases running and strength volume slightly while keeping intensity controlled."
    return "This week reaches a higher build load with more race-specific volume and sharper transitions."


def get_week_focus_label(
    week_number: int, preparation_weeks: int, progression: dict
) -> str:
    """Create a specific focus label so weeks do not look identical."""
    phase = progression["phase"]
    build_week_index = ((week_number - 1) % 4) + 1

    if progression["is_taper"]:
        if week_number == preparation_weeks:
            return "Taper - Race Week Recovery"
        return "Taper - Reduce Volume"

    if progression["is_deload"]:
        return f"{phase} - Deload and Technique"

    focus_steps = {
        1: "Baseline Control",
        2: "Volume Increase",
        3: "Longer Repeats",
        4: "Race Rhythm",
    }
    return f"{phase} - {focus_steps.get(build_week_index, 'Progression')}"


def get_weekly_recommendations(
    week_number: int, progression: dict, weak_station_names: list[str]
) -> list[str]:
    """Return small week-specific coaching notes so each week is distinct."""
    if progression["is_taper"]:
        return [
            "Keep all work light and confidence-focused",
            "Prioritize sleep, hydration, mobility, and short technique touches",
        ]

    if progression["is_deload"]:
        return [
            "Reduce total work by about one-third this week",
            "Keep movement quality high and avoid chasing personal bests",
        ]

    recommendations = [
        f"Use this as week {week_number}'s progression step, not a repeat of last week",
    ]
    if weak_station_names:
        recommendations.append(
            f"Keep extra attention on: {', '.join(weak_station_names[:3])}"
        )
    return recommendations


def get_weekly_schedule(training_days_per_week: int) -> list[dict]:
    """Return all 7 days with exact workout/rest split rules."""
    if training_days_per_week <= 3:
        workout_days = ["Monday", "Wednesday", "Friday"]
    elif training_days_per_week == 4:
        workout_days = ["Monday", "Tuesday", "Thursday", "Friday"]
    elif training_days_per_week == 5:
        workout_days = ["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"]
    else:
        workout_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    return [
        {"day": day, "is_workout_day": day in workout_days}
        for day in DAYS_OF_WEEK
    ]


def build_weekly_schedule_rules(training_days_per_week: int) -> dict:
    """Summarize workout and rest days for the response."""
    schedule = get_weekly_schedule(training_days_per_week)
    return {
        "training_days_per_week": training_days_per_week,
        "workout_days": [
            item["day"] for item in schedule if item["is_workout_day"]
        ],
        "rest_days": [
            item["day"] for item in schedule if not item["is_workout_day"]
        ],
    }


def get_workout_type_for_day(day: str, training_days_per_week: int) -> str:
    """Assign workout type based on the exact weekly split."""
    if training_days_per_week <= 3:
        return {
            "Monday": "Running + Strength Foundation",
            "Wednesday": "HYROX Station Skills",
            "Friday": "Endurance + Mini Circuit",
        }.get(day, "Rest")

    if training_days_per_week == 4:
        return {
            "Monday": "Running Intervals",
            "Tuesday": "Strength Training",
            "Thursday": "HYROX Station Skills",
            "Friday": "Endurance / Mini Simulation",
        }.get(day, "Rest")

    if training_days_per_week == 5:
        return {
            "Monday": "Running Intervals",
            "Tuesday": "Strength Training",
            "Wednesday": "HYROX Station Skills",
            "Friday": "Endurance Run",
            "Saturday": "Mini HYROX Simulation",
        }.get(day, "Rest")

    return {
        "Monday": "Running Intervals",
        "Tuesday": "Strength Training",
        "Wednesday": "HYROX Station Skills",
        "Thursday": "Endurance Run",
        "Friday": "Strength + Carries",
        "Saturday": "Mini HYROX Simulation",
    }.get(day, "Rest")


def build_week_plan(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    goal_type: str,
    training_days_per_week: int,
    weak_station_names: list[str],
    station_addons: list[str],
    body_type_adjustments: list[str],
) -> list[dict]:
    """Build all 7 days for one week, including rest days."""
    schedule = get_weekly_schedule(training_days_per_week)
    week_days = []

    for item in schedule:
        day = item["day"]
        if not item["is_workout_day"]:
            week_days.append(build_rest_day(day))
            continue

        workout_type = get_workout_type_for_day(day, training_days_per_week)
        week_days.append(
            build_workout_for_type(
                day=day,
                workout_type=workout_type,
                week_number=week_number,
                progression=progression,
                experience=experience,
                category=category,
                goal_type=goal_type,
                weak_station_names=weak_station_names,
                station_addons=station_addons,
                body_type_adjustments=body_type_adjustments,
            )
        )

    return week_days


def build_rest_day(day: str) -> dict:
    """Return the exact rest day format requested in Stage 10."""
    return {"day": day, **REST_DAY}


def build_workout_for_type(
    day: str,
    workout_type: str,
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    goal_type: str,
    weak_station_names: list[str],
    station_addons: list[str],
    body_type_adjustments: list[str],
) -> dict:
    """Route a workout type to the correct detailed session builder."""
    if workout_type == "Running + Strength Foundation":
        first = build_running_intervals(
            week_number, progression, experience, category, goal_type, weak_station_names, body_type_adjustments
        )
        second = build_strength_training(
            week_number, progression, experience, category, weak_station_names, station_addons, body_type_adjustments
        )
        return combine_workouts(day, workout_type, first, second, "60 minutes")

    if workout_type == "Endurance + Mini Circuit":
        first = build_endurance_run(
            week_number, progression, experience, category, weak_station_names, body_type_adjustments
        )
        second = build_mini_simulation(
            week_number, progression, experience, category, weak_station_names, station_addons, compact=True
        )
        return combine_workouts(day, workout_type, first, second, "60 minutes")

    if workout_type == "Running Intervals":
        return with_day(
            day,
            build_running_intervals(
                week_number, progression, experience, category, goal_type, weak_station_names, body_type_adjustments
            ),
        )

    if workout_type == "Strength Training":
        return with_day(
            day,
            build_strength_training(
                week_number, progression, experience, category, weak_station_names, station_addons, body_type_adjustments
            ),
        )

    if workout_type == "HYROX Station Skills":
        return with_day(
            day,
            build_station_skills(
                week_number, progression, experience, category, weak_station_names, station_addons
            ),
        )

    if workout_type == "Endurance Run":
        return with_day(
            day,
            build_endurance_run(
                week_number, progression, experience, category, weak_station_names, body_type_adjustments
            ),
        )

    if workout_type == "Strength + Carries":
        return with_day(
            day,
            build_strength_and_carries(
                week_number, progression, experience, category, weak_station_names, station_addons
            ),
        )

    return with_day(
        day,
        build_mini_simulation(
            week_number, progression, experience, category, weak_station_names, station_addons
        ),
    )


def analyze_stations(request: PlanRequest) -> list[dict]:
    """Classify every station using current_value first, then level/difficulty."""
    return [
        classify_station_performance(
            station_name=station.station_name,
            current_value=station.current_value,
            level=station.level,
            difficulty=station.difficulty,
            category=request.goal.category,
            gender=request.fitness_profile.gender,
        )
        for station in request.hyrox_assessment.stations
    ]


def get_weak_station_names(station_analysis: list[dict], main_weakness: str) -> list[str]:
    """Combine classified weak stations with the user's selected main weakness."""
    weak_station_names = [
        item["station_name"]
        for item in station_analysis
        if item.get("classification") == "weak"
    ]

    main_weakness_station = match_weakness_to_station(main_weakness)
    if main_weakness_station:
        weak_station_names.append(main_weakness_station)

    return remove_duplicates(weak_station_names)


def match_weakness_to_station(main_weakness: str) -> str | None:
    """Convert free-text weakness into a known station name."""
    weakness = (main_weakness or "").lower()
    for station_name, keywords in STATION_KEYWORDS.items():
        if any(keyword in weakness for keyword in keywords):
            return station_name
    return None


def get_body_type_adjustments(profile) -> list[str]:
    """Add simple training adjustments based on body type, BMI, and weight."""
    body_type = (profile.body_type or "").lower()
    weight = float(profile.weight or 0)
    height_m = float(profile.height or 0) / 100 if profile.height else 0
    bmi = weight / (height_m * height_m) if height_m else 0
    adjustments = []

    if (
        "overweight" in body_type
        or "higher body fat" in body_type
        or "body fat" in body_type
        or bmi >= 30
        or weight >= 100
    ):
        adjustments.extend(
            [
                "Reduce jump volume early and build impact tolerance gradually",
                "Use lower-impact conditioning when fatigue or joint stress rises",
                "Add mobility, recovery, and walking on rest days",
                "Avoid increasing running volume too soon",
            ]
        )
    elif "lean" in body_type:
        adjustments.append("Add strength-building emphasis to support sleds and carries")
    elif "muscular" in body_type:
        adjustments.append("Add running efficiency and aerobic endurance emphasis")
    elif "average" in body_type:
        adjustments.append("Use a balanced split across running, strength, and skills")

    return remove_duplicates(adjustments)


def build_summary(
    experience: str,
    category: str,
    training_phase: str,
    training_days_per_week: int,
    weak_station_names: list[str],
    body_type_adjustments: list[str],
) -> str:
    """Build a readable summary of the plan decisions."""
    level_summary = {
        "beginner": "This plan builds confidence with controlled running, basic strength, station skill practice, and recovery.",
        "intermediate": "This plan improves race pace with structured intervals, moderate strength work, station focus, and simulations.",
        "advanced": "This plan sharpens performance with harder intervals, heavier strength, loaded carries, and race-specific simulation.",
    }[experience]
    category_summary = (
        " Open category intensity stays balanced with technical learning."
        if category == "Open"
        else " Pro category intensity is higher with more sled strength and race simulation."
    )
    weakness_summary = (
        f" Extra work is added for {', '.join(weak_station_names)}."
        if weak_station_names
        else ""
    )
    body_summary = (
        f" Body-type adjustments include: {'; '.join(body_type_adjustments)}."
        if body_type_adjustments
        else ""
    )

    return (
        f"{level_summary}{category_summary} The plan follows a "
        f"{training_phase.lower()} with {training_days_per_week} training days "
        f"per week and Sunday always protected as rest.{weakness_summary}{body_summary}"
    )


def build_weakness_focus(
    weak_station_names: list[str], station_addons: list[str]
) -> list[str]:
    """Create 3-4 readable station weakness notes for the frontend."""
    focus = []
    for station_name in weak_station_names:
        training_focus = STATION_TRAINING_FOCUS.get(
            station_name, "Station-specific technique and pacing"
        )
        focus.append(f"{training_focus} added because {station_name} needs attention")

    return remove_duplicates(focus)[:4]


def build_recommendations(
    experience: str,
    category: str,
    training_phase: str,
    weak_station_names: list[str],
    body_type_adjustments: list[str],
) -> list[str]:
    """Create practical coaching recommendations."""
    recommendations = [
        "Prioritize consistency over intensity",
        "Do mobility after every session",
        "Keep Sunday as complete rest",
        "Avoid increasing volume too quickly",
    ]

    if experience == "beginner":
        recommendations.append("Keep most sessions controlled and finish with good form")
    if category == "Pro":
        recommendations.append("Practice fast but calm race transitions every week")
    if training_phase == "Compressed preparation plan":
        recommendations.append("Focus on key sessions and protect recovery")
    if training_phase == "Progressive preparation plan":
        recommendations.append("Increase volume gradually before adding race intensity")
    if weak_station_names:
        recommendations.append(
            f"Prioritize weak stations first: {', '.join(weak_station_names)}"
        )

    recommendations.extend(body_type_adjustments)
    return remove_duplicates(recommendations)


def get_intensity(category: str, experience: str, phase: str, goal_type: str) -> str:
    """Return intensity label from category, level, goal, and phase."""
    if "Taper" in phase:
        return "Low to Moderate" if category == "Open" else "Moderate"

    if category == "Pro" or goal_type == "compete":
        if experience == "advanced":
            return "High"
        if experience == "intermediate":
            return "Moderate to High"
        return "Moderate"

    if experience == "beginner":
        return "Low to Moderate"
    if experience == "intermediate":
        return "Moderate"
    return "Moderate to High"


def get_progressive_intensity(
    category: str, experience: str, progression: dict, goal_type: str
) -> str:
    """Return intensity label using phase plus deload/taper flags."""
    if progression["is_taper"]:
        return "Low" if category == "Open" else "Low to Moderate"
    if progression["is_deload"]:
        return "Low to Moderate"
    return get_intensity(category, experience, progression["phase"], goal_type)


def scaled_count(base: int, progression: dict, minimum: int = 1) -> int:
    """Scale reps/rounds by the weekly volume multiplier."""
    return max(minimum, round(base * progression["volume_multiplier"]))


def scaled_minutes(base: int, progression: dict, minimum: int = 20) -> int:
    """Scale workout minutes by the weekly volume multiplier."""
    return max(minimum, round(base * progression["volume_multiplier"]))


def get_progression_modifier(week_number: int, phase: str, experience: str) -> int:
    """Small progression number used to scale reps without getting wild."""
    if "Taper" in phase:
        return -1
    if phase == "Foundation":
        return 0
    base = min(2, week_number // 4)
    if experience == "advanced":
        return base + 1
    return base


def get_session_progression_label(week_number: int, progression: dict) -> str:
    """Create a short label used in workout titles and details."""
    if progression["is_taper"]:
        return f"Week {week_number} Taper"
    if progression["is_deload"]:
        return f"Week {week_number} Deload"
    if progression["volume_multiplier"] <= 1.05:
        return f"Week {week_number} Baseline"
    if progression["volume_multiplier"] <= 1.25:
        return f"Week {week_number} Build"
    return f"Week {week_number} Peak Build"


def make_progressive_title(
    base_title: str, week_number: int, progression: dict
) -> str:
    """Prefix workout titles so weeks look clearly different in the UI."""
    return f"{get_session_progression_label(week_number, progression)}: {base_title}"


def add_week_marker(week_number: int, progression: dict, details: str) -> str:
    """Add a visible week marker to workout details."""
    label = get_session_progression_label(week_number, progression)
    return f"{label} session. {details}"


def build_running_intervals(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    goal_type: str,
    weak_station_names: list[str],
    body_type_adjustments: list[str],
) -> dict:
    """Build detailed running intervals based on level and weak running."""
    intensity = get_progressive_intensity(category, experience, progression, goal_type)
    running_is_weak = "1 km run" in weak_station_names
    lower_impact = has_lower_impact_adjustment(body_type_adjustments)
    build_week_index = ((week_number - 1) % 4) + 1
    extra_pacing = " Extra pacing focus: keep the first rep conservative and repeat the same pace." if running_is_weak else ""

    if experience == "beginner":
        if progression["is_taper"]:
            rounds = 4
            details = (
                "Warm-up 8 min brisk walk + mobility, then 4 rounds of 90 sec easy jog "
                "and 90 sec walk. Finish with mobility. No hard running this week."
            )
        elif progression["is_deload"]:
            rounds = 5
            details = (
                "Warm-up 8 min walk + mobility, then 5 rounds of easy jog/walk. "
                "Keep effort at 5/10 and finish feeling fresh."
            )
        elif week_number <= 3:
            if build_week_index == 1:
                rounds, jog_minutes = 6, 2
            elif build_week_index == 2:
                rounds, jog_minutes = 8, 2
            else:
                rounds, jog_minutes = 6, 3
            details = (
                f"Warm-up 8-10 min easy walk/jog + mobility, then {rounds} rounds "
                f"of {jog_minutes} min jog + 1 min walk. Keep effort at 6/10."
            )
        elif lower_impact:
            rounds = scaled_count(6, progression, 5)
            details = (
                f"Warm-up 8 min brisk walk + mobility, then run/walk intervals: "
                f"{rounds} rounds of 2 min jog + 1 min walk. Finish with 4 x 20 sec "
                "relaxed strides only if joints feel good. Keep effort at 6/10."
            )
        elif running_is_weak:
            repeats = scaled_count(4, progression, 4)
            distance = "400m" if week_number < 7 else "600m"
            details = (
                f"Warm-up 10 min easy jog + mobility, then {repeats} x {distance} at "
                f"controlled pace with 90 sec walk recovery. Finish with 5 min cool down."
            )
        else:
            rounds = scaled_count(6, progression, 5)
            details = (
                f"Warm-up 10 min easy jog + mobility, then {rounds} rounds of "
                "2 min jog + 1 min walk. Keep effort smooth at 6/10."
            )
        title = "Run/Walk 1km Foundation"
        duration = "35 minutes"
    elif experience == "intermediate":
        if progression["is_taper"]:
            repeats, distance, pace_note = 3, "600m", "relaxed pace"
        elif progression["is_deload"]:
            repeats, distance, pace_note = 3, "600m", "controlled pace"
        elif build_week_index == 1:
            repeats, distance, pace_note = 4, "600m", "moderate pace"
        elif build_week_index == 2:
            repeats, distance, pace_note = 5, "600m", "moderate pace"
        elif build_week_index == 3:
            repeats, distance, pace_note = 4, "800m", "moderate-hard pace"
        else:
            repeats, distance, pace_note = 3, "600m", "relaxed pace"
        if week_number >= 5 and not progression["is_deload"] and not progression["is_taper"]:
            repeats = scaled_count(5, progression, 4)
            distance = "1km" if running_is_weak or week_number >= 7 else "800m"
            pace_note = "HYROX race pace" if category == "Pro" else "moderate-hard pace"
        details = (
            f"Warm-up 10 min easy jog + drills, then {repeats} x {distance} at "
            f"{pace_note} with 90 sec rest, finish with 5 min cool down. "
            "Keep effort at 7/10 and avoid sprinting the first reps."
        )
        title = "Controlled HYROX Run Intervals"
        duration = "45 minutes"
    else:
        if progression["is_taper"]:
            repeats, distance, pace_note = 3, "800m", "controlled pace"
        elif progression["is_deload"]:
            repeats, distance, pace_note = 3, "800m", "controlled pace"
        elif build_week_index == 1:
            repeats, distance, pace_note = 5, "800m", "threshold rhythm"
        elif build_week_index == 2:
            repeats, distance, pace_note = 4, "1km", "race pace"
        else:
            repeats, distance, pace_note = scaled_count(5, progression, 4), "1km", "race pace"
        rest = "2 min recovery" if category == "Pro" else "90 sec recovery"
        details = (
            f"Warm-up 12 min easy jog + drills, then {repeats} x {distance} at "
            f"{pace_note if category == 'Pro' else 'controlled HYROX pace'} "
            f"with {rest}. Finish with 6 min cool down and pacing notes."
        )
        title = "1km Race-Pace Repeats"
        duration = "60 minutes" if category == "Pro" else "55 minutes"

    if progression["is_taper"]:
        details += " Taper rule: keep it light and avoid max efforts."
    elif progression["is_deload"]:
        details += " Deload rule: reduce volume and prioritize smooth mechanics."
    details += extra_pacing
    details = add_week_marker(week_number, progression, details)

    return workout(
        workout_type="Running",
        workout_title=make_progressive_title(title, week_number, progression),
        details=details,
        hyrox_focus="Improves running between HYROX stations and 1km repeat pacing",
        intensity=intensity,
        duration=duration,
    )


def build_strength_training(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    weak_station_names: list[str],
    station_addons: list[str],
    body_type_adjustments: list[str],
) -> dict:
    """Build detailed HYROX strength work."""
    intensity = get_progressive_intensity(category, experience, progression, "improve")
    sled_is_weak = "Sled push" in weak_station_names or "Sled pull" in weak_station_names
    lean_strength = any("strength-building" in item for item in body_type_adjustments)
    build_week_index = ((week_number - 1) % 4) + 1

    if experience == "beginner":
        exercises = "goblet squats, bodyweight lunges, step-ups, plank"
        if progression["is_taper"]:
            sets = "2 easy rounds"
        elif progression["is_deload"]:
            sets = "2-3 lighter rounds"
        elif build_week_index == 1:
            sets = "3 controlled sets"
        elif build_week_index == 2:
            sets = "3-4 controlled sets"
        else:
            sets = "4 sets with step-ups or light carries"
    elif experience == "intermediate":
        exercises = "front squats, Romanian deadlifts, walking lunges, rows"
        if progression["is_deload"] or progression["is_taper"]:
            sets = "3 lighter sets"
        elif build_week_index == 1:
            sets = "4 sets"
        elif build_week_index == 2:
            sets = "4 sets with slightly more load or reps"
        else:
            sets = "4 sets plus a sled-style circuit"
    else:
        exercises = "back squats, Romanian deadlifts, sled-style push drives, heavy carries"
        if progression["is_deload"] or progression["is_taper"]:
            sets = "3 controlled sets at 60-70% effort"
        elif category == "Pro":
            sets = f"{scaled_count(5, progression, 4)} hard sets"
        else:
            sets = f"{scaled_count(4, progression, 4)} hard sets"

    extras = []
    if sled_is_weak:
        extras.append("add 6 x 15m sled-style push drives or heavy plate pushes")
    if "Sled pull" in weak_station_names:
        extras.append("add rope pulls, rows, and posterior chain work")
    if "Sandbag lunges" in weak_station_names:
        extras.append("add sandbag lunge volume and core bracing")
    if "Wall balls" in weak_station_names:
        extras.append("add squat endurance sets before wall ball practice")
    if lean_strength:
        extras.append("add one extra strength set on the main lower-body lift")

    details = (
        f"Warm-up 10 min mobility and activation, then {sets}: {exercises}. "
        "Rest 60-90 sec between strength movements and keep form crisp."
    )
    if extras:
        details += " " + " ".join(extras)
    if station_addons:
        details += f" Station add-ons: {', '.join(station_addons[:4])}."
    if progression["is_deload"]:
        details += " Deload: reduce load and total sets by about 30%."
    if progression["is_taper"]:
        details += " Taper: move well, skip grinders, and leave the gym fresh."
    details = add_week_marker(week_number, progression, details)

    return workout(
        workout_type="Strength",
        workout_title=make_progressive_title(
            "HYROX Strength Builder", week_number, progression
        ),
        details=details,
        hyrox_focus="Builds strength for sleds, carries, lunges, and wall balls",
        intensity=intensity,
        duration=f"{scaled_minutes({'beginner': 40, 'intermediate': 50, 'advanced': 60}[experience], progression, 30)} minutes",
    )


def build_station_skills(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    weak_station_names: list[str],
    station_addons: list[str],
) -> dict:
    """Build station practice based on weak station classifications."""
    intensity = get_progressive_intensity(category, experience, progression, "improve")
    build_week_index = ((week_number - 1) % 4) + 1
    base_rounds = {"beginner": 2, "intermediate": 3, "advanced": 4}[experience]
    rounds = scaled_count(base_rounds, progression, 2)
    if category == "Pro":
        rounds += 1
    if progression["is_taper"] or progression["is_deload"]:
        rounds = max(2, rounds - 1)

    if progression["is_taper"]:
        station_blocks = [
            "short SkiErg technique 3 x 200m smooth",
            "easy wall ball rhythm sets",
            "transition walk-throughs",
        ]
    elif progression["is_deload"]:
        station_blocks = [
            "easy SkiErg technique 3 x 250m",
            "sled push/pull footwork only",
            "rowing 2 x 300m relaxed",
        ]
    elif build_week_index == 1:
        station_blocks = [
            "SkiErg technique 4 x 250m smooth",
            "sled push/pull footwork practice",
            "rowing pace control",
        ]
    elif build_week_index == 2:
        station_blocks = [
            "SkiErg technique 4 x 300m",
            "sled push/pull footwork practice",
            "rowing 3 x 300m at controlled split",
        ]
    else:
        station_blocks = [
            "SkiErg 4 x 350m",
            "sled push/pull footwork under fatigue",
            "rowing 3 x 400m at controlled split",
            "wall ball rhythm sets",
        ]

    if progression["phase"] in ["Race Specific", "Simulation + Taper"] and not progression["is_taper"]:
        station_blocks.append("1km run + station pairings with smooth transitions")

    weak_station_blocks = {
        "SkiErg": "SkiErg 6 x 250m with long strokes and 45 sec rest",
        "Sled push": "sled-style push drills with strong leg drive",
        "Sled pull": "rope pulls, rows, and braced backward steps",
        "Burpee broad jumps": "burpee technique EMOM with soft landings",
        "Rowing": "rowing intervals with split-control pacing",
        "Farmer's carry": "loaded carries and grip holds",
        "Sandbag lunges": "sandbag lunge sets with upright torso",
        "Wall balls": "wall ball volume progression and shoulder endurance",
    }

    for station_name in weak_station_names:
        if station_name in weak_station_blocks:
            station_blocks.append(weak_station_blocks[station_name])

    beginner_note = (
        " Keep reps low and technique clean."
        if experience == "beginner" and "Burpee broad jumps" in weak_station_names
        else ""
    )

    return workout(
        workout_type="HYROX Station Skills",
        workout_title=make_progressive_title(
            "Station Skill Circuit", week_number, progression
        ),
        details=(
            f"{get_session_progression_label(week_number, progression)} session. "
            f"Warm-up 8 min easy machine work, then {rounds} controlled rounds: "
            f"{'; '.join(remove_duplicates(station_blocks))}. "
            f"Add-ons: {', '.join(station_addons[:5]) if station_addons else 'smooth transitions and breathing control'}."
            f"{beginner_note}"
        ),
        hyrox_focus="Improves station technique and reduces wasted race energy",
        intensity=intensity,
        duration=f"{scaled_minutes({'beginner': 35, 'intermediate': 45, 'advanced': 55}[experience], progression, 30)} minutes",
    )


def build_endurance_run(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    weak_station_names: list[str],
    body_type_adjustments: list[str],
) -> dict:
    """Build aerobic endurance with lower-impact options when needed."""
    running_is_weak = "1 km run" in weak_station_names
    lower_impact = has_lower_impact_adjustment(body_type_adjustments)
    base_minutes = {"beginner": 28, "intermediate": 40, "advanced": 50}[experience]
    if running_is_weak:
        base_minutes += 5
    if category == "Pro":
        base_minutes += 5
    base_minutes = scaled_minutes(base_minutes, progression, 22)
    if progression["is_taper"]:
        base_minutes = max(20, base_minutes - 15)
    elif progression["is_deload"]:
        base_minutes = max(25, base_minutes - 10)

    if lower_impact and experience == "beginner":
        details = (
            f"{base_minutes} minutes low-impact aerobic work: incline walk, bike, "
            "or row at conversational pace. Add 6 x 30 sec relaxed jog only if "
            "impact feels comfortable."
        )
    else:
        finish = " with final 10 min steady" if experience == "advanced" else ""
        details = (
            f"Warm-up 5 min easy, then {base_minutes} minutes Zone 2 running "
            f"at conversational pace{finish}. Keep posture tall and cadence relaxed."
        )
    if progression["is_deload"]:
        details += " Deload: keep it relaxed and finish with extra mobility."
    if progression["is_taper"]:
        details += " Taper: this is a short confidence aerobic session only."
    details = add_week_marker(week_number, progression, details)

    return workout(
        workout_type="Endurance Run",
        workout_title=make_progressive_title(
            "Aerobic Base Builder", week_number, progression
        ),
        details=details,
        hyrox_focus="Builds the engine needed to recover between HYROX stations",
        intensity="Low to Moderate" if category == "Open" else "Moderate",
        duration=f"{base_minutes} minutes",
    )


def build_strength_and_carries(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    weak_station_names: list[str],
    station_addons: list[str],
) -> dict:
    """Build a second strength day for 6-day plans."""
    intensity = get_progressive_intensity(category, experience, progression, "compete")
    build_week_index = ((week_number - 1) % 4) + 1
    carry_focus = (
        "heavy farmer carries, suitcase carries, grip holds, and trunk stability"
        if "Farmer's carry" in weak_station_names
        else "farmer carries, sandbag carries, core bracing, and sled-position drills"
    )
    base_rounds = {"beginner": 3, "intermediate": 4, "advanced": 5}[experience]
    if category == "Pro":
        base_rounds += 1

    if progression["is_taper"]:
        rounds = max(2, round(base_rounds * 0.55))
        effort_note = "light technique carries, easy turns, and no grip max-outs"
    elif progression["is_deload"]:
        rounds = max(2, round(base_rounds * 0.7))
        effort_note = "lighter carries with perfect posture and extra rest"
    else:
        rounds = scaled_count(base_rounds, progression, 3)
        effort_note = (
            "longer carry distances and heavier holds"
            if build_week_index >= 3 or category == "Pro"
            else "controlled carry distances and clean turns"
        )

    carry_distance = {"beginner": 80, "intermediate": 120, "advanced": 160}[experience]
    if category == "Pro":
        carry_distance += 40
    if progression["is_taper"]:
        carry_distance = max(60, carry_distance - 60)
    elif progression["is_deload"]:
        carry_distance = max(70, carry_distance - 40)

    return workout(
        workout_type="Strength + Carries",
        workout_title=make_progressive_title(
            "Loaded Carry Strength", week_number, progression
        ),
        details=(
            f"{get_session_progression_label(week_number, progression)} session. "
            f"Warm-up 10 min, then {rounds} rounds of {carry_distance}m carries: "
            f"{carry_focus}. Add lunges, rows, and anti-rotation core. Focus on "
            f"{effort_note}. Station add-ons: "
            f"{', '.join(station_addons[:4]) if station_addons else 'steady posture and clean turns'}."
        ),
        hyrox_focus="Improves farmer carry, sled control, sandbag stability, and grip endurance",
        intensity=intensity,
        duration=f"{scaled_minutes({'beginner': 40, 'intermediate': 50, 'advanced': 60}[experience], progression, 30)} minutes",
    )


def build_mini_simulation(
    week_number: int,
    progression: dict,
    experience: str,
    category: str,
    weak_station_names: list[str],
    station_addons: list[str],
    compact: bool = False,
) -> dict:
    """Build a run + station simulation session."""
    intensity = get_progressive_intensity(category, experience, progression, "compete")
    phase = progression["phase"]

    if progression["is_taper"]:
        blocks = 2
        run_segment = "400-600m"
        title = "Short Confidence Simulation"
        simulation_note = "Taper: keep it smooth, skip max efforts, and finish fresh."
    elif progression["is_deload"]:
        blocks = 2 if experience == "beginner" else 3
        run_segment = "600m"
        title = "Deload Run + Station Flow"
        simulation_note = "Deload: reduce pressure, focus on clean transitions, and add extra rest."
    elif phase in ["Race Specific", "Simulation + Taper"]:
        base_blocks = {"beginner": 4, "intermediate": 6, "advanced": 7}[experience]
        if category == "Pro":
            base_blocks += 1
        blocks = scaled_count(base_blocks, progression, 3)
        run_segment = "1km"
        title = "Race-Specific HYROX Simulation"
        simulation_note = "Race-specific: link running with station work and practice calm transitions."
    elif phase in ["Build", "Strength + Endurance Build"]:
        base_blocks = {"beginner": 3, "intermediate": 4, "advanced": 5}[experience]
        if category == "Pro":
            base_blocks += 1
        blocks = scaled_count(base_blocks, progression, 3)
        run_segment = "800m-1km"
        title = "Progressive Run + Station Simulation"
        simulation_note = "Build: add one more race-style block while keeping form under control."
    else:
        base_blocks = {"beginner": 2, "intermediate": 3, "advanced": 4}[experience]
        if category == "Pro":
            base_blocks += 1
        blocks = scaled_count(base_blocks, progression, 2)
        run_segment = "600-800m"
        title = "Mini HYROX Simulation"
        simulation_note = "Foundation: learn the rhythm of running into stations without rushing."

    if compact:
        blocks = max(2, blocks - 1)
    blocks = min(blocks, 8)

    stations = prioritize_stations(
        [
            "SkiErg",
            "Sled push",
            "Sled pull",
            "Burpee broad jumps",
            "Rowing",
            "Farmer's carry",
            "Sandbag lunges",
            "Wall balls",
        ],
        weak_station_names,
    )

    details = (
        f"Warm-up 10 min easy, then {blocks} blocks: {run_segment} run into one "
        f"station ({', '.join(stations[:blocks])}). Keep transitions calm, "
        f"breathe before each station, and stop one rep before form breaks. "
        f"{simulation_note}"
    )
    if station_addons:
        details += f" Use add-ons after the circuit: {', '.join(station_addons[:3])}."
    details = add_week_marker(week_number, progression, details)

    return workout(
        workout_type="Mini HYROX Simulation",
        workout_title=make_progressive_title(title, week_number, progression),
        details=details,
        hyrox_focus="Connects running with station work like race day",
        intensity=intensity,
        duration=f"{scaled_minutes({'beginner': 40, 'intermediate': 55, 'advanced': 70}[experience], progression, 30)} minutes",
    )


def build_running_workout(
    level: str, category: str, week_number: int, progression: dict, weakness_flags: list[str]
) -> dict:
    """Compatibility helper for a progressive running session."""
    return build_running_intervals(
        week_number, progression, level, category, "improve", weakness_flags, []
    )


def build_strength_workout(
    level: str, category: str, week_number: int, progression: dict, weakness_flags: list[str]
) -> dict:
    """Compatibility helper for a progressive strength session."""
    return build_strength_training(
        week_number, progression, level, category, weakness_flags, [], []
    )


def build_hyrox_skills_workout(
    level: str, category: str, week_number: int, progression: dict, weakness_flags: list[str]
) -> dict:
    """Compatibility helper for a progressive HYROX skills session."""
    return build_station_skills(week_number, progression, level, category, weakness_flags, [])


def build_endurance_workout(
    level: str, category: str, week_number: int, progression: dict, weakness_flags: list[str]
) -> dict:
    """Compatibility helper for a progressive endurance session."""
    return build_endurance_run(week_number, progression, level, category, weakness_flags, [])


def build_simulation_workout(
    level: str, category: str, week_number: int, progression: dict, weakness_flags: list[str]
) -> dict:
    """Compatibility helper for a progressive run-and-station simulation."""
    return build_mini_simulation(week_number, progression, level, category, weakness_flags, [])


def build_recovery_workout() -> dict:
    """Compatibility helper for the standard recovery day."""
    return REST_DAY.copy()


def combine_workouts(
    day: str, workout_type: str, first: dict, second: dict, duration: str
) -> dict:
    """Combine two focused blocks for 3-day plans."""
    return {
        "day": day,
        "workout_type": workout_type,
        "workout_title": f"{first['workout_title']} + {second['workout_title']}",
        "details": f"{first['details']} Then: {second['details']}",
        "hyrox_focus": f"{first['hyrox_focus']} Also: {second['hyrox_focus']}",
        "intensity": first["intensity"],
        "duration": duration,
    }


def prioritize_stations(stations: list[str], weak_station_names: list[str]) -> list[str]:
    """Move weak stations earlier in simulations."""
    priority = [station for station in weak_station_names if station in stations]
    return remove_duplicates(priority + stations)


def has_lower_impact_adjustment(body_type_adjustments: list[str]) -> bool:
    """Check whether the profile calls for lower-impact progressions."""
    return any("lower-impact" in item or "jump volume" in item for item in body_type_adjustments)


def with_day(day: str, workout_data: dict) -> dict:
    """Attach day name to a workout dictionary."""
    return {"day": day, **workout_data}


def workout(
    workout_type: str,
    workout_title: str,
    details: str,
    hyrox_focus: str,
    intensity: str,
    duration: str,
) -> dict:
    """Small helper to keep workout dictionaries consistent."""
    return {
        "workout_type": workout_type,
        "workout_title": workout_title,
        "details": details,
        "hyrox_focus": hyrox_focus,
        "intensity": intensity,
        "duration": duration,
    }


def remove_duplicates(items: list[str]) -> list[str]:
    """Keep list order while removing repeated values."""
    unique_items = []
    for item in items:
        if item and item not in unique_items:
            unique_items.append(item)
    return unique_items
