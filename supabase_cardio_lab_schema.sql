-- Cardio Lab tables for HYROXFit AI
-- Run this in the Supabase SQL Editor after the main Stage 6 schema.

create table if not exists public.cardio_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  cardio_goal text,
  preferred_training_mode text,
  experience_level text,
  training_days_per_week int,
  current_1km_time text,
  current_5km_time text,
  current_long_run_distance text,
  resting_heart_rate int,
  max_heart_rate int,
  available_session_duration text,
  injury_or_limitation text,
  created_at timestamp with time zone default now()
);

create table if not exists public.cardio_week_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  cardio_profile_id uuid references public.cardio_profiles(id) on delete cascade,
  week_number int,
  plan_json jsonb,
  ai_status text,
  created_at timestamp with time zone default now()
);

create table if not exists public.cardio_week_reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  cardio_plan_id uuid references public.cardio_week_plans(id) on delete cascade,
  week_number int,
  workouts_completed int,
  total_workouts int,
  average_energy_level text,
  average_difficulty text,
  hardest_session text,
  updated_1km_time text,
  updated_5km_time text,
  notes text,
  created_at timestamp with time zone default now()
);

alter table public.cardio_profiles enable row level security;
alter table public.cardio_week_plans enable row level security;
alter table public.cardio_week_reviews enable row level security;

drop policy if exists "Users can select own cardio profiles" on public.cardio_profiles;
drop policy if exists "Users can insert own cardio profiles" on public.cardio_profiles;
drop policy if exists "Users can update own cardio profiles" on public.cardio_profiles;
drop policy if exists "Users can delete own cardio profiles" on public.cardio_profiles;

create policy "Users can select own cardio profiles"
on public.cardio_profiles for select
using (auth.uid() = user_id);

create policy "Users can insert own cardio profiles"
on public.cardio_profiles for insert
with check (auth.uid() = user_id);

create policy "Users can update own cardio profiles"
on public.cardio_profiles for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own cardio profiles"
on public.cardio_profiles for delete
using (auth.uid() = user_id);

drop policy if exists "Users can select own cardio plans" on public.cardio_week_plans;
drop policy if exists "Users can insert own cardio plans" on public.cardio_week_plans;
drop policy if exists "Users can update own cardio plans" on public.cardio_week_plans;
drop policy if exists "Users can delete own cardio plans" on public.cardio_week_plans;

create policy "Users can select own cardio plans"
on public.cardio_week_plans for select
using (auth.uid() = user_id);

create policy "Users can insert own cardio plans"
on public.cardio_week_plans for insert
with check (auth.uid() = user_id);

create policy "Users can update own cardio plans"
on public.cardio_week_plans for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own cardio plans"
on public.cardio_week_plans for delete
using (auth.uid() = user_id);

drop policy if exists "Users can select own cardio reviews" on public.cardio_week_reviews;
drop policy if exists "Users can insert own cardio reviews" on public.cardio_week_reviews;
drop policy if exists "Users can update own cardio reviews" on public.cardio_week_reviews;
drop policy if exists "Users can delete own cardio reviews" on public.cardio_week_reviews;

create policy "Users can select own cardio reviews"
on public.cardio_week_reviews for select
using (auth.uid() = user_id);

create policy "Users can insert own cardio reviews"
on public.cardio_week_reviews for insert
with check (auth.uid() = user_id);

create policy "Users can update own cardio reviews"
on public.cardio_week_reviews for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own cardio reviews"
on public.cardio_week_reviews for delete
using (auth.uid() = user_id);
