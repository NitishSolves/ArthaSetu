-- ============================================================================
-- Reference data: shared/public tables that are not scoped to a single user.
-- ============================================================================
-- government_schemes existed on the old project but its CREATE TABLE was
-- never captured in any tracked SQL file -- this recreates it from the
-- shape frontend/src/services/database.ts and docs/DATABASE_TABLES_
-- DOCUMENTATION.md expect. Writes happen via the service-role key only
-- (see 20260811000400_rls_policies.sql); there is no admin UI for this yet.

create table if not exists government_schemes (
    scheme_id uuid primary key default gen_random_uuid(),
    scheme_name varchar(255) not null,
    scheme_code varchar(50),
    description text,
    eligibility_criteria jsonb default '{}',
    benefits text,
    application_process text,
    required_documents jsonb default '[]',
    scheme_type varchar(50),
    max_benefit_amount decimal(12,2),
    interest_rate decimal(5,2),
    government_level varchar(20),
    state_applicable varchar(100),
    valid_from date,
    valid_until date,
    official_url text,
    contact_info jsonb default '{}',
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_government_schemes_type on government_schemes(scheme_type);
create index if not exists idx_government_schemes_active on government_schemes(is_active);

do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'fk_user_scheme_applications_scheme'
    ) then
        alter table user_scheme_applications
            add constraint fk_user_scheme_applications_scheme
            foreign key (scheme_id) references government_schemes(scheme_id)
            on delete set null;
    end if;
end $$;
