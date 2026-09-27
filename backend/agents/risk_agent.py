"""
Risk Assessment Agent
Computes debt-to-income ratio, emergency fund coverage, and a composite risk
score from real transactions and profile data (see
finance_helpers.compute_risk_assessment) -- deterministic formula, not an
LLM-guessed score. The LLM is only used for a one-line narrative summary.
Writes to: risk_assessments table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    fetch_profile,
    compute_income_expense_stats,
    compute_risk_assessment,
    generate_narrative,
    write_record,
)

logger = logging.getLogger(__name__)


class RiskAssessmentAgent:
    """Evaluates financial risk from real data and decides if escalation is needed."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Risk Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            profile = fetch_profile(user_id)
            stats = compute_income_expense_stats(transactions)
            assessment = compute_risk_assessment(stats, profile)

            narrative = await generate_narrative(
                system_prompt=(
                    "You are a financial risk assistant for Indian gig workers. "
                    "Given real computed risk metrics, explain the overall picture "
                    "in 1-2 short plain-language sentences. Do not invent numbers "
                    "beyond what is given."
                ),
                user_prompt=(
                    f"Risk level: {assessment['overall_risk_level']} "
                    f"(score {assessment['risk_score']}/10). "
                    f"Debt-to-income ratio: {assessment['debt_to_income_ratio'] * 100:.1f}%. "
                    f"Emergency fund covers {assessment['emergency_fund_coverage']} months of expenses."
                ),
                max_tokens=200,
            )
            assessment["ai_risk_analysis"] = narrative

            record = {
                **assessment,
                "user_id": user_id,
                "assessment_date": datetime.now().date().isoformat(),
            }
            written = write_record("risk_assessments", record)
            logger.info(f"[Risk Agent] Created risk assessment: {assessment['overall_risk_level']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "risk_assessment",
                "result": written,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Risk Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "risk_assessment",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = RiskAssessmentAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Risk Assessment Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
