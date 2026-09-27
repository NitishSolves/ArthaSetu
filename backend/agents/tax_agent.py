"""
Tax and Compliance Agent
Calculates gig-worker tax liability under the presumptive taxation scheme
using the same New Regime FY 2024-25 slabs + Section 87A rebate logic as
frontend/src/pages/Tax.tsx's calculator (see finance_helpers.compute_gig_worker_tax)
-- deterministic tax-slab arithmetic, not an LLM re-deriving tax law. The
LLM is only used for a short filing-suggestions narrative.
Writes to: tax_records table
"""

import asyncio
import json
import logging
from datetime import datetime

from finance_helpers import (
    fetch_transactions,
    fetch_profile,
    compute_gig_worker_tax,
    generate_narrative,
    write_record,
)

logger = logging.getLogger(__name__)


def _current_financial_year() -> str:
    """Indian FY runs April-March, e.g. Aug 2026 -> "2026-27"."""
    now = datetime.now()
    start_year = now.year if now.month >= 4 else now.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


class TaxComplianceAgent:
    """Calculates presumptive-scheme tax liability for a gig worker from real income."""

    def __init__(self, mcp_servers: str = ".mcp.json"):
        self.mcp_servers = mcp_servers

    async def analyze_user(self, user_id: str) -> dict:
        logger.info(f"[Tax Agent] Starting analysis for user {user_id}")

        try:
            # Full financial year of income, not the shorter 90-day window
            # other agents use -- tax is computed on annual income.
            transactions = fetch_transactions(user_id, days=365)
            gross_income = sum(
                float(t["amount"]) for t in transactions if t.get("transaction_type") == "income"
            )
            fetch_profile(user_id)  # not currently used for tax, kept for future deduction logic

            tax = compute_gig_worker_tax(gross_gig_income=gross_income, presumptive_rate=0.06, tds_deducted=0)

            narrative = await generate_narrative(
                system_prompt=(
                    "You are a tax assistant for Indian gig workers filing under "
                    "presumptive taxation (Section 44AD/44ADA). Given real computed "
                    "figures, give 1-2 short plain-language filing suggestions. "
                    "Do not invent numbers beyond what is given."
                ),
                user_prompt=(
                    f"Gross annual gig income: Rs {tax['gross_income']}. "
                    f"Taxable income under 6% presumptive rate: Rs {tax['taxable_income']}. "
                    f"Total tax liability after cess: Rs {tax['total_tax_liability']}. "
                    f"Tax-free: {tax['is_tax_free']}."
                ),
                max_tokens=200,
            )

            record = {
                "user_id": user_id,
                "financial_year": _current_financial_year(),
                "gross_income": tax["gross_income"],
                "income_by_source": {"gig_work": tax["gross_income"]},
                "total_deductions": 0,
                "deduction_details": {"presumptive_scheme": "44AD/44ADA at 6% of gross receipts"},
                "taxable_income": tax["taxable_income"],
                "tax_liability": tax["total_tax_liability"],
                "tax_paid": tax["tds_deducted"],
                "refund_amount": tax["refund_amount"],
                "itr_form_type": tax["itr_form_type"],
                "filing_status": "not_filed",
            }
            written = write_record("tax_records", record)
            logger.info(f"[Tax Agent] Created tax record for FY {record['financial_year']}: "
                        f"liability Rs {tax['total_tax_liability']}")

            return {
                "success": True,
                "user_id": user_id,
                "agent": "tax_compliance",
                "result": {**written, "narrative": narrative},
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Tax Agent] Error analyzing user {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "agent": "tax_compliance",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


async def main():
    agent = TaxComplianceAgent()
    test_user_id = "153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    print(f"Testing Tax Compliance Agent with user {test_user_id}")
    result = await agent.analyze_user(test_user_id)
    print("\nResult:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
