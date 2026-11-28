"""HTTP boundary for the existing remote manual pipeline; never fabricates an answer."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from services.common.config import get_settings
from services.common.schemas import RagAnswer


class RagUnavailable(Exception):
    def __init__(self, message, status_code=503, retryable=True, retry_after="2"):
        super().__init__(message)
        self.status_code, self.retryable = status_code, retryable
        self.retry_after = retry_after


def rag_headers() -> dict[str, str]:
    token = get_settings().rag_api_token
    return {"Authorization": f"Bearer {token}"} if token else {}


def rag_url(path: str) -> str:
    base = get_settings().rag_service_url.rstrip("/")
    if not base:
        raise RagUnavailable("车书问答服务尚未配置，请联系管理员连接服务。")
    return f"{base}{path}"


def query_manual(question: str, case_id: str | None = None) -> RagAnswer:
    try:
        response = httpx.post(
            rag_url("/rag/query"),
            json={"query": question, "case_id": case_id},
            headers=rag_headers(),
            timeout=get_settings().rag_request_timeout_seconds,
            trust_env=False,
        )
        response.raise_for_status()
        return RagAnswer.model_validate(response.json())
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise RagUnavailable(
            "车书问答服务繁忙，请稍后重试。" if status == 429 else "车书问答服务暂时无法回答。",
            status_code=status if status in {429, 502, 503, 504} else 502,
            retryable=(status in {429, 502, 503, 504}
                       and exc.response.headers.get("X-RAG-Retryable") != "false"),
            retry_after=exc.response.headers.get("Retry-After", "2"),
        ) from exc
    except httpx.TimeoutException as exc:
        raise RagUnavailable("车书问答服务响应超时，请稍后重试。") from exc
    except (ValidationError, ValueError) as exc:
        raise RagUnavailable("车书服务返回的证据信息不完整，请联系管理员。", 502, False) from exc
    except httpx.HTTPError as exc:
        raise RagUnavailable("车书问答服务暂时不可用，请检查远程服务连接后重试。") from exc


def manual_backend_status() -> dict:
    try:
        response = httpx.get(
            rag_url("/health/ready"),
            headers=rag_headers(),
            timeout=3.0,
            trust_env=False,
        )
        data = response.json() if response.status_code == 200 else {}
        ready = (data.get("status") == "ready" and data.get("contract_version") == 2
                 and data.get("mode") in {"live", "fixture"})
    except (RagUnavailable, httpx.HTTPError, ValueError):
        ready = False
    return {"status": "ready" if ready else "unavailable", "ready": ready,
            "mode": data.get("mode", "unknown") if ready else "unknown",
            "demo_kind": data.get("demo_kind") if ready else None}


def fetch_manual_asset(path: str) -> httpx.Response:
    try:
        response = httpx.get(rag_url(path), headers=rag_headers(), timeout=60.0, trust_env=False)
        response.raise_for_status()
        return response
    except (RagUnavailable, httpx.HTTPError) as exc:
        raise RagUnavailable("手册文件暂时无法读取，请稍后重试。") from exc
