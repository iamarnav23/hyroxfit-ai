-- Stage 8: Diet Suggestion Engine
-- Run this in the Supabase SQL Editor after the Stage 6 base schema.

create table if not exists public.diet_suggestions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  goal_type text,
  daily_calories int,
  protein_min numeric,
  protein_max numeric,
  hydration_advice text,
  carb_strategy text,
  fat_strategy text,
  pre_workout_meal text,
  post_workout_meal text,
  general_tips jsonb,
  disclaimer text,
  created_at timestamp with time zone default now()
);

alter table public.diet_suggestions enable row level security;

drop policy if exists "Users can select their own diet suggestions"
on public.diet_suggestions;

create policy "Users can select their own diet suggestions"
on public.diet_suggestions
for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert their own diet suggestions"
on public.diet_suggestions;

create policy "Users can insert their own diet suggestions"
on public.diet_suggestions
for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update their own diet suggestions"
on public.diet_suggestions;

create policy "Users can update their own diet suggestions"
on public.diet_suggestions
for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own diet suggestions"
on public.diet_suggestions;

create policy "Users can delete their own diet suggestions"
on public.diet_suggestions
for delete
using (auth.uid() = user_id);
