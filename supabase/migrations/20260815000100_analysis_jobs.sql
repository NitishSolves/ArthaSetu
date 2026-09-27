-- ============================================================================
-- analysis_jobs: durable replacement for backend/main.py's old in-memory
-- analysis_status dict. One row per user, upserted on each /api/analyze
-- trigger, so job status survives a backend process restart instead of
-- being lost (previously /api/status/{user_id} would 404 forever after a
-- restart even though the agents had already written real partial results).
-- ============================================================================

create table if not exists analysis_jobs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    status text default 'pending' check (status in ('pending', 'in_progress', 'completed', 'failed')),
    agents_completed integer default 0,
    total_agents integer default 9,
    started_at timestamptz default now(),
    updated_at timestamptz default now(),
    error_message text
);
create unique index if not exists idx_analysis_jobs_user_id on analysis_jobs(user_id);

-- Same owner-only RLS pattern as every other table (see
-- 20260811000400_rls_policies.sql) -- that migration's apply_owner_rls
-- helper function was dropped after use, so it's recreated + dropped again
-- here rather than left permanently in the schema.
create or replace function apply_owner_rls(target_table text) returns void
language plpgsql
as $$
begin
    execute format('alter table %I enable row level security', target_table);

    execute format('drop policy if exists "select_own" on %I', target_table);
    execute format(
        'create policy "select_own" on %I for select using (auth.uid() = user_id)',
        target_table
    );

    execute format('drop policy if exists "insert_own" on %I', target_table);
    execute format(
        'create policy "insert_own" on %I for insert with check (auth.uid() = user_id)',
        target_table
    );

    execute format('drop policy if exists "update_own" on %I', target_table);
    execute format(
        'create policy "update_own" on %I for update using (auth.uid() = user_id) with check (auth.uid() = user_id)',
        target_table
    );

    execute format('drop policy if exists "delete_own" on %I', target_table);
    execute format(
        'create policy "delete_own" on %I for delete using (auth.uid() = user_id)',
        target_table
    );
end;
$$;

select apply_owner_rls('analysis_jobs');

drop function apply_owner_rls(text);
