# Pre-existing AutoDL RAG source and runtime assets

The RAG implementation and prepared models/indexes existed before the local W07
integration and were supplied as part of the user's AutoDL project. Team Odie's
milestone contribution is the HTTP adapter, durable local application integration,
browser workflow, failure handling, validation and documentation. This submission
does not claim that the team authored the original retrieval framework, built the
upstream models, or trained the existing checkpoints during this milestone.

The remote `infer.py` retains its original author/copyright header. Its read-only
snapshot and the core remote source hashes are in
`../submissions/week07/evidence/autodl-source/` and `autodl-runtime.json`.
The local source folder preserves the provided backend source. Differences in
comments/formatting can exist; it is not claimed to be byte-identical to every
remote file. The HTTP adapter SHA-256 was verified against the deployed copy.

The following stay outside Git: `config.ini` and swap files; `data/` including
PDF, parsed documents, indexes, images and MongoDB files; `models/`; MongoDB
executables; upstream `LLaMA-Factory-main/` and `RAG-Retrieval/` checkouts and
trained outputs. The legacy `requirements.txt` is a snapshot of the existing
GPU environment, not a lightweight local application dependency list.

Required existing paths on AutoDL are recorded in `src/constant.py`: the manual
under `data/Tesla_Manual.pdf`, BM25 pickle and Milvus Lite file under
`data/saved_index/`, BGE models/checkpoint, and the local vLLM Qwen3 model directory.
Use only assets that the operator is entitled to use. Preserve upstream notices
when reproducing or redistributing those external components. The milestone
repository does not redistribute model weights or the complete manual.
