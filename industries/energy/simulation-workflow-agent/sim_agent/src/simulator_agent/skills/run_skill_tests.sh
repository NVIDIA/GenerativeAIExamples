#!/usr/bin/env bash
#
# Run all skill tests (for use inside Docker or from repo root with same paths).
#
# Usage (inside Docker):
#   docker exec -it sim-agent bash
#   cd /workspace/sim_agent && ./src/simulator_agent/skills/run_skill_tests.sh
#   # or run a subset:
#   ./src/simulator_agent/skills/run_skill_tests.sh input_file simulation
#
# Usage (from host, from sim_agent dir):
#   docker exec -it sim-agent bash -c "cd /workspace/sim_agent && ./src/simulator_agent/skills/run_skill_tests.sh"
#
# Optional env (Docker already sets these when using docker-compose):
#   MILVUS_URI=http://standalone:19530  (for RAG skill)
#   NVIDIA_API_KEY=...                  (for modify_simulation_input_file if using LLM)
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Repo root: skills -> simulator_agent -> src -> sim_agent
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

# Paths that work inside Docker (working_dir = /workspace/sim_agent)
DATA_FILE="${DATA_FILE:-data/knowledge_base/examples/spe1/SPE1CASE1.DATA}"
OUTPUT_DIR="${OUTPUT_DIR:-data/knowledge_base/examples/spe1}"
CONFIG="${CONFIG:-config/config.yaml}"

run_test() {
    local name="$1"
    shift
    echo ""
    echo "=============================================="
    echo "  Skill: $name"
    echo "=============================================="
    if "$@"; then
        echo "  $name: OK"
        return 0
    else
        echo "  $name: FAILED (exit $?)"
        return 1
    fi
}

# Which skills to run (default: all)
SKILLS=("$@")
if [ ${#SKILLS[@]} -eq 0 ]; then
    SKILLS=(input_file simulation rag results plot)
fi

FAILED=0

for skill in "${SKILLS[@]}"; do
    case "$skill" in
        input_file)
            if [ ! -f "$DATA_FILE" ]; then
                echo "Skip input_file_skill: $DATA_FILE not found"
                continue
            fi
            run_test "input_file_skill" python -m simulator_agent.skills.input_file_skill.test --file "$DATA_FILE" || FAILED=$((FAILED+1))
            ;;
        simulation)
            if [ ! -f "$DATA_FILE" ]; then
                echo "Skip simulation_skill: $DATA_FILE not found"
                continue
            fi
            run_test "simulation_skill (run_simulation)" python -m simulator_agent.skills.simulation_skill.test \
                --file "$DATA_FILE" --output-dir "$OUTPUT_DIR" --tool run_simulation || FAILED=$((FAILED+1))
            ;;
        rag)
            if [ -n "$CONFIG" ] && [ -f "$CONFIG" ]; then
                run_test "rag_skill" python -m simulator_agent.skills.rag_skill.test \
                    --query "COMPDAT keyword format" --config "$CONFIG" || FAILED=$((FAILED+1))
            else
                echo "Skip rag_skill: config not found ($CONFIG). Need Milvus + ingested docs."
            fi
            ;;
        results)
            CASE_PATH="${CASE_PATH:-$DATA_FILE}"
            if [ ! -f "$CASE_PATH" ]; then
                echo "Skip results_skill: $CASE_PATH not found"
                continue
            fi
            run_test "results_skill" python -m simulator_agent.skills.results_skill.test --case "$CASE_PATH" || FAILED=$((FAILED+1))
            ;;
        plot)
            if [ ! -d "$OUTPUT_DIR" ]; then
                echo "Skip plot_skill: output dir $OUTPUT_DIR not found"
                continue
            fi
            if ! compgen -G "$OUTPUT_DIR"/*.SMSPEC >/dev/null 2>&1; then
                echo "Skip plot_skill: no .SMSPEC in $OUTPUT_DIR (run a simulation first)"
                continue
            fi
            run_test "plot_skill" python -m simulator_agent.skills.plot_skill.test --output-dir "$OUTPUT_DIR" || FAILED=$((FAILED+1))
            ;;
        *)
            echo "Unknown skill: $skill (use: input_file simulation rag results plot)"
            FAILED=$((FAILED+1))
            ;;
    esac
done

echo ""
echo "=============================================="
if [ "$FAILED" -eq 0 ]; then
    echo "  All requested skill tests completed successfully."
    exit 0
else
    echo "  $FAILED skill test(s) failed."
    exit 1
fi
