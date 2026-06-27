-- Run this in the Supabase SQL Editor after creating your project.

create table if not exists profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  display_name text default '',
  created_at timestamptz default now()
);

create table if not exists gmail_tokens (
  user_id uuid references auth.users on delete cascade primary key,
  tokens jsonb not null,
  updated_at timestamptz default now()
);

create table if not exists subscriptions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  service_name text not null,
  amount numeric,
  currency text,
  frequency text default 'unknown',
  last_charge_date text,
  trial_end_date text,
  is_trial boolean default false,
  source_email_subject text,
  category text,
  updated_at timestamptz default now()
);

create table if not exists tos_analyses (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  flags jsonb not null default '[]',
  risk_summary text,
  source text,
  analyzed_at timestamptz default now()
);

create table if not exists category_cache (
  service_name_key text primary key,
  service_name text not null,
  category text not null,
  updated_at timestamptz default now()
);

create index if not exists idx_subscriptions_user_id on subscriptions(user_id);
create index if not exists idx_tos_analyses_user_id on tos_analyses(user_id);

alter table profiles enable row level security;
alter table gmail_tokens enable row level security;
alter table subscriptions enable row level security;
alter table tos_analyses enable row level security;
alter table category_cache enable row level security;

-- Backend uses the service role key and bypasses RLS.
-- These policies allow authenticated users to access their own data via the anon key if needed later.

create policy "Users can read own profile" on profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

create policy "Users can read own subscriptions" on subscriptions
  for select using (auth.uid() = user_id);

create policy "Users can read own tos analyses" on tos_analyses
  for select using (auth.uid() = user_id);
