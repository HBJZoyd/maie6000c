"""Copy this one file into the existing RAG directory and run it in its environment.

Uses the same retrievers, reranker, local LLM client and post-processing as infer.py.
No import of infer.py: its top-level input loop is intentionally left untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import secrets
import sys
import threading
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("maie.rag")


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    case_id: str | None = Field(default=None, max_length=100)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Question is too short")
        return value


class ManualPipeline:
    def __init__(self, rag_dir: Path):
        self.root = rag_dir.resolve()
        if not (self.root / "src").is_dir():
            raise RuntimeError("RAG_DIR must contain the existing src directory")
        os.chdir(self.root)
        sys.path.insert(0, str(self.root))
        from src.client.llm_local_client import request_chat
        from src.constant import bge_reranker_tuned_model_path
        from src.reranker.bge_m3_reranker import BGEM3ReRanker
        from src.retriever.bm25_retriever import BM25
        from src.retriever.milvus_retriever import MilvusRetriever
        from src.utils import merge_docs, post_processing

        self.bm25 = BM25(docs=None, retrieve=True)
        self.milvus = MilvusRetriever(docs=None, retrieve=True)
        self.reranker = BGEM3ReRanker(model_path=bge_reranker_tuned_model_path)
        self.milvus.retrieve_topk("这是一条测试数据", topk=3)
        self.request_chat = request_chat
        self.merge_docs = merge_docs
        self.post_processing = post_processing
        self.images: dict[str, Path] = {}

    def image_record(self, image: dict) -> dict | None:
        raw_path = image.get("image_path", "")
        if not raw_path:
            return None
        path = Path(raw_path)
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        data_dir = (self.root / "data").resolve()
        if not path.is_relative_to(data_dir) or not path.is_file():
            return None
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            return None
        image_id = hashlib.sha256(str(path.relative_to(data_dir)).encode()).hexdigest()[:32]
        self.images[image_id] = path
        page = int(image.get("page", 0))
        if page < 1:
            return None
        return {"id": image_id, "page": page, "title": image.get("title") or "手册插图"}

    def image_path(self, image_id: str) -> Path | None:
        if not re.fullmatch(r"[a-f0-9]{32}", image_id):
            return None
        if image_id not in self.images:
            # Rebuild identifiers after restart so persisted question images still work.
            for path in (self.root / "data" / "saved_images").glob("*"):
                if path.is_file():
                    self.image_record({"image_path": str(path), "page": 1})
        return self.images.get(image_id)

    def answer(self, query: str) -> dict[str, Any]:
        bm25_docs = self.bm25.retrieve_topk(query, topk=10)
        milvus_docs = self.milvus.retrieve_topk(query, topk=10)
        merged_docs = self.merge_docs(bm25_docs, milvus_docs)
        if not merged_docs:
            return {
                "answer": "车主手册中没有检索到相关内容，请换一种问法。",
                "cite_pages": [],
                "sources": [],
                "related_images": [],
            }
        ranked_docs = self.reranker.rank(query, merged_docs, topk=5)
        context = "\n".join(
            f"【{index + 1}】{doc.page_content}" for index, doc in enumerate(ranked_docs)
        )
        stream = self.request_chat(query, context, stream=True)
        response = ""
        for chunk in stream:
            if chunk.choices:
                response += chunk.choices[0].delta.content or ""
        if not response.strip():
            raise RuntimeError("The LLM returned an empty answer")
        result = self.post_processing(response, ranked_docs)
        pages = sorted({int(page) for page in result.get("cite_pages", []) if int(page) > 0})
        sources = []
        seen = set()
        for doc in ranked_docs:
            page = int(doc.metadata.get("page", 0))
            if page in pages and page not in seen:
                sources.append(
                    {"page": page, "title": "Model 3 车主手册", "excerpt": doc.page_content[:4000]}
                )
                seen.add(page)
        images = []
        seen_images = set()
        for image in result.get("related_images", []):
            record = self.image_record(image)
            if record and record["id"] not in seen_images:
                images.append(record)
                seen_images.add(record["id"])
        return {
            "answer": result["answer"].strip(),
            "cite_pages": pages,
            "sources": sources,
            "related_images": images[:30],
        }


def create_app(pipeline=None, rag_dir: Path | None = None, api_token: str | None = None):
    root = (rag_dir or Path(os.environ.get("RAG_DIR", "."))).resolve()
    token = os.environ.get("RAG_API_TOKEN", "") if api_token is None else api_token
    inference_lock = threading.Lock()
    cache: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()

    @asynccontextmanager
    async def lifespan(app):
        app.state.pipeline = pipeline or ManualPipeline(root)
        yield

    app = FastAPI(title="Model 3 Manual RAG", version="1.0.0", lifespan=lifespan)

    def authorize(authorization: str | None = Header(default=None)):
        if token and not secrets.compare_digest(authorization or "", f"Bearer {token}"):
            raise HTTPException(status_code=401, detail="Unauthorized")

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready", dependencies=[Depends(authorize)])
    def ready():
        return {"status": "ready", "pipeline": "bm25-milvus-rerank-llm"}

    @app.post("/rag/query", dependencies=[Depends(authorize)])
    def query(payload: QueryRequest):
        key = (payload.case_id, payload.query)
        if not inference_lock.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Inference busy; retry later")
        try:
            if key in cache and time.monotonic() - cache[key][0] < 3600:
                return cache[key][1]
            started = time.monotonic()
            result = app.state.pipeline.answer(payload.query)
            cache[key] = (time.monotonic(), result)
            cache.move_to_end(key)
            while len(cache) > 256:
                cache.popitem(last=False)
            logger.info(
                "rag_completed case=%s duration=%.2f pages=%s",
                payload.case_id,
                time.monotonic() - started,
                result.get("cite_pages", []),
            )
            return result
        except Exception as exc:
            logger.exception("RAG inference failed")
            raise HTTPException(status_code=502, detail="RAG inference failed") from exc
        finally:
            inference_lock.release()

    @app.get("/rag/manual", dependencies=[Depends(authorize)])
    def manual():
        path = root / "data" / "Tesla_Manual.pdf"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Manual not found")
        return FileResponse(path, media_type="application/pdf")

    @app.get("/rag/images/{image_id}", dependencies=[Depends(authorize)])
    def image(image_id: str):
        path = app.state.pipeline.image_path(image_id)
        if path is None:
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(path, headers={"X-Content-Type-Options": "nosniff"})

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rag-dir", default=os.environ.get("RAG_DIR", "."))
    parser.add_argument("--port", type=int, default=6001)
    args = parser.parse_args()
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(create_app(rag_dir=Path(args.rag_dir)), host="127.0.0.1", port=args.port, workers=1)
