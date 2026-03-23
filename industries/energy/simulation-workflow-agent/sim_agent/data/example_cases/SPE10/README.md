# Example Cases

This dataset is a derivative of the [SPE10 benchmark model](https://www.spe.org/web/csp/datasets/set02.htm) (Society of Petroleum Engineers Comparative Solution Project). It uses a top-layer subset for faster runs.

**License:** [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1.0/)

## Structure

```
SPE10/
├── CASE/
│   ├── SPE10_TOPLAYER.DATA             # Base case
│   ├── SPE10_TOPLAYER_INFILL.DATA      # Infill scenario
│   └── SPE10_TOPLAYER_INFILL_TEST.DATA # Infill scenario with seeded error (for self-healing tests)
├── INCLUDE/
│   ├── PERMX_TOPLAYER.GRDECL        # Permeability
│   └── PORO_TOPLAYER.GRDECL         # Porosity
└── README.md
```

