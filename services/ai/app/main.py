from __future__ import annotations

import logging
from time import perf_counter

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from services.common.config import configure_logging
from services.common.rag_client import (
    RagUnavailable,
    manual_backend_status,
    query_manual,
)
from services.common.schemas import (
    HealthResponse,
    RagAnswer,
    RagRequest,
    TriageRequest,
    TriageResponse,
)

configure_logging()
logger = logging.getLogger("services.ai.main")

app = FastAPI(title="Model 3 AI Gateway", version="0.2.0")

TRIAGE_REQUESTS = Counter("ai_triage_requests_total", "Total triage requests", ["label"])
TRIAGE_LATENCY = Histogram("ai_triage_duration_seconds", "Triage duration in seconds")

LABEL_KEYWORDS = {
    "incident": {"error", "outage", "down", "failed", "failure", "broken", "crash", "bug"},
    "access": {"login", "password", "access", "permission", "unlock", "sign in", "signin"},
    "billing": {"invoice", "charge", "refund", "billing", "payment", "subscription"},
    "maintenance": {"upgrade", "patch", "maintenance", "deploy", "deployment", "scheduled"},
}


def shorten(text: str, max_words: int = 24) -> str:
    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def triage_text(title: str, description: str) -> TriageResponse:
    text = f"{title} {description}".lower()
    scores = {
        label: sum(1 for keyword in keywords if keyword in text)
        for label, keywords in LABEL_KEYWORDS.items()
    }

    label, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        label = "general"
        confidence = 0.45
    else:
        confidence = min(0.55 + 0.08 * score, 0.95)

    summary = shorten(f"{title.strip()}: {description.strip()}")
    return TriageResponse(label=label, summary=summary, confidence=round(confidence, 2))


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(service="ai", status="ok")


@app.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return HealthResponse(service="ai", status="ok")


@app.get("/health/ready", response_model=HealthResponse)
def health_ready() -> HealthResponse:
    return HealthResponse(service="ai", status="ok")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/triage", response_model=TriageResponse)
def triage(payload: TriageRequest) -> TriageResponse:
    start = perf_counter()
    result = triage_text(payload.title, payload.description)
    TRIAGE_REQUESTS.labels(result.label).inc()
    TRIAGE_LATENCY.observe(perf_counter() - start)
    logger.info(
        "triage_completed",
        extra={
            "case_id": payload.case_id,
            "label": result.label,
            "confidence": result.confidence,
        },
    )
    return result


@app.get("/rag/status")
def rag_status() -> dict:
    return manual_backend_status()


@app.post("/rag/query", response_model=RagAnswer)
def rag_query(payload: RagRequest) -> RagAnswer:
    try:
        return query_manual(payload.question, payload.case_id)
    except RagUnavailable as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc), headers={
            "Retry-After": exc.retry_after,
            "X-RAG-Retryable": "true" if exc.retryable else "false",
        }) from exc
