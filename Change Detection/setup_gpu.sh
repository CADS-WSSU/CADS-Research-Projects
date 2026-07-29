#!/usr/bin/env bash
# Idempotent setup for the SCADS GPU VM (A10G). Safe to re-run; only does missing work.
# After a VM wipe:  rsync code from Mac, then `bash vm_bootstrap.sh`, then rsync caches.
set -e
cd "$(dirname "$0")"

[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -U pip

# cdet-api declares python>=3.13 but runs fine on 3.12 -> ignore the constraint.
python -c "import cdet_api" 2>/dev/null || \
  pip install -q --ignore-requires-python "git+https://github.com/trec-changedet/cdet-api"

# Default torch wheel is too new for this driver -> install the cu121 build.
python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null || \
  pip install -q "torch==2.4.*" --index-url https://download.pytorch.org/whl/cu121

pip install -q sentence-transformers rank-bm25 spacy huggingface_hub pytest
python -c "import en_core_web_sm" 2>/dev/null || python -m spacy download en_core_web_sm -q

# Use the GPU.
grep -q 'device = "cuda"' config.toml || sed -i 's/device = "mps"/device = "cuda"/' config.toml
mkdir -p data logs state embeddings_cache

# Corpus + doc DB (skip if already present).
[ -f data/eng-docs.jsonl ] || \
  curl -sL -o data/eng-docs.jsonl "https://huggingface.co/datasets/trec-ragtime/ragtime1/resolve/main/eng-docs.jsonl"
[ -f docs.db ] || python -m cdet_api.scripts.build_doc_db data/eng-docs.jsonl

python -c "import torch; print('cuda available:', torch.cuda.is_available())"
echo "BOOTSTRAP OK."
echo "If embeddings_cache/{emb,docfeat,rerank}.sqlite are missing, copy them from the Mac:"
echo "  rsync -az embeddings_cache/*.sqlite scads-vm:~/cdet-2026/embeddings_cache/"
echo "(or regenerate: python -m cdet2026.precompute_embeddings && python -m cdet2026.precompute_features)"
