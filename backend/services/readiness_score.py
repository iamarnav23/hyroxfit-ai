from schemas.plan_schema import PlanRequest


LEVEL_POINTS = {
    "beginner": 0.45,
    "intermediate": 0.70,
    "advanced": 1.00,
}

DIFFICULTY_PENALTY = {
    "easy": 0.00,
    "medium": 0.10,
    "hard": 0.25,
}


def calculate_readiness_score(request: PlanRequest) -> dict:
    """Calculate a simple HYROX readiness score out of 100."""
    stations = request.hyrox_assessment.stations
    profile = request.fitness_profile
    goal = request.goal

    running = _score_station_group(stations, ["run"], 25)
    strength = _score_station_group(
        stations,
        ["sled push", "sled pull", "farmer", "sandbag", "wall ball"],
        25,
    )
    hyrox_skill = _score_station_group(
        stations,
        [
            "skierg",
            "sled push",
            "sled pull",
            "burpee",
            "rowing",
            "farmer",
            "sandbag",
            "wall ball",
        ],
        25,
    )
    consistency = _score_consistency(profile.training_days_per_week)
    recovery_diet = _score_recovery(profile.injury_history, goal.preparation_weeks)

    breakdown = {
        "running": running,
        "strength": strength,
        "hyrox_skill": hyrox_skill,
        "consistency": consistency,
        "recovery_diet": recovery_diet,
    }
    total_score = sum(breakdown.values())

    return {
        "total_score": total_score,
        "status": _build_status(total_score, goal.category, stations),
        "breakdown": breakdown,
    }


def _score_station_group(stations: list, keywords: list[str], max_score: int) -> int:
    """Score a group of stations based on level and difficulty."""
    matching_stations = [
        station
        for station in stations
        if any(keyword in station.station_name.lower() for keyword in keywords)
    ]

    if not matching_stations:
        return int(max_score * 0.5)

    station_scores = []
    for station in matching_stations:
        base = LEVEL_POINTS[station.level]
        penalty = DIFFICULTY_PENALTY[station.difficulty]
        station_scores.append(max(base - penalty, 0.1))

    average_score = sum(station_scores) / len(station_scores)
    return round(average_score * max_score)


def _score_consistency(training_days_per_week: int) -> int:
    """Score consistency from planned weekly training frequency."""
    if training_days_per_week >= 5:
        return 15
    if training_days_per_week == 4:
        return 12
    if training_days_per_week == 3:
        return 10
    if training_days_per_week == 2:
        return 7
    return 5


def _score_recovery(injury_history: str, preparation_weeks: int) -> int:
    """Estimate recovery readiness from injury history and available prep time."""
    injury_text = injury_history.lower()
    has_injury = "no" not in injury_text and "none" not in injury_text

    score = 8
    if preparation_weeks >= 12:
        score += 2
    elif preparation_weeks < 8:
        score -= 1

    if has_injury:
        score -= 3

    return max(1, min(score, 10))


def _build_status(total_score: int, category: str, stations: list) -> str:
    """Turn the numeric score into useful feedback."""
    weak_stations = [
        station.station_name
        for station in stations
        if station.difficulty == "hard" or station.level == "beginner"
    ]
    weak_text = ", ".join(weak_stations[:3])

    if total_score >= 80:
        return f"Strong readiness for {category} category"

    if total_score >= 65:
        if weak_text:
            return (
                f"Ready for {category} category but needs improvement in {weak_text}"
            )
        return f"Ready for {category} category with a few areas to improve"

    if total_score >= 50:
        if weak_text:
            return f"Building toward {category} category readiness; focus on {weak_text}"
        return f"Building toward {category} category readiness"

    if weak_text:
        return f"Not race-ready yet; build base fitness and improve {weak_text}"

    return "Not race-ready yet; build base fitness first"
