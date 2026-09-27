"""
Background Scheduler Service
Runs all 9 agents periodically for active users
"""

import asyncio
import json
from datetime import datetime
from typing import List
import sys

# Import all agents
from pattern_agent import PatternRecognitionAgent
from budget_agent import BudgetAnalysisAgent
from context_agent import ContextIntelligenceAgent
from volatility_agent import VolatilityForecasterAgent
from knowledge_agent import KnowledgeIntegrationAgent
from tax_agent import TaxComplianceAgent
from recommendation_agent import RecommendationAgent
from risk_agent import RiskAssessmentAgent
from action_agent import ActionExecutionAgent


class AgentScheduler:
    """Coordinates periodic execution of all 9 financial agents"""

    def __init__(self, mcp_config_path: str = ".mcp.json"):
        self.mcp_config_path = mcp_config_path

        # Initialize all 9 agents
        self.agents = {
            "pattern": PatternRecognitionAgent(mcp_config_path),
            "budget": BudgetAnalysisAgent(mcp_config_path),
            "context": ContextIntelligenceAgent(mcp_config_path),
            "volatility": VolatilityForecasterAgent(mcp_config_path),
            "knowledge": KnowledgeIntegrationAgent(mcp_config_path),
            "tax": TaxComplianceAgent(mcp_config_path),
            "recommendation": RecommendationAgent(mcp_config_path),
            "risk": RiskAssessmentAgent(mcp_config_path),
            "action": ActionExecutionAgent(mcp_config_path)
        }

    async def run_all_agents(self, user_id: str) -> dict:
        """
        Run all 9 agents for a specific user in sequence

        Args:
            user_id: UUID of the user to analyze

        Returns:
            dict with results from all agents
        """
        print(f"\n{'='*60}")
        print(f"Starting complete analysis for user {user_id}")
        print(f"{'='*60}\n")

        results = {
            "user_id": user_id,
            "analysis_started": datetime.now().isoformat(),
            "agents": {}
        }

        # Run agents in order (some depend on others)
        # 1. Pattern Recognition (foundation)
        print("[1/9] Running Pattern Recognition Agent...")
        results["agents"]["pattern"] = await self.agents["pattern"].analyze_user(user_id)
        await asyncio.sleep(2)  # Brief pause between agents

        # 2. Context Intelligence (enriches patterns)
        print("\n[2/9] Running Context Intelligence Agent...")
        results["agents"]["context"] = await self.agents["context"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 3. Volatility Forecaster (needs patterns)
        print("\n[3/9] Running Volatility Forecaster Agent...")
        results["agents"]["volatility"] = await self.agents["volatility"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 4. Budget Analysis (needs patterns and forecasts)
        print("\n[4/9] Running Budget Analysis Agent...")
        results["agents"]["budget"] = await self.agents["budget"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 5. Knowledge Integration (independent)
        print("\n[5/9] Running Knowledge Integration Agent...")
        results["agents"]["knowledge"] = await self.agents["knowledge"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 6. Tax & Compliance (needs income data)
        print("\n[6/9] Running Tax & Compliance Agent...")
        results["agents"]["tax"] = await self.agents["tax"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 7. Risk Assessment (needs all financial data)
        print("\n[7/9] Running Risk Assessment Agent...")
        results["agents"]["risk"] = await self.agents["risk"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 8. Recommendation Engine (needs everything)
        print("\n[8/9] Running Recommendation Engine Agent...")
        results["agents"]["recommendation"] = await self.agents["recommendation"].analyze_user(user_id)
        await asyncio.sleep(2)

        # 9. Action Execution (needs recommendations)
        print("\n[9/9] Running Action Execution Agent...")
        results["agents"]["action"] = await self.agents["action"].analyze_user(user_id)

        results["analysis_completed"] = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print(f"Analysis complete for user {user_id}")
        print(f"{'='*60}\n")

        return results

    async def run_parallel_agents(self, user_ids: List[str]) -> List[dict]:
        """
        Run analysis for multiple users in parallel

        Args:
            user_ids: List of user UUIDs to analyze

        Returns:
            List of results for each user
        """
        print(f"\nStarting parallel analysis for {len(user_ids)} users...")

        tasks = [self.run_all_agents(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def scheduled_run(self, interval_seconds: int = 3600):
        """
        Run scheduler in a loop with specified interval

        Args:
            interval_seconds: Time between runs (default: 3600 = 1 hour)
        """
        print(f"Starting scheduled service (interval: {interval_seconds}s)")

        # For MVP, we'll use a hardcoded list of users
        # In production, this would query the database for active users
        active_users = [
            "153735c8-b1e3-4fc6-aa4e-7deb6454990b"  # Test user
        ]

        while True:
            try:
                print(f"\n[{datetime.now().isoformat()}] Starting scheduled analysis cycle...")

                for user_id in active_users:
                    await self.run_all_agents(user_id)

                print(f"\n[{datetime.now().isoformat()}] Cycle complete. Sleeping for {interval_seconds}s...")
                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\nScheduler stopped by user")
                break
            except Exception as e:
                print(f"\nError in scheduled cycle: {str(e)}")
                print(f"Retrying in {interval_seconds}s...")
                await asyncio.sleep(interval_seconds)


async def main():
    """Main entry point for the scheduler"""
    scheduler = AgentScheduler()

    # Check if running in scheduled mode or one-time mode
    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheduled":
            # Run as background service
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
            await scheduler.scheduled_run(interval_seconds=interval)
        elif sys.argv[1] == "--user":
            # Run for specific user
            user_id = sys.argv[2]
            result = await scheduler.run_all_agents(user_id)
            print("\nFinal Result:")
            print(json.dumps(result, indent=2))
        else:
            print("Usage:")
            print("  python scheduler.py --user <user_id>          # Run once for specific user")
            print("  python scheduler.py --scheduled [interval]    # Run as background service")
    else:
        # Default: run once for test user
        test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
        result = await scheduler.run_all_agents(test_user_id)
        print("\nFinal Result:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
