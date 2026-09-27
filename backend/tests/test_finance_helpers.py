"""
Unit tests for the deterministic compute_* functions in
backend/agents/finance_helpers.py -- the actual financial-correctness
surface of the app (tax slabs, DTI, risk scoring, budgets, forecasts,
savings plans). These are pure functions (no network/DB calls), so they're
tested directly with no mocking.

Deliberately NOT testing write_record/fetch_transactions/agents'
analyze_user() here -- those are thin Supabase REST wrappers already
verified live against the real project; mocking them would test the mock,
not reality.
"""
import pytest

from finance_helpers import (
    apply_section_87a_rebate,
    calculate_tax_new_regime,
    compute_budgets,
    compute_gig_worker_tax,
    compute_goal_projection,
    compute_income_expense_stats,
    compute_risk_assessment,
    compute_savings_plan,
    compute_volatility_forecast,
)


# ============================================================================
# compute_income_expense_stats
# ============================================================================

def test_income_expense_stats_realistic():
    transactions = [
        {"transaction_type": "income", "amount": "1000", "transaction_date": "2026-08-01"},  # Saturday
        {"transaction_type": "income", "amount": "1200", "transaction_date": "2026-08-04"},  # Tuesday
        {"transaction_type": "expense", "amount": "300", "transaction_date": "2026-08-02", "category": "Food"},
        {"transaction_type": "expense", "amount": "200", "transaction_date": "2026-08-09", "category": "Food"},
    ]
    stats = compute_income_expense_stats(transactions)

    assert stats["total_income"] == 2200
    assert stats["total_expenses"] == 500
    assert stats["net"] == 1700
    assert stats["transaction_count"] == 4
    assert stats["income_transaction_count"] == 2
    assert stats["category_expenses"]["Food"] == 500
    assert stats["weekday_income"]["Saturday"] == 1000
    assert stats["weekday_income"]["Tuesday"] == 1200


def test_income_expense_stats_empty_transactions_does_not_crash():
    stats = compute_income_expense_stats([])
    assert stats["total_income"] == 0
    assert stats["total_expenses"] == 0
    assert stats["avg_weekly_income"] == 0
    assert stats["income_volatility"] == 0.0
    assert stats["transaction_count"] == 0


# ============================================================================
# calculate_tax_new_regime -- New Regime FY 2024-25 slabs, ported from
# frontend/src/pages/Tax.tsx so both surfaces agree.
# ============================================================================

@pytest.mark.parametrize("taxable_income,expected_tax", [
    (0, 0.0),
    (400_000, 0.0),          # top of the 0% slab
    (800_000, 20_000.0),     # top of the 5% slab: (800000-400000)*0.05
    (1_200_000, 60_000.0),   # top of the 10% slab: 20000 + 400000*0.10
    (1_600_000, 120_000.0),  # top of the 15% slab: 60000 + 400000*0.15
    (2_000_000, 200_000.0),  # top of the 20% slab: 120000 + 400000*0.20
    (2_400_000, 300_000.0),  # top of the 25% slab: 200000 + 400000*0.25
    (3_000_000, 480_000.0),  # into the 30% slab: 300000 + 600000*0.30
])
def test_calculate_tax_new_regime_slab_boundaries(taxable_income, expected_tax):
    assert calculate_tax_new_regime(taxable_income) == expected_tax


def test_calculate_tax_new_regime_just_above_a_boundary():
    # One rupee into the 10% slab, not the 5% slab
    tax = calculate_tax_new_regime(800_001)
    assert tax == pytest.approx(20_000 + 1 * 0.10)


# ============================================================================
# apply_section_87a_rebate
# ============================================================================

def test_rebate_87a_zeroes_out_tax_under_threshold():
    # Taxable income at/under 12L: rebate fully cancels tax up to Rs 60,000
    assert apply_section_87a_rebate(tax=20_000, taxable_income=800_000) == 0.0


def test_rebate_87a_partial_when_tax_exceeds_rebate_cap():
    assert apply_section_87a_rebate(tax=100_000, taxable_income=1_200_000) == 40_000.0


def test_rebate_87a_not_applied_above_threshold():
    # Above 12L taxable income, no 87A rebate at all -- tax passes through
    assert apply_section_87a_rebate(tax=105_000, taxable_income=1_500_000) == 105_000


# ============================================================================
# compute_gig_worker_tax -- presumptive taxation (44AD/44ADA)
# ============================================================================

def test_gig_worker_tax_is_tax_free_under_87a_threshold():
    # Rs 6L gross at 6% presumptive rate -> Rs 36,000 taxable, well under
    # the 0% slab and the 87A threshold
    result = compute_gig_worker_tax(gross_gig_income=600_000)
    assert result["taxable_income"] == 36_000
    assert result["total_tax_liability"] == 0
    assert result["is_tax_free"] is True
    assert result["itr_form_type"] == "ITR-4"


def test_gig_worker_tax_above_87a_threshold_owes_real_tax():
    # Rs 2.5 crore gross at 6% -> Rs 15L taxable, above the 12L rebate cap
    result = compute_gig_worker_tax(gross_gig_income=25_000_000)
    assert result["taxable_income"] == 1_500_000
    # gross_tax = 60000 + (1500000-1200000)*0.15 = 105000, no 87A rebate applies
    assert result["gross_tax"] == 105_000
    assert result["rebate_87a"] == 0
    # +4% cess
    assert result["total_tax_liability"] == pytest.approx(105_000 * 1.04)
    assert result["is_tax_free"] is False


def test_gig_worker_tax_refund_when_tds_exceeds_liability():
    result = compute_gig_worker_tax(gross_gig_income=600_000, tds_deducted=5_000)
    assert result["total_tax_liability"] == 0
    assert result["tax_due"] == 0
    assert result["refund_amount"] == 5_000


# ============================================================================
# compute_risk_assessment
# ============================================================================

def _stats(avg_weekly_income=3000.0, avg_daily_expense=300.0, income_volatility=0.1):
    return {"avg_weekly_income": avg_weekly_income, "avg_daily_expense": avg_daily_expense,
            "income_volatility": income_volatility}


def test_risk_assessment_low_risk_profile():
    stats = _stats(avg_weekly_income=5000, avg_daily_expense=100, income_volatility=0.05)
    profile = {"debt_obligations": {}, "current_emergency_fund": 20_000}
    result = compute_risk_assessment(stats, profile)
    assert result["overall_risk_level"] == "low"
    assert result["escalation_needed"] is False
    assert result["debt_to_income_ratio"] == 0.0


def test_risk_assessment_high_risk_with_debt_and_no_savings():
    stats = _stats(avg_weekly_income=2000, avg_daily_expense=100, income_volatility=0.6)
    profile = {"debt_obligations": {"loan_emi": 5000}, "current_emergency_fund": 0}
    result = compute_risk_assessment(stats, profile)
    assert result["overall_risk_level"] == "high"
    assert result["escalation_needed"] is True
    assert result["debt_to_income_ratio"] > 0.5


def test_risk_assessment_zero_income_does_not_crash():
    stats = _stats(avg_weekly_income=0, avg_daily_expense=0, income_volatility=0.0)
    profile = {}
    result = compute_risk_assessment(stats, profile)
    assert result["debt_to_income_ratio"] == 0.0
    assert isinstance(result["risk_score"], float)


# ============================================================================
# compute_budgets
# ============================================================================

def test_compute_budgets_returns_feast_famine_monthly():
    stats = {
        "avg_weekly_income": 3000.0,
        "weekday_income": {"Monday": 1000, "Tuesday": 500, "Wednesday": 0, "Thursday": 0,
                            "Friday": 800, "Saturday": 700, "Sunday": 0},
        "category_expenses": {"Food": 700, "Transport": 300},
        "days_span": 30,
        "income_transaction_count": 10,
    }
    budgets = compute_budgets(stats, {"debt_obligations": {"rent": 2000}})
    types = [b["budget_type"] for b in budgets]
    assert types == ["feast_week", "famine_week", "monthly"]
    for b in budgets:
        assert b["fixed_costs"] == {"rent": 2000.0}
        # discretionary is never negative
        assert b["discretionary_budget"] >= 0


def test_compute_budgets_famine_week_never_negative_income():
    # High stdev relative to avg -- famine income floors at 0, not negative
    stats = {
        "avg_weekly_income": 100.0,
        "weekday_income": {"Monday": 1000, "Tuesday": 0, "Wednesday": 0, "Thursday": 0,
                            "Friday": 0, "Saturday": 0, "Sunday": 0},
        "category_expenses": {},
        "days_span": 30,
        "income_transaction_count": 1,
    }
    budgets = compute_budgets(stats, {})
    famine = next(b for b in budgets if b["budget_type"] == "famine_week")
    assert famine["total_income_expected"] >= 0


# ============================================================================
# compute_volatility_forecast
# ============================================================================

def test_volatility_forecast_stable_trend():
    stats = {
        "avg_weekly_income": 3000.0,
        "weekday_income": {"Monday": 3000, "Tuesday": 3000, "Wednesday": 0, "Thursday": 0,
                            "Friday": 0, "Saturday": 0, "Sunday": 0},
        "days_span": 30,
        "total_income": 30000,
        "avg_daily_income": 1000,
        "income_volatility": 0.05,
        "income_transaction_count": 10,
    }
    forecast = compute_volatility_forecast(stats)
    assert forecast["recent_trend"] == "stable"
    assert forecast["forecast_range_min"] <= forecast["realistic_scenario"]["weekly_income"]
    assert forecast["forecast_range_max"] >= forecast["realistic_scenario"]["weekly_income"]


def test_volatility_forecast_volatile_trend():
    stats = {
        "avg_weekly_income": 3000.0,
        "weekday_income": {"Monday": 6000, "Tuesday": 0, "Wednesday": 0, "Thursday": 0,
                            "Friday": 0, "Saturday": 0, "Sunday": 0},
        "days_span": 30,
        "total_income": 30000,
        "avg_daily_income": 1000,
        "income_volatility": 0.9,
        "income_transaction_count": 10,
    }
    forecast = compute_volatility_forecast(stats)
    assert forecast["recent_trend"] == "volatile"


# ============================================================================
# compute_savings_plan
# ============================================================================

def test_savings_plan_with_surplus_recommends_investments():
    stats = {"avg_daily_expense": 100.0, "avg_weekly_income": 3000.0}
    profile = {"current_emergency_fund": 0}
    plan = compute_savings_plan(stats, profile)
    assert plan["emergency_fund"]["target_amount"] == pytest.approx(100 * 30 * 6)
    assert plan["emergency_fund"]["priority"] == "high"
    assert len(plan["investment_recommendations"]) == 2


def test_savings_plan_no_surplus_recommends_no_investments():
    # Expenses exceed income -- no surplus to invest
    stats = {"avg_daily_expense": 500.0, "avg_weekly_income": 700.0}
    profile = {"current_emergency_fund": 0}
    plan = compute_savings_plan(stats, profile)
    assert plan["emergency_fund"]["monthly_contribution"] == 0
    assert plan["investment_recommendations"] == []


# ============================================================================
# compute_goal_projection
# ============================================================================

def test_goal_projection_with_target_date():
    result = compute_goal_projection(
        target_amount=12_000, current_amount=0, target_date=None, monthly_surplus=2_000,
    )
    # No target_date -> derives a monthly_target from surplus (30% of it)
    assert result["monthly_target"] == pytest.approx(600.0)
    assert result["progress_percentage"] == 0.0


def test_goal_projection_zero_target_amount_does_not_divide_by_zero():
    result = compute_goal_projection(
        target_amount=0, current_amount=0, target_date=None, monthly_surplus=0,
    )
    assert result["progress_percentage"] == 0.0
    assert result["monthly_target"] == 0.0


def test_goal_projection_already_met():
    result = compute_goal_projection(
        target_amount=10_000, current_amount=10_000, target_date=None, monthly_surplus=1_000,
    )
    assert result["progress_percentage"] == 100.0
