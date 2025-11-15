"""
Command-line interface for running the Upsonic investment workflow.
"""

from __future__ import annotations

import argparse
from typing import List

from .workflow import InvestmentWorkflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Upsonic investment workflow from the command line."
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        help="Ticker symbols to analyse (e.g. AAPL MSFT NVDA).",
    )
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="Persist markdown reports to ./reports/investment.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbols: List[str] = [symbol.upper() for symbol in args.symbols]

    if not symbols:
        raise SystemExit(
            "Provide at least one ticker symbol, e.g. `python -m upsonic_investment_generator AAPL`."
        )

    workflow = InvestmentWorkflow()
    result = workflow.run(symbols, write_reports=args.write_reports)

    print(result.summary.headline)
    if result.report_paths:
        print("Reports saved to:")
        for path in result.report_paths:
            print(f" - {path}")

