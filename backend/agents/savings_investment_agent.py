"""
Savings & Investment Agent
Computes an emergency-fund target (6 months of real expenses) and
low-risk investment recommendations from real surplus income (see
finance_helpers.compute_savings_plan) -- investment return rates are real
published figures, not LLM-invented, though they're fixed constants that
need periodic updates as government/market rates change (see
finance_helpers.INVESTMENT_OPTIONS). The LLM is only used for a one-line
narrative.
Writes to: savings_goals, investment_recommendations tables
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    fetch_profile,
    compute_income_expense_stats,
    compute_savings_plan,
    generate_narrative,
    write_record,
)

logger = logging.getLogger(__name__)


class SavingsInvestmentAgent:
    """Recommends an emergency fund target and low-risk investments from real data."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Savings Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            profile = fetch_profile(user_id)
            stats = compute_income_expense_stats(transactions)
            plan = compute_savings_plan(stats, profile)

            narrative = await generate_narrative(
                system_prompt=(
                    "You are a savings assistant for Indian gig workers. Given "
                    "real computed numbers, explain the plan in 1-2 short "
                    "plain-language sentences."
                ),
                user_prompt=(
                    f"Emergency fund target: Rs {plan['emergency_fund']['target_amount']}, "
                    f"current: Rs {plan['emergency_fund']['current_amount']}, "
                    f"suggested monthly contribution: Rs {plan['emergency_fund']['monthly_contribution']}."
                ),
                max_tokens=200,
            )
            plan["emergency_fund"]["reasoning"] = narrative

            ef = plan["emergency_fund"]
            savings_record = write_record("savings_goals", {
                "user_id": user_id,
                "goal_type": "emergency_fund",
                "goal_name": "Emergency Fund",
                "target_amount": ef["target_amount"],
                "current_amount": ef["current_amount"],
                "monthly_contribution": ef["monthly_contribution"],
                "priority": ef["priority"],
                "status": ef["status"],
                "reasoning": ef["reasoning"],
            })
            logger.info("[Savings Agent] Created emergency fund goal")

            investment_records = []
            for inv in plan["investment_recommendations"]:
                investment_records.append(write_record("investment_recommendations", {
                    "user_id": user_id,
                    "investment_type": inv["investment_type"],
                    "provider": inv["provider"],
                    "recommended_amount": inv["recommended_amount"],
                    "frequency": inv["frequency"],
                    "expected_return": inv["expected_return"],
                    "risk_level": inv["risk_level"],
                    "min_lock_in_months": inv["min_lock_in_months"],
                    "reasoning": inv["reasoning"],
                }))
                logger.info(f"[Savings Agent] Created investment recommendation: {inv['investment_type']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "savings_investment",
                "result": {"emergency_fund": savings_record, "investments": investment_records},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Savings Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "savings_investment",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = SavingsInvestmentAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Savings & Investment Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
