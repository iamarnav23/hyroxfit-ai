from fastapi import FastAPI

from routes.ai_routes import router as ai_router
from routes.cardio_routes import router as cardio_router
from routes.diet_routes import router as diet_router
from routes.goal_routes import router as goal_router
from routes.plan_routes import router as plan_router
from routes.profile_routes import router as profile_router
from routes.progress_routes import router as progress_router


app = FastAPI(
    title="HYROXFit AI Backend",
    description="Backend MVP for personalized HYROX race preparation planning.",
    version="1.0.0",
)


@app.get("/")
def health_check():
    """Simple route to confirm that the backend server is running."""
    return {"message": "HYROXFit AI Backend is running"}


# Routes are split by feature so the backend stays simple as it grows.
app.include_router(profile_router)
app.include_router(goal_router)
app.include_router(plan_router)
app.include_router(progress_router)
app.include_router(diet_router)
app.include_router(ai_router)
app.include_router(cardio_router)
