"""Rebuild the migrated empty Milvus index on the target, retaining rollback proof."""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def worker(root, destination):
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['RAG_DIR'] = str(root)
    sys.path.insert(0, str(root))
    from src import constant
    constant.milvus_db_path = str(destination)
    from src.client.mongodb_config import MongoConfig
    from langchain_core.documents import Document
    collection = MongoConfig.get_collection('manual_text')
    unique = {}
    for row in collection.find({}, {'_id': 0}):
        uid = row.get('unique_id') or row.get('metadata', {}).get('unique_id')
        if not uid or not row.get('page_content'):
            raise ValueError('A manual record has no unique_id or page_content')
        metadata = dict(row['metadata'])
        if metadata.get('unique_id') not in (None, uid):
            raise ValueError('Manual unique_id differs between record and metadata')
        metadata['unique_id'] = uid
        unique.setdefault(uid, Document(page_content=row['page_content'], metadata=metadata))
    docs = list(unique.values())
    if not docs:
        raise ValueError('Refusing to build an empty vector index')
    longest = max(len(doc.page_content.encode('utf-8')) for doc in docs)
    limit = max(512, 2 ** math.ceil(math.log2(max(1, longest))))
    if limit > 65535:
        raise ValueError('A manual chunk exceeds the supported Milvus text field')
    from src.retriever import milvus_retriever as original
    original.MAX_TEXT_LENGTH = limit
    retriever = original.MilvusRetriever(docs=docs, retrieve=False)
    retriever.col.flush()
    actual = retriever.col.num_entities
    if actual != len(docs):
        raise ValueError(f'Vector count {actual} differs from input count {len(docs)}')
    original.connections.disconnect('default')
    print('REBUILD_STATS ' + json.dumps({'documents': len(docs), 'vector_rows': actual,
                                        'max_chunk_utf8_bytes': longest,
                                        'text_field_max_length': limit}), flush=True)


COUNT_CODE = ('import json,sqlite3,sys; from pathlib import Path; '
              'p=Path(sys.argv[1]).resolve(); '
              'db=sqlite3.connect(p.as_uri()+"?mode=ro",uri=True); '
              'print(json.dumps({"hybrid_bge_m3_rows":'
              'db.execute(\'SELECT COUNT(*) FROM "hybrid_bge_m3"\').fetchone()[0]})); '
              'db.close()')


def transaction(root, folder):
    folder.mkdir(parents=True, exist_ok=True)
    original = root / 'data/saved_index/milvus.db'
    pristine = folder / 'BASELINE.sqlite'
    modified = folder / 'MODIFIED_FILE.db'
    patch = folder / 'DIFF_FILE.json'
    verification = folder / 'VERIFICATION.txt'
    rollback = folder / 'ROLLBACK.sh'
    if pristine.exists() or modified.exists():
        raise FileExistsError('Use a new transaction folder; existing proof is retained')
    baseline_hash = digest(original)
    shutil.copy2(original, pristine)
    shutil.copy2(original, modified)
    ledger = []

    def execute(label, command):
        result = subprocess.run(command, capture_output=True, text=True)
        ledger.append({'label': label, 'command': command, 'stdout': result.stdout,
                       'stderr': result.stderr, 'exit_status': result.returncode})
        verification.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n',
                                encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'{label} failed; see {verification}')
        return result

    baseline = execute('BASELINE', [sys.executable, '-c', COUNT_CODE, str(pristine)])
    if json.loads(baseline.stdout)['hybrid_bge_m3_rows'] != 0:
        raise ValueError('This repair is restricted to the observed empty source index')
    build = execute('BUILD_ON_TARGET', [sys.executable, str(Path(__file__).resolve()),
                                       '--root', str(root), '--worker', str(modified)])
    worker_stats = json.loads(next(line[len('REBUILD_STATS '):]
                                  for line in build.stdout.splitlines()
                                  if line.startswith('REBUILD_STATS ')))
    connection = sqlite3.connect(modified)
    try:
        checkpoint = connection.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
        if checkpoint[0] != 0:
            raise ValueError('Cannot checkpoint the staged index while a writer is active')
        if connection.execute('PRAGMA journal_mode=DELETE').fetchone()[0] != 'delete':
            raise ValueError('Staged index is not a self-contained SQLite file')
        integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
    finally:
        connection.close()
    if integrity != 'ok':
        raise ValueError('Rebuilt SQLite integrity check failed')
    changed = execute('MODIFIED', [sys.executable, '-c', COUNT_CODE, str(modified)])
    rows = json.loads(changed.stdout)['hybrid_bge_m3_rows']
    if rows <= 0 or rows != worker_stats['vector_rows']:
        raise ValueError('Stored SQLite rows differ from the successfully embedded documents')
    old, new = pristine.read_bytes(), modified.read_bytes()
    prefix = 0
    while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(old), len(new)) - prefix and
           old[-suffix - 1] == new[-suffix - 1]):
        suffix += 1
    replacement = new[prefix:len(new) - suffix if suffix else len(new)]
    delta = {'format': 'binary-replace-v1', 'baseline_sha256': baseline_hash,
             'modified_sha256': digest(modified), 'prefix_bytes': prefix,
             'suffix_bytes': suffix,
             'replacement_base64': base64.b64encode(replacement).decode('ascii')}
    patch.write_text(json.dumps(delta) + '\n', encoding='utf-8')
    loaded = json.loads(patch.read_text(encoding='utf-8'))
    reconstructed = (old[:loaded['prefix_bytes']] +
                     base64.b64decode(loaded['replacement_base64']) +
                     (old[len(old) - loaded['suffix_bytes']:] if loaded['suffix_bytes'] else b''))
    if hashlib.sha256(reconstructed).hexdigest() != delta['modified_sha256']:
        raise ValueError('Binary patch did not reconstruct the modified file')
    rollback.write_bytes(b'#!/bin/sh\nset -eu\n'
                         b'if [ "$#" -ne 1 ]; then '
                         b'echo "usage: ROLLBACK.sh TARGET_COPY" >&2; exit 2; fi\n'
                         b'dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                         b'case "$1" in "$dir/BASELINE.sqlite"|'
                         b'"$dir/MODIFIED_FILE.db") exit 2;; esac\n'
                         b'cp -- "$dir/BASELINE.sqlite" "$1"\n')
    rollback.chmod(0o700)
    restored = folder / 'rollback-copy.sqlite'
    shutil.copy2(modified, restored)
    execute('EXECUTE_ROLLBACK', ['/bin/sh', str(rollback), str(restored)])
    restored_result = execute('ROLLBACK', [sys.executable, '-c', COUNT_CODE, str(restored)])
    if json.loads(restored_result.stdout)['hybrid_bge_m3_rows'] != 0:
        raise ValueError('Rollback did not restore the original empty collection')
    if digest(restored) != baseline_hash:
        raise ValueError('Restored file does not match pristine source bytes')
    if digest(original) != baseline_hash:
        raise ValueError('Original target copy changed while the repair was staged')
    shutil.copy2(modified, original)
    deployed = execute('DEPLOY_MODIFIED', [sys.executable, '-c', COUNT_CODE, str(original)])
    if json.loads(deployed.stdout)['hybrid_bge_m3_rows'] != rows:
        raise ValueError('Deployed collection differs from the verified modified artifact')
    if digest(original) != delta['modified_sha256']:
        raise ValueError('Deployed index differs from verified modified artifact')
    result = {'changed_field': 'hybrid_bge_m3 vector rows', 'baseline_rows': 0,
              'modified_rows': rows, 'rollback_rows': 0, 'baseline_sha256': baseline_hash,
              'modified_sha256': delta['modified_sha256'], 'rollback_sha256': digest(restored),
              'binary_patch_verified': True, 'deployed': True, 'build': worker_stats,
              'roles': {name: str(path.resolve()) for name, path in
                        [('MODIFIED_FILE', modified), ('DIFF_FILE', patch),
                         ('VERIFICATION', verification), ('ROLLBACK', rollback)]}}
    (folder / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for path in (modified, patch, verification, rollback):
        with path.open('rb') as stream:
            stream.read(1)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--transaction-dir', type=Path)
    parser.add_argument('--worker', type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.root.resolve(), args.worker.resolve())
    elif args.transaction_dir:
        transaction(args.root.resolve(), args.transaction_dir.resolve())
    else:
        parser.error('--transaction-dir is required for the verified repair')
