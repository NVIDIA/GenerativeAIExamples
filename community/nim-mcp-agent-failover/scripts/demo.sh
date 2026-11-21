#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
# SPDX-License-Identifier: Apache-2.0
# The 5 minute live demo, in one command.
#
#   bash scripts/demo.sh              hosted NIM (needs NVIDIA_API_KEY) plus the offline failover act
#   bash scripts/demo.sh --offline    everything against the bundled mock, no network, no key
#   DEMO_PAUSE=1 bash scripts/demo.sh wait for Enter between acts (use this on stage)
#
# Point it at a self-hosted NIM or any OpenAI-compatible server with NIM_BASE_URL.
set -euo pipefail
cd "$(dirname "$0")/.."

OFFLINE=0
[ "${1:-}" = "--offline" ] && OFFLINE=1
MOCK_PORT="${MOCK_PORT:-8089}"
MOCK_BASE="http://127.0.0.1:${MOCK_PORT}/v1"
BENCH_MODELS=()

act() {
  if [ "${DEMO_PAUSE:-0}" = "1" ]; then read -r -p $'\n[Enter for the next act] ' _; fi
  printf '\n\033[1;32m=== %s ===\033[0m\n' "$1"
}
run() { printf '\033[2m$ %s\033[0m\n' "$*"; "$@"; }

[ -d node_modules/@modelcontextprotocol/sdk ] || { echo "Run npm install first (the agent needs the MCP SDK)."; exit 1; }

node local/mock-nim.mjs --port "$MOCK_PORT" >/dev/null 2>&1 &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT
for _ in $(seq 1 40); do curl -fsS "$MOCK_BASE/models" >/dev/null 2>&1 && break; sleep 0.1; done
# Make sure the thing answering on that port is OUR mock, not a leftover or another server.
if ! kill -0 "$MOCK_PID" 2>/dev/null || ! curl -fsS -D - -o /dev/null "$MOCK_BASE/models" 2>/dev/null | grep -qi '^x-mock-nim: 1'; then
  echo "Port $MOCK_PORT is busy or the mock did not start. Try: MOCK_PORT=8189 bash scripts/demo.sh"
  exit 1
fi

if [ "$OFFLINE" = "1" ]; then
  export NIM_BASE_URL="$MOCK_BASE"
  export NIM_MODEL="mock/fast"
  BENCH_MODELS=(--models mock/fast,mock/slow)
  echo "Offline mode: every call below goes to the bundled mock at $MOCK_BASE. No model is running."
elif [ -z "${NVIDIA_API_KEY:-}" ] && [ -z "${NIM_BASE_URL:-}" ]; then
  echo "Set NVIDIA_API_KEY first (free at https://build.nvidia.com), or run: bash scripts/demo.sh --offline"
  exit 1
fi

act "Act 1: first call. Discover a model, stream an answer"
run node quickstart/node/quickstart.mjs

act "Act 2: benchmark. Time to first token and tokens per second, measured right now"
run node router/nim-route.mjs bench --runs 2 --max-tokens 128 ${BENCH_MODELS[@]+"${BENCH_MODELS[@]}"}

act "Act 3: failover. One model is rate limited, one is end of life, the router still answers"
echo "This act always uses the offline mock so the failures are repeatable."
NIM_BASE_URL="$MOCK_BASE" run node router/nim-route.mjs route --no-bench \
  --models mock/busy,mock/retired,mock/fast --prompt "Who served this request?"

act "Act 4: route for real. Rank by measured speed, send the prompt to the fastest healthy model"
run node router/nim-route.mjs route --runs 1 ${BENCH_MODELS[@]+"${BENCH_MODELS[@]}"} \
  --prompt "In two sentences: why does time to first token matter for a voice agent?"

act "Act 5: the agent. Nemotron calls MCP tools to answer a developer question"
if [ "$OFFLINE" = "1" ]; then
  run node agent/agent.mjs "Is mock/retired still available?" --model mock/fast
else
  run node agent/agent.mjs "Is meta/llama-3.1-8b-instruct still available? If not, which small NVIDIA Nemotron model should I use for a tool-calling agent? Check that your pick is alive and supports tools."
fi

printf '\n\033[1;32mDone.\033[0m Same client code for every act. Only NIM_BASE_URL changed.\n'
