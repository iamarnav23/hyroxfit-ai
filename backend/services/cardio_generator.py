from schemas.cardio_schema import CardioPlanRequest, CardioWeeklyReview


SAFETY_DISCLAIMER = "This is general fitness guidance and not medical advice."


def calculate_training_zones(max_heart_rate: int | None) -> list[dict]:
    """Build standard cardio zones, adding HR ranges when max HR is available."""
    zone_data = [
        ("Zone 1", "Recovery", 0.50, 0.60, "2-3"),
        ("Zone 2", "Aerobic base", 0.60, 0.70, "4-5"),
        ("Zone 3", "Tempo", 0.70, 0.80, "6"),
        ("Zone 4", "Threshold", 0.80, 0.90, "7-8"),
        ("Zone 5", "VO2 max / high intensity", 0.90, 1.00, "9-10"),
    ]

    zones = []
    for zone, purpose, low, high, rpe in zone_data:
        item = {
            "zone": zone,
            "purpose": purpose,
            "percent_max_hr": f"{round(low * 100)}-{round(high * 100)}% max HR",
            "rpe": rpe,
        }
        if max_heart_rate:
            item["heart_rate_range"] = (
                f"{round(max_heart_rate * low)}-{round(max_heart_rate * high)} bpm"
            )
        else:
            item["heart_rate_range"] = None
        zones.append(item)

    return zones


def get_cardio_weekly_schedule(training_days_per_week: int) -> list[dict]:
    """Return a seven-day schedule with Sunday always protected as recovery."""
    if training_days_per_week <= 2:
        workouts = {
            "Tuesday": "Zone 2 Base",
            "Friday": "Zone 5 Intervals",
        }
    elif training_days_per_week == 3:
        workouts = {
            "Monday": "Zone 2 Base",
            "Wednesday": "Zone 5 Intervals",
            "Friday": "Tempo / Endurance",
        }
    elif training_days_per_week == 4:
        workouts = {
            "Monday": "Zone 5 Intervals",
            "Tuesday": "Zone 2 Base",
            "Thursday": "Zone 4 Threshold",
            "Saturday": "Long Zone 2 Endurance",
        }
    elif training_days_per_week == 5:
        workouts = {
            "Monday": "Zone 5 Intervals",
            "Tuesday": "Zone 2 Base",
            "Wednesday": "Zone 1/2 Recovery Technique",
            "Friday": "Zone 4 Threshold",
            "Saturday": "Long Zone 2 Endurance",
        }
    else:
        workouts = {
            "Monday": "Zone 5 Intervals",
            "Tuesday": "Zone 2 Base",
            "Wednesday": "Technique / Zone 1 Recovery",
            "Thursday": "Zone 4 Threshold",
            "Friday": "Zone 2 Steady",
            "Saturday": "Long Endurance / Mixed",
        }

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return [
        {
            "day": day,
            "is_workout_day": day in workouts,
            "session_focus": workouts.get(day, "Rest / Recovery"),
        }
        for day in days
    ]


def generate_base_cardio_plan(
    request: CardioPlanRequest, previous_review: CardioWeeklyReview | dict | None = None
) -> dict:
    """Generate the safe rule-based one-week Cardio Lab plan before AI refinement."""
    adjustment = get_next_week_adjustment(previous_review)
    zones = calculate_training_zones(request.max_heart_rate)
    schedule = get_cardio_weekly_schedule(request.training_days_per_week)
    days = [
        build_cardio_day(request, item, adjustment)
        for item in schedule
    ]

    return {
        "week_number": request.week_number,
        "cardio_goal": request.cardio_goal,
        "preferred_training_mode": request.preferred_training_mode,
        "experience_level": request.experience_level,
        "training_days_per_week": request.training_days_per_week,
        "week_summary": build_week_summary(request, adjustment),
        "plan_reasoning": build_plan_reasoning(request, adjustment),
        "training_zones": zones,
        "days": days,
        "zone_distribution": calculate_zone_distribution(days),
        "progression_advice": adjustment["message"],
        "recovery_advice": build_recovery_advice(request, adjustment),
        "safety_disclaimer": SAFETY_DISCLAIMER,
        "ai_status": "rule_based",
    }


def build_cardio_day(request: CardioPlanRequest, schedule_item: dict, adjustment: dict) -> dict:
    """Build one cardio day using the requested mode, goal, level, and safety flags."""
    day = schedule_item["day"]
    focus = schedule_item["session_focus"]

    if not schedule_item["is_workout_day"] or day == "Sunday":
        return {
            "day": day,
            "workout_type": "Rest / Recovery",
            "training_mode": "Recovery",
            "zone": "Zone 1",
            "workout_title": "Complete Recovery Day",
            "details": "Rest from structured cardio. Optional easy walk, mobility, hydration, and sleep focus.",
            "intensity": "Very Low",
            "duration": "Rest day",
            "rpe": "1-2",
            "coaching_tip": "Recovery is where adaptation happens. Keep Sunday protected.",
            "safety_note": SAFETY_DISCLAIMER,
        }

    workout_type = adjust_focus_for_goal(focus, request)
    mode = choose_training_mode(request, day, workout_type, adjustment)
    duration = choose_duration(request, workout_type, adjustment)
    zone = get_zone_for_workout(workout_type)
    title = build_workout_title(mode, workout_type, request.week_number)
    details = build_workout_details(mode, workout_type, request, adjustment)

    return {
        "day": day,
        "workout_type": workout_type,
        "training_mode": mode,
        "zone": zone,
        "workout_title": title,
        "details": details,
        "intensity": get_intensity_label(zone, adjustment),
        "duration": duration,
        "rpe": get_rpe_for_zone(zone),
        "coaching_tip": build_coaching_tip(request, workout_type, mode),
        "safety_note": build_safety_note(request, workout_type),
    }


def adjust_focus_for_goal(focus: str, request: CardioPlanRequest) -> str:
    """Adjust the schedule focus for goals that need more aerobic or less intensity."""
    goal = request.cardio_goal.lower()
    level = request.experience_level

    if "marathon" in goal and "Zone 5" in focus:
        return "Zone 3 Tempo" if level == "advanced" else "Zone 2 Base"
    if "cardiovascular health" in goal and "Zone 5" in focus and level == "beginner":
        return "Easy Intervals"
    if "zone 5" in goal and "Zone 5" in focus:
        return "Zone 5 Intervals"
    if "hyrox" in goal and "Tempo" in focus:
        return "1km Repeat Endurance"
    return focus


def choose_training_mode(
    request: CardioPlanRequest, day: str, workout_type: str, adjustment: dict
) -> str:
    """Choose sport mode, preferring low-impact work when injury is mentioned."""
    if adjustment["reduce_impact"]:
        if request.preferred_training_mode == "Swimming":
            return "Swimming"
        return "Cycling"

    if request.preferred_training_mode != "Mixed":
        return request.preferred_training_mode

    mixed_modes = {
        "Monday": "Running",
        "Tuesday": "Cycling",
        "Wednesday": "Swimming",
        "Thursday": "Running",
        "Friday": "Cycling",
        "Saturday": "Swimming",
    }
    return mixed_modes.get(day, "Running")


def choose_duration(request: CardioPlanRequest, workout_type: str, adjustment: dict) -> str:
    """Pick a readable duration from user availability and adaptive adjustment."""
    base_minutes = parse_duration_minutes(request.available_session_duration)
    level_bonus = {"beginner": -5, "intermediate": 0, "advanced": 8}[request.experience_level]

    if "Long" in workout_type or "Endurance" in workout_type:
        base_minutes += 15
    if "Zone 5" in workout_type and request.experience_level == "beginner":
        base_minutes -= 5
    if "Zone 5" in workout_type and request.cardio_goal == "Marathon preparation":
        base_minutes -= 8

    adjusted = round((base_minutes + level_bonus) * adjustment["volume_multiplier"])
    return f"{max(20, adjusted)} minutes"


def parse_duration_minutes(duration: str) -> int:
    """Convert duration labels into an approximate middle value."""
    value = (duration or "").lower()
    if "60+" in value:
        return 70
    if "45-60" in value:
        return 55
    if "30-45" in value:
        return 40
    return 40


def get_zone_for_workout(workout_type: str) -> str:
    """Map workout type to the main target zone."""
    if "Zone 5" in workout_type:
        return "Zone 5"
    if "Threshold" in workout_type:
        return "Zone 4"
    if "Tempo" in workout_type or "1km Repeat" in workout_type:
        return "Zone 3/4"
    if "Recovery" in workout_type or "Technique" in workout_type:
        return "Zone 1/2"
    return "Zone 2"


def build_workout_title(mode: str, workout_type: str, week_number: int) -> str:
    """Create a compact title for the day card."""
    return f"Week {week_number}: {mode} {workout_type}"


def build_workout_details(
    mode: str, workout_type: str, request: CardioPlanRequest, adjustment: dict
) -> str:
    """Create detailed but safe cardio workout instructions."""
    level = request.experience_level
    reduce_zone5 = adjustment["reduce_zone5"]

    if "Zone 5" in workout_type:
        if level == "beginner" or reduce_zone5:
            interval = {
                "Running": "6 x 30 sec hard effort at RPE 9 with 90 sec easy walk recovery",
                "Cycling": "8 x 45 sec hard effort with 90 sec easy spin",
                "Swimming": "8 x 50m fast with 45-60 sec rest",
            }.get(mode, "6 x 30 sec hard effort with full easy recovery")
            return f"Warm-up 10 min easy. Then {interval}. Cool down 5-10 min."
        if level == "intermediate":
            interval = {
                "Running": "6 x 400m hard controlled effort with 90 sec rest",
                "Cycling": "6 x 2 min hard with 2 min easy spin",
                "Swimming": "10 x 50m fast with 45 sec rest",
            }.get(mode, "6 controlled high-intensity repeats with full recovery")
            return f"Warm-up 10 min. Then {interval}. Cool down 10 min."
        interval = {
            "Running": "5 x 3 min at Zone 5 effort with 3 min easy recovery",
            "Cycling": "5 x 3 min hard with 3 min easy spin",
            "Swimming": "12 x 50m fast or 6 x 100m strong with full recovery",
        }.get(mode, "5 x 3 min Zone 5 with equal easy recovery")
        return f"Warm-up 15 min. Then {interval}. Cool down 10 min."

    if "Threshold" in workout_type or "Tempo" in workout_type or "1km Repeat" in workout_type:
        if "hyrox" in request.cardio_goal.lower():
            return "Warm-up 10 min. Then 4-6 controlled 1km-style efforts or 4 min blocks with 2 min easy recovery. Cool down 10 min."
        if mode == "Cycling":
            return "Warm-up 10 min easy spin. Then 3 x 8 min strong steady effort with 3 min easy spin. Cool down 8 min."
        if mode == "Swimming":
            return "Warm-up 200m easy. Then 6 x 100m steady-hard with 30 sec rest. Cool down 100-200m easy."
        return "Warm-up 10 min easy. Then 20-25 min controlled tempo effort or 3 x 8 min threshold blocks. Cool down 10 min."

    if "Recovery" in workout_type or "Technique" in workout_type:
        if mode == "Swimming":
            return "Easy technique swim with relaxed breathing, drills, and long rests. Stay mostly Zone 1-2."
        return "Easy recovery cardio with relaxed breathing. Add mobility and stop before fatigue builds."

    if "Long" in workout_type or "Endurance" in workout_type or "Steady" in workout_type:
        if mode == "Cycling":
            return "Continuous Zone 2 ride at conversational effort. Keep cadence smooth and avoid surges."
        if mode == "Swimming":
            return "Continuous easy swim or steady intervals with relaxed breathing and full control."
        return "Continuous Zone 2 endurance session at conversational effort. Keep pace controlled and finish fresh."

    if mode == "Cycling":
        return "Easy Zone 2 ride at conversational effort. Keep cadence smooth and breathing controlled."
    if mode == "Swimming":
        return "Easy continuous swim or relaxed intervals. Keep technique calm and effort aerobic."
    return "Easy Zone 2 run or run/walk at conversational effort. Stay relaxed and avoid racing the session."


def get_intensity_label(zone: str, adjustment: dict) -> str:
    """Return user-facing intensity label."""
    if adjustment["intensity_modifier"] == "reduced":
        return "Controlled"
    if "Zone 5" in zone:
        return "High"
    if "Zone 4" in zone or "Zone 3" in zone:
        return "Moderate to Hard"
    return "Low to Moderate"


def get_rpe_for_zone(zone: str) -> str:
    """Return RPE label for a zone."""
    if "Zone 5" in zone:
        return "9-10"
    if "Zone 4" in zone:
        return "7-8"
    if "Zone 3" in zone:
        return "6-8"
    if "Zone 1" in zone:
        return "2-5"
    return "4-5"


def build_coaching_tip(request: CardioPlanRequest, workout_type: str, mode: str) -> str:
    """Add a practical coaching tip."""
    if "Zone 5" in workout_type:
        return "Hard means controlled, not reckless. Stop the interval before form collapses."
    if "marathon" in request.cardio_goal.lower():
        return "Keep aerobic work easy enough that you could speak in short sentences."
    if "hyrox" in request.cardio_goal.lower():
        return "Think about recovering quickly after each effort, like running between HYROX stations."
    if mode == "Swimming":
        return "Technique comes first. Smooth breathing beats forcing speed."
    return "Finish with the feeling that you could do a little more."


def build_safety_note(request: CardioPlanRequest, workout_type: str) -> str:
    """Add safety guidance, especially around injury and intensity."""
    limitation = (request.injury_or_limitation or "").strip()
    if limitation:
        return (
            "Because you listed a limitation, reduce impact and stop if pain increases. "
            "Consider guidance from a qualified medical or physiotherapy professional."
        )
    if "Zone 5" in workout_type:
        return "Do not sprint all-out. Use controlled high intensity and recover fully."
    return SAFETY_DISCLAIMER


def build_week_summary(request: CardioPlanRequest, adjustment: dict) -> str:
    """Summarize the generated week."""
    return (
        f"Week {request.week_number} focuses on {request.cardio_goal.lower()} using "
        f"{request.training_days_per_week} cardio days with {request.preferred_training_mode.lower()} preference."
    )


def build_plan_reasoning(request: CardioPlanRequest, adjustment: dict) -> str:
    """Explain why the base structure was chosen."""
    reasons = [
        f"{request.experience_level.title()} level controls interval volume",
        f"{request.cardio_goal} shapes the zone mix",
        "Sunday remains recovery",
    ]
    if request.injury_or_limitation:
        reasons.append("impact is reduced because a limitation was listed")
    if adjustment["source"] != "none":
        reasons.append("last week feedback adjusted the next week")
    return "; ".join(reasons) + "."


def build_recovery_advice(request: CardioPlanRequest, adjustment: dict) -> str:
    """Return recovery advice for the week."""
    if adjustment["reduce_impact"] or request.injury_or_limitation:
        return "Keep recovery strict, use lower-impact cardio, and seek professional guidance if pain persists."
    if request.experience_level == "beginner":
        return "Protect easy days, hydrate, and avoid adding extra Zone 5 work."
    return "Keep easy days easy, sleep well, and avoid stacking hard sessions back to back."


def calculate_zone_distribution(days: list[dict]) -> dict:
    """Count the main zone emphasis across the week."""
    distribution = {
        "zone_1": 0,
        "zone_2": 0,
        "zone_3": 0,
        "zone_4": 0,
        "zone_5": 0,
    }
    for day in days:
        zone = day.get("zone", "")
        if "Zone 5" in zone:
            distribution["zone_5"] += 1
        elif "Zone 4" in zone:
            distribution["zone_4"] += 1
        elif "Zone 3" in zone:
            distribution["zone_3"] += 1
        elif "Zone 2" in zone:
            distribution["zone_2"] += 1
        else:
            distribution["zone_1"] += 1
    return distribution


def get_next_week_adjustment(previous_review) -> dict:
    """Translate weekly feedback into simple adaptive rules for the next plan."""
    adjustment = {
        "source": "none",
        "volume_multiplier": 1.0,
        "intensity_modifier": "normal",
        "reduce_zone5": False,
        "reduce_impact": False,
        "message": "Progress gradually while keeping easy days easy and Sunday as recovery.",
    }

    if not previous_review:
        return adjustment

    review = (
        previous_review.model_dump()
        if hasattr(previous_review, "model_dump")
        else dict(previous_review)
    )
    completed = int(review.get("workouts_completed") or 0)
    total = max(1, int(review.get("total_workouts") or 1))
    completion = completed / total
    energy = (review.get("average_energy_level") or "").lower()
    difficulty = (review.get("average_difficulty") or "").lower()
    notes = (review.get("notes") or "").lower()

    adjustment["source"] = "weekly_review"

    if completion < 0.6:
        adjustment["volume_multiplier"] *= 0.85
        adjustment["intensity_modifier"] = "reduced"
        adjustment["message"] = "Completion was below 60%, so next week simplifies volume and keeps intensity controlled."

    if energy == "low":
        adjustment["volume_multiplier"] *= 0.9
        adjustment["reduce_zone5"] = True
        adjustment["message"] = "Low energy reported, so Zone 5 volume is reduced and recovery is emphasized."

    if difficulty == "hard":
        adjustment["volume_multiplier"] *= 0.9
        adjustment["intensity_modifier"] = "reduced"
        adjustment["message"] = "Difficulty was hard, so duration or intensity is reduced next week."

    if completion >= 0.85 and energy == "high" and difficulty != "hard":
        adjustment["volume_multiplier"] *= 1.08
        adjustment["message"] = "Strong completion and high energy reported, so next week progresses slightly."

    if review.get("updated_1km_time") or review.get("updated_5km_time"):
        adjustment["message"] += " Updated time data was received, so progression is maintained cautiously."

    if any(word in notes for word in ["pain", "injury", "hurt", "ache", "dizzy", "chest", "faint"]):
        adjustment["volume_multiplier"] *= 0.8
        adjustment["reduce_zone5"] = True
        adjustment["reduce_impact"] = True
        adjustment["intensity_modifier"] = "reduced"
        adjustment["message"] = (
            "Pain or medical warning language was reported, so impact and intensity are reduced. "
            "Seek qualified medical or physiotherapy guidance if symptoms continue."
        )

    adjustment["volume_multiplier"] = round(max(0.65, min(1.12, adjustment["volume_multiplier"])), 2)
    return adjustment
