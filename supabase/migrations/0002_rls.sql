-- ════════════════════════════════════════════════════════════════════
-- Veedra · 0002 · row-level security
-- Every table: owner-only read/write. Service role bypasses for backend.
-- ════════════════════════════════════════════════════════════════════

alter table public.profiles      enable row level security;
alter table public.projects      enable row level security;
alter table public.scenes        enable row level security;
alter table public.assets        enable row level security;
alter table public.jobs          enable row level security;
alter table public.agent_events  enable row level security;

-- ─── profiles ────────────────────────────────────────────────────────
create policy "profiles: read own" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles: update own" on public.profiles
  for update using (auth.uid() = id);
create policy "profiles: insert own" on public.profiles
  for insert with check (auth.uid() = id);

-- ─── projects ────────────────────────────────────────────────────────
create policy "projects: owner all" on public.projects
  for all using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- ─── scenes (joined via project) ─────────────────────────────────────
create policy "scenes: via project" on public.scenes
  for all using (
    exists (select 1 from public.projects p
            where p.id = scenes.project_id and p.owner_id = auth.uid())
  );

-- ─── assets ──────────────────────────────────────────────────────────
create policy "assets: owner all" on public.assets
  for all using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- ─── jobs ────────────────────────────────────────────────────────────
create policy "jobs: owner read" on public.jobs
  for select using (auth.uid() = owner_id);
-- Inserts/updates go through the backend with the service role.

-- ─── agent_events (via job) ──────────────────────────────────────────
create policy "agent_events: via job" on public.agent_events
  for select using (
    exists (select 1 from public.jobs j
            where j.id = agent_events.job_id and j.owner_id = auth.uid())
  );

-- ─── auto-create profile on signup ───────────────────────────────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
