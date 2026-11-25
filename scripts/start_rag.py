"""Supervise the real GPU backend. No model downloads or package changes are implicit."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from scripts.rag_assets import check_mongo, mongo_collection, verify
except ModuleNotFoundError:
    from rag_assets import check_mongo, mongo_collection, verify


def model_ready(url, model):
    try:
        request = Request(url.rstrip("/") + "/models", headers={
            "Authorization": "Bearer " + os.environ.get("RAG_LLM_TOKEN", "EMPTY")})
        with urlopen(request, timeout=2) as response:
            models = json.load(response)["data"]
        if model not in {m["id"] for m in models}:
            raise ValueError("LLM port is occupied by a different model")
        return True
    except URLError:
        return False


def wait_until(check, children, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(child.poll() is not None for child in children):
            raise RuntimeError("A managed backend process exited; inspect its log")
        if check():
            return
        time.sleep(2)
    raise TimeoutError("Backend readiness deadline exceeded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--check-assets-only", action="store_true")
    parser.add_argument("--manage-services", action="store_true")
    parser.add_argument("--mongod", type=Path)
    parser.add_argument("--port", type=int, default=6001)
    parser.add_argument("--llm-memory-fraction", type=float, default=0.55)
    args = parser.parse_args()
    if not 0 < args.llm_memory_fraction < 1 or not 1 <= args.port <= 65535:
        parser.error("Invalid GPU memory fraction or gateway port")
    root = args.root.resolve()
    manifest_path = (args.manifest or root / "asset-manifest.json").resolve()
    manifest = verify(root, manifest_path)
    print(f"Verified assets for {manifest['manual']['manual_version']}", flush=True)
    if args.check_assets_only:
        return
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("A compatible CUDA GPU is required for the real backend")
    model = os.environ.get("RAG_MODEL_ID", "LLaMA-Factory-main/output/qwen3_lora_sft_int4")
    url = os.environ.get("RAG_LLM_URL", "http://127.0.0.1:8000/v1")
    env = dict(os.environ, RAG_DIR=str(root), RAG_ASSET_MANIFEST=str(manifest_path))
    os.environ.update(RAG_DIR=str(root))
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    children, logs = [], []

    def launch(command, name):
        log = (runtime / (name + ".log")).open("ab")
        logs.append(log)
        process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=log)
        children.append(process)
        return process

    def mongo_ready():
        from pymongo import MongoClient
        client = MongoClient(
            host=os.environ.get("MONGO_HOST", "127.0.0.1"),
            port=int(os.environ.get("MONGO_PORT", "27017")),
            username=os.environ.get("MONGO_USERNAME"), password=os.environ.get("MONGO_PASSWORD"),
            authSource=os.environ.get("MONGO_AUTH_SOURCE", "admin"),
            serverSelectionTimeoutMS=2000,
        )
        try:
            client.admin.command("ping")
            return True
        except Exception:
            return False
        finally:
            client.close()

    try:
        if not mongo_ready():
            if not args.manage_services or not args.mongod or not args.mongod.is_file():
                raise RuntimeError("MongoDB is offline; supply --manage-services --mongod PATH")
            data = runtime / "mongo"
            data.mkdir(exist_ok=True)
            launch([str(args.mongod.resolve()), "--dbpath", str(data), "--bind_ip", "127.0.0.1",
                    "--port", os.environ.get("MONGO_PORT", "27017")], "mongo")
            wait_until(mongo_ready, children, 60)
        collection = mongo_collection(root)
        if collection.count_documents({}) == 0 and args.manage_services:
            rows = [json.loads(line) for line in (root / "data/manual_text.jsonl").read_text(
                encoding="utf-8").splitlines()]
            collection.insert_many(rows)
        check_mongo(root)
        print("MongoDB manual snapshot verified", flush=True)
        if not model_ready(url, model):
            if not args.manage_services or url != "http://127.0.0.1:8000/v1":
                raise RuntimeError("Start the configured LLM or enable local managed services")
            print("Loading vLLM; waiting for actual model readiness (up to 900s)", flush=True)
            launch([sys.executable, "-m", "vllm.entrypoints.openai.api_server",
                    "--model", str(root / model), "--served-model-name", model,
                    "--host", "127.0.0.1", "--port", "8000",
                    "--gpu-memory-utilization", str(args.llm_memory_fraction)], "llm")
            wait_until(lambda: model_ready(url, model), children, 900)
        print("LLM ready; initializing retrieval gateway", flush=True)
        gateway = launch([sys.executable, str(Path(__file__).with_name("rag_gateway.py")),
                          "--rag-dir", str(root), "--port", str(args.port)], "rag")
        def gateway_ready():
            try:
                req = Request(f"http://127.0.0.1:{args.port}/health/ready", headers={
                    "Authorization": "Bearer " + os.environ.get("RAG_API_TOKEN", "")})
                with urlopen(req, timeout=3) as response:
                    return json.load(response).get("status") == "ready"
            except (URLError, TimeoutError):
                return False
        wait_until(gateway_ready, children, 300)
        print("Real RAG backend ready; keep this supervisor running", flush=True)
        while gateway.poll() is None:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("A managed dependency exited")
            time.sleep(1)
        raise RuntimeError("Gateway exited; inspect runtime/rag.log")
    finally:
        # Only processes created by this supervisor are stopped.
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
        for log in logs:
            log.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
