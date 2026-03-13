from __future__ import annotations

from fastapi import FastAPI

from .config import load_config
from .schemas import TriageRequest, TriageResponse
from .triage_agent import TriageAgent

app = FastAPI(title="Triage Agent API", version="1.0.0")
config = load_config()
agent = TriageAgent(config)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_enabled": bool(config.openai_api_key),
        "model": config.openai_model,
    }


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest) -> TriageResponse:
    return agent.triage(req)
