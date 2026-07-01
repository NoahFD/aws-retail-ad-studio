#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required. Install Node 20.19+ or 22.12+ before running the frontend." >&2
  exit 1
fi

node - <<'NODE'
const [major, minor] = process.versions.node.split(".").map(Number);
const supported = (major === 20 && minor >= 19) || major >= 22;
if (!supported) {
  console.error(`Unsupported Node.js ${process.versions.node}. Vite requires Node 20.19+ or 22.12+; Node 21.x is not supported.`);
  process.exit(1);
}
NODE

if [ ! -d ".venv" ]; then
  python3.11 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r backend/requirements.txt

if [ ! -d "frontend/node_modules" ]; then
  (cd frontend && npm install)
fi

cleanup() {
  jobs -p | xargs -r kill
}
trap cleanup EXIT

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
(cd frontend && npm run dev)
