#!/bin/bash
export CPTR_DATA_DIR="${CPTR_DATA_DIR:-$(cd "$(dirname "$0")" && pwd)/.cptr}"

# run in normal mode
uv run --extra all cptr run --reload --host 0.0.0.0 --port 9741 --headless

# run in debug mode
# uv run --extra all python -m debugpy --listen 5678 --wait-for-client -m cptr.cli run --host 127.0.0.1 --port 9741 --headless