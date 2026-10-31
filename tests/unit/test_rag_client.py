import httpx
import pytest

from services.common import rag_client


def test_unavailable_upstream_does_not_fall_back_to_triage(monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("private diagnostic")

    monkeypatch.setattr(rag_client.httpx, "post", timeout)
    with pytest.raises(rag_client.RagUnavailable, match="超时"):
        rag_client.query_manual("哨兵模式怎么用？")


def test_invalid_response_and_invalid_citations_are_rejected(monkeypatch):
    def bad_response(url, **kwargs):
        return httpx.Response(
            200, request=httpx.Request("POST", url), json={"answer": " ", "cite_pages": [-1]}
        )

    monkeypatch.setattr(rag_client.httpx, "post", bad_response)
    with pytest.raises(rag_client.RagUnavailable):
        rag_client.query_manual("哨兵模式怎么用？")
