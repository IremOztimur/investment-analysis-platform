"""
💰 Investment Report Generator - Upsonic Workflow

This script demonstrates how to build a multi-stage investment analysis pipeline with Upsonic agents.
The workflow delivers:
1. Comprehensive stock analysis and market research
2. Investment potential evaluation and ranking
3. Strategic portfolio allocation recommendations

Dependencies:
    pip install upsonic yfinance pydantic

Ensure the OPENAI_API_KEY environment variable is set before running the script.
"""

import datetime
import random
from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from typing import Dict, List, Tuple

import yfinance as yf
from pydantic import BaseModel
from upsonic import Agent, Task
from dotenv import load_dotenv

load_dotenv()

# --- Example scenarios for user convenience ---
EXAMPLE_SCENARIOS = [
    "AAPL, MSFT, GOOGL",  # Tech Giants
    "NVDA, AMD, INTC",  # Semiconductor Leaders
    "TSLA, F, GM",  # Automotive Innovation
    "JPM, BAC, GS",  # Banking Sector
    "AMZN, WMT, TGT",  # Retail Competition
    "PFE, JNJ, MRNA",  # Healthcare Focus
    "XOM, CVX, BP",  # Energy Sector
]

ANALYSIS_MESSAGE = (
    "Generate comprehensive investment analysis and portfolio allocation recommendations."
)

REPORTS_DIR = Path(__file__).parent.joinpath("reports", "investment")
STOCK_ANALYST_REPORT = REPORTS_DIR.joinpath("stock_analyst_report.md")
RESEARCH_ANALYST_REPORT = REPORTS_DIR.joinpath("research_analyst_report.md")
INVESTMENT_REPORT = REPORTS_DIR.joinpath("investment_report.md")


# --- Response models ---
class CompanyInsight(BaseModel):
    symbol: str
    company_name: str
    market_research: str
    financial_analysis: str
    risk_assessment: str


class StockAnalysisResult(BaseModel):
    overview: str
    company_symbols: str
    companies: List[CompanyInsight]
    key_recommendations: str


class InvestmentRanking(BaseModel):
    ranked_companies: str
    investment_rationale: str
    risk_evaluation: str
    growth_potential: str


class PortfolioAllocation(BaseModel):
    allocation_strategy: str
    investment_thesis: str
    risk_management: str
    final_recommendations: str


# --- Helpers for market data ---
def reset_reports_directory() -> None:
    if REPORTS_DIR.exists():
        rmtree(REPORTS_DIR, ignore_errors=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_stock_data(ticker: str, period: str = "6mo") -> Dict[str, object]:
    symbol = ticker.upper()
    ticker_obj = yf.Ticker(symbol)
    history = ticker_obj.history(period=period)

    if history.empty:
        raise ValueError(f"No price history found for {symbol}")

    info = getattr(ticker_obj, "info", {}) or {}

    return {
        "ticker": symbol,
        "company_name": info.get("shortName", symbol),
        "sector": info.get("sector", "N/A"),
        "current_price": float(history["Close"].iloc[-1]),
        "average_price": float(history["Close"].mean()),
        "volatility": float(history["Close"].std()),
        "high_6m": float(history["High"].max()),
        "low_6m": float(history["Low"].min()),
        "data_points": int(len(history)),
    }


def collect_market_snapshots(symbols: List[str]) -> Tuple[List[Dict[str, object]], List[str]]:
    snapshots: List[Dict[str, object]] = []
    errors: List[str] = []

    for symbol in symbols:
        try:
            snapshots.append(fetch_stock_data(symbol))
        except Exception as exc:  # pylint: disable=broad-except
            errors.append(f"{symbol.upper()}: {exc}")

    return snapshots, errors


def build_snapshot_markdown(snapshots: List[Dict[str, object]]) -> str:
    blocks = []
    for entry in snapshots:
        blocks.append(
            dedent(
                f"""
                ### {entry['company_name']} ({entry['ticker']})
                - Sector: {entry['sector']}
                - Current Price: ${entry['current_price']:.2f}
                - 6-Month Average Price: ${entry['average_price']:.2f}
                - 6-Month Volatility (σ): {entry['volatility']:.2f}
                - 6-Month High: ${entry['high_6m']:.2f}
                - 6-Month Low: ${entry['low_6m']:.2f}
                - Observations: {entry['data_points']} trading days analyzed
                """
            ).strip()
        )
    return "\n\n".join(blocks)


def build_snapshot_text(snapshots: List[Dict[str, object]]) -> str:
    lines = []
    for entry in snapshots:
        lines.append(
            dedent(
                f"""
                Company: {entry['company_name']} ({entry['ticker']})
                Sector: {entry['sector']}
                Current Price: ${entry['current_price']:.2f}
                6-Month Average: ${entry['average_price']:.2f}
                Volatility (σ): {entry['volatility']:.2f}
                6-Month High/Low: ${entry['high_6m']:.2f} / ${entry['low_6m']:.2f}
                Sample Size: {entry['data_points']} trading days
                """
            ).strip()
        )
    return "\n\n".join(lines)


# --- Presentation helpers ---
def render_stock_analysis_report(result: StockAnalysisResult) -> str:
    lines = [
        "## Stock Analyst Report",
        "",
        "# Comprehensive Market Analysis Report",
        "",
        "## Overview",
        "",
        result.overview.strip(),
        "",
        "---",
    ]

    for index, company in enumerate(result.companies):
        if index > 0:
            lines.append("")
        lines.extend(
            [
                f"## {company.company_name} ({company.symbol})",
                "",
                "### Market Research 📊",
                "",
                company.market_research.strip(),
                "",
                "### Financial Analysis 💹",
                "",
                company.financial_analysis.strip(),
                "",
                "### Risk Assessment 🎯",
                "",
                company.risk_assessment.strip(),
                "",
                "---",
            ]
        )

    lines.extend(
        [
            "",
            "## Key Recommendations",
            "",
            result.key_recommendations.strip(),
        ]
    )

    return "\n".join(lines).strip() + "\n"


def summarize_companies_for_prompt(result: StockAnalysisResult) -> str:
    sections = []
    for company in result.companies:
        sections.append(
            dedent(
                f"""
                Company: {company.company_name} ({company.symbol})
                Market Research: {company.market_research}
                Financial Analysis: {company.financial_analysis}
                Risk Assessment: {company.risk_assessment}
                """
            ).strip()
        )
    return "\n\n".join(sections)


# --- Agent definitions ---
stock_analyst = Agent(
    name="Stock Analyst",
    model="openai/gpt-4o",
    instructions=dedent(
        """\
        You are MarketMaster-X, an elite Senior Investment Analyst at Goldman Sachs with expertise in:
        - Comprehensive market analysis
        - Financial statement evaluation
        - Industry trend identification
        - News impact assessment
        - Risk factor analysis
        - Growth potential evaluation

        Follow this process:
        1. Market Research 📊
           - Analyze fundamentals and recent performance
           - Evaluate competitive positioning and industry context
           - Incorporate relevant macro or news factors
        2. Financial Analysis 💹
           - Highlight key financial ratios and trends
           - Describe analyst sentiment and catalysts
           - Identify strengths and pressure points
        3. Risk Assessment 🎯
           - Assess market, sector, and company-specific risks
           - Call out red flags and mitigation approaches

        Produce professional research for educational purposes only.
        """
    ),
)

research_analyst = Agent(
    name="Research Analyst",
    model="openai/gpt-4o",
    instructions=dedent(
        """\
        You are ValuePro-X, a Senior Research Analyst at Goldman Sachs specializing in:
        - Investment opportunity evaluation
        - Comparative company analysis
        - Risk-reward assessment
        - Growth potential ranking

        Workflow:
        1. Investment Analysis 🔍
           - Evaluate each company's upside potential
           - Compare valuations and competitive positioning
        2. Risk Evaluation 📈
           - Analyze risk factors and market sensitivity
           - Consider execution, financial, and macro risks
        3. Company Ranking 🏆
           - Rank companies from strongest to weakest opportunity
           - Provide detailed rationale tied to risk-adjusted returns
        """
    ),
)

investment_lead = Agent(
    name="Investment Lead",
    model="openai/gpt-4o",
    instructions=dedent(
        """\
        You are PortfolioSage-X, a Senior Investment Lead at Goldman Sachs focused on:
        - Portfolio strategy development
        - Asset allocation optimization
        - Risk management frameworks

        Execute the following:
        1. Portfolio Strategy 💼
           - Recommend allocation percentages
           - Balance diversification with conviction
        2. Investment Rationale 📝
           - Justify each allocation with insights and catalysts
           - Highlight how risks are mitigated
        3. Recommendation Delivery 📊
           - Deliver actionable guidance with clear next steps
           - Emphasize educational-use disclaimer
        """
    ),
)


# --- Workflow steps ---
def run_stock_analysis(message: str, symbols: List[str], snapshots: List[Dict[str, object]]) -> StockAnalysisResult:
    prompt = dedent(
        f"""
        {message}

        Analyze the following companies: {", ".join(symbols)}.

        Quantitative market snapshots:
        {build_snapshot_text(snapshots)}

        Requirements:
        - Return JSON that matches the StockAnalysisResult schema.
        - `overview`: 3-5 sentences summarizing broad themes across all companies.
        - `company_symbols`: Comma-separated symbols in the same order as provided.
        - `companies`: One entry per company with fields:
            * `symbol`: Uppercase ticker.
            * `company_name`: Proper company name.
            * `market_research`: Bullet-style or paragraph summary of market positioning, industry trends, market cap, price range.
            * `financial_analysis`: Include notable financial ratios, revenue/growth drivers, analyst sentiment.
            * `risk_assessment`: Identify key risks across market, company-specific, and macro factors.
        - `key_recommendations`: Concise actionable guidance synthesizing opportunities and watch items.
        - Use vivid yet professional tone; keep each section tightly focused.
        """
    ).strip()

    task = Task(description=prompt, response_format=StockAnalysisResult)
    return stock_analyst.do(task)


def run_investment_ranking(stock_analysis: StockAnalysisResult) -> InvestmentRanking:
    company_details = summarize_companies_for_prompt(stock_analysis)
    symbols_csv = stock_analysis.company_symbols
    prompt = dedent(
        f"""
        Based on the comprehensive stock analysis below, rank the companies by investment potential.

        COMPANY SYMBOLS:
        {symbols_csv}

        COMPANY DETAILS:
        {company_details}

        KEY RECOMMENDATIONS:
        {stock_analysis.key_recommendations}

        Deliverables:
        1. Ranked list from strongest to weakest opportunity.
        2. Investment rationale for each position.
        3. Risk evaluation and mitigation considerations.
        4. Growth potential analysis.
        """
    ).strip()

    task = Task(description=prompt, response_format=InvestmentRanking)
    return research_analyst.do(task)


def run_portfolio_allocation(ranking: InvestmentRanking) -> PortfolioAllocation:
    prompt = dedent(
        f"""
        Develop a strategic portfolio allocation using the analysis below.

        COMPANY RANKINGS:
        {ranking.ranked_companies}

        INVESTMENT RATIONALE:
        {ranking.investment_rationale}

        RISK EVALUATION:
        {ranking.risk_evaluation}

        GROWTH POTENTIAL:
        {ranking.growth_potential}

        Provide:
        1. Allocation percentages for each company (sum to 100%).
        2. Investment thesis supporting the strategy.
        3. Risk management approach and contingencies.
        4. Final actionable recommendations and reminders.
        """
    ).strip()

    task = Task(description=prompt, response_format=PortfolioAllocation)
    return investment_lead.do(task)


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"✅ Report saved to {path}")


def summarize_workflow(symbols: List[str], portfolio: PortfolioAllocation) -> str:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return dedent(
        f"""
        🎉 INVESTMENT ANALYSIS WORKFLOW COMPLETED!

        Timestamp: {timestamp}
        Companies Analyzed: {", ".join(symbols)}

        Key Portfolio Insight:
        {portfolio.allocation_strategy}

        Disclaimer: Educational purposes only. Not financial advice.
        """
    ).strip()


def prompt_for_companies() -> List[str]:
    suggestion = random.choice(EXAMPLE_SCENARIOS)
    raw_input_value = input(
        f"Enter company symbols (comma-separated) [press Enter for suggestion {suggestion}]: "
    ).strip()
    if not raw_input_value:
        raw_input_value = suggestion
    symbols = [symbol.strip().upper() for symbol in raw_input_value.split(",") if symbol.strip()]
    return symbols


def main() -> None:
    print("Upsonic Investment Analysis Workflow")
    symbols = prompt_for_companies()

    if not symbols:
        print("❌ No company symbols provided. Exiting.")
        return

    print(f"\n🚀 Starting investment analysis for: {', '.join(symbols)}")
    reset_reports_directory()

    snapshots, errors = collect_market_snapshots(symbols)
    if errors:
        print("\n⚠️ Data retrieval issues:")
        for err in errors:
            print(f"   - {err}")

    if not snapshots:
        print("❌ Unable to retrieve market data for the provided symbols.")
        return

    print("\n📊 PHASE 1: COMPREHENSIVE STOCK ANALYSIS")
    stock_analysis = run_stock_analysis(ANALYSIS_MESSAGE, symbols, snapshots)

    write_report(STOCK_ANALYST_REPORT, render_stock_analysis_report(stock_analysis))

    print("\n🏆 PHASE 2: INVESTMENT POTENTIAL RANKING")
    ranking = run_investment_ranking(stock_analysis)

    write_report(
        RESEARCH_ANALYST_REPORT,
        dedent(
            f"""# Investment Ranking Report

            ## Company Rankings
            {ranking.ranked_companies}

            ## Investment Rationale
            {ranking.investment_rationale}

            ## Risk Evaluation
            {ranking.risk_evaluation}

            ## Growth Potential
            {ranking.growth_potential}
            """
        ).strip()
        + "\n",
    )

    print("\n💼 PHASE 3: PORTFOLIO ALLOCATION STRATEGY")
    portfolio = run_portfolio_allocation(ranking)

    write_report(
        INVESTMENT_REPORT,
        dedent(
            f"""# Investment Portfolio Report

            ## Allocation Strategy
            {portfolio.allocation_strategy}

            ## Investment Thesis
            {portfolio.investment_thesis}

            ## Risk Management
            {portfolio.risk_management}

            ## Final Recommendations
            {portfolio.final_recommendations}
            """
        ).strip()
        + "\n",
    )

    print("\n" + summarize_workflow(symbols, portfolio))
    print("\n📁 Reports directory:", REPORTS_DIR)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ An error occurred: {exc}")
