"""
Core Upsonic investment workflow orchestration.

The workflow combines three Upsonic agents to:
1. Generate comprehensive market research.
2. Rank opportunities by investment potential.
3. Produce a portfolio allocation strategy.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from textwrap import dedent
from typing import Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from upsonic import Agent, Task
from upsonic.tools.common_tools import YFinanceTools

from .models import (
    InvestmentRanking,
    PortfolioAllocation,
    StockAnalysisResult,
    WorkflowRequest,
    WorkflowResult,
    WorkflowSummary,
)

load_dotenv()  # Load environment variables for API keys if available.

DEFAULT_REPORT_DIR = Path("reports/investment").absolute()


def _normalize_text_block(text: str) -> str:
    """Collapse awkward line breaks while preserving paragraphs and bullets."""

    if not text:
        return ""

    lines = text.splitlines()
    normalized: List[str] = []
    paragraph: List[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if not line.strip():
            if paragraph:
                normalized.append(" ".join(paragraph).strip())
                paragraph = []
            if normalized and normalized[-1] != "":
                normalized.append("")
            continue

        bullet_prefixes = ("- ", "* ", "+ ", "1. ", "2. ", "3. ", "4. ", "5. ")
        if line.lstrip().startswith(bullet_prefixes):
            if paragraph:
                normalized.append(" ".join(paragraph).strip())
                paragraph = []
            normalized.append(line.strip())
        else:
            paragraph.append(line.strip())

    if paragraph:
        normalized.append(" ".join(paragraph).strip())

    # Clean up the text
    cleaned: List[str] = []
    blank_pending = False
    for entry in normalized:
        if entry == "":
            if not blank_pending and cleaned:
                cleaned.append("")
            blank_pending = True
        else:
            cleaned.append(entry)
            blank_pending = False

    joined = "\n".join(cleaned).strip()

    joined = re.sub(r'([\w.,$%€£]+)\s+\1([\w.,$%€£]+)', r'\1\2', joined)

    joined = re.sub(r"([A-Za-z])(\d)", r"\1 \2", joined)
    joined = re.sub(r"(\d)([A-Za-z])", r"\1 \2", joined)

    joined = re.sub(r"(?<=\d)\s+(?=[A-Za-z$%])", "", joined)
    joined = re.sub(r"(?<=[$€£])\s+(?=\d)", "", joined)

    def _squash(match: re.Match[str]) -> str:
        return match.group(0).replace(" ", "")

    joined = re.sub(r"\b(?:[a-z]\s+){2,}[a-z]\b", _squash, joined)
    joined = re.sub(r"\b(?:[A-Z]\s+){2,}[A-Z]\b", _squash, joined)
    joined = re.sub(r"\s+([,.;:%])", r"\1", joined)
    joined = re.sub(r"([,.;:%])(?!\s)", r"\1 ", joined)
    joined = re.sub(r"\s{2,}", " ", joined)

    return joined.strip()

def _clean_stock_analysis(result: StockAnalysisResult) -> StockAnalysisResult:
    cleaned_companies: List[CompanyInsight] = []

    for company in result.companies:
        print(
            "[DEBUG] Raw financial_analysis for "
            f"{company.company_name} ({company.symbol}):\n"
            f"{company.financial_analysis}\n"
        )

        normalized_financials = _normalize_text_block(company.financial_analysis)

        print(
            "[DEBUG] Normalized financial_analysis for "
            f"{company.company_name} ({company.symbol}):\n"
            f"{normalized_financials}\n"
        )

        cleaned_companies.append(
            company.model_copy(
                update={
                    "market_research": _normalize_text_block(company.market_research),
                    "financial_analysis": normalized_financials,
                    "risk_assessment": _normalize_text_block(company.risk_assessment),
                }
            )
        )

    return result.model_copy(
        update={
            "overview": _normalize_text_block(result.overview),
            "companies": cleaned_companies,
            "key_recommendations": _normalize_text_block(result.key_recommendations),
        }
    )


def _clean_investment_ranking(ranking: InvestmentRanking) -> InvestmentRanking:
    return ranking.model_copy(
        update={
            "ranked_companies": _normalize_text_block(ranking.ranked_companies),
            "investment_rationale": _normalize_text_block(ranking.investment_rationale),
            "risk_evaluation": _normalize_text_block(ranking.risk_evaluation),
            "growth_potential": _normalize_text_block(ranking.growth_potential),
        }
    )


def _clean_portfolio_allocation(portfolio: PortfolioAllocation) -> PortfolioAllocation:
    return portfolio.model_copy(
        update={
            "allocation_strategy": _normalize_text_block(portfolio.allocation_strategy),
            "investment_thesis": _normalize_text_block(portfolio.investment_thesis),
            "risk_management": _normalize_text_block(portfolio.risk_management),
            "final_recommendations": _normalize_text_block(portfolio.final_recommendations),
        }
    )


def _render_stock_analysis_report(result: StockAnalysisResult) -> str:
    """Render a rich markdown report from the stock analysis stage."""
    lines: List[str] = [
        "# Stock Analyst Report",
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


def _render_investment_ranking_report(ranking: InvestmentRanking) -> str:
    return dedent(
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
    ).strip() + "\n"


def _render_portfolio_report(portfolio: PortfolioAllocation) -> str:
    return dedent(
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
    ).strip() + "\n"


def _summarize_workflow(symbols: Sequence[str], portfolio: PortfolioAllocation) -> WorkflowSummary:
    headline = dedent(
        f"""Completed investment workflow for {", ".join(symbols)}.
        Portfolio insight highlights:
        {portfolio.allocation_strategy.strip()}
        """
    ).strip()

    return WorkflowSummary(headline=headline)


class InvestmentWorkflow:
    """
    High-level facade around the Upsonic agent pipeline.

    The workflow is intentionally synchronous to prioritise clarity.
    Use `fastapi.concurrency.run_in_threadpool` when integrating with async code.
    """

    def __init__(
        self,
        *,
        reports_directory: Path = DEFAULT_REPORT_DIR,
        yfinance_tools: Optional[YFinanceTools] = None,
    ) -> None:
        self._reports_directory = reports_directory
        self._yfinance_tools = yfinance_tools or YFinanceTools(enable_all=True)
        self._yfinance_tools.enable_all_tools()
        self._stock_analyst = self._create_stock_analyst()
        self._research_analyst = self._create_research_analyst()
        self._investment_lead = self._create_investment_lead()

    # --- Agent definitions -------------------------------------------------

    @staticmethod
    def _create_stock_analyst() -> Agent:
        return Agent(
            name="Stock Analyst",
            model="openai/gpt-4o",
            instructions=dedent(
                """\
                You are MarketMaster-X, an elite Senior Investment Analyst at Goldman Sachs.
                Deliver deep market research, financial analysis, and risk assessment.
                """
            ),
        )

    @staticmethod
    def _create_research_analyst() -> Agent:
        return Agent(
            name="Research Analyst",
            model="openai/gpt-4o",
            instructions=dedent(
                """\
                You are ValuePro-X, Senior Research Analyst.
                Rank opportunities based on comparative strength, upside, and risk.
                """
            ),
        )

    @staticmethod
    def _create_investment_lead() -> Agent:
        return Agent(
            name="Investment Lead",
            model="openai/gpt-4o",
            instructions=dedent(
                """\
                You are PortfolioSage-X, Senior Investment Lead.
                Craft a diversified allocation strategy with clear rationale.
                """
            ),
        )

    # --- Core execution ----------------------------------------------------

    def run(
        self,
        symbols: Iterable[str] | WorkflowRequest,
        *,
        write_reports: bool | None = None,
    ) -> WorkflowResult:
        """
        Execute the full three-stage workflow.

        Args:
            symbols: Iterable of ticker symbols or a `WorkflowRequest`.
            write_reports: Overrides whether markdown reports are written to disk.
        """
        request = (
            symbols
            if isinstance(symbols, WorkflowRequest)
            else WorkflowRequest(symbols=list(symbols))
        )
        if write_reports is not None:
            request.write_reports = write_reports

        stock_analysis = self._run_stock_analysis(request.symbols)
        ranking = self._run_investment_ranking(stock_analysis)
        portfolio = self._run_portfolio_allocation(ranking)

        report_paths = (
            self._write_reports(stock_analysis, ranking, portfolio)
            if request.write_reports
            else None
        )

        summary = _summarize_workflow(request.symbols, portfolio)

        return WorkflowResult(
            symbols=request.symbols,
            stock_analysis=stock_analysis,
            investment_ranking=ranking,
            portfolio_allocation=portfolio,
            summary=summary,
            report_paths=report_paths,
        )

    # --- Stage helpers -----------------------------------------------------

    def _run_stock_analysis(self, symbols: Sequence[str]) -> StockAnalysisResult:
        prompt = dedent(
            f"""
            Perform comprehensive market research, financial analysis, and risk assessment
            for the following companies: {", ".join(symbols)}.

            Deliver a professional markdown report with the sections:
            - Overview (<=120 words)
            - Company breakdowns with market research, financial analysis, and risk insights
              • Each subsection should stay within 120 words and highlight no more than 3 bullet metrics
            - Key recommendations (<=80 words)

            Reminder: Educational purposes only.
            Format the response with concise paragraphs and bullet lists for key metrics.
            Keep financial figures on a single line (e.g., "$416B" rather than spreading characters).
            Highlight 3-5 quantitative data points per company using markdown bullets when possible.
            Total output should not exceed 600 words.
            """
        ).strip()

        task = Task(
            description=prompt,
            response_format=StockAnalysisResult,
            tools=[self._yfinance_tools],
        )
        return _clean_stock_analysis(self._stock_analyst.do(task))

    def _run_investment_ranking(
        self, stock_analysis: StockAnalysisResult
    ) -> InvestmentRanking:
        prompt = dedent(
            f"""
            Rank the analysed companies by investment potential using the data below.

            COMPANY SYMBOLS:
            {stock_analysis.company_symbols}

            COMPANY DETAILS:
            {"; ".join(f"{c.company_name} ({c.symbol})" for c in stock_analysis.companies)}

            KEY RECOMMENDATIONS:
            {stock_analysis.key_recommendations}

            Provide (each section <=120 words):
            1. Ranked list from strongest to weakest.
            2. Investment rationale for each position.
            3. Risk evaluation and mitigations.
            4. Growth potential analysis.
            Keep the overall response under 450 words with tight bullet formatting.
            """
        ).strip()

        task = Task(description=prompt, response_format=InvestmentRanking)
        return _clean_investment_ranking(self._research_analyst.do(task))

    def _run_portfolio_allocation(
        self, ranking: InvestmentRanking
    ) -> PortfolioAllocation:
        prompt = dedent(
            f"""
            Develop a portfolio allocation strategy using the ranking insights below.

            RANKED COMPANIES:
            {ranking.ranked_companies}

            INVESTMENT RATIONALE:
            {ranking.investment_rationale}

            RISK EVALUATION:
            {ranking.risk_evaluation}

            GROWTH POTENTIAL:
            {ranking.growth_potential}

            Output must cover (each section <=120 words, total <=450 words):
            - Allocation percentages (sum to 100%).
            - Investment thesis with catalysts.
            - Risk management approach and contingencies.
            - Final actionable recommendations with educational reminder.
            Use bullet lists where appropriate and keep figures on a single line.
            """
        ).strip()

        task = Task(description=prompt, response_format=PortfolioAllocation)
        return _clean_portfolio_allocation(self._investment_lead.do(task))

    # --- Report persistence ------------------------------------------------

    def _write_reports(
        self,
        stock: StockAnalysisResult,
        ranking: InvestmentRanking,
        portfolio: PortfolioAllocation,
    ) -> List[str]:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = self._reports_directory / timestamp
        directory.mkdir(parents=True, exist_ok=True)

        stock_path = directory / "stock_analyst_report.md"
        ranking_path = directory / "investment_ranking_report.md"
        portfolio_path = directory / "portfolio_allocation_report.md"

        stock_path.write_text(_render_stock_analysis_report(stock), encoding="utf-8")
        ranking_path.write_text(_render_investment_ranking_report(ranking), encoding="utf-8")
        portfolio_path.write_text(_render_portfolio_report(portfolio), encoding="utf-8")

        return [str(path) for path in (stock_path, ranking_path, portfolio_path)]

