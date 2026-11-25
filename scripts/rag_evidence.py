"""Pure Python evidence contract, also deployed beside the remote gateway.

Checks reference integrity and provenance, not semantic correctness of an answer.
"""

import hashlib
import json
import re


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def candidate_sources(docs, manual):
    sources = []
    for doc in docs:
        page = doc.metadata.get("page")
        if type(page) is not int or not 1 <= page <= manual["page_count"]:
            raise ValueError("Retrieved page is outside the configured document")
        excerpt = doc.page_content[:4000].strip()
        if not excerpt:
            raise ValueError("Empty retrieved evidence")
        identity = f'{manual["document_sha256"]}:{page}:{doc.metadata.get("unique_id", "")}:'
        sources.append({
            "chunk_id": digest(identity + excerpt), "page": page,
            "title": "Model 3 车主手册", "excerpt": excerpt,
            "excerpt_sha256": digest(excerpt),
            **{k: manual[k] for k in ("manual_id", "manual_version", "document_sha256")},
        })
    return sources


def empty_answer(kind, manual, provenance, message=None):
    return {
        "schema_version": 2, "answer_type": kind,
        "answer": message or (
            "请补充具体操作场景和车辆信息。" if kind == "needs_clarification" else
            "当前手册中未找到足以支持回答的证据，请查阅原文或咨询专业人员。"
        ),
        "manual": manual, "provenance": provenance,
        "steps": [], "sources": [], "cite_pages": [], "related_images": [],
    }


def build_answer(response, sources, manual, provenance):
    data = json.loads(response)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    kind = data.get("answer_type")
    if kind in {"insufficient_evidence", "needs_clarification"}:
        message = data.get("message") if kind == "needs_clarification" else None
        result = empty_answer(kind, manual, provenance, message)
    else:
        if kind != "answered" or not isinstance(data.get("steps"), list) or not data["steps"]:
            raise ValueError("Expected structured, cited answer")
        available = {s["chunk_id"]: s for s in sources}
        used, steps = set(), []
        for step in data["steps"]:
            ids, text = step.get("source_ids"), step.get("text")
            if not isinstance(ids, list) or not ids or any(i not in available for i in ids):
                raise ValueError("Citation is not in this retrieval")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Empty answer step")
            used.update(ids)
            steps.append({"text": text.strip(), "source_ids": list(dict.fromkeys(ids))})
        selected = [s for s in sources if s["chunk_id"] in used]
        result = {
            "schema_version": 2, "answer_type": "answered",
            "answer": "\n".join(s["text"] for s in steps), "steps": steps,
            "sources": selected, "cite_pages": sorted({s["page"] for s in selected}),
            "related_images": [], "manual": manual, "provenance": provenance,
        }
    validate_payload(result)
    return result


def validate_payload(data):
    if data.get("schema_version") != 2:
        raise ValueError("Unsupported RAG contract; deploy the matching gateway")
    if not isinstance(data.get("answer"), str) or not data["answer"].strip():
        raise ValueError("Empty answer")
    manual = data.get("manual")
    if not isinstance(manual, dict):
        raise ValueError("Manual identity is required")
    for key in ("manual_id", "manual_version"):
        if not isinstance(manual.get(key), str) or not manual[key].strip():
            raise ValueError("Missing manual identity")
    if not re.fullmatch(r"[a-f0-9]{64}", manual.get("document_sha256", "")):
        raise ValueError("Invalid document hash")
    if type(manual.get("page_count")) is not int or manual["page_count"] < 1:
        raise ValueError("Invalid document page count")
    sources, steps, ids = data.get("sources", []), data.get("steps", []), set()
    for source in sources:
        chunk_id = source.get("chunk_id", "")
        if not re.fullmatch(r"[a-f0-9]{64}", chunk_id) or chunk_id in ids:
            raise ValueError("Invalid or duplicate evidence ID")
        ids.add(chunk_id)
        if any(source.get(k) != manual[k] for k in (
            "manual_id", "manual_version", "document_sha256"
        )):
            raise ValueError("Evidence belongs to a different manual version")
        page, excerpt = source.get("page"), source.get("excerpt", "")
        if type(page) is not int or not 1 <= page <= manual["page_count"]:
            raise ValueError("Invalid evidence page")
        if not isinstance(excerpt, str) or not excerpt.strip():
            raise ValueError("Missing evidence excerpt")
        if source.get("excerpt_sha256") != digest(excerpt):
            raise ValueError("Evidence excerpt checksum mismatch")
    pages = sorted({s["page"] for s in sources})
    if sorted(set(data.get("cite_pages", []))) != pages:
        raise ValueError("Citation pages and evidence do not match")
    kind = data.get("answer_type")
    if kind == "answered":
        if not sources or not steps:
            raise ValueError("Answered results require evidence and cited steps")
        used = set()
        for step in steps:
            refs = step.get("source_ids", [])
            if not step.get("text", "").strip() or not refs or any(i not in ids for i in refs):
                raise ValueError("Invalid step evidence")
            used.update(refs)
        if used != ids or data["answer"] != "\n".join(s["text"] for s in steps):
            raise ValueError("Answer does not match the cited steps")
    elif kind in {"insufficient_evidence", "needs_clarification"}:
        if sources or steps or pages or data.get("related_images"):
            raise ValueError("Unanswered results must not contain fabricated citations")
    else:
        raise ValueError("Invalid answer type")
    if any(i.get("page") not in pages for i in data.get("related_images", [])):
        raise ValueError("Image is not attached to a cited page")
    provenance = data.get("provenance", {})
    for key in ("model_id", "index_version", "prompt_version", "mode"):
        if not isinstance(provenance.get(key), str) or not provenance[key].strip():
            raise ValueError("Missing generation provenance")
    if provenance["mode"] not in {"live", "fixture"}:
        raise ValueError("Invalid inference mode")
