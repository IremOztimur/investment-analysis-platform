from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from ..models import WorkflowRequest, WorkflowResult
from ..workflow import InvestmentWorkflow

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Upsonic Investment Intelligence API",
    version="0.1.0",
    description=(
        "Three-stage investment analysis workflow leveraging Upsonic agents, "
        "with FastAPI providing a clean, inspectable interface."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

workflow = InvestmentWorkflow()


@app.get("/", summary="Health check")
async def index() -> dict[str, str]:
    return {"status": "ok", "message": "Upsonic investment workflow ready."}


@app.post("/analyze", response_model=WorkflowResult, summary="Run investment workflow")
async def analyze(request: WorkflowRequest) -> WorkflowResult:
    try:
        return await run_in_threadpool(
            workflow.run, request.symbols, write_reports=request.write_reports
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Investment workflow failed")
        raise HTTPException(status_code=500, detail="Workflow execution failed") from exc

