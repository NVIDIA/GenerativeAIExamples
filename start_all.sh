#!/usr/bin/env bash
set -euo pipefail

SESSION="historical-rag"
ROOT="$(pwd)"

# --- helpers ---
have() { command -v "$1" >/dev/null 2>&1; }
port_open() { ss -ltn | awk '{print $4}' | grep -qE ":$1$"; }

if ! have tmux; then
  echo "ERROR: tmux not installed. Install: sudo apt-get install -y tmux"
  exit 1
fi

# Kill old session if it exists
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"

tmux new-session -d -s "$SESSION" -n "rag"

# Pane 1: RAG backend (8001)
tmux send-keys -t "$SESSION:rag" "cd \"$ROOT/backend-rag\" || exit 1" C-m
tmux send-keys -t "$SESSION:rag" "echo '[RAG] starting on :8001...'" C-m
# If you start it differently, replace the next line with your known start command
tmux send-keys -t "$SESSION:rag" "python3 -m uvicorn app:app --host 0.0.0.0 --port 8001" C-m

# Pane 2: LLM proxy (8002)
tmux split-window -h -t "$SESSION:rag"
tmux send-keys -t "$SESSION:rag.1" "cd \"$ROOT/backend-dynamo/llm-proxy\" || exit 1" C-m
tmux send-keys -t "$SESSION:rag.1" "echo '[PROXY] starting on :8002...'" C-m
tmux send-keys -t "$SESSION:rag.1" "python3 proxy.py" C-m

# Window: frontend (3000)
tmux new-window -t "$SESSION" -n "frontend"
tmux send-keys -t "$SESSION:frontend" "cd \"$ROOT/frontend\" || exit 1" C-m
tmux send-keys -t "$SESSION:frontend" "echo '[FRONTEND] starting on :3000...'" C-m
tmux send-keys -t "$SESSION:frontend" "npm start" C-m

# Show quick hints
tmux new-window -t "$SESSION" -n "status"
tmux send-keys -t "$SESSION:status" "echo 'Attach: tmux attach -t $SESSION'" C-m
tmux send-keys -t "$SESSION:status" "echo 'Stop:   tmux kill-session -t $SESSION'" C-m
tmux send-keys -t "$SESSION:status" "echo 'Ports:'" C-m
tmux send-keys -t "$SESSION:status" "ss -ltn | egrep ':3000|:8001|:8002' || true" C-m

echo "Started. Attach with: tmux attach -t $SESSION"