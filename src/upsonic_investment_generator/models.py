"""
Domain models shared across the Upsonic investment workflow, API, and UI.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class CompanyInsight(BaseModel):
    symbol: str = Field(..., description="Ticker symbol in uppercase.")
    company_name: str = Field(..., description="Common name of the company.")
    market_research: str = Field(..., description="Narrative market assessment.")
    financial_analysis: str = Field(..., description="Financial statement insights.")
    risk_assessment: str = Field(..., description="Key risks and mitigations.")


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


class WorkflowSummary(BaseModel):
    generated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )
    headline: str
    reminder: str = "Educational purposes only. Not financial advice."


class WorkflowResult(BaseModel):
    symbols: List[str]
    stock_analysis: StockAnalysisResult
    investment_ranking: InvestmentRanking
    portfolio_allocation: PortfolioAllocation
    summary: WorkflowSummary
    report_paths: Optional[List[str]] = Field(
        default=None, description="Absolute paths to written markdown reports."
    )


class WorkflowRequest(BaseModel):
    symbols: List[str] = Field(
        ..., min_items=1, description="List of ticker symbols to analyze."
    )
    write_reports: bool = Field(
        default=False, description="Persist markdown reports to disk."
    )

    @validator("symbols")
    def normalize_symbols(cls, value: List[str]) -> List[str]:
        normalized = [symbol.strip().upper() for symbol in value if symbol.strip()]
        if not normalized:
            raise ValueError("At least one ticker symbol is required.")
        return normalized

