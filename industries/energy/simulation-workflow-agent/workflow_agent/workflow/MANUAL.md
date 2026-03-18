# Workflow Manual

Documentation for workflow modules. Each module can be run standalone via Docker.

---

## optimization

GA/PSO optimization for reservoir simulation templates using OPM Flow.

### What It Does

The tool runs GA or PSO optimization on a reservoir template (`.DATA`) with
`${VAR}` placeholders. For each candidate solution it:

1. Substitutes variables into the template
2. Runs the simulator command
3. Evaluates EUR or NPV
4. Tracks the best solution and writes results

### Algorithms Supported

Two single-objective global optimization algorithms are available (via **pymoo**):

| Algorithm | Description |
|-----------|-------------|
| **GA** (Genetic Algorithm) | Evolutionary search: population of individuals, selection, crossover (SBX), and mutation (PM). Default. |
| **PSO** (Particle Swarm Optimization) | Swarm-based search: particles move in the variable space; velocity is updated using personal best and global best. |

Select in config with `algorithm.type: "GA"` or `"PSO"`.

### GA — Tuning Parameters and Equations

**Config block:** `algorithm.ga_params`

**Simulated Binary Crossover (SBX).** From two parents $x^{(1)}_d$, $x^{(2)}_d$ (per dimension $d$), sample $u \in [0,1]$ and compute spread factor $\bar\beta$ using distribution index $\eta_c$ (crossover_eta):

$$
\bar\beta = \begin{cases} (2u)^{1/(\eta_c+1)} & u \le 0.5 \\[6pt] \dfrac{1}{\bigl(2(1-u)\bigr)^{1/(\eta_c+1)}} & u > 0.5 \end{cases}
$$

Offspring:

$$
c^{(1)}_d = \frac{1}{2}\Bigl[\bigl(x^{(1)}_d + x^{(2)}_d\bigr) - \bar\beta\,\bigl|x^{(2)}_d - x^{(1)}_d\bigr|\Bigr], \qquad
c^{(2)}_d = \frac{1}{2}\Bigl[\bigl(x^{(1)}_d + x^{(2)}_d\bigr) + \bar\beta\,\bigl|x^{(2)}_d - x^{(1)}_d\bigr|\Bigr]
$$

Larger $\eta_c$ gives offspring closer to the parents; smaller $\eta_c$ allows more spread.

**Polynomial Mutation (PM).** For a variable $x_d \in [x_d^L, x_d^U]$, sample $u \in [0,1]$ and compute $\bar\delta$ using distribution index $\eta_m$ (mutation_eta):

$$
\bar\delta = \begin{cases} \bigl(2u\bigr)^{1/(\eta_m+1)} - 1 & u < 0.5 \\[6pt] 1 - \bigl(2(1-u)\bigr)^{1/(\eta_m+1)} & u \ge 0.5 \end{cases}
$$

Mutated value: $x'_d = x_d + \bar\delta\,(x_d^U - x_d^L)$. Larger $\eta_m$ gives smaller perturbations.

| Parameter | Config key | Default | Meaning |
|-----------|------------|---------|--------|
| Population size | `pop_size` | 20 | Number of individuals per generation. |
| Generations | `n_generations` | 10 | Number of generations. |
| Crossover probability | `crossover_prob` | 0.9 | Probability of applying crossover to a parent pair. |
| Crossover eta | `crossover_eta` | 15 | Distribution index for SBX; larger η gives offspring closer to parents. |
| Mutation probability | `mutation_prob` | 0.1 | Probability of mutating each variable. |
| Mutation eta | `mutation_eta` | 20 | Distribution index for PM; controls spread of mutation. |

**Note:** Variables are integer; the problem uses appropriate bounds and sampling. The solver minimizes the negative objective so that maximizing EUR or NPV is equivalent to minimizing $-f$.

### PSO — Tuning Parameters and Equations

**Config block:** `algorithm.pso_params`

**Velocity and position update (conventional PSO):**

$$
v_{i,d}^{t+1} = w\, v_{i,d}^t + c_1 r_1 (p_{i,d} - x_{i,d}^t) + c_2 r_2 (g_d - x_{i,d}^t)
$$

$$
x_{i,d}^{t+1} = x_{i,d}^t + v_{i,d}^{t+1}
$$

- $v_{i,d}$: velocity of particle $i$ in dimension $d$
- $x_{i,d}$: position
- $p_i$: personal best position of particle $i$
- $g$: global best position
- $r_1, r_2$: random numbers in $[0,1]$

| Parameter | Config key | Default | Meaning |
|-----------|------------|---------|--------|
| Population size | `pop_size` | 20 | Number of particles (swarm size). |
| Generations | `n_generations` | 10 | Number of iterations. |
| Inertia weight | `w` | 0.9 | Weight of previous velocity. |
| Cognitive coefficient | `c1` | 2.0 | Weight of attraction to personal best. |
| Social coefficient | `c2` | 2.0 | Weight of attraction to global best. |
| Adaptive | `adaptive` | true | Use adaptive PSO variant when available. |

### Objective Methods Supported

| Method | Description |
|--------|-------------|
| **EUR** | Maximize cumulative field oil production at end of simulation (Mstb). |
| **NPV** | Maximize net present value: discounted cash flows including initial drilling cost (USD). |

Set in config with `objective.mode: "EUR"` or `"NPV"`. For NPV, an `economics` block is required (see [Economics (NPV Only)](#economics-npv-only)).

### How EUR Is Calculated

Cumulative field oil production at the end of the run (from simulation summary FOPT), converted to thousands of stock-tank barrels:

$$
\text{EUR} = \frac{\text{FOPT}_{\text{end}}}{1000} \quad \text{(Mstb)}
$$

- **FOPT:** field oil production total from the simulator summary (stb). The code uses the last time step.

### How NPV Is Calculated

NPV is the sum of discounted cash flows, with the drilling cost as the initial cash flow (step 0):

$$
\text{NPV} = \sum_{k=0}^{N} \frac{\text{CF}_k}{(1+r)^{t_k}}
$$

- $\text{CF}_0 = -C_{\text{drill}}$: initial cash flow at $t_0=0$ (drilling cost). $C_{\text{drill}} = n_{\text{wells}} \times L_{\text{well}} \times c_{\text{m}}$.
- $\text{CF}_k$ ($k \geq 1$): net operating cash flow in period $k$ = oil revenue + water production cost + water injection cost (all in USD). Revenue and costs use simulator rates (FOPR, FWPR, FWIR) and the economics parameters.
- $r$: annual discount rate.
- $t_k$: time in years for period $k$ (from simulation time steps; $t_0=0$).

The implementation computes discounted operating cash flows per period and subtracts the drilling cost once (equivalent to including $\text{CF}_0 = -C_{\text{drill}}$ in the sum).

### Requirements

- Docker: use `workflow` container (OPM Flow and dependencies pre-installed)

### Run (Docker)

```bash
# From workflow_agent/workflow
docker compose up -d
docker exec -it workflow bash

# Inside container (working_dir: /workspace/workflow)
python optimization/src/run_optimization.py optimization/conf/testcase_ga.yaml
```

To validate a config without running simulations:

```bash
python optimization/src/run_optimization.py optimization/conf/testcase_ga.yaml --dry-run
```

### Config Format (YAML)

Every config must include these sections:

```
paths:
  template: "dataset/CASE/TEMPLATE/CASE.DATA"
  sim_dir_base: "dataset/CASE"
  case_name: "CASE_RUN"

variables:
  VAR1: {min: 1, max: 10, type: int}
  VAR2: {min: 5, max: 20, type: int}

algorithm:
  type: "GA"   # or "PSO"
  pop_size: 20
  n_generations: 10
  n_parallel: 4
  seed: 42
  ga_params:
    crossover_prob: 0.9
    crossover_eta: 15
    mutation_prob: 0.1
    mutation_eta: 20
  # for PSO:
  # pso_params:
  #   w: 0.9
  #   c1: 2.0
  #   c2: 2.0
  #   adaptive: true

objective:
  mode: "EUR"  # or "NPV"

simulation:
  simulator_command: "flow ${sim_file_path}"
  timeout: 600

output:
  run_name: "my_run"
  save_comprehensive: true
  save_log: true
  log_file: "my_run.log"
  save_plots: true
```

### simulator_command

This string is executed for each candidate simulation. The placeholder
`${sim_file_path}` is replaced with the absolute path to the generated `.DATA`
file. Example:

```
simulation:
  simulator_command: "mpirun -np 2 flow ${sim_file_path}"
```

### Economics (NPV Only)

If `objective.mode` is `NPV`, an `economics` block is required:

```
economics:
  oil_price: 70.0
  water_injection_cost: -5.0
  water_production_cost: -2.0
  discount_rate: 0.10
  num_wells: 30
  well_length: 1700
  drilling_cost_per_meter: 5000
```

### Outputs

Each run creates:

```
dataset/<CASE>/<SIM_NAME>_YYYYMMDD_HHMMSS.sim/
```

Files:

- `<run_name>_config.json`
- `<run_name>_results.json`
- `<run_name>_evaluations.csv`
- `<run_name>_summary.txt`
- plots (if enabled)

Typical contents:

- `*_config.json`: resolved config + metadata (paths, algorithm, objective)
- `*_results.json`: best solution, run stats, convergence history
- `*_evaluations.csv`: row per evaluation with variables + objective
- `*_summary.txt`: human-readable overview of the run
- plots: progress over evaluations and best-so-far trend

### Troubleshooting

- If the simulator fails, check the command in `simulation.simulator_command`.
- For `NPV` runs, confirm `economics` is present and valid.
- If you see timeouts, increase `simulation.timeout`.

---

## history_matching

*Placeholder – coming soon.*

History matching workflow for reservoir model calibration.
