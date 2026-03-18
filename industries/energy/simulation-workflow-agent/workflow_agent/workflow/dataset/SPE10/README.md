# SPE10 Dataset (Workflow Optimization)

This dataset is a derivative of the [SPE10 benchmark model](https://www.spe.org/web/csp/datasets/set02.htm) (Society of Petroleum Engineers Comparative Solution Project). It uses a top-layer subset for faster runs.

**License:** [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1.0/)

## Structure

```
SPE10/
├── BASE/
│   └── SPE10.DATA             # Base case (reference)
├── TEMPLATE/
│   └── SPE10.DATA             # Template for optimization runs (variables substituted)
├── INCLUDE/
│   ├── PERMX_TOPLAYER.GRDECL  # Permeability
│   └── PORO_TOPLAYER.GRDECL   # Porosity
└── README.md
```

Used by the workflow optimization agent (GA, PSO) for injector placement and similar optimization tasks.
