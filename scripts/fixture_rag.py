"""Explicit offline engineering fixture; never an AI or factual vehicle answer."""

import json
from pathlib import Path
from types import SimpleNamespace

try:
    from scripts.rag_assets import file_hash
    from scripts.rag_evidence import build_answer, candidate_sources
except ModuleNotFoundError:
    from rag_assets import file_hash
    from rag_evidence import build_answer, candidate_sources


def fixture_pdf():
    text = b"BT /F1 16 Tf 40 740 Td (OFFLINE ENGINEERING FIXTURE - NOT A VEHICLE MANUAL) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
               b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"\nendstream"]
    result, offsets = b"%PDF-1.4\n", [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += b"xref\n0 6\n0000000000 65535 f \n"
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return result + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


class FixturePipeline:
    mode = "fixture"
    fingerprint = "offline-fixture-v2"

    def __init__(self, root):
        self.root = Path(root)
        path = self.root / "data/Tesla_Manual.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fixture_pdf())
        self.manual = {"manual_id": "engineering-fixture", "manual_version": "fixture-v2",
                       "document_sha256": file_hash(path), "page_count": 1}

    def answer(self, query):
        doc = SimpleNamespace(page_content="Synthetic fixture for engineering tests only.",
                              metadata={"unique_id": "fixture", "page": 1})
        sources = candidate_sources([doc], self.manual)
        sources[0]["title"] = "工程测试片段（模拟）"
        return build_answer(json.dumps({"answer_type": "answered", "steps": [{
            "text": ("【离线工程测试】已完成队列处理和证据保存。"
                     "这是模拟结果，不提供真实车辆操作指导。"),
            "source_ids": [sources[0]["chunk_id"]],
        }]}), sources, self.manual, {"model_id": "fixture-no-model",
             "index_version": "fixture-v2", "prompt_version": "fixture-v2", "mode": "fixture"})

    def image_path(self, image_id):
        return None

    def ready(self):
        return True
