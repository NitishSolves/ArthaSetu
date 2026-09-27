"""
Budget Analysis Agent
Computes feast/famine/monthly budgets from the user's real transaction
history and profile -- deterministic math (see finance_helpers.compute_budgets),
not LLM-guessed numbers. The LLM is only used for a one-line narrative.
Writes to: budgets table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    fetch_profile,
    compute_income_expense_stats,
    compute_budgets,
    generate_narrative,
    write_record,
)

logger = logging.getLogger(__name__)


class BudgetAnalysisAgent:
    """Creates feast/famine/monthly budgets for gig workers from real data."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Budget Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            profile = fetch_profile(user_id)
            stats = compute_income_expense_stats(transactions)
            budgets = compute_budgets(stats, profile)

            narrative = await generate_narrative(
                system_prompt=(
                    "You are a budgeting assistant for Indian gig workers. "
                    "Given real weekly budget numbers, explain in 1-2 short "
                    "plain-language sentences why the feast/famine split makes sense."
                ),
                user_prompt=(
                    f"Feast week income: Rs {budgets[0]['total_income_expected']}, "
                    f"famine week income: Rs {budgets[1]['total_income_expected']}, "
                    f"monthly average: Rs {budgets[2]['total_income_expected']}. "
                    f"Based on {stats['income_transaction_count']} income transactions."
                ),
                max_tokens=200,
            )

            written = []
            for budget in budgets:
                record = {**budget, "user_id": user_id, "is_active": True}
                written.append(write_record("budgets", record))
                logger.info(f"[Budget Agent] Created budget: {budget['budget_type']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "budget_analysis",
                "result": {"budgets": written, "narrative": narrative},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Budget Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "budget_analysis",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = BudgetAnalysisAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Budget Analysis Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
