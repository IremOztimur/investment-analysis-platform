from upsonic_investment_generator.models import WorkflowRequest
from upsonic_investment_generator.models import (
    CompanyInsight,
    InvestmentRanking,
    PortfolioAllocation,
    StockAnalysisResult,
    WorkflowResult,
    WorkflowSummary,
)
import datetime as dt


def test_workflow_request_normalizes_symbols():
    request = WorkflowRequest(symbols=[" aapl", "msft "])
    assert request.symbols == ["AAPL", "MSFT"]


def test_workflow_request_requires_symbols():
    try:
        WorkflowRequest(symbols=["  "])
    except ValueError as exc:
        assert "At least one ticker symbol is required" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for empty symbols input")


def test_workflow_request_defaults_write_reports_to_false():
    request = WorkflowRequest(symbols=["AAPL"])
    assert request.write_reports is False


def test_workflow_summary_defaults_to_utc_timestamp():
    summary = WorkflowSummary(headline="Test summary")
    assert summary.generated_at.tzinfo is dt.timezone.utc
    assert summary.reminder == "Educational purposes only. Not financial advice."


def test_workflow_result_preserves_nested_models_and_reports():
    company = CompanyInsight(
        symbol="AAPL",
        company_name="Apple Inc.",
        market_research="Market research",
        financial_analysis="Financial analysis",
        risk_assessment="Risk assessment",
    )
    stock_analysis = StockAnalysisResult(
        overview="Overview",
        company_symbols="AAPL",
        companies=[company],
        key_recommendations="Key recommendations",
    )
    ranking = InvestmentRanking(
        ranked_companies="1. AAPL",
        investment_rationale="Rationale",
        risk_evaluation="Risks",
        growth_potential="Growth",
    )
    portfolio = PortfolioAllocation(
        allocation_strategy="60% AAPL",
        investment_thesis="Thesis",
        risk_management="Risk",
        final_recommendations="Final",
    )
    summary = WorkflowSummary(headline="Summary")

    result = WorkflowResult(
        symbols=["AAPL"],
        stock_analysis=stock_analysis,
        investment_ranking=ranking,
        portfolio_allocation=portfolio,
        summary=summary,
        report_paths=["/tmp/report.md"],
    )

    assert result.report_paths == ["/tmp/report.md"]
    assert result.stock_analysis.companies[0].symbol == "AAPL"
    assert result.summary is summary

