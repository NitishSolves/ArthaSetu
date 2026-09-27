"""
Action Execution Agent
Proposes concrete action suggestions (e.g. "transfer X to savings") from
REAL savings goals and upcoming bills already on file -- amounts come
directly from those records, not invented. NEVER executes actual money
movement; every action is created with status="pending" and
user_approved=False, requiring explicit user approval in the UI
(see frontend/src/pages/Actions.tsx).
Writes to: executed_actions table
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

from finance_helpers import fetch_records, write_record

logger = logging.getLogger(__name__)


class ActionExecutionAgent:
    """Suggests (but never executes) savings transfers and bill payments from real data."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Action Agent] Starting analysis for user {user_id}")

        try:
            savings_rows = fetch_records("savings_goals", user_id, order_by="created_at.desc", limit=5)
            bill_rows = fetch_records("bills", user_id, order_by="due_date.asc", limit=10)

            created = []

            ef_goal = next((s for s in savings_rows if s.get("goal_type") == "emergency_fund"), None)
            if ef_goal and float(ef_goal.get("monthly_contribution", 0)) > 0:
                action = write_record("executed_actions", {
                    "user_id": user_id,
                    "action_type": "savings_transfer",
                    "action_description": f"Transfer Rs {ef_goal['monthly_contribution']} to your emergency fund",
                    "status": "pending",
                    "amount": ef_goal["monthly_contribution"],
                    "schedule": "monthly",
                    "next_execution": (datetime.now() + timedelta(days=7)).date().isoformat(),
                    "user_approved": False,
                    "is_reversible": True,
                })
                created.append(action)
                logger.info(f"[Action Agent] Suggested savings transfer: Rs {ef_goal['monthly_contribution']}")

            upcoming_cutoff = (datetime.now() + timedelta(days=14)).date().isoformat()
            for bill in bill_rows:
                if bill.get("status") != "pending" or not bill.get("due_date"):
                    continue
                if bill["due_date"] > upcoming_cutoff:
                    continue
                action = write_record("executed_actions", {
                    "user_id": user_id,
                    "action_type": "bill_payment",
                    "action_description": f"Pay {bill['bill_name']} (Rs {bill['amount']}, due {bill['due_date']})",
                    "status": "pending",
                    "amount": bill["amount"],
                    "schedule": "once",
                    "next_execution": bill["due_date"],
                    "user_approved": False,
                    "is_reversible": True,
                })
                created.append(action)
                logger.info(f"[Action Agent] Suggested bill payment: {bill['bill_name']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "action_execution",
                "result": {"actions_suggested": created},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Action Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "action_execution",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = ActionExecutionAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Action Execution Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
