# Rox Zone

Rox Zone is a personalized HYROX race preparation planner. Users can sign up,
enter fitness details, assess HYROX stations, choose a race goal, generate a
rule-based training plan, save workout progress, generate simple diet guidance,
and ask an AI coach for safe personalization suggestions.

Current stage: **Cardio Lab module added - Adaptive Cardio + Zone 5 Planner**

Not included yet:

- Payments

## Project Structure

```text
backend/
  main.py
  routes/
    ai_routes.py
  schemas/
    ai_schema.py
  services/
    ai_coach.py
  database/
    supabase_client.py

frontend/
  pages/
    index.js
    signup.js
    login.js
    form.js
    plan.js
    dashboard.js
    diet.js
    cardio-lab.js
    ai-coach.js
  components/
  lib/
    supabaseClient.js
    useRequireUser.js

supabase_schema.sql
supabase_stage8_diet_schema.sql
supabase_stage9_ai_schema.sql
supabase_cardio_lab_schema.sql
```

## Supabase Setup

1. Create a Supabase project.
2. Go to Supabase SQL Editor.
3. Open [supabase_schema.sql](/Users/arnav/Desktop/personal-portfolio/hyrox%20ai/supabase_schema.sql).
4. Paste the SQL into Supabase SQL Editor and run it.

This creates:

- `fitness_profiles`
- `hyrox_assessments`
- `goals`
- `workout_plans`
- `workout_progress`
- `race_readiness_scores`

It also enables Row Level Security so users can only manage rows where
`auth.uid() = user_id`.

For Stage 8 diet suggestions:

1. Open [supabase_stage8_diet_schema.sql](/Users/arnav/Desktop/personal-portfolio/hyrox%20ai/supabase_stage8_diet_schema.sql).
2. Paste the SQL into Supabase SQL Editor and run it.

This creates:

- `diet_suggestions`

It also enables Row Level Security for diet suggestions.

For Stage 9 AI Coach:

1. Open [supabase_stage9_ai_schema.sql](/Users/arnav/Desktop/personal-portfolio/hyrox%20ai/supabase_stage9_ai_schema.sql).
2. Paste the SQL into Supabase SQL Editor and run it.

This creates:

- `ai_recommendations`

It also adds versioning columns to `workout_plans`:

- `parent_plan_id`
- `version_number`
- `source`
- `ai_recommendation_id`

For Cardio Lab:

1. Open [supabase_cardio_lab_schema.sql](/Users/arnav/Desktop/personal-portfolio/hyrox%20ai/supabase_cardio_lab_schema.sql).
2. Paste the SQL into Supabase SQL Editor and run it.

This creates:

- `cardio_profiles`
- `cardio_week_plans`
- `cardio_week_reviews`

It also enables Row Level Security so each user can only manage rows where
`auth.uid() = user_id`.

## Environment Variables

Do not commit real `.env` files.

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
```

Fill:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Backend:

```bash
cd backend
cp .env.example .env
```

Fill:

```text
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Important:

- Frontend uses only the anon key.
- Backend can use the service role key for server-side inserts.
- Never put the service role key in frontend code.
- Never put the OpenAI API key in frontend code.

## Install Backend

```bash
cd "/Users/arnav/Desktop/personal-portfolio/hyrox ai/backend"
source venv/bin/activate
pip install -r requirements.txt
```

## Run Backend

```bash
cd "/Users/arnav/Desktop/personal-portfolio/hyrox ai/backend"
source venv/bin/activate
uvicorn main:app --reload
```

Backend health check:

```text
http://127.0.0.1:8000/
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

## Install Frontend

```bash
cd "/Users/arnav/Desktop/personal-portfolio/hyrox ai/frontend"
npm install
```

## Run Frontend

```bash
cd "/Users/arnav/Desktop/personal-portfolio/hyrox ai/frontend"
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Main API Endpoints

```text
GET  /
POST /generate-plan
GET  /plans/latest/{user_id}
POST /workout-progress
GET  /workout-progress/{user_id}/{workout_plan_id}
GET  /dashboard/{user_id}
POST /diet-suggestion
GET  /diet-suggestion/latest/{user_id}
POST /ai/personalize-plan
POST /ai/adjust-plan
POST /ai/adjust-diet
POST /ai/apply-plan-changes
POST /cardio/generate-week-plan
GET  /cardio/current-plan/{user_id}
POST /cardio/weekly-review
POST /cardio/generate-next-week-plan
POST /calculate-readiness-score
```

`POST /generate-plan` now accepts:

```json
{
  "user_id": "supabase-auth-user-id",
  "fitness_profile": {
    "age": 24,
    "gender": "male",
    "height": 175,
    "weight": 72,
    "body_type": "athletic",
    "training_experience": "beginner",
    "training_days_per_week": 4,
    "injury_history": "No major injuries"
  },
  "hyrox_assessment": [
    {
      "station_name": "1 km run",
      "level": "beginner",
      "current_value": "6:30 per km",
      "difficulty": "hard"
    }
  ],
  "goal": {
    "preparation_reason": "Preparing for my first HYROX race",
    "category": "Open",
    "target_time": "1:30:00",
    "preparation_weeks": 12,
    "main_weakness": "running",
    "goal_type": "finish"
  }
}
```

It returns:

```json
{
  "message": "Plan generated and saved successfully",
  "plan_id": "saved-plan-id",
  "plan": {
    "plan_type": "Beginner Open 12-week HYROX Plan"
  }
}
```

## Stage 7 Workout Tracking

The plan page now lets logged-in users track every workout day from the saved
HYROX plan.

For each workout, users can save:

- Completed status
- Time taken
- Energy level
- Difficulty level
- Notes

## Cardio Lab

Cardio Lab is an independent module for one-week cardio plans. It does not
reuse or modify the HYROX plan generator.

It supports:

- HYROX endurance
- Marathon preparation
- General cardiovascular health
- Zone 5 / VO2 max improvement
- Fat loss endurance
- Mixed endurance performance
- Running, cycling, swimming, or mixed training

The backend first creates a safe rule-based plan, then uses the backend-only
OpenAI API key to refine coaching notes when available. If `OPENAI_API_KEY` is
missing or the AI call fails, the app returns and saves the safe rule-based
fallback plan with `ai_status: "fallback_used"`.

Testing flow:

1. Run the Cardio Lab SQL in Supabase.
2. Start backend and frontend.
3. Log in.
4. Open `/cardio-lab`.
5. Generate Week 1.
6. Submit a weekly review.
7. Click `Generate Next Week Plan`.
8. Confirm Sunday remains rest/recovery and Zone 5 appears safely, not every day.

Progress is saved in the existing Supabase `workout_progress` table.

Example `POST /workout-progress` body:

```json
{
  "user_id": "supabase-auth-user-id",
  "workout_plan_id": "saved-workout-plan-id",
  "workout_id": "week-1-day-monday",
  "completed": true,
  "time_taken": "42 minutes",
  "energy_level": "high",
  "difficulty_level": "medium",
  "notes": "Felt strong on running but wall balls were hard"
}
```

The dashboard page now shows:

- Total workouts
- Completed workouts
- Completion percentage
- Consistency score
- Latest plan type
- Current training phase
- Weak areas
- Race readiness score
- Recent workout notes

## Stage 8 Diet Suggestion

The diet engine is rule-based. It uses body weight, goal type, HYROX category,
training days per week, and preparation weeks.

Calories:

- `cut` or fat-loss style goal: `weight * 25`
- `maintain`, `finish`, or general fitness: `weight * 30`
- `bulk`, `strength`, `compete`, or `Pro`: `weight * 36`

Protein:

- `weight * 1.5` to `weight * 2.0` grams per day

Example `POST /diet-suggestion` body:

```json
{
  "user_id": "supabase-auth-user-id",
  "weight": 75,
  "goal_type": "compete",
  "category": "Pro",
  "training_days_per_week": 5,
  "preparation_weeks": 12
}
```

It returns:

```json
{
  "message": "Diet suggestion generated successfully",
  "diet_id": "saved-diet-id",
  "diet": {
    "daily_calories": 2700,
    "protein_range": "112-150 g/day",
    "hydration": "3-4 liters/day. Add extra 500-1000 ml around intense training sessions.",
    "carb_strategy": "Higher carb guidance",
    "fat_strategy": "Healthy fat guidance",
    "pre_workout_meal": "Pre-workout meal guidance",
    "post_workout_meal": "Post-workout meal guidance",
    "general_tips": ["Simple repeatable nutrition tips"],
    "disclaimer": "This is general fitness nutrition guidance and not medical advice."
  }
}
```

The `/diet` page:

- Requires login
- Loads the latest saved fitness profile and goal when available
- Generates and saves a diet suggestion
- Shows calories, protein, hydration, carb strategy, fat strategy, meal timing,
  general tips, and disclaimer

## Stage 9 AI Coach

The AI Coach does not replace the rule-based plan generator. The rule-based
plan remains the safe base. AI adds coaching notes, plan adjustment suggestions,
and diet adjustment suggestions.

AI changes are not applied automatically. For plan adjustments:

1. AI creates a recommendation.
2. User reviews the recommendation.
3. User clicks `Apply Changes`.
4. Backend creates a new `workout_plans` version.
5. Old plan remains saved.

AI endpoints:

```text
POST /ai/personalize-plan
POST /ai/adjust-plan
POST /ai/adjust-diet
POST /ai/apply-plan-changes
```

Safety rules:

- AI must not diagnose injuries or medical conditions.
- If pain, injury, dizziness, chest pain, fainting, severe discomfort, or a
  medical condition is mentioned, AI should reduce intensity and recommend
  qualified medical or physio guidance.
- AI must not suggest extreme calorie cuts.
- AI must not suggest unsafe training volume jumps.
- AI must not remove all rest days.
- AI must not promise guaranteed HYROX results.

If OpenAI fails or `OPENAI_API_KEY` is missing, the backend returns:

```json
{
  "error": "AI coach is temporarily unavailable. Your rule-based plan is still safe to use."
}
```

## Test Full Flow

1. Run Supabase SQL from `supabase_schema.sql`.
2. Run Supabase SQL from `supabase_stage8_diet_schema.sql`.
3. Run Supabase SQL from `supabase_stage9_ai_schema.sql`.
4. Fill frontend and backend environment variables.
5. Add `OPENAI_API_KEY` to backend `.env`.
6. Start backend on `http://127.0.0.1:8000`.
7. Start frontend on `http://127.0.0.1:3000`.
8. Open `/signup`.
9. Create an account.
10. Go to `/form`.
11. Fill the HYROX form.
12. Submit the form.
13. Confirm `/plan` shows the latest saved plan.
14. Mark one workout as completed.
15. Add time taken, energy, difficulty, and notes.
16. Click Save Progress.
17. Refresh `/plan` and confirm the progress is still filled.
18. Open `/diet`.
19. Click Generate Diet Suggestion.
20. Refresh `/diet` and confirm the latest diet suggestion still appears.
21. Open `/ai-coach`.
22. Test plan explanation, plan adjustment, and diet adjustment.
23. Apply a plan adjustment and confirm `/plan` shows a new plan version.
24. Open Supabase Table Editor and confirm AI recommendation rows were saved.
25. Click Logout and confirm protected pages redirect to `/login`.

## Stage 9 Checklist

- Signup works
- Login works
- `/form`, `/plan`, `/dashboard`, `/diet`, and `/ai-coach` are protected
- Logged-in user can submit the form
- Plan is generated by FastAPI
- Fitness profile, assessment, goal, and plan are saved in Supabase
- `/plan` fetches the latest saved plan
- Workout progress can be saved from `/plan`
- Saved workout progress remains after refresh
- `/dashboard` shows completion percentage and readiness score
- `/diet` generates calorie, protein, hydration, carb, fat, and meal timing guidance
- Diet suggestion saves in Supabase
- `/diet` fetches the latest saved diet suggestion after refresh
- `/dashboard` shows the diet card
- AI Coach page opens after login
- Plan personalization works
- Plan adjustment works for hard plan, missed workouts, no sled equipment, and knee pain prompts
- Diet adjustment works for low energy, hunger during cut, and performance prompts
- AI recommendations save to Supabase
- Apply Changes creates a new plan version
- Old plan is not deleted
- Missing API key fallback is friendly
- OpenAI API key is never exposed in frontend
- Logout works
- RLS policies restrict users to their own rows
