# Simulator agent skills

Skills implement the tools used by the reservoir simulation assistant (parse simulator input files, run simulations, RAG, plot results, etc.). Each skill has a `test.py` you can run to verify it in isolation.

## Testing skills in Docker

The recommended way to test skills is inside the Docker environment, where the simulator (OPM Flow) and (optionally) Milvus are available.

### 1. Start containers and attach

```bash
# From repo root
cd sim_agent
docker compose up -d
docker exec -it sim-agent bash
```

Inside the container you're at `/workspace/sim_agent`.

### 2. Run all skill tests (or a subset)

```bash
# Run all skills: input_file → simulation → rag → results → plot
./src/simulator_agent/skills/run_skill_tests.sh

# Run only specific skills
./src/simulator_agent/skills/run_skill_tests.sh input_file
./src/simulator_agent/skills/run_skill_tests.sh input_file simulation rag
```

**Requirements per skill:**

| Skill        | Requires                          | Notes |
|-------------|------------------------------------|-------|
| input_file   | A simulator input file (default: spe1) | No extra deps. |
| simulation  | Simulator, input file              | Runs a short `run_simulation` test. |
| rag         | Milvus + ingested collections      | Set `MILVUS_URI`; ingest docs first. |
| results     | A case with .SMSPEC (and optionally .INIT/.EGRID) | Use a directory where a simulation was run. |
| plot        | A directory with .SMSPEC files     | Run a simulation first or use existing output. |

### 3. Run a single skill’s test by hand

Use the same paths as in the script (paths are valid inside the container):

```bash
# Data file skill (parse, validate, modify, patch)
python -m simulator_agent.skills.input_file_skill.test --file data/knowledge_base/examples/spe1/SPE1CASE1.DATA
python -m simulator_agent.skills.input_file_skill.test --file data/knowledge_base/examples/spe1/SPE1CASE1.DATA --tool parse_simulation_input_file

# Simulation skill (run_simulation, monitor, stop)
python -m simulator_agent.skills.simulation_skill.test --file data/knowledge_base/examples/spe1/SPE1CASE1.DATA --output-dir data/knowledge_base/examples/spe1 --tool run_simulation

# RAG skill (simulator_manual, simulator_examples) – needs Milvus + ingested docs
python -m simulator_agent.skills.rag_skill.test --config config/config.yaml --tool simulator_manual

# Results skill (read_simulation_summary, read_grid_properties, etc.) – needs .SMSPEC
python -m simulator_agent.skills.results_skill.test --case data/knowledge_base/examples/spe1/SPE1CASE1.DATA

# Plot skill – needs directory with .SMSPEC files
python -m simulator_agent.skills.plot_skill.test --output-dir data/knowledge_base/examples/spe1
```

### 4. Override paths (inside Docker)

```bash
export DATA_FILE=data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA
export OUTPUT_DIR=data/example_cases/SPE10/CASE
./src/simulator_agent/skills/run_skill_tests.sh input_file simulation
```

## Skill list

- **input_file_skill** – parse_simulation_input_file, modify_simulation_input_file, patch_simulation_input_keyword  
- **simulation_skill** – run_and_heal, run_simulation, monitor_simulation, stop_simulation  
- **rag_skill** – simulator_manual, simulator_examples  
- **results_skill** – read_simulation_summary, read_grid_properties  
- **plot_skill** – plot_summary_metric, plot_compare_summary_metric  

Each skill’s `test.py` supports `--tool <name>` to run a single tool and `--help` for options.
