"""HTTP boundary for the existing remote manual pipeline; never fabricates an answer."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from services.common.config import get_settings
from services.common.schemas import RagAnswer


class RagUnavailable(Exception):
    pass


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
    except httpx.TimeoutException as exc:
        raise RagUnavailable("车书问答服务响应超时，请稍后重试。") from exc
    except (httpx.HTTPError, ValidationError, ValueError) as exc:
        raise RagUnavailable("车书问答服务暂时不可用，请检查远程服务连接后重试。") from exc


def manual_backend_status() -> dict:
    try:
        response = httpx.get(
            rag_url("/health/ready"),
            headers=rag_headers(),
            timeout=3.0,
            trust_env=False,
        )
        ready = response.status_code == 200 and response.json().get("status") == "ready"
    except (RagUnavailable, httpx.HTTPError, ValueError):
        ready = False
    return {"status": "ready" if ready else "unavailable", "ready": ready}


def fetch_manual_asset(path: str) -> httpx.Response:
    try:
        response = httpx.get(rag_url(path), headers=rag_headers(), timeout=60.0, trust_env=False)
        response.raise_for_status()
        return response
    except (RagUnavailable, httpx.HTTPError) as exc:
        raise RagUnavailable("手册文件暂时无法读取，请稍后重试。") from exc
