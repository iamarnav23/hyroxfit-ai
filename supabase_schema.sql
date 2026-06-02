create extension if not exists "pgcrypto";

create table if not exists public.fitness_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  age int,
  gender text,
  height numeric,
  weight numeric,
  body_type text,
  training_experience text,
  training_days_per_week int,
  injury_history text,
  created_at timestamp with time zone default now()
);

create table if not exists public.hyrox_assessments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  station_name text,
  level text,
  current_value text,
  difficulty text,
  created_at timestamp with time zone default now()
);

create table if not exists public.goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  preparation_reason text,
  category text,
  target_time text,
  preparation_weeks int,
  main_weakness text,
  goal_type text,
  created_at timestamp with time zone default now()
);

create table if not exists public.workout_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  plan_type text,
  summary text,
  training_phase text,
  plan_json jsonb,
  created_at timestamp with time zone default now()
);

create table if not exists public.workout_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  workout_plan_id uuid references public.workout_plans(id) on delete cascade,
  workout_id text,
  completed boolean default false,
  time_taken text,
  energy_level text,
  difficulty_level text,
  notes text,
  created_at timestamp with time zone default now()
);

create table if not exists public.race_readiness_scores (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  running_score int,
  strength_score int,
  hyrox_skill_score int,
  consistency_score int,
  recovery_diet_score int,
  total_score int,
  status text,
  created_at timestamp with time zone default now()
);

alter table public.fitness_profiles enable row level security;
alter table public.hyrox_assessments enable row level security;
alter table public.goals enable row level security;
alter table public.workout_plans enable row level security;
alter table public.workout_progress enable row level security;
alter table public.race_readiness_scores enable row level security;

drop policy if exists "Users can manage own fitness profiles" on public.fitness_profiles;
create policy "Users can manage own fitness profiles"
on public.fitness_profiles
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage own hyrox assessments" on public.hyrox_assessments;
create policy "Users can manage own hyrox assessments"
on public.hyrox_assessments
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage own goals" on public.goals;
create policy "Users can manage own goals"
on public.goals
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage own workout plans" on public.workout_plans;
create policy "Users can manage own workout plans"
on public.workout_plans
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage own workout progress" on public.workout_progress;
create policy "Users can manage own workout progress"
on public.workout_progress
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can manage own race readiness scores" on public.race_readiness_scores;
create policy "Users can manage own race readiness scores"
on public.race_readiness_scores
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
