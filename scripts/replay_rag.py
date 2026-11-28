"""Deterministic presentation adapter backed by a dated W07 recording.

The API, database, worker and evidence validation run normally. Only the inference
boundary replays a recorded answer. Its provenance always remains fixture mode.
"""

import hashlib
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

try:
    from scripts.rag_assets import file_hash
    from scripts.rag_evidence import build_answer, candidate_sources, empty_answer
except ModuleNotFoundError:
    from rag_assets import file_hash
    from rag_evidence import build_answer, candidate_sources, empty_answer


class ReplayPipeline:
    mode = "fixture"
    demo_kind = "recorded-replay"

    def __init__(self, root, delay=1.5):
        self.root = Path(root)
        self.delay = delay
        assets = Path(__file__).resolve().parent / "demo_data"
        recording = assets / "sentry-recording.json"
        self.record = json.loads(recording.read_text(encoding="utf-8"))
        target = self.root / "data/Tesla_Manual.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets / "source-excerpts.pdf", target)
        self.manual = {"manual_id": "w07-recorded-demo-excerpts",
                       "manual_version": "Demo excerpts / recording 2026-10-31",
                       "document_sha256": file_hash(target), "page_count": 2}
        self.fingerprint = hashlib.sha256(
            recording.read_bytes() + target.read_bytes() + b"replay-v1"
        ).hexdigest()
        docs = [SimpleNamespace(page_content=s["excerpt"], metadata={
            "page": i + 1, "unique_id": f"w07-original-page-{s['page']}"
        }) for i, s in enumerate(self.record["sources"])]
        self.sources = candidate_sources(docs, self.manual)
        for source, original in zip(self.sources, self.record["sources"]):
            source["title"] = f"W07 录制摘录（原手册第 {original['page']} 页）"
        self.provenance = {"mode": "fixture", "model_id": "recorded-w07-no-model-call",
                           "index_version": self.fingerprint,
                           "prompt_version": "recorded-answer-replay-v1"}

    def answer(self, query):
        time.sleep(self.delay)
        if query.strip() != self.record["question"]:
            return empty_answer("insufficient_evidence", self.manual, self.provenance,
                                "本演示回放已录制的固定场景，请点击“哨兵模式演示”提交标准问题。")
        return build_answer(json.dumps({"answer_type": "answered", "steps": [{
            "text": self.record["answer"],
            "source_ids": [s["chunk_id"] for s in self.sources],
        }]}), self.sources, self.manual, self.provenance)

    def image_path(self, image_id):
        return None

    def ready(self):
        return True
