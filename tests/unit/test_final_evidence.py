import pytest

from scripts.collect_final_evidence import require_mode


def test_real_evidence_refuses_healthy_fixture_and_unready_backend():
    for status in ({"rag": "ready", "mode": "fixture"},
                   {"rag": "unavailable", "mode": "live"}, {"rag": "ready"}):
        with pytest.raises(RuntimeError):
            require_mode(status, "live")
    require_mode({"rag": "ready", "mode": "live"}, "live")


def test_fixture_evidence_refuses_real_backend():
    with pytest.raises(RuntimeError):
        require_mode({"rag": "ready", "mode": "live"}, "fixture")
