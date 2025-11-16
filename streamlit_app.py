"""
Streamlit dashboard for interacting with the Upsonic investment workflow.

Run with:
    uv run streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
from typing import Iterable, List

import re
import requests
import streamlit as st
from ftfy import fix_text

DEFAULT_API_URL = os.getenv("UPSONIC_API_URL", "http://localhost:8000")


def _call_api(symbols: List[str], write_reports: bool) -> dict:
    payload = {"symbols": symbols, "write_reports": write_reports}
    response = requests.post(f"{DEFAULT_API_URL}/analyze", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


_BULLET_CHARS = ("•", "◦", "▪", "‣", "⁃", "∙", "●", "○")
_STANDARD_LIST_PREFIXES = ("- ", "* ", "+ ")
_BULLET_REGEX = "[" + "".join(_BULLET_CHARS) + "]"
_INLINE_BULLET_PATTERN = re.compile(
    rf"(?<!\n)(?<!^)\s*({_BULLET_REGEX})\s+", flags=re.MULTILINE
)


def _normalize_bullet_line(line: str) -> str:
    stripped = line.lstrip()
    for bullet in _BULLET_CHARS:
        if stripped.startswith(bullet):
            remainder = stripped[len(bullet) :]
            if remainder and not remainder[0].isspace():
                continue
            indent = len(line) - len(stripped)
            return " " * indent + "- " + remainder.lstrip()
    return line


def _separate_inline_bullets(text: str) -> str:
    return _INLINE_BULLET_PATTERN.sub(
        lambda match: f"\n{match.group(1)} ",
        text,
    )


def _is_list_item(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith(_STANDARD_LIST_PREFIXES):
        return True
    if stripped and stripped[0] in _BULLET_CHARS:
        return True
    return bool(
        re.match(r"^\d+\.\s", stripped)
        or stripped.startswith("#")
    )


def _clean_line(line: str) -> str:
    line = _normalize_bullet_line(line)
    line = line.strip()
    line = re.sub(r"(?<=\d)\s+(?=[A-Za-z$€£%])", "", line)
    line = re.sub(r"([$€£])\s+(?=\d)", r"\1", line)
    line = re.sub(r"(\d)\s+(?=\d)", r"\1", line)
    line = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", line)
    line = re.sub(r"\s+([,.;:%])", r"\1", line)
    line = re.sub(r"(?<=[,.;:%])\s+(\*\*|__)", r"\1", line)
    line = re.sub(r"([,.;:%])(?!\s|$|[*_])", r"\1 ", line)
    line = re.sub(r"\s{2,}", " ", line)
    return line.strip()


def _format_text_block(text: str) -> str:
    """Tidy agent markdown by collapsing stray newlines inside sentences."""

    if not text:
        return ""

    text = fix_text(text, normalization="NFKC")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _separate_inline_bullets(text)

    blocks: List[str] = []
    for raw_block in re.split(r"\n{2,}", text):
        raw_lines = [ln for ln in raw_block.split("\n") if ln.strip()]
        lines = [_normalize_bullet_line(ln) for ln in raw_lines]
        if not lines:
            continue

        if any(_is_list_item(ln) for ln in lines):
            cleaned_lines = [_clean_line(ln) for ln in lines if ln.strip()]
            blocks.append("\n".join(cleaned_lines))
        else:
            paragraph = " ".join(_clean_line(ln) for ln in lines)
            blocks.append(paragraph.strip())

    formatted = "\n\n".join(blocks)
    formatted = re.sub(r"\s{2,}", " ", formatted)
    formatted = re.sub(r"(?<!\\)\$", r"\\$", formatted)

    return formatted.strip()


st.set_page_config(
    page_title="Upsonic Investment Intelligence",
    page_icon="💹",
    layout="wide",
)

st.title("💹 Upsonic Investment Intelligence")
st.caption(
    "Three-stage investment insights powered by Upsonic agents. "
    "Provide a set of ticker symbols to receive market research, rankings, "
    "and portfolio guidance."
)

symbols_input = st.text_input(
    "Ticker symbols",
    placeholder="AAPL, MSFT, NVDA",
    help="Provide comma-separated tickers. Minimum of one symbol.",
)
write_reports = st.checkbox(
    "Persist markdown reports", value=False, help="Stores reports under ./reports."
)
run_button = st.button("Run Analysis", type="primary")

if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None
    st.session_state.error = None

if run_button:
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    if not symbols:
        st.warning("Please provide at least one ticker symbol.")
    else:
        with st.spinner("Running Upsonic workflow..."):
            try:
                st.session_state.workflow_result = _call_api(symbols, write_reports)
                st.session_state.error = None
            except requests.HTTPError as exc:
                st.session_state.error = exc.response.json().get("detail", str(exc))
                st.session_state.workflow_result = None
            except Exception as exc:  # pragma: no cover
                st.session_state.error = str(exc)
                st.session_state.workflow_result = None

if st.session_state.error:
    st.error(f"Workflow failed: {st.session_state.error}")

result = st.session_state.workflow_result
if result:
    st.success(
        f"Analysis completed for {', '.join(result['symbols'])} "
        f"({result['summary']['headline']})."
    )

    with st.expander("Stock Analyst Report", expanded=True):
        st.markdown(_format_text_block(result["stock_analysis"]["overview"]))
        for company in result["stock_analysis"]["companies"]:
            st.subheader(f"{company['company_name']} ({company['symbol']})")
            st.markdown(
                f"**Market Research**\n\n{_format_text_block(company['market_research'])}"
            )
            st.markdown(
                f"**Financial Analysis**\n\n{_format_text_block(company['financial_analysis'])}"
            )
            st.markdown(
                f"**Risk Assessment**\n\n{_format_text_block(company['risk_assessment'])}"
            )
        st.markdown("**Key Recommendations**")
        st.markdown(_format_text_block(result["stock_analysis"]["key_recommendations"]))

    col1, col2 = st.columns(2)
    with col1:
        st.header("🏆 Investment Ranking")
        st.markdown(_format_text_block(result["investment_ranking"]["ranked_companies"]))
        st.markdown(
            "**Investment Rationale**\n\n"
            + _format_text_block(result["investment_ranking"]["investment_rationale"])
        )
    with col2:
        st.header("⚖️ Risk & Growth")
        st.markdown(
            "**Risk Evaluation**\n\n"
            + _format_text_block(result["investment_ranking"]["risk_evaluation"])
        )
        st.markdown(
            "**Growth Potential**\n\n"
            + _format_text_block(result["investment_ranking"]["growth_potential"])
        )

    st.header("💼 Portfolio Allocation")
    st.markdown("**Strategy**")
    st.markdown(_format_text_block(result["portfolio_allocation"]["allocation_strategy"]))
    st.markdown("**Investment Thesis**")
    st.markdown(_format_text_block(result["portfolio_allocation"]["investment_thesis"]))
    st.markdown("**Risk Management**")
    st.markdown(_format_text_block(result["portfolio_allocation"]["risk_management"]))
    st.markdown("**Final Recommendations**")
    st.markdown(_format_text_block(result["portfolio_allocation"]["final_recommendations"]))

    st.info(result["summary"]["reminder"])

    if result.get("report_paths"):
        st.caption(
            "Reports saved to:\n" + "\n".join(f"- `{path}`" for path in result["report_paths"])
        )

