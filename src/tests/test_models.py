from upsonic_investment_generator.models import WorkflowRequest


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

