-- ============================================================================
-- Domain tables: every table the frontend (frontend/src/services/database.ts)
-- or backend (backend/autogen_runtime.py) actually reads/writes.
-- ============================================================================
-- Tables documented in docs/DATABASE_TABLES_DOCUMENTATION.md but never
-- queried anywhere in the code (transactions_backup, income_patterns,
-- action_outcomes, outcomes, notifications, context_events, user_schemes,
-- human_escalations) are intentionally NOT created here -- they were dead
-- schema. Add them back in a future migration if a real feature needs them.

create table if not exists user_profiles (
    profile_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    monthly_income_min decimal(12,2) default 0,
    monthly_income_max decimal(12,2) default 0,
    monthly_expenses_avg decimal(12,2) default 0,
    emergency_fund_target decimal(12,2) default 0,
    current_emergency_fund decimal(12,2) default 0,
    risk_tolerance varchar(20) default 'moderate',
    financial_goals jsonb default '{}',
    income_sources jsonb default '{}',
    debt_obligations jsonb default '{}',
    dependents integer default 0,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_user_profiles_user_id on user_profiles(user_id);

create table if not exists bank_accounts (
    account_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    account_name varchar(255) not null,
    provider varchar(100) default '',
    account_number varchar(50) default '',
    current_balance decimal(12,2) default 0,
    currency varchar(10) default 'INR',
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_bank_accounts_user_id on bank_accounts(user_id);

create table if not exists transactions (
    transaction_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    transaction_date date not null default current_date,
    transaction_time time default current_time,
    amount decimal(12,2) not null default 0,
    transaction_type varchar(10) default 'expense' check (transaction_type in ('income', 'expense')),
    category varchar(50) default 'Other',
    subcategory varchar(50) default '',
    description text default '',
    payment_method varchar(50) default 'cash',
    merchant_name varchar(100) default '',
    location varchar(100) default '',
    source varchar(50) default '',
    account_id uuid references bank_accounts(account_id),
    input_method varchar(20) default 'manual',
    verified boolean default true,
    confidence_score decimal(3,2) default 1.0,
    is_recurring boolean default false,
    recurring_frequency varchar(20),
    tags text[] default '{}',
    balance_after decimal(12,2),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_transactions_user_id on transactions(user_id);
create index if not exists idx_transactions_date on transactions(transaction_date);

create table if not exists budgets (
    budget_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    budget_type varchar(20) default 'normal',
    valid_from date default current_date,
    valid_until date default (current_date + interval '1 month'),
    total_income_expected decimal(12,2) default 0,
    fixed_costs jsonb default '{}',
    variable_costs jsonb default '{}',
    savings_target decimal(12,2) default 0,
    discretionary_budget decimal(12,2) default 0,
    category_limits jsonb default '{}',
    confidence_score decimal(3,2) default 0.8,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_budgets_user_id on budgets(user_id);

create table if not exists recommendations (
    recommendation_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    recommendation_type varchar(50) default 'general',
    priority varchar(10) default 'medium',
    title varchar(255) not null,
    description text default '',
    reasoning text default '',
    action_items jsonb default '[]',
    target_amount decimal(12,2),
    target_date date,
    confidence_score decimal(3,2) default 0.8,
    expected_outcome text,
    success_probability decimal(3,2),
    agent_source varchar(50) default '',
    context_data jsonb default '{}',
    status varchar(20) default 'pending',
    user_feedback text,
    actual_outcome jsonb,
    delivered_at timestamptz,
    actioned_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_recommendations_user_id on recommendations(user_id);

create table if not exists risk_assessments (
    risk_assessment_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    overall_risk_level varchar(20) default 'medium',
    risk_score decimal(3,1) default 0,
    risk_factors jsonb default '[]',
    debt_to_income_ratio decimal(5,2),
    income_drop_percentage decimal(5,2),
    expense_spike_factor decimal(5,2),
    emergency_fund_coverage decimal(5,2),
    transaction_anomalies jsonb default '[]',
    escalation_needed boolean default false,
    escalation_priority varchar(20),
    escalation_reason text,
    recommended_actions jsonb default '[]',
    ai_risk_analysis text,
    assessment_date date default current_date,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_risk_assessments_user_id on risk_assessments(user_id);

create table if not exists tax_records (
    tax_record_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    financial_year varchar(10) not null,
    gross_income decimal(12,2) default 0,
    income_by_source jsonb default '{}',
    total_deductions decimal(12,2) default 0,
    deduction_details jsonb default '{}',
    taxable_income decimal(12,2) default 0,
    tax_liability decimal(12,2) default 0,
    tax_paid decimal(12,2) default 0,
    refund_amount decimal(12,2) default 0,
    itr_form_type varchar(20),
    filing_status varchar(20) default 'not_filed',
    filing_date date,
    acknowledgement_number varchar(50),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_tax_records_user_id on tax_records(user_id);

create table if not exists user_scheme_applications (
    id bigserial primary key,
    user_id uuid references profiles(user_id) on delete cascade,
    scheme_id uuid,
    application_date date default current_date,
    application_status varchar(30) default 'submitted',
    benefit_received decimal(12,2),
    benefit_currency varchar(10) default 'INR',
    documents_submitted jsonb,
    documents_verified jsonb,
    approval_date date,
    disbursement_date date,
    application_notes text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_user_scheme_applications_user_id on user_scheme_applications(user_id);

create table if not exists executed_actions (
    action_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    action_type varchar(50) not null,
    action_description text default '',
    status varchar(20) default 'pending',
    amount decimal(12,2) default 0,
    target_account varchar(100),
    target_entity varchar(100),
    user_approved boolean default false,
    approval_date timestamptz,
    requires_2fa boolean default false,
    security_verification_id varchar(100),
    execution_date timestamptz,
    transaction_id uuid references transactions(transaction_id),
    schedule varchar(20) default 'once',
    next_execution date,
    recurrence_count integer default 0,
    is_reversible boolean default true,
    reversal_requested boolean default false,
    reversal_date timestamptz,
    audit_trail jsonb default '[]',
    error_message text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_executed_actions_user_id on executed_actions(user_id);

create table if not exists income_forecasts (
    forecast_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    forecast_date date default current_date,
    forecast_start_date date,
    forecast_end_date date,
    historical_days integer,
    historical_total_income decimal(12,2),
    historical_avg_daily decimal(12,2),
    historical_std_dev decimal(12,2),
    volatility_index decimal(5,2),
    pessimistic_scenario jsonb default '{}',
    realistic_scenario jsonb default '{}',
    optimistic_scenario jsonb default '{}',
    weighted_forecast decimal(12,2),
    forecast_range_min decimal(12,2),
    forecast_range_max decimal(12,2),
    weekday_breakdown jsonb default '{}',
    recent_trend varchar(20),
    forecast_confidence decimal(3,2),
    ai_reasoning text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_income_forecasts_user_id on income_forecasts(user_id);

create table if not exists financial_health (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    health_category varchar(20),
    health_score decimal(3,1),
    assessment_date date default current_date,
    summary text,
    details jsonb default '{}',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_financial_health_user_id on financial_health(user_id);

create table if not exists savings_goals (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    goal_type text not null default 'savings',
    goal_name text not null,
    target_amount decimal(12,2) not null default 0,
    current_amount decimal(12,2) default 0,
    monthly_contribution decimal(12,2) default 0,
    priority text default 'medium' check (priority in ('high', 'medium', 'low')),
    status text default 'not_started' check (status in ('not_started', 'in_progress', 'completed', 'paused')),
    reasoning text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_savings_goals_user_id on savings_goals(user_id);
create index if not exists idx_savings_goals_status on savings_goals(status);

create table if not exists investment_recommendations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    investment_type text not null,
    provider text,
    recommended_amount decimal(12,2) default 0,
    frequency text default 'monthly',
    expected_return decimal(5,2) default 0,
    risk_level text default 'low' check (risk_level in ('low', 'moderate', 'high')),
    min_lock_in_months integer default 0,
    reasoning text,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_investment_recommendations_user_id on investment_recommendations(user_id);
create index if not exists idx_investment_recommendations_risk on investment_recommendations(risk_level);

create table if not exists bills (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    bill_name text not null,
    bill_type text default 'utility' check (bill_type in ('rent', 'emi', 'utility', 'telecom', 'insurance', 'subscription', 'tax', 'other')),
    amount decimal(12,2) not null default 0,
    due_date date,
    frequency text default 'monthly' check (frequency in ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'one_time')),
    priority text default 'medium' check (priority in ('critical', 'high', 'medium', 'low')),
    auto_pay_recommended boolean default false,
    auto_pay_enabled boolean default false,
    payment_method text default 'upi',
    late_fee decimal(10,2) default 0,
    grace_period_days integer default 0,
    remaining_emis integer,
    status text default 'pending' check (status in ('pending', 'paid', 'overdue', 'scheduled', 'cancelled')),
    last_paid_date date,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_bills_user_id on bills(user_id);
create index if not exists idx_bills_due_date on bills(due_date);
create index if not exists idx_bills_status on bills(status);

create table if not exists bill_payment_schedule (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    bill_id uuid references bills(id) on delete cascade,
    pay_date date not null,
    amount decimal(12,2) not null,
    income_source text,
    confidence decimal(3,2) default 0.5,
    status text default 'scheduled' check (status in ('scheduled', 'paid', 'missed', 'rescheduled')),
    created_at timestamptz default now()
);
create index if not exists idx_bill_payment_schedule_user_id on bill_payment_schedule(user_id);
create index if not exists idx_bill_payment_schedule_pay_date on bill_payment_schedule(pay_date);

create table if not exists financial_goals (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    goal_name text not null,
    goal_type text default 'savings' check (goal_type in ('emergency_fund', 'asset_purchase', 'education', 'healthcare', 'retirement', 'lifestyle', 'business', 'debt_repayment', 'savings', 'other')),
    description text,
    target_amount decimal(12,2) not null default 0,
    current_amount decimal(12,2) default 0,
    target_date date,
    priority integer default 1 check (priority >= 1 and priority <= 5),
    status text default 'not_started' check (status in ('not_started', 'in_progress', 'completed', 'paused')),
    monthly_target decimal(12,2) default 0,
    progress_percentage decimal(5,2) default 0,
    explanation jsonb default '{}',
    milestones jsonb default '[]',
    action_steps jsonb default '[]',
    potential_obstacles jsonb default '[]',
    contingency_plan text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_financial_goals_user_id on financial_goals(user_id);
create index if not exists idx_financial_goals_status on financial_goals(status);
create index if not exists idx_financial_goals_priority on financial_goals(priority);

create table if not exists goal_milestones (
    id uuid primary key default gen_random_uuid(),
    goal_id uuid references financial_goals(id) on delete cascade,
    user_id uuid references profiles(user_id) on delete cascade,
    milestone_name text not null,
    target_amount decimal(12,2) default 0,
    target_date date,
    status text default 'not_started' check (status in ('not_started', 'in_progress', 'completed')),
    reward text,
    completed_at timestamptz,
    created_at timestamptz default now()
);
create index if not exists idx_goal_milestones_goal_id on goal_milestones(goal_id);

-- Internal agent execution logs, read by backend/main.py's
-- /api/agent-logs/{user_id} via the service-role key (not directly by the
-- frontend). No public UI today.
create table if not exists agent_logs (
    log_id uuid primary key default gen_random_uuid(),
    user_id uuid references profiles(user_id) on delete cascade,
    agent_name varchar(50),
    execution_timestamp timestamptz default now(),
    input_data jsonb default '{}',
    output_data jsonb default '{}',
    confidence_score decimal(3,2),
    execution_time_ms integer,
    success boolean default true,
    error_message text,
    model_version varchar(50),
    created_at timestamptz default now()
);
create index if not exists idx_agent_logs_user_id on agent_logs(user_id);
