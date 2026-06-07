-- NeuralCut · 0001_init.sql
-- Run FIRST in the Supabase SQL Editor (Database -> SQL Editor -> New query).
-- The `jobs` row is the contract shared by API, worker, and frontend.

create extension if not exists "uuid-ossp";

create table if not exists projects (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null default 'Untitled',
  created_at timestamptz not null default now()
);

create table if not exists jobs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  prompt text not null,
  status text not null default 'queued',   -- queued | running | done | failed
  output_url text,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists jobs_user_idx on jobs(user_id);
create index if not exists jobs_created_idx on jobs(created_at desc);
