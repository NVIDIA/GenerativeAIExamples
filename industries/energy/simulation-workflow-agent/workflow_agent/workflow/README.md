# Workflow Modules

Independent workflow modules used by the agentic workflow. Each can be run standalone via Docker. Builds `workflow:latest` image, which workflow_agent reuses.

## Optimization

GA/PSO optimization for reservoir simulation templates using OPM Flow.

**Quick Start (Docker)**

```bash
# From workflow_agent/workflow
docker compose build
docker compose up -d
docker exec -it workflow bash

# Inside container (working_dir: /workspace/workflow)
python optimization/src/run_optimization.py optimization/conf/testcase_ga.yaml
```

Or from workflow_agent: `docker compose -f workflow/docker-compose.yml up -d`

**Configs** (in `optimization/conf/`):

- `testcase_ga.yaml` – SPE10 top-layer, GA
- `testcase_pso.yaml` – SPE10 top-layer, PSO

See `MANUAL.md` for full documentation.

## History Matching

*Placeholder – coming soon.*

## Design of Experiment

*Placeholder – coming soon.*
