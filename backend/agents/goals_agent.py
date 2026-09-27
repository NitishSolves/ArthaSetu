"""
Financial Goals Agent
Financial goals are primarily user-created via the Goals page UI
(db.financialGoals.create in the frontend). This agent's job is narrower
than the original "invent goals with milestones" design: recompute
monthly_target/progress_percentage for existing goals from real numbers
(see finance_helpers.compute_goal_projection), and create one starter
Emergency Fund goal only for users who have none yet, using the same real
savings-plan math savings_investment_agent uses. No invented target amounts
for goals the user hasn't set.
Writes to: financial_goals table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    fetch_profile,
    fetch_records,
    compute_income_expense_stats,
    compute_savings_plan,
    compute_goal_projection,
    write_record,
    update_record,
)

logger = logging.getLogger(__name__)


class FinancialGoalsAgent:
    """Recomputes real progress for existing goals; seeds one starter goal if none exist."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Goals Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            profile = fetch_profile(user_id)
            stats = compute_income_expense_stats(transactions)
            monthly_surplus = max(stats["avg_weekly_income"] * 4.33 - stats["avg_daily_expense"] * 30, 0)

            existing_goals = fetch_records("financial_goals", user_id)
            updated = []

            if existing_goals:
                for goal in existing_goals:
                    projection = compute_goal_projection(
                        target_amount=float(goal["target_amount"]),
                        current_amount=float(goal["current_amount"]),
                        target_date=goal.get("target_date"),
                        monthly_surplus=monthly_surplus,
                    )
                    updated_goal = update_record("financial_goals", goal["id"], {
                        "monthly_target": projection["monthly_target"],
                        "progress_percentage": projection["progress_percentage"],
                    })
                    if updated_goal:
                        updated.append(updated_goal)
                        logger.info(f"[Goals Agent] Updated progress for goal: {goal['goal_name']}")
            else:
                plan = compute_savings_plan(stats, profile)
                ef = plan["emergency_fund"]
                projection = compute_goal_projection(
                    target_amount=ef["target_amount"],
                    current_amount=ef["current_amount"],
                    target_date=None,
                    monthly_surplus=monthly_surplus,
                )
                goal_record = write_record("financial_goals", {
                    "user_id": user_id,
                    "goal_name": "Emergency Fund",
                    "goal_type": "emergency_fund",
                    "description": "6 months of expenses in accessible savings, sized from your real transaction history.",
                    "target_amount": ef["target_amount"],
                    "current_amount": ef["current_amount"],
                    "priority": 1,
                    "status": "not_started" if ef["current_amount"] == 0 else "in_progress",
                    "monthly_target": projection["monthly_target"],
                    "progress_percentage": projection["progress_percentage"],
                })
                updated.append(goal_record)
                logger.info("[Goals Agent] Created starter emergency fund goal (no existing goals found)")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "financial_goals",
                "result": {"goals": updated},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Goals Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "financial_goals",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = FinancialGoalsAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Financial Goals Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
