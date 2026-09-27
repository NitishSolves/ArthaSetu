"""
Agent Monitoring Script
View what agents have pushed to the database
"""

import asyncio
import sys
from datetime import datetime, timedelta
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from autogen_runtime import run_autogen_mcp_task


class AgentMonitor:
    """Monitor what agents have written to the database"""

    def __init__(self, mcp_config_path: str = ".mcp.json"):
        self.mcp_config_path = mcp_config_path

    async def view_agent_logs(self, user_id: str = None, hours: int = 24):
        """
        View agent activity logs

        Args:
            user_id: Filter by specific user (optional)
            hours: Show logs from last N hours (default: 24)
        """
        system_prompt = """You are a monitoring assistant that queries the database to show agent activity.

Query the agent_logs table and present the results in a readable format.

Available MCP tools:
- mcp__supabase-postgres__postgrestRequest: Execute database queries"""

        user_filter = f"for user {user_id}" if user_id else "for all users"

        prompt = f"""Show agent activity logs {user_filter} from the last {hours} hours.

Query the agent_logs table and show:
- Timestamp
- Agent name
- User ID
- Action performed
- Status (success/failure)

Order by most recent first.

Present in a clear, readable table format."""

        result = await run_autogen_mcp_task(
            agent_name="monitor_agent_logs",
            system_prompt=system_prompt,
            task=prompt,
            mcp_config_path=self.mcp_config_path,
        )
        print(result)

    async def view_user_analysis(self, user_id: str):
        """
        View complete analysis results for a specific user

        Args:
            user_id: UUID of the user
        """
        system_prompt = """You are a monitoring assistant that shows what agents have written to the database.

Query multiple tables to show a complete picture of what analysis has been done.

Available MCP tools:
- mcp__supabase-postgres__postgrestRequest: Execute database queries"""

        prompt = f"""Show all analysis results for user {user_id}.

Query these tables and show what agents have written:

1. income_patterns:
   - Average income
   - Weekday patterns
   - Monthly trend
   - Confidence score

2. budgets:
   - Feast week budget
   - Famine week budget
   - Monthly budget
   - Category limits

3. income_forecasts:
   - Next 30-day prediction
   - Scenarios (pessimistic, realistic, optimistic)
   - Volatility index
   - Forecast confidence

4. risk_assessments:
   - Overall risk level
   - Risk score
   - Key risk factors
   - Escalation needed?

5. recommendations:
   - Top recommendations
   - Priority levels
   - Action items

6. tax_records:
   - Assessment year
   - Gross income
   - Tax liability
   - Filing status

7. user_schemes:
   - Matched government schemes
   - Eligibility status

8. executed_actions:
   - Scheduled actions
   - Status

Present in a well-organized, readable format with clear sections."""

        result = await run_autogen_mcp_task(
            agent_name="monitor_user_analysis",
            system_prompt=system_prompt,
            task=prompt,
            mcp_config_path=self.mcp_config_path,
        )
        print(result)

    async def view_table_summary(self):
        """View summary of what's in each analysis table"""
        system_prompt = """You are a monitoring assistant that shows database table summaries.

Available MCP tools:
- mcp__supabase-postgres__postgrestRequest: Execute database queries"""

        prompt = """Show a summary of all agent analysis tables:

For each table, show:
- Table name
- Record count
- Latest update timestamp
- Sample of recent records

Tables to check:
- income_patterns
- budgets
- income_forecasts
- risk_assessments
- recommendations
- tax_records
- user_schemes
- executed_actions
- action_outcomes
- agent_logs

Present as a clear summary."""

        result = await run_autogen_mcp_task(
            agent_name="monitor_table_summary",
            system_prompt=system_prompt,
            task=prompt,
            mcp_config_path=self.mcp_config_path,
        )
        print(result)

    async def view_recent_changes(self, minutes: int = 60):
        """
        View what agents pushed in the last N minutes

        Args:
            minutes: Show changes from last N minutes (default: 60)
        """
        system_prompt = """You are a monitoring assistant that shows recent database changes.

Available MCP tools:
- mcp__supabase-postgres__postgrestRequest: Execute database queries"""

        prompt = f"""Show what agents have pushed to the database in the last {minutes} minutes.

Check these tables for recent inserts/updates:
- income_patterns (last_updated column)
- budgets (created_at column)
- income_forecasts (created_at column)
- risk_assessments (assessment_date column)
- recommendations (created_at column)
- tax_records (created_at column)
- user_schemes (matched_at column)
- executed_actions (created_at column)
- agent_logs (created_at column)

For each recent change, show:
- Table name
- User ID
- What was written
- Timestamp

Present in chronological order (most recent first)."""

        result = await agent.run(prompt)
        print(result)


async def main():
    """Main entry point for the monitor"""
    monitor = AgentMonitor()

    if len(sys.argv) < 2:
        print("Agent Monitor - View what agents have pushed to the database")
        print("\nUsage:")
        print("  python monitor.py --user <user_id>              # View all analysis for a user")
        print("  python monitor.py --logs [user_id] [hours]      # View agent activity logs")
        print("  python monitor.py --summary                     # View table summary")
        print("  python monitor.py --recent [minutes]            # View recent changes")
        print("\nExamples:")
        print("  python monitor.py --user 153735c8-b1e3-4fc6-aa4e-7deb6454990b")
        print("  python monitor.py --logs")
        print("  python monitor.py --logs 153735c8-b1e3-4fc6-aa4e-7deb6454990b 48")
        print("  python monitor.py --summary")
        print("  python monitor.py --recent 30")
        return

    command = sys.argv[1]

    if command == "--user":
        if len(sys.argv) < 3:
            print("Error: User ID required")
            print("Usage: python monitor.py --user <user_id>")
            return
        user_id = sys.argv[2]
        await monitor.view_user_analysis(user_id)

    elif command == "--logs":
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
        await monitor.view_agent_logs(user_id, hours)

    elif command == "--summary":
        await monitor.view_table_summary()

    elif command == "--recent":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        await monitor.view_recent_changes(minutes)

    else:
        print(f"Unknown command: {command}")
        print("Run 'python monitor.py' for usage help")


if __name__ == "__main__":
    asyncio.run(main())
