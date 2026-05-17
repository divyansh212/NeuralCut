-- ════════════════════════════════════════════════════════════════════
-- Veedra · 0003 · storage buckets
-- For hosted Supabase, run via the Supabase CLI. The local dockerized
-- postgres does not include storage; backend falls back to local disk.
-- ════════════════════════════════════════════════════════════════════

-- Only run if the storage schema exists (hosted Supabase)
do $$
begin
  if exists (select 1 from information_schema.schemata where schema_name = 'storage') then
    -- assets: per-scene images + per-scene voice clips
    insert into storage.buckets (id, name, public)
    values ('veedra-assets', 'veedra-assets', false)
    on conflict (id) do nothing;

    -- renders: final composed videos + thumbnails
    insert into storage.buckets (id, name, public)
    values ('veedra-renders', 'veedra-renders', true)
    on conflict (id) do nothing;

    -- read own assets
    create policy "assets: read own"
      on storage.objects for select
      using (bucket_id = 'veedra-assets' and owner = auth.uid());

    -- write own assets
    create policy "assets: write own"
      on storage.objects for insert
      with check (bucket_id = 'veedra-assets' and owner = auth.uid());

    -- public read on renders
    create policy "renders: public read"
      on storage.objects for select
      using (bucket_id = 'veedra-renders');
  end if;
end $$;
