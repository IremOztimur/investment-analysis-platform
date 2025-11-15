# Upsonic Investment Generator

Upsonic Investment Generator is a three-stage investment intelligence platform built on FastAPI, Streamlit, and Upsonic agents. It delivers:

1. **Comprehensive stock analysis** with market research, financial review, and risk assessment.
2. **Investment potential ranking** to compare opportunities based on upside and risks.
3. **Portfolio allocation recommendations** that balance conviction with diversification.

The project uses [uv](https://github.com/astral-sh/uv) for dependency management and offers both API and UI front-ends.

## Getting started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) installed
- An `OPENAI_API_KEY` or compatible key available in the environment

Optional: create a `.env` file with secret values. The workflow loads environment variables through `python-dotenv`.

### Installation

```bash
make install
```

This installs runtime and development dependencies into a uv-managed virtual environment.

### Running the FastAPI service

```bash
uv run uvicorn upsonic_investment_generator.api.main:app --reload --port 8000
```
or
```bash
make api
```

The OpenAPI schema is available at `http://localhost:8000/docs`.

### Running the Streamlit dashboard

```bash
uv run streamlit run streamlit_app.py
```
or
```bash
make streamlit
```

Set `UPSONIC_TELEMETRY` false to disable telemetry.

### Combined developer workflow

```bash
make dev
```

Runs FastAPI (on port 8000) and Streamlit (default port 8501) simultaneously.

### Command-line interface

```bash
uv run upsonic-investment-generator AAPL MSFT --write-reports
```

The CLI executes the full workflow and optionally persists markdown reports under `reports/investment/<timestamp>/`.

## Project layout

- `src/upsonic_investment_generator/` – core package with workflow, API, CLI utilities
- `streamlit_app.py` – Streamlit UI
- `Makefile` – helper targets for installing, running, and cleaning

## Tests & linting

```bash
make test  # runs pytest
```

Add your own tests under `tests/` and configure linting as needed.

## License

Proprietary – for internal Upsonic experimentation.
