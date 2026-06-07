-- NeuralCut · 0003_storage.sql
-- Run THIRD. Creates the public 'renders' bucket and its policies.
-- Renders are stored under renders/{user_id}/{job_id}.mp4 so the owner-write
-- policy works via the folder prefix.

insert into storage.buckets (id, name, public)
values ('renders', 'renders', true)
on conflict (id) do nothing;

drop policy if exists "renders_owner_write" on storage.objects;
create policy "renders_owner_write" on storage.objects
  for insert with check (
    bucket_id = 'renders' and auth.uid()::text = (storage.foldername(name))[1]
  );

drop policy if exists "renders_public_read" on storage.objects;
create policy "renders_public_read" on storage.objects
  for select using (bucket_id = 'renders');
