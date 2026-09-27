-- ============================================================================
-- Row Level Security: every user can only read/write their own rows.
-- ============================================================================
-- Postgres has no "CREATE POLICY IF NOT EXISTS", so each policy is dropped
-- and recreated -- safe to re-run this file any number of times.

-- profiles is keyed on user_id as its own primary key (not a separate id),
-- so its policy compares auth.uid() to user_id directly, same as every
-- other table.
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

select apply_owner_rls('profiles');
select apply_owner_rls('user_profiles');
select apply_owner_rls('bank_accounts');
select apply_owner_rls('transactions');
select apply_owner_rls('budgets');
select apply_owner_rls('recommendations');
select apply_owner_rls('risk_assessments');
select apply_owner_rls('tax_records');
select apply_owner_rls('user_scheme_applications');
select apply_owner_rls('executed_actions');
select apply_owner_rls('income_forecasts');
select apply_owner_rls('financial_health');
select apply_owner_rls('savings_goals');
select apply_owner_rls('investment_recommendations');
select apply_owner_rls('bills');
select apply_owner_rls('financial_goals');
select apply_owner_rls('goal_milestones');
select apply_owner_rls('agent_logs');

drop function apply_owner_rls(text);

-- government_schemes: public reference data, readable by anyone
-- (including anonymous callers), writable only by the service-role key
-- (which bypasses RLS entirely) -- so no insert/update/delete policy is
-- defined for the anon/authenticated roles.
alter table government_schemes enable row level security;
drop policy if exists "public_read" on government_schemes;
create policy "public_read" on government_schemes for select using (true);
