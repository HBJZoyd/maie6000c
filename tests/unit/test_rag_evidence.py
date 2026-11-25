import ast
import copy
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.rag_assets import capture, verify
from scripts.rag_evidence import build_answer, empty_answer, validate_payload
from services.common.schemas import RagAnswer
from tests.rag_fixtures import make_answer


@pytest.mark.parametrize("change", [
    lambda p: p["sources"][0].update(page=0),
    lambda p: p["sources"][0].update(page=301),
    lambda p: p["sources"][0].update(manual_version="another-version"),
    lambda p: p["sources"][0].update(excerpt="changed excerpt"),
    lambda p: p["steps"][0].update(source_ids=["0"]),
    lambda p: p.update(cite_pages=[116]),
    lambda p: p.update(sources=[]),
    lambda p: p.update(answer="unrelated uncited replacement"),
])
def test_corrupt_or_mismatched_evidence_is_rejected(change):
    payload = make_answer()
    change(payload)
    with pytest.raises(ValueError):
        RagAnswer.model_validate(payload)


def test_unknown_model_source_id_is_rejected_before_mapping_to_pages():
    payload = make_answer()
    model = {"answer_type": "answered", "steps": [{"text": "claim", "source_ids": ["0"]}]}
    with pytest.raises(ValueError, match="not in this retrieval"):
        build_answer(
            json.dumps(model), payload["sources"], payload["manual"], payload["provenance"])


def test_model_json_array_is_rejected_as_non_retryable_evidence_error():
    payload = make_answer()
    with pytest.raises(ValueError, match="JSON object"):
        build_answer("[]", payload["sources"], payload["manual"], payload["provenance"])


@pytest.mark.parametrize("kind", ["insufficient_evidence", "needs_clarification"])
def test_unanswered_results_are_distinct_and_cannot_have_citations(kind):
    good = make_answer()
    payload = empty_answer(kind, good["manual"], good["provenance"])
    assert RagAnswer.model_validate(payload).answer_type == kind
    payload["sources"] = good["sources"]
    with pytest.raises(ValueError):
        validate_payload(payload)


def test_legacy_zero_reference_does_not_select_last_document():
    # Extract the pure function without importing GPU/MongoDB modules.
    module = ast.parse(Path("RAG/src/utils.py").read_text(encoding="utf-8"))
    function = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                    and n.name == "post_processing")
    scope = {"re": re}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "post_processing", "exec"), scope)
    docs = [SimpleNamespace(metadata={"page": 115, "images_info": []})]
    assert scope["post_processing"]("answer【0, 2】", docs)["cite_pages"] == []
    assert scope["post_processing"]("answer【1】", docs)["cite_pages"] == [115]


def test_asset_manifest_detects_changed_file_and_path_escape(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    pdf = data / "Tesla_Manual.pdf"
    pdf.write_bytes(b"test-only-pdf-bytes")
    manifest = capture(tmp_path, "test-v1", paths=["data/Tesla_Manual.pdf"], page_count=1)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert verify(tmp_path, path)["manual"]["manual_version"] == "test-v1"
    pdf.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        verify(tmp_path, path)
    bad = copy.deepcopy(manifest)
    bad["artifacts"][0]["path"] = "../private"
    import hashlib
    bad["index_version"] = hashlib.sha256(
        json.dumps(bad["artifacts"], sort_keys=True).encode()).hexdigest()
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="inside"):
        verify(tmp_path, path)
