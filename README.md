# Rox Zone
Rox Zone is a performance-focused web app built for athletes preparing for HYROX and endurance-based training.
It combines personalized training plans, cardio programming, workout tracking, diet guidance, and AI coaching into one clean fitness platform.


## What I Built
I built Rox Zone, a full-stack fitness and performance web app designed for HYROX race preparation and endurance training. The app allows users to sign up, enter their fitness profile, assess their HYROX station performance, choose a race goal, and generate a personalized training plan. It also includes workout tracking, a performance dashboard, a diet suggestion engine, an AI Coach for plan and diet improvements, and a separate Cardio Lab for adaptive endurance and Zone 5 training.

## How I Built It
I built the frontend using Next.js, React, and Tailwind CSS, with a dark, sporty, premium design that works on both desktop and mobile. The backend was built using FastAPI in Python, where the main training logic runs through rule-based engines for HYROX plans, diet suggestions, readiness scoring, and cardio plans. I used Supabase for user authentication and database storage, so each user can save their profile, goals, workout plans, progress, diet suggestions, cardio plans, and AI recommendations.

I also integrated the OpenAI API through the FastAPI backend to power the AI Coach. The AI does not replace the rule-based plan generator; instead, it adds safe coaching suggestions and plan or diet adjustments that the user can review before applying. The frontend is deployed on Vercel, the backend is deployed on Render, and Supabase handles the database and authentication.

## How Users Use Rox Zone
1. Sign Up / Log In
   Users create an account so their plans and progress can be saved.

2. Build Their HYROX Profile
   They enter fitness level, body details, training days, injury history, race goal, and HYROX station performance.

3. Generate A Personalized Plan
   Rox Zone creates a structured HYROX plan based on their goal, category, weak stations, timeline, and experience level.

4. Track Workouts
  Users mark workouts as completed and log time, energy, difficulty, and notes.

5. View Performance Dashboard
   The dashboard shows readiness score, consistency, weak areas, recovery, endurance, and progress trends.

6. Use Cardio Lab
   Users can generate weekly cardio plans for running, cycling, swimming, marathon prep, cardiovascular health, or Zone 5 improvement.

7. Get Diet Guidance
   The diet engine gives simple calorie, protein, hydration, carb, fat, and meal timing recommendations.

8. Ask AI Coach
   Users can ask for safer plan changes, diet adjustments, or coaching advice based on their progress.


### LINK FOR THE WEBSITE : https://hyroxfit-ai.vercel.app/ 

