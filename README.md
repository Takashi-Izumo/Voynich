# Voynich shelf reconstruction reproducibility package

See `README_JA.md` for the full documentation. The package contains the source data snapshot, exact 600+8 tablet inventories, reconstructed analysis code, archived simulation outputs, and explicit provenance notes.

Quick start:

```bash
python -m pip install -r requirements.txt
python code/12_run_all.py --budget-runs 50
python code/13_verify_package.py
```

Important limitation: the original integer optimizer that produced every 475--650-tablet candidate was not recovered. The exact published 600-tablet inventory is preserved and can be simulated exactly; the budget sensitivity code is a transparent reconstruction around that inventory.
