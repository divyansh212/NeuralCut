-- NeuralCut · 0002_rls.sql
-- Run SECOND. Row-level security makes "scoped to owner" enforced by the DB.
-- The backend uses the service key (which bypasses RLS) and ALSO filters by
-- user_id in every query — belt and suspenders.

alter table projects enable row level security;
alter table jobs enable row level security;

drop policy if exists "own_projects" on projects;
create policy "own_projects" on projects
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "own_jobs" on jobs;
create policy "own_jobs" on jobs
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
