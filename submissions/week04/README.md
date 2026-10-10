# Week 04 Submission — Team Architecture Proposal and Project Plan

## 1. Proposal Summary

### Problem

Tesla Model 3 owners need quick, accurate answers to questions about vehicle operation (e.g., "how to enable auto-lock on walk-away"). The official manual is a lengthy PDF that is difficult to search and lacks interactivity. Traditional keyword search cannot understand the semantics of natural-language questions, making it hard to precisely locate relevant manual passages and generate concise, cited answers. The existing starter template's keyword classification (incident/access/billing/maintenance) is designed for customer support ticket triage and does not match the manual Q&A domain, providing no valuable answers to vehicle owners.

### Solution

Building on the starter template's three-service architecture (API + Worker + AI Service + PostgreSQL), the AI Service's keyword matching will be replaced with a Retrieval-Augmented Generation (RAG) pipeline. A new RAG service will be added as a FastAPI microservice (port 6001), encapsulating the full pipeline: BM25 recall → Milvus hybrid search (BGE-M3 dense+sparse) → merge/dedup → BGE-M3 reranking → LLM generates cited answer. The Worker and API require no changes — the Worker still calls the AI Service via `POST /triage`, and the AI Service internally forwards the request to the RAG service's `POST /rag/query`, returning `answer`/`label`/`confidence` mapped to the Case's `ai_label`/`ai_summary`/`ai_confidence` fields. The knowledge base uses the Tesla Model 3 owner's manual PDF as the data source, processed through PDF parsing → LLM cleaning → semantic chunking to build BM25 and Milvus indexes, with document text stored in MongoDB.

## 2. Milestone Plan

| Week | Target | Deliverables |
|-----|--------|--------------|
| Week 5 | RAG service prototype | `RAG/src/server/rag_service.py` (FastAPI `POST /rag/query`); encapsulate `infer.py` pipeline as HTTP service |
| Week 6 | Index building and data preparation | Run `build_index.py` to build BM25 + Milvus indexes; import manual document chunks into MongoDB |
| Week 7 | End-to-end integration (midterm) | AI Service removes `triage_text()`, replaces with RAG call; `compose.yaml` adds `rag` service definition; smoke tests pass |
| Week 9 | Testing and observability | Update unit tests (mock RAG calls); update smoke test `ai_label` assertions; RAG service health check endpoints + Prometheus metrics |
| Week 11 | Performance optimization and fault tolerance | Tune retrieval top-k parameters; increase Worker timeout; RAG service warmstart optimization; GPU/CPU fallback strategy |
| Week 13 | Final delivery | Complete documentation (`architecture.md`/`architecture_zh.md` + `operations.md` + ADR); final technical brief; AI use statement |
