from fastapi import APIRouter

from schemas.profile_schema import FitnessProfile, HyroxAssessment


router = APIRouter(tags=["Profile"])


@router.post("/fitness-profile")
def save_fitness_profile(profile: FitnessProfile):
    """Validate a fitness profile.

    Database saving will be added later when Supabase is connected.
    """
    return {
        "message": "Fitness profile received",
        "fitness_profile": profile,
    }


@router.post("/hyrox-assessment")
def save_hyrox_assessment(assessment: HyroxAssessment):
    """Validate HYROX station assessment data."""
    return {
        "message": "HYROX assessment received",
        "hyrox_assessment": assessment,
    }
