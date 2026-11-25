import json
from types import SimpleNamespace

from scripts.rag_evidence import build_answer, candidate_sources


def make_answer(text="Test fixture answer."):
    manual = {"manual_id": "test-manual", "manual_version": "test-v1",
              "document_sha256": "f" * 64, "page_count": 300}
    doc = SimpleNamespace(page_content="Quoted test fixture", metadata={"page": 115})
    sources = candidate_sources([doc], manual)
    return build_answer(json.dumps({"answer_type": "answered", "steps": [
        {"text": text, "source_ids": [sources[0]["chunk_id"]]},
    ]}), sources, manual, {"model_id": "test-no-model", "index_version": "test-v1",
                          "prompt_version": "test-v1", "mode": "fixture"})
