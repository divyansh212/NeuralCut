-- ════════════════════════════════════════════════════════════════════
-- Veedra schema · 0001 · core tables
-- ════════════════════════════════════════════════════════════════════

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- ─── profiles ────────────────────────────────────────────────────────
-- Mirrors auth.users with public, user-editable fields.
create table if not exists public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  email        text unique not null,
  display_name text,
  avatar_url   text,
  plan         text not null default 'free',     -- free | pro | team
  credits      int  not null default 50,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- ─── projects ────────────────────────────────────────────────────────
-- Top-level container. One "video" the user is working on.
create table if not exists public.projects (
  id            uuid primary key default uuid_generate_v4(),
  owner_id      uuid not null references public.profiles(id) on delete cascade,
  title         text not null default 'Untitled',
  prompt        text,                              -- original user prompt
  style         jsonb not null default '{}'::jsonb, -- {aspect, tone, voice_id, ...}
  status        text not null default 'draft',    -- draft | rendering | ready | failed
  thumbnail_url text,
  final_url     text,
  duration_s    numeric,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index on public.projects (owner_id, created_at desc);

-- ─── scenes ──────────────────────────────────────────────────────────
-- A project decomposes into N ordered scenes. Each scene has narration
-- and one visual (image or short video clip).
create table if not exists public.scenes (
  id            uuid primary key default uuid_generate_v4(),
  project_id    uuid not null references public.projects(id) on delete cascade,
  idx           int  not null,                    -- order
  narration     text,
  visual_prompt text,
  visual_url    text,                             -- in assets bucket
  voice_url     text,                             -- in assets bucket
  duration_s    numeric default 4,
  created_at    timestamptz not null default now()
);
create unique index on public.scenes (project_id, idx);

-- ─── assets ──────────────────────────────────────────────────────────
-- Uploaded source media (for the video-understanding flow) and any
-- intermediate artifacts the agent generates.
create table if not exists public.assets (
  id          uuid primary key default uuid_generate_v4(),
  owner_id    uuid not null references public.profiles(id) on delete cascade,
  project_id  uuid references public.projects(id) on delete cascade,
  kind        text not null,                      -- image | audio | video | script
  storage_path text not null,                     -- bucket/key
  mime_type   text,
  size_bytes  bigint,
  meta        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);
create index on public.assets (project_id);
create index on public.assets (owner_id, created_at desc);

-- ─── jobs ────────────────────────────────────────────────────────────
-- Long-running async work tracked for the UI (renders, agent runs,
-- understanding analyses).
create table if not exists public.jobs (
  id          uuid primary key default uuid_generate_v4(),
  owner_id    uuid not null references public.profiles(id) on delete cascade,
  project_id  uuid references public.projects(id) on delete cascade,
  kind        text not null,                      -- agent_run | render | analyze
  status      text not null default 'queued',    -- queued | running | done | failed
  progress    int  not null default 0,            -- 0..100
  payload     jsonb not null default '{}'::jsonb,
  result      jsonb,
  error       text,
  celery_id   text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index on public.jobs (owner_id, created_at desc);
create index on public.jobs (project_id, created_at desc);

-- ─── agent_events ────────────────────────────────────────────────────
-- Per-step trace of an agent run. The frontend streams these for the
-- "Director thinking" UI.
create table if not exists public.agent_events (
  id         uuid primary key default uuid_generate_v4(),
  job_id     uuid not null references public.jobs(id) on delete cascade,
  step       text not null,           -- script | visual | voice | compose
  role       text not null,           -- agent | tool | system
  content    jsonb not null,
  created_at timestamptz not null default now()
);
create index on public.agent_events (job_id, created_at);

-- ─── updated_at trigger ──────────────────────────────────────────────
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

create trigger trg_projects_updated before update on public.projects
  for each row execute function public.touch_updated_at();
create trigger trg_profiles_updated before update on public.profiles
  for each row execute function public.touch_updated_at();
create trigger trg_jobs_updated     before update on public.jobs
  for each row execute function public.touch_updated_at();
