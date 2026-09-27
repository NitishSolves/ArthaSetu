"""
Shared real-data fetching, deterministic financial calculations, and DB
writes for the agent pipeline. Every agent should compute its numbers from
here rather than asking the LLM to invent them -- the LLM (via
llm_client.generate_narrative, re-exported below) is only used for turning
already-computed real numbers into a short narrative/explanation string.
"""

import logging
import os
import statistics
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

# Every agent imports this module, so configuring the root logger here (once,
# idempotently -- basicConfig no-ops if a handler is already set) covers the
# whole live pipeline without touching each of the 9 agent files. Replaces
# plain print() calls with real levels/timestamps so output can be redirected
# to a file or log aggregator in production instead of going only to stdout.
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from llm_client import generate_narrative  # noqa: F401 -- re-exported for agents


def _supabase_headers() -> Dict[str, str]:
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def write_record(table: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert one row into `table` via the Supabase REST API using the
    service-role key (bypasses RLS -- the agent writes on the user's behalf
    server-side after the caller's ownership was already verified upstream).
    Raises on failure rather than silently swallowing it, so a broken write
    surfaces instead of reporting false success.
    """
    resp = requests.post(
        f"{os.environ['SUPABASE_URL']}/rest/v1/{table}",
        headers={**_supabase_headers(), "Prefer": "return=representation"},
        json=record,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Insert into {table} failed: {resp.status_code} {resp.text}")
    rows = resp.json()
    return rows[0] if rows else {}


def update_record(table: str, record_id: str, updates: Dict[str, Any], id_column: str = "id") -> Dict[str, Any]:
    """Patch one row by id via the Supabase REST API using the service-role key."""
    resp = requests.patch(
        f"{os.environ['SUPABASE_URL']}/rest/v1/{table}",
        headers={**_supabase_headers(), "Prefer": "return=representation"},
        params={id_column: f"eq.{record_id}"},
        json=updates,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Update {table} id={record_id} failed: {resp.status_code} {resp.text}")
    rows = resp.json()
    return rows[0] if rows else {}


def fetch_records(table: str, user_id: str, order_by: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
    """Real rows for a user from any table -- used by agents that build on
    another agent's already-written output (e.g. recommendation_agent
    reading risk_assessments/budgets rather than re-deriving them)."""
    params = {"user_id": f"eq.{user_id}", "limit": str(limit)}
    if order_by:
        params["order"] = order_by
    resp = requests.get(
        f"{os.environ['SUPABASE_URL']}/rest/v1/{table}",
        headers=_supabase_headers(),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_transactions(user_id: str, days: int = 90) -> List[Dict[str, Any]]:
    """Real transaction rows for a user from the last `days` days."""
    since = (datetime.now() - timedelta(days=days)).date().isoformat()
    url = f"{os.environ['SUPABASE_URL']}/rest/v1/transactions"
    resp = requests.get(
        url,
        headers=_supabase_headers(),
        params={
            "user_id": f"eq.{user_id}",
            "transaction_date": f"gte.{since}",
            "order": "transaction_date.asc",
            "limit": "2000",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_profile(user_id: str) -> Dict[str, Any]:
    """Merge profiles + user_profiles into one dict (empty fields default to 0/None)."""
    base = f"{os.environ['SUPABASE_URL']}/rest/v1"
    headers = _supabase_headers()

    profile_resp = requests.get(
        f"{base}/profiles", headers=headers,
        params={"user_id": f"eq.{user_id}", "limit": "1"}, timeout=15,
    )
    profile_resp.raise_for_status()
    profile_rows = profile_resp.json()
    profile = profile_rows[0] if profile_rows else {}

    fin_resp = requests.get(
        f"{base}/user_profiles", headers=headers,
        params={"user_id": f"eq.{user_id}", "limit": "1"}, timeout=15,
    )
    fin_resp.raise_for_status()
    fin_rows = fin_resp.json()
    fin_profile = fin_rows[0] if fin_rows else {}

    return {**profile, **fin_profile}


def compute_income_expense_stats(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate stats from real transactions -- no LLM involved."""
    income = [float(t["amount"]) for t in transactions if t.get("transaction_type") == "income"]
    expenses = [float(t["amount"]) for t in transactions if t.get("transaction_type") == "expense"]

    total_income = sum(income)
    total_expenses = sum(expenses)

    # Group income by ISO weekday for a weekday breakdown (Mon..Sun)
    weekday_income: Dict[str, float] = {d: 0.0 for d in
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    for t in transactions:
        if t.get("transaction_type") != "income" or not t.get("transaction_date"):
            continue
        dt = datetime.fromisoformat(t["transaction_date"])
        weekday_income[dt.strftime("%A")] += float(t["amount"])

    # Category breakdown for expenses (used by budget/goals agents)
    category_expenses: Dict[str, float] = {}
    for t in transactions:
        if t.get("transaction_type") != "expense":
            continue
        cat = t.get("category") or "Other"
        category_expenses[cat] = category_expenses.get(cat, 0.0) + float(t["amount"])

    days_span = _date_span_days(transactions)
    weeks_span = max(days_span / 7, 1)

    avg_weekly_income = total_income / weeks_span
    income_volatility = (statistics.pstdev(income) / avg_weekly_income) if len(income) > 1 and avg_weekly_income > 0 else 0.0

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net": round(total_income - total_expenses, 2),
        "avg_weekly_income": round(avg_weekly_income, 2),
        "avg_daily_income": round(total_income / max(days_span, 1), 2),
        "avg_daily_expense": round(total_expenses / max(days_span, 1), 2),
        "income_volatility": round(min(income_volatility, 1.0), 3),
        "weekday_income": {k: round(v, 2) for k, v in weekday_income.items()},
        "category_expenses": {k: round(v, 2) for k, v in category_expenses.items()},
        "transaction_count": len(transactions),
        "income_transaction_count": len(income),
        "days_span": days_span,
    }


def _date_span_days(transactions: List[Dict[str, Any]]) -> int:
    dates = [t["transaction_date"] for t in transactions if t.get("transaction_date")]
    if not dates:
        return 30
    d0 = datetime.fromisoformat(min(dates))
    d1 = datetime.fromisoformat(max(dates))
    return max((d1 - d0).days, 1)


# ============================================================================
# Tax calculation -- ported from frontend/src/pages/Tax.tsx's
# calculateTaxNewRegime()/applyRebate() so both surfaces agree on the same
# New Regime FY 2024-25 numbers instead of an LLM re-deriving tax law.
# ============================================================================

def calculate_tax_new_regime(taxable_income: float) -> float:
    if taxable_income <= 400_000:
        return 0.0
    if taxable_income <= 800_000:
        return (taxable_income - 400_000) * 0.05
    if taxable_income <= 1_200_000:
        return 20_000 + (taxable_income - 800_000) * 0.10
    if taxable_income <= 1_600_000:
        return 60_000 + (taxable_income - 1_200_000) * 0.15
    if taxable_income <= 2_000_000:
        return 120_000 + (taxable_income - 1_600_000) * 0.20
    if taxable_income <= 2_400_000:
        return 200_000 + (taxable_income - 2_000_000) * 0.25
    return 300_000 + (taxable_income - 2_400_000) * 0.30


def apply_section_87a_rebate(tax: float, taxable_income: float) -> float:
    if taxable_income <= 1_200_000:
        return max(0.0, tax - 60_000)
    return tax


def compute_gig_worker_tax(gross_gig_income: float, presumptive_rate: float = 0.06,
                            tds_deducted: float = 0.0) -> Dict[str, Any]:
    """
    Presumptive taxation (Section 44AD/44ADA): only presumptive_rate of gross
    receipts is taxable income, not the full amount. presumptive_rate is 0.06
    for ≥95% digital receipts, 0.08 otherwise -- matches the Tax.tsx
    calculator's default.
    """
    taxable_income = gross_gig_income * presumptive_rate
    gross_tax = calculate_tax_new_regime(taxable_income)
    tax_after_rebate = apply_section_87a_rebate(gross_tax, taxable_income)
    total_tax = tax_after_rebate * 1.04  # 4% health & education cess
    tax_due = max(0.0, total_tax - tds_deducted)
    refund = max(0.0, tds_deducted - total_tax)

    return {
        "gross_income": round(gross_gig_income, 2),
        "taxable_income": round(taxable_income, 2),
        "gross_tax": round(gross_tax, 2),
        "rebate_87a": round(gross_tax - tax_after_rebate, 2),
        "cess": round(tax_after_rebate * 0.04, 2),
        "total_tax_liability": round(total_tax, 2),
        "tds_deducted": round(tds_deducted, 2),
        "tax_due": round(tax_due, 2),
        "refund_amount": round(refund, 2),
        "itr_form_type": "ITR-4",
        "is_tax_free": total_tax == 0,
    }


# ============================================================================
# Risk scoring -- deterministic formula, not LLM-guessed
# ============================================================================

def compute_risk_assessment(income_stats: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    monthly_income = income_stats["avg_weekly_income"] * 4.33
    monthly_expenses = income_stats["avg_daily_expense"] * 30 or 1.0

    debt_obligations = profile.get("debt_obligations") or {}
    monthly_debt = sum(float(v) for v in debt_obligations.values()) if isinstance(debt_obligations, dict) else 0.0
    debt_to_income_ratio = round(monthly_debt / monthly_income, 3) if monthly_income > 0 else 0.0

    current_emergency_fund = float(profile.get("current_emergency_fund") or 0)
    emergency_fund_coverage = round(current_emergency_fund / monthly_expenses, 2) if monthly_expenses > 0 else 0.0

    income_volatility = income_stats["income_volatility"]

    # Weighted composite score, 0-10. Each factor contributes proportionally
    # to how far it is from a "healthy" threshold.
    dti_risk = min(debt_to_income_ratio / 0.5, 1.0) * 4        # >50% DTI = max risk contribution
    fund_risk = max(0, 1 - emergency_fund_coverage / 6) * 3    # <6 months coverage = risk
    volatility_risk = min(income_volatility, 1.0) * 3
    risk_score = round(dti_risk + fund_risk + volatility_risk, 1)

    if risk_score <= 3:
        overall_risk_level = "low"
    elif risk_score <= 6:
        overall_risk_level = "medium"
    else:
        overall_risk_level = "high"

    escalation_needed = debt_to_income_ratio > 0.5 or (emergency_fund_coverage < 1 and income_volatility > 0.5)

    risk_factors = [
        {"factor": "Debt-to-income ratio", "impact": f"{debt_to_income_ratio * 100:.1f}% of monthly income"},
        {"factor": "Emergency fund", "impact": f"{emergency_fund_coverage:.1f} months of expenses covered"},
        {"factor": "Income volatility", "impact": f"{income_volatility * 100:.1f}% variation week to week"},
    ]

    recommended_actions = []
    if emergency_fund_coverage < 6:
        recommended_actions.append({
            "action": "Build emergency fund",
            "description": "Target at least 6 months of expenses in liquid savings",
        })
    if debt_to_income_ratio > 0.4:
        recommended_actions.append({
            "action": "Reduce debt burden",
            "description": "Keep total debt obligations below 40% of monthly income",
        })
    if income_volatility > 0.4:
        recommended_actions.append({
            "action": "Smooth income volatility",
            "description": "Set aside a larger buffer during high-income weeks to cover low-income weeks",
        })

    return {
        "overall_risk_level": overall_risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "debt_to_income_ratio": debt_to_income_ratio,
        "income_drop_percentage": 0.0,
        "expense_spike_factor": round(monthly_expenses / (income_stats["avg_daily_expense"] * 30 or 1), 2) if monthly_expenses else 1.0,
        "emergency_fund_coverage": emergency_fund_coverage,
        "transaction_anomalies": None,
        "escalation_needed": escalation_needed,
        "escalation_priority": "high" if escalation_needed else None,
        "escalation_reason": "High debt burden with low emergency fund coverage" if escalation_needed else None,
        "recommended_actions": recommended_actions,
    }


# ============================================================================
# Budget: feast/famine/monthly, derived from real income stats + real fixed
# costs (debt_obligations from user_profiles), not invented.
# ============================================================================

def compute_budgets(income_stats: Dict[str, Any], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    avg_weekly = income_stats["avg_weekly_income"]
    weekday_values = [v for v in income_stats["weekday_income"].values() if v > 0]
    stdev = statistics.pstdev(weekday_values) if len(weekday_values) > 1 else avg_weekly * 0.3

    feast_income = round(avg_weekly + stdev, 2)
    famine_income = round(max(avg_weekly - stdev, 0), 2)
    monthly_income = round(avg_weekly * 4.33, 2)

    debt_obligations = profile.get("debt_obligations") or {}
    fixed_costs = {k: float(v) for k, v in debt_obligations.items()} if isinstance(debt_obligations, dict) else {}
    total_fixed = sum(fixed_costs.values())

    category_expenses = income_stats["category_expenses"]
    weeks_span = max(income_stats["days_span"] / 7, 1)
    variable_costs = {k: round(v / weeks_span, 2) for k, v in category_expenses.items()}
    total_variable = sum(variable_costs.values())

    def _budget(budget_type: str, income: float, savings_rate: float) -> Dict[str, Any]:
        savings_target = round(max(income - total_fixed - total_variable, 0) * savings_rate, 2)
        discretionary = round(max(income - total_fixed - total_variable - savings_target, 0), 2)
        return {
            "budget_type": budget_type,
            "valid_from": datetime.now().date().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=7)).date().isoformat(),
            "total_income_expected": income,
            "fixed_costs": fixed_costs,
            "variable_costs": variable_costs,
            "savings_target": savings_target,
            "discretionary_budget": discretionary,
            "category_limits": {k: round(v * 1.15, 2) for k, v in variable_costs.items()},
            "confidence_score": 0.8 if income_stats["income_transaction_count"] >= 8 else 0.5,
        }

    return [
        _budget("feast_week", feast_income, savings_rate=0.35),
        _budget("famine_week", famine_income, savings_rate=0.0),
        _budget("monthly", monthly_income, savings_rate=0.20),
    ]


# ============================================================================
# Income volatility forecast -- statistical, not LLM-guessed. One schema
# (not the two contradictory ones the original prompt had).
# ============================================================================

def compute_volatility_forecast(income_stats: Dict[str, Any]) -> Dict[str, Any]:
    weekday_values = [v for v in income_stats["weekday_income"].values() if v > 0]
    avg = income_stats["avg_weekly_income"]
    stdev = statistics.pstdev(weekday_values) if len(weekday_values) > 1 else avg * 0.3
    volatility_index = income_stats["income_volatility"]

    pessimistic = round(max(avg - stdev, 0), 2)
    optimistic = round(avg + stdev, 2)

    if volatility_index < 0.2:
        recent_trend = "stable"
    elif volatility_index < 0.5:
        recent_trend = "moderate"
    else:
        recent_trend = "volatile"

    return {
        "forecast_date": datetime.now().date().isoformat(),
        "historical_days": income_stats["days_span"],
        "historical_total_income": income_stats["total_income"],
        "historical_avg_daily": income_stats["avg_daily_income"],
        "historical_std_dev": round(stdev, 2),
        "volatility_index": volatility_index,
        "pessimistic_scenario": {"weekly_income": pessimistic},
        "realistic_scenario": {"weekly_income": round(avg, 2)},
        "optimistic_scenario": {"weekly_income": optimistic},
        "weighted_forecast": round(pessimistic * 0.25 + avg * 0.5 + optimistic * 0.25, 2),
        "forecast_range_min": pessimistic,
        "forecast_range_max": optimistic,
        "weekday_breakdown": income_stats["weekday_income"],
        "recent_trend": recent_trend,
        "forecast_confidence": 0.8 if income_stats["income_transaction_count"] >= 8 else 0.5,
    }


# ============================================================================
# Savings & investment -- emergency fund target is a standard 6-months-of-
# expenses formula. Investment return rates are REAL published rates (not
# LLM-invented) but are fixed constants that drift as rates change --
# flagged here so a future pass wires up a live-rate source instead of
# hardcoding.
# ============================================================================

# Approximate published rates as of this codebase's last update. Government
# small-savings rates are revised quarterly (PPF/RD/NSC) and NPS/SIP returns
# are market-linked historical averages, not guarantees.
INVESTMENT_OPTIONS = [
    {"investment_type": "PPF", "provider": "Post Office / Banks", "expected_return": 7.1, "risk_level": "low", "min_lock_in_months": 180},
    {"investment_type": "Post Office RD", "provider": "India Post", "expected_return": 6.7, "risk_level": "low", "min_lock_in_months": 60},
    {"investment_type": "Bank FD", "provider": "Scheduled Banks", "expected_return": 6.5, "risk_level": "low", "min_lock_in_months": 12},
    {"investment_type": "NPS", "provider": "PFRDA", "expected_return": 9.0, "risk_level": "moderate", "min_lock_in_months": 0},
    {"investment_type": "SIP (Index Fund)", "provider": "Mutual Fund", "expected_return": 11.0, "risk_level": "moderate", "min_lock_in_months": 0},
]


def compute_savings_plan(income_stats: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    monthly_expenses = income_stats["avg_daily_expense"] * 30
    monthly_income = income_stats["avg_weekly_income"] * 4.33

    emergency_target = round(monthly_expenses * 6, 2)
    current_fund = float(profile.get("current_emergency_fund") or 0)

    net_monthly = max(monthly_income - monthly_expenses, 0)
    monthly_contribution = round(min(net_monthly * 0.2, max(emergency_target - current_fund, 0)), 2)

    surplus_after_emergency = max(net_monthly - monthly_contribution, 0)

    investments = []
    if surplus_after_emergency > 0:
        # Split surplus across low-risk options once the emergency fund is
        # adequately funded; keep it low-risk given income volatility.
        per_option = round(surplus_after_emergency / 2, 2)
        for opt in INVESTMENT_OPTIONS[:2]:
            investments.append({
                **opt,
                "recommended_amount": per_option,
                "frequency": "monthly",
                "reasoning": f"Low-risk option suitable for volatile gig income, {opt['expected_return']}% approx. return.",
            })

    return {
        "emergency_fund": {
            "target_amount": emergency_target,
            "current_amount": current_fund,
            "monthly_contribution": monthly_contribution,
            "priority": "high" if current_fund < emergency_target * 0.5 else "medium",
            "status": "completed" if current_fund >= emergency_target else "in_progress",
        },
        "investment_recommendations": investments,
    }


# ============================================================================
# Financial goals -- real progress math, not invented numbers. Goals
# themselves are primarily user-created via the UI (Goals.tsx); this is
# used when the agent suggests a starter goal for a user with none.
# ============================================================================

def compute_goal_projection(target_amount: float, current_amount: float,
                             target_date: Optional[str], monthly_surplus: float) -> Dict[str, Any]:
    remaining = max(target_amount - current_amount, 0)
    progress_percentage = round((current_amount / target_amount) * 100, 2) if target_amount > 0 else 0.0

    months_remaining = None
    if target_date:
        try:
            months_remaining = max(
                (datetime.fromisoformat(target_date).year - datetime.now().year) * 12
                + (datetime.fromisoformat(target_date).month - datetime.now().month), 1
            )
        except ValueError:
            months_remaining = None

    if months_remaining:
        monthly_target = round(remaining / months_remaining, 2)
    elif monthly_surplus > 0:
        monthly_target = round(monthly_surplus * 0.3, 2)
        months_remaining = round(remaining / monthly_target) if monthly_target > 0 else None
    else:
        monthly_target = 0.0

    return {
        "monthly_target": monthly_target,
        "progress_percentage": progress_percentage,
        "estimated_months_remaining": months_remaining,
    }
