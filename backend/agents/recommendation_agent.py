"""
Recommendation Agent
Generates recommendations grounded in the REAL numbers other agents already
computed and wrote this run (risk_assessments, budgets, savings_goals,
tax_records) -- runs last in the orchestration order (see main.py) so that
data exists. The LLM only phrases an already-decided recommendation's
description; it does not decide target_amount/confidence_score/etc, which
are derived directly from the real records.
Writes to: recommendations table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import fetch_records, generate_narrative, write_record

logger = logging.getLogger(__name__)


class RecommendationAgent:
    """Builds recommendations from real risk/budget/savings/tax data already on file."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Recommendation Agent] Starting analysis for user {user_id}")

        try:
            risk_rows = fetch_records("risk_assessments", user_id, order_by="assessment_date.desc", limit=1)
            budget_rows = fetch_records("budgets", user_id, order_by="created_at.desc", limit=3)
            savings_rows = fetch_records("savings_goals", user_id, order_by="created_at.desc", limit=5)
            tax_rows = fetch_records("tax_records", user_id, order_by="created_at.desc", limit=1)

            candidates = []

            if risk_rows and risk_rows[0].get("overall_risk_level") in ("medium", "high"):
                risk = risk_rows[0]
                candidates.append({
                    "recommendation_type": "risk",
                    "priority": "high" if risk["overall_risk_level"] == "high" else "medium",
                    "title": f"Address {risk['overall_risk_level']} financial risk",
                    "target_amount": None,
                    "confidence_score": 0.9,
                    "context": f"Risk score {risk['risk_score']}/10, debt-to-income {risk['debt_to_income_ratio']*100:.0f}%, "
                               f"emergency fund covers {risk['emergency_fund_coverage']} months.",
                })

            ef_goal = next((s for s in savings_rows if s.get("goal_type") == "emergency_fund"), None)
            if ef_goal and float(ef_goal["current_amount"]) < float(ef_goal["target_amount"]):
                remaining = float(ef_goal["target_amount"]) - float(ef_goal["current_amount"])
                candidates.append({
                    "recommendation_type": "savings",
                    "priority": ef_goal.get("priority", "medium"),
                    "title": "Keep building your emergency fund",
                    "target_amount": round(remaining, 2),
                    "confidence_score": 0.85,
                    "context": f"Rs {remaining:.0f} more needed to reach your Rs {ef_goal['target_amount']} target, "
                               f"suggested Rs {ef_goal['monthly_contribution']}/month.",
                })

            famine_budget = next((b for b in budget_rows if b.get("budget_type") == "famine_week"), None)
            if famine_budget and float(famine_budget.get("discretionary_budget", 0)) == 0:
                candidates.append({
                    "recommendation_type": "budget",
                    "priority": "medium",
                    "title": "Plan for low-income weeks",
                    "target_amount": None,
                    "confidence_score": 0.8,
                    "context": f"In a famine week your budget has Rs {famine_budget['total_income_expected']} income "
                               f"with no discretionary spending room after fixed and variable costs.",
                })

            if tax_rows and float(tax_rows[0].get("refund_amount", 0)) > 0:
                tax = tax_rows[0]
                candidates.append({
                    "recommendation_type": "tax",
                    "priority": "low",
                    "title": "You may be eligible for a tax refund",
                    "target_amount": float(tax["refund_amount"]),
                    "confidence_score": 0.75,
                    "context": f"Estimated refund of Rs {tax['refund_amount']} for FY {tax['financial_year']} "
                               f"based on TDS already deducted.",
                })

            written = []
            for c in candidates:
                description = await generate_narrative(
                    system_prompt=(
                        "You are a financial recommendation assistant for Indian gig workers. "
                        "Given a real, already-decided recommendation and its context, write a "
                        "2-3 sentence description and one sentence of reasoning. Do not invent "
                        "numbers beyond what is given. Reply as: DESCRIPTION: ... REASONING: ..."
                    ),
                    user_prompt=f"Title: {c['title']}\nContext: {c['context']}",
                    max_tokens=250,
                )
                description_text, reasoning_text = _split_description_reasoning(description)

                record = write_record("recommendations", {
                    "user_id": user_id,
                    "recommendation_type": c["recommendation_type"],
                    "priority": c["priority"],
                    "title": c["title"],
                    "description": description_text,
                    "reasoning": reasoning_text,
                    "action_items": [],
                    "target_amount": c["target_amount"],
                    "confidence_score": c["confidence_score"],
                    "agent_source": "recommendation_agent",
                    "status": "pending",
                })
                written.append(record)
                logger.info(f"[Recommendation Agent] Created recommendation: {c['title']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "recommendation",
                "result": {"recommendations": written},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Recommendation Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "recommendation",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


def _split_description_reasoning(text: str) -> tuple:
    description, reasoning = text, ""
    if "REASONING:" in text:
        parts = text.split("REASONING:", 1)
        description = parts[0].replace("DESCRIPTION:", "").strip()
        reasoning = parts[1].strip()
    elif "DESCRIPTION:" in text:
        description = text.replace("DESCRIPTION:", "").strip()
    return description, reasoning


async def main():
    agent = RecommendationAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Recommendation Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
