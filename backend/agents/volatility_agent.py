"""
Volatility Forecaster Agent
Computes pessimistic/realistic/optimistic income scenarios from the
statistical spread of real historical transactions (see
finance_helpers.compute_volatility_forecast) -- one consistent schema, not
the two contradictory ones the original LLM-only prompt had. The LLM is
only used for a one-line trend narrative.
Writes to: income_forecasts table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    compute_income_expense_stats,
    compute_volatility_forecast,
    generate_narrative,
    write_record,
)

logger = logging.getLogger(__name__)


class VolatilityForecasterAgent:
    """Forecasts near-term income scenarios from real transaction volatility."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Volatility Agent] Starting analysis for user {user_id}")

        try:
            transactions = fetch_transactions(user_id, days=90)
            stats = compute_income_expense_stats(transactions)
            forecast = compute_volatility_forecast(stats)

            narrative = await generate_narrative(
                system_prompt=(
                    "You are an income forecasting assistant for Indian gig workers. "
                    "Given real computed forecast numbers, explain what to expect "
                    "next week in 1-2 short plain-language sentences."
                ),
                user_prompt=(
                    f"Realistic weekly income forecast: Rs {forecast['realistic_scenario']['weekly_income']}, "
                    f"range Rs {forecast['forecast_range_min']} to Rs {forecast['forecast_range_max']}. "
                    f"Trend: {forecast['recent_trend']}."
                ),
                max_tokens=200,
            )
            forecast["ai_reasoning"] = narrative

            record = {**forecast, "user_id": user_id}
            written = write_record("income_forecasts", record)
            logger.info(f"[Volatility Agent] Created income forecast, trend: {forecast['recent_trend']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "volatility_forecaster",
                "result": written,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Volatility Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "volatility_forecaster",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = VolatilityForecasterAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Volatility Forecaster Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
