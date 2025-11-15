.PHONY: install api streamlit dev test clean

install:
	uv sync --dev
	uv pip install --editable . --no-deps
	uv sync --extra dev

api: install
	uv run uvicorn upsonic_investment_generator.api.main:app --reload --port 8000

streamlit: install
	uv run streamlit run streamlit_app.py

dev: install
	uv run uvicorn upsonic_investment_generator.api.main:app --reload --port 8000 &
	uv run streamlit run streamlit_app.py

test: install
	uv run pytest

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "\033[91mCleaned up the project.\033[0m"


