import re
from typing import Optional


# Internal planning benchmarks only. These are not official HYROX rankings.
HYROX_BENCHMARKS = {
    "men_open": {
        "1 km run": {
            "standard": "1km run",
            "strong_seconds": 270,
            "average_seconds": 360,
            "weak_seconds": 420,
        },
        "SkiErg": {
            "standard": "1000m SkiErg",
            "strong_seconds": 240,
            "average_seconds": 300,
            "weak_seconds": 360,
        },
        "Sled push": {
            "standard": "50m sled push at 152kg including sled",
            "strong_seconds": 120,
            "average_seconds": 180,
            "weak_seconds": 240,
        },
        "Sled pull": {
            "standard": "50m sled pull at 103kg including sled",
            "strong_seconds": 150,
            "average_seconds": 210,
            "weak_seconds": 270,
        },
        "Burpee broad jumps": {
            "standard": "80m burpee broad jumps",
            "strong_seconds": 240,
            "average_seconds": 360,
            "weak_seconds": 480,
        },
        "Rowing": {
            "standard": "1000m rowing",
            "strong_seconds": 220,
            "average_seconds": 280,
            "weak_seconds": 340,
        },
        "Farmer's carry": {
            "standard": "200m farmer's carry with 2x24kg kettlebells",
            "strong_seconds": 120,
            "average_seconds": 180,
            "weak_seconds": 240,
        },
        "Sandbag lunges": {
            "standard": "100m sandbag lunges with 20kg",
            "strong_seconds": 240,
            "average_seconds": 360,
            "weak_seconds": 480,
        },
        "Wall balls": {
            "standard": "100 wall balls with 6kg",
            "strong_seconds": 300,
            "average_seconds": 420,
            "weak_seconds": 540,
        },
    }
}


STATION_TRAINING_FOCUS = {
    "1 km run": "1km repeat pacing, Zone 2 endurance, and run efficiency",
    "SkiErg": "SkiErg intervals, lat endurance, and stroke technique",
    "Sled push": "Lower-body strength, leg drive, and sled-style push drills",
    "Sled pull": "Posterior chain strength, rows, deadlifts, and rope pulls",
    "Burpee broad jumps": "Burpee rhythm, explosive conditioning, and landing control",
    "Rowing": "Rowing intervals, split control, and pacing drills",
    "Farmer's carry": "Grip strength, loaded carries, and trunk stability",
    "Sandbag lunges": "Lunge volume, unilateral strength, and core stability",
    "Wall balls": "Squat endurance, shoulder endurance, and wall ball progression",
}


STATION_ADDONS = {
    "1 km run": [
        "1km repeat progressions",
        "Zone 2 endurance work",
        "pacing notes between stations",
    ],
    "SkiErg": [
        "SkiErg intervals",
        "lat and upper-body pulling endurance",
        "stroke technique notes",
    ],
    "Sled push": [
        "squats and lunges",
        "sled-style push drives",
        "leg drive and acceleration work",
    ],
    "Sled pull": [
        "deadlifts and rows",
        "rope pull drills",
        "posterior chain work",
    ],
    "Burpee broad jumps": [
        "burpee broad jump technique",
        "explosive conditioning",
        "reduced beginner volume",
    ],
    "Rowing": [
        "rowing intervals",
        "pacing drills",
        "controlled split practice",
    ],
    "Farmer's carry": [
        "loaded carries",
        "grip strength",
        "trunk stability",
    ],
    "Sandbag lunges": [
        "lunge volume",
        "core stability",
        "unilateral strength",
    ],
    "Wall balls": [
        "squat endurance",
        "shoulder endurance",
        "wall ball volume progression",
    ],
}


def parse_current_value_to_seconds(current_value: str) -> Optional[int]:
    """Parse common performance strings into seconds when possible."""
    if not current_value:
        return None

    value = current_value.strip().lower()

    seconds_match = re.search(r"(\d+(?:\.\d+)?)\s*(sec|secs|second|seconds)\b", value)
    if seconds_match:
        return round(float(seconds_match.group(1)))

    minutes_match = re.search(r"(\d+(?:\.\d+)?)\s*(min|mins|minute|minutes)\b", value)
    if minutes_match:
        return round(float(minutes_match.group(1)) * 60)

    time_matches = re.findall(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", value)
    if time_matches:
        minutes, seconds = time_matches[-1]
        return int(minutes) * 60 + int(seconds)

    plain_number_match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", value)
    if plain_number_match:
        number = float(plain_number_match.group(1))
        # For messy single-number input, treat realistic race station numbers as minutes.
        if number <= 30:
            return round(number * 60)
        return round(number)

    return None


def get_benchmark_key(category: str, gender: str) -> str:
    """Choose a benchmark set. Men Open is the current Stage 10 default."""
    return "men_open"


def classify_station_performance(
    station_name: str,
    current_value: str,
    level: str,
    difficulty: str,
    category: str,
    gender: str,
) -> dict:
    """Classify one station as strong, average, weak, or unknown."""
    parsed_seconds = parse_current_value_to_seconds(current_value)
    benchmarks = HYROX_BENCHMARKS[get_benchmark_key(category, gender)].get(station_name)

    if parsed_seconds is not None and benchmarks:
        if parsed_seconds <= benchmarks["strong_seconds"]:
            classification = "strong"
            reason = f"User time is faster than the strong benchmark for {benchmarks['standard']}"
        elif parsed_seconds <= benchmarks["average_seconds"]:
            classification = "average"
            reason = f"User time is near the average benchmark for {benchmarks['standard']}"
        elif parsed_seconds >= benchmarks["weak_seconds"]:
            classification = "weak"
            reason = f"User time is slower than the weak benchmark for {benchmarks['standard']}"
        else:
            classification = "weak"
            reason = f"User time is slower than the average benchmark for {benchmarks['standard']}"
    else:
        classification = classify_from_level_and_difficulty(level, difficulty)
        reason = "No parseable time was found, so level and difficulty were used"

    return {
        "station_name": station_name,
        "parsed_seconds": parsed_seconds,
        "classification": classification,
        "reason": reason,
        "training_focus": STATION_TRAINING_FOCUS.get(
            station_name, "Station technique and pacing practice"
        ),
    }


def classify_from_level_and_difficulty(level: str, difficulty: str) -> str:
    """Fallback classification when current_value cannot be parsed."""
    level = (level or "").lower()
    difficulty = (difficulty or "").lower()

    if level == "beginner" and difficulty == "hard":
        return "weak"
    if level == "beginner" and difficulty == "medium":
        return "average"
    if level == "intermediate" and difficulty == "hard":
        return "weak"
    if level == "intermediate" and difficulty == "medium":
        return "average"
    if level == "advanced" and difficulty == "easy":
        return "strong"
    if level == "advanced":
        return "average"
    return "average"


def get_station_specific_addons(station_classifications: list[dict]) -> list[str]:
    """Return station-specific training add-ons for weak stations."""
    addons = []
    for station in station_classifications:
        if station.get("classification") != "weak":
            continue
        station_name = station.get("station_name")
        for addon in STATION_ADDONS.get(station_name, []):
            if addon not in addons:
                addons.append(addon)
    return addons
