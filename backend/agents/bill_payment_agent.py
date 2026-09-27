"""
Bill Payment Agent
Bills are primarily user-managed via the Actions page UI (db.bills.* in the
frontend). This agent's real value-add: detect genuinely recurring expense
patterns in real transactions (same category + similar amount appearing 2+
times) and suggest them as bills, skipping anything that already has a
matching bill entry -- not inventing bill amounts from nothing.
Writes to: bills table
"""

import asyncio
import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from finance_helpers import fetch_transactions, fetch_records, write_record

logger = logging.getLogger(__name__)

MIN_OCCURRENCES = 2
AMOUNT_TOLERANCE = 0.15  # 15% variation still counts as "the same" recurring bill


class BillPaymentAgent:
    """Detects recurring expenses from real transactions and suggests them as bills."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Bill Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            existing_bills = fetch_records("bills", user_id)
            existing_names = {b["bill_name"].lower() for b in existing_bills}

            by_category: dict = defaultdict(list)
            for t in transactions:
                if t.get("transaction_type") == "expense":
                    by_category[t.get("category") or "Other"].append(t)

            created = []
            for category, txns in by_category.items():
                if len(txns) < MIN_OCCURRENCES:
                    continue

                amounts = sorted(float(t["amount"]) for t in txns)
                median = amounts[len(amounts) // 2]
                close_amounts = [a for a in amounts if abs(a - median) <= median * AMOUNT_TOLERANCE]
                if len(close_amounts) < MIN_OCCURRENCES:
                    continue  # amounts vary too much to be a real recurring bill

                bill_name = f"{category} (recurring)"
                if bill_name.lower() in existing_names:
                    continue

                # Estimate next due date: one interval after the most recent occurrence
                dates = sorted(t["transaction_date"] for t in txns)
                last_date = datetime.fromisoformat(dates[-1])
                if len(dates) >= 2:
                    interval_days = (datetime.fromisoformat(dates[-1]) - datetime.fromisoformat(dates[-2])).days
                else:
                    interval_days = 30
                due_date = (last_date + timedelta(days=max(interval_days, 7))).date().isoformat()

                bill = write_record("bills", {
                    "user_id": user_id,
                    "bill_name": bill_name,
                    "bill_type": "utility" if category.lower() in ("utilities", "electricity", "water", "internet") else "other",
                    "amount": round(statistics.median(close_amounts), 2),
                    "due_date": due_date,
                    "frequency": "monthly" if 25 <= interval_days <= 35 else "weekly" if 5 <= interval_days <= 9 else "irregular",
                    "priority": "medium",
                    "auto_pay_recommended": False,
                    "payment_method": "upi",
                    "status": "pending",
                })
                created.append(bill)
                logger.info(f"[Bill Agent] Detected recurring bill: {bill_name} (~Rs {bill['amount']})")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "bill_payment",
                "result": {"bills_detected": created},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Bill Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "bill_payment",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = BillPaymentAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Bill Payment Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
