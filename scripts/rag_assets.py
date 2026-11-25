"""Capture/verify private RAG assets without committing them or loading GPU models."""

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

DEFAULT_PATHS = [
    "data/Tesla_Manual.pdf", "data/stopwords.txt", "data/saved_index/bm25retriever.pkl",
    "data/saved_index/milvus.db", "data/manual_text.jsonl", "data/saved_images",
    "models/BAAI/bge-m3",
    "RAG-Retrieval/rag_retrieval/train/reranker/output/bert/runs/checkpoints/checkpoint_0",
    "LLaMA-Factory-main/output/qwen3_lora_sft_int4",
]


def file_hash(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def safe_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or Path(relative).is_absolute():
        raise ValueError("Asset must be inside RAG root")
    return path


def capture(root, manual_version, paths=None, page_count=None):
    root = Path(root).resolve()
    artifacts = []
    for relative in paths or DEFAULT_PATHS:
        path = safe_path(root, relative)
        if not path.exists():
            raise ValueError(f"Missing required asset: {relative}")
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        for file in files:
            if file.is_file():
                if not file.resolve().is_relative_to(root):
                    raise ValueError("Asset symlink escapes RAG root")
                artifacts.append({"path": file.relative_to(root).as_posix(),
                                  "sha256": file_hash(file), "size": file.stat().st_size})
    if page_count is None:
        import fitz
        with fitz.open(root / "data/Tesla_Manual.pdf") as pdf:
            page_count = len(pdf)
    packages = {}
    for name in ("torch", "vllm", "transformers", "pymilvus", "milvus-lite", "pymongo"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    identity = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
    return {
        "schema_version": 1, "source_root": str(root),
        "manual": {"manual_id": "tesla-model3-zh", "manual_version": manual_version,
                   "document_sha256": file_hash(root / "data/Tesla_Manual.pdf"),
                   "page_count": page_count},
        "index_version": identity, "artifacts": artifacts,
        "runtime": {"python": sys.version.split()[0], "packages": packages},
    }


def verify(root, manifest_path):
    root = Path(root).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not manifest.get("artifacts"):
        raise ValueError("Invalid or empty asset manifest")
    identity = hashlib.sha256(
        json.dumps(manifest["artifacts"], sort_keys=True).encode()).hexdigest()
    if manifest.get("index_version") != identity:
        raise ValueError("Asset list identity mismatch")
    for asset in manifest["artifacts"]:
        path = safe_path(root, asset["path"])
        if not path.is_file() or file_hash(path) != asset["sha256"]:
            raise ValueError(f'Asset missing or changed: {asset["path"]}')
    if file_hash(root / "data/Tesla_Manual.pdf") != manifest["manual"]["document_sha256"]:
        raise ValueError("Manual identity mismatch")
    return manifest


def verify_runtime(manifest):
    expected = manifest["runtime"]
    if expected["python"].split(".")[:2] != sys.version.split()[0].split(".")[:2]:
        raise ValueError("GPU Python version differs from the captured environment")
    for name, version in expected["packages"].items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = "not-installed"
        if version == "not-installed" or actual != version:
            raise ValueError(f"GPU package missing or changed: {name}")


def mongo_collection(root):
    sys.path.insert(0, str(Path(root).resolve()))
    from src.client.mongodb_config import MongoConfig
    return MongoConfig.get_collection("manual_text")


def mongo_lines(collection):
    rows = [json.dumps(row, ensure_ascii=False, sort_keys=True)
            for row in collection.find({}, {"_id": 0})]
    return sorted(rows)


def check_mongo(root):
    expected = sorted((Path(root) / "data/manual_text.jsonl").read_text(
        encoding="utf-8").splitlines())
    if not expected or mongo_lines(mongo_collection(root)) != expected:
        raise ValueError("MongoDB data differs from the captured asset snapshot")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["capture", "verify", "export-mongo", "restore-mongo"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manual-version")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest or root / "asset-manifest.json"
    if args.action == "capture":
        if not args.manual_version:
            parser.error("capture requires --manual-version from the actual document")
        data = capture(root, args.manual_version)
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Captured {len(data['artifacts'])} assets; index {data['index_version']}")
    elif args.action == "verify":
        verify(root, manifest)
        print("Asset checksums verified")
    elif args.action == "export-mongo":
        rows = mongo_lines(mongo_collection(root))
        if not rows:
            raise ValueError("Cannot export an empty manual collection")
        path = root / "data/manual_text.jsonl"
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"Exported {len(rows)} manual records")
    else:
        verify(root, manifest)
        collection = mongo_collection(root)
        if collection.count_documents({}) != 0:
            raise ValueError("Restore requires an empty collection; no live data was changed")
        rows = [json.loads(line) for line in (root / "data/manual_text.jsonl").read_text(
            encoding="utf-8").splitlines()]
        collection.insert_many(rows)
        check_mongo(root)
        print(f"Restored and verified {len(rows)} records")


if __name__ == "__main__":
    main()
