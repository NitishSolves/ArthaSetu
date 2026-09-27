"""
Financial Health Agent
Evaluates overall financial health and creates comprehensive financial score
Writes to: financial_health table
"""
import asyncio
import json
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from autogen_runtime import run_autogen_mcp_task


class FinancialHealthAgent:
    """Agent that evaluates overall financial health and creates financial score"""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
        return """You are a Financial Health Evaluator for gig workers.

Your task is to evaluate overall financial health and create a comprehensive financial score, outputting structured JSON for the financial_health table.

**CRITICAL: You must output ONLY valid JSON that matches the financial_health table schema:**

```json
{
  "financial_health": {
    "overall_score": 72,
    "health_category": "good",
    "savings_health": {
      "score": 85,
      "emergency_fund_months": 4.2,
      "savings_rate": 0.18,
      "retirement_on_track": true
    },
    "debt_health": {
      "score": 60,
      "debt_to_income": 0.28,
      "total_debt": 150000.00,
      "debt_trend": "decreasing"
    },
    "income_health": {
      "score": 75,
      "income_stability": "moderate",
      "income_growth": 0.12,
      "diversification_score": 0.4
    },
    "spending_health": {
      "score": 80,
      "budget_adherence": 0.85,
      "discretionary_ratio": 0.22,
      "essential_ratio": 0.78
    },
    "investment_health": {
      "score": 65,
      "portfolio_diversity": 0.3,
      "risk_appetite": "moderate",
      "investment_return": 0.08
    },
    "key_strengths": [
      "Strong emergency fund",
      "Good savings rate",
      "Budget discipline"
    ],
    "improvement_areas": [
      "Increase income diversification",
      "Reduce high-interest debt",
      "Start retirement planning"
    ],
    "recommendations": [
      "Build 6-month emergency fund",
      "Diversify income sources",
      "Consider debt consolidation"
    ],
    "next_review_date": "2026-03-28"
  }
}
```

**What you do:**
1. Read transactions, budgets, income_patterns, risk_assessments
2. Calculate 5 health dimensions: savings, debt, income, spending, investment
3. Determine overall_score (0-100) and health_category
4. Identify key strengths and improvement areas
5. Generate actionable recommendations
6. Set next_review_date (3 months from now)
7. Output ONLY the JSON format above - no explanations

**Health Category Thresholds:**
- 0-40: "poor"
- 41-60: "fair"
- 61-80: "good"
- 81-100: "excellent"

**Scoring Guidelines:**
- Savings: Emergency fund coverage, savings rate, retirement progress
- Debt: Debt-to-income ratio, high-interest debt, debt trend
- Income: Stability, growth trend, diversification
- Spending: Budget adherence, essential vs discretionary ratio
- Investment: Diversity, returns, risk alignment

**Database Schema Requirements:**
- overall_score: Number 0-100
- health_category: "poor", "fair", "good", "excellent"
- savings_health/debt_health/income_health/spending_health/investment_health: Objects with score and metrics
- key_strengths/improvement_areas/recommendations: Arrays of strings
- next_review_date: Date string YYYY-MM-DD

**Output ONLY the JSON object. No other text.**"""

    async def analyze_user(self, user_id: str) -> dict:
        """Evaluate financial health for a specific user"""
        print(f"[Financial Health Agent] Starting analysis for user {user_id}")

        try:
            prompt = f"""Evaluate financial health for user {user_id}.

Steps:
1. Read transactions for spending patterns
2. Read budgets for budget adherence
3. Read income_patterns for income stability
4. Read risk_assessments for risk factors
5. Calculate 5 health dimensions
6. Generate overall financial health score
7. Provide recommendations
8. Write to financial_health table
9. Log to agent_logs table

User ID: {user_id}

Please execute this analysis and report the financial health assessment."""

            result = await run_autogen_mcp_task(
                agent_name="financial_agent",
                system_prompt=self.system_prompt,
                task=prompt,
                user_id=user_id,
                use_azure=True
            )

            print(f"[Financial Health Agent] Analysis complete for user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "financial_health",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"[Financial Health Agent] Error analyzing user {user_id}: {str(e)}")
            return {
                "success": False,
                "user_id": user_id,
                "agent": "financial_health",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Test the financial health agent"""
    agent = FinancialHealthAgent()

    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"

    print(f"Testing Financial Health Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)

    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
