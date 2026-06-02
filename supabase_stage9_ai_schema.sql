-- Stage 9: AI Personalization Layer + AI Coach
-- Run this in the Supabase SQL Editor after Stage 6 and Stage 8 SQL.

alter table public.workout_plans
add column if not exists parent_plan_id uuid references public.workout_plans(id) on delete set null;

alter table public.workout_plans
add column if not exists version_number int default 1;

alter table public.workout_plans
add column if not exists source text default 'rule_based';

alter table public.workout_plans
add column if not exists ai_recommendation_id uuid;

create table if not exists public.ai_recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  plan_id uuid references public.workout_plans(id) on delete cascade,
  recommendation_type text,
  user_message text,
  ai_response jsonb,
  status text default 'pending',
  created_at timestamp with time zone default now()
);

alter table public.workout_plans
drop constraint if exists workout_plans_ai_recommendation_id_fkey;

alter table public.workout_plans
add constraint workout_plans_ai_recommendation_id_fkey
foreign key (ai_recommendation_id)
references public.ai_recommendations(id)
on delete set null;

alter table public.ai_recommendations enable row level security;

drop policy if exists "Users can manage own AI recommendations"
on public.ai_recommendations;

create policy "Users can manage own AI recommendations"
on public.ai_recommendations
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
