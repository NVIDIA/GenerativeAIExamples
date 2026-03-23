# Reservoir Simulation Assistant - Example Queries

Quick examples of what you can ask the assistant. This repo uses a reference simulator (OPM Flow in the examples).

## 🚀 Getting Started

### Interactive Mode
```bash
python -m simulator_agent --config config/config.yaml --interactive
```

### Single Query
```bash
python -m simulator_agent --config config/config.yaml \
    --input "Your question here"
```

---

## 📚 Example Questions

### 1. Understanding Simulator Keywords

```
What does the WELSPECS keyword do?
```

```
Explain the WCONPROD keyword and its parameters
```

```
What is the difference between WCONPROD and WCONINJE?
```

---

### 2. Simulator Input File Structure

```
What are the required sections in a simulator input file?
```

```
How do I specify well locations in the input file?
```

```
What is the correct format for TSTEP?
```

---

### 3. Working with Simulator Input Files

```
Parse the input file at /path/to/CASE.DATA and explain its structure
```

```
Modify /path/to/CASE.DATA to set well PROD1 to 5000 STB/day
```

```
Validate the input file at /path/to/MODIFIED.DATA
```

---

### 4. Running Simulations

```
Run the simulation on data/knowledge_base/examples/spe1/SPE1CASE1.DATA 
```

```
Run the test case data/knowledge_base/examples/spe1/SPE1CASE1.DATA with 2 MPI processes (np=2)
```

```
Monitor the simulation at /path/to/CASE.DATA and show progress
```

```
Parse the simulation output from /path/to/CASE.PRT
```

---

### 5. Scenario testing (modify then run)

Test a variant of a case: the agent will parse the simulator input file, apply your change to a **new** file named `BASENAME_AGENT_GENERATED.DATA` (same directory as the original), run that file, and report results. You can use `@path` or plain paths.

**Single-query (copy-paste):**

```bash
python -m simulator_agent --config config/config.yaml --input "Can you test a scenario with increased water injection rate at I1 in data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA" --log-file debug.log
```

**With @-style path (e.g. from Cursor):**

```bash
python -m simulator_agent --config config/config.yaml --input "Can you test a scenario with increased water injection rate at I1 in @sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA" --log-file debug.log
```

**Other example phrasings:**

```
Test a scenario with higher water injection at well I1 in data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA
```

```
Run a case with decreased BHP at producers in data/knowledge_base/examples/spe1/SPE1CASE1.DATA
```

---

### 6. Analyzing Results

```
Read simulation summary from /path/to/CASE for variables FOPT and FOPR
```

```
Analyze production performance for /path/to/CASE.DATA
```

**Flow diagnostics** (time-of-flight, injector-producer allocation, F-Phi, Lorenz coefficient). Requires simulation run with `RPTRST BASIC=2 FLOWS PRESSURE ALLPROPS`:

```
Run flow diagnostics on data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA
```

```
Compute flow diagnostics for the attached case to get time-of-flight and allocation factors
```

```
Get grid structure information from /path/to/CASE.DATA
```

```
Read pressure and saturation from /path/to/CASE.DATA for the last timestep
```

---

### 7. Visualization

```
Plot FOPT vs time from /path/to/CASE.DATA
```

```
Compare oil production rates between /path/to/CASE1.DATA and /path/to/CASE2.DATA
```

```
Plot well WOPR for producers in /path/to/CASE.DATA
```

---

### 8. Best Practices

```
What are best practices for setting timesteps?
```

```
What convergence parameters should I use for a black oil model?
```

```
What summary keywords should I use to track oil production?
```

---

### 9. Complex Workflows

```
I have a reservoir at /path/to/BASE.DATA. Parse it, then create a modified version 
with well PROD1 at 4000 STB/day, run the simulation, and plot the results.
```

```
Compare production strategies: run /path/to/RATE_CONTROL.DATA and 
/path/to/BHP_CONTROL.DATA, then plot cumulative oil production for both.
```

```
Analyze the grid structure of /path/to/CASE.DATA and show permeability distribution.
```

---

## 💡 Tips

### Be Specific with Paths
Instead of:
```
Parse the simulator input file
```

Use:
```
Parse /home/user/cases/SPE1/SPE1.DATA
```

---

### Ask Follow-up Questions
The assistant has conversation memory, so you can ask follow-ups:

```
User: Parse /path/to/CASE.DATA
Assistant: [shows structure]

User: What does the WCONPROD section do?
Assistant: [explains with context from the file]

User: Change PROD1 rate to 5000
Assistant: [modifies the file]
```

---

### Request Multiple Steps
```
Parse /path/to/BASE.DATA, modify well PROD1 to 6000 STB/day, 
validate the changes, then run the simulation.
```

---

### Ask for Documentation
```
Show me examples of WELSPECS from the simulator manual
```

```
What parameters does WCONPROD accept according to the documentation?
```

---

## 🎯 Common Use Cases

### Use Case 1: Quick Keyword Lookup
```bash
python -m simulator_agent --config config/config.yaml \
    --input "What parameters does TSTEP accept?"
```

### Use Case 2: File Analysis
```bash
python -m simulator_agent --config config/config.yaml \
    --input "Parse /data/reservoir/SPE1.DATA and explain the well configuration"
```

### Use Case 3: Batch Processing
```bash
# Create a script with multiple queries
cat << EOF > queries.txt
Parse /data/CASE1.DATA
Analyze production performance
Plot FOPT vs time
EOF

# Run interactively and paste queries
python -m simulator_agent --config config/config.yaml --interactive
```

---

## 🏃 Fast Mode

For quicker responses (3-5x faster):

```bash
python -m simulator_agent --config config/config.yaml --interactive
```

See `SPEED_OPTIMIZATIONS.md` for details.

---

## 📖 More Information

- **Full setup guide:** See `QUICKSTART.md`
- **Speed optimization:** See `SPEED_OPTIMIZATIONS.md`
- **Tool reference:** See `README.md`
