# Paper result → code/output map

| Paper location | Result | Code | Principal output |
|---|---|---|---|
| §2.1 | 23-character frequency threshold | `01_prepare_data.py` | `data/derived/whole_manuscript_glyph_counts.csv` |
| Table 1 | Seven-layer coverage/directionality | `02_seven_layer_analysis.py` | `outputs/tables/table1_seven_layer_directionality.json` |
| Table 1 | 50,000 randomizations | `02_seven_layer_analysis.py` | `outputs/tables/table1_randomization_rates.csv` |
| Table 2 | Seven-layer bifolium classification | `02_seven_layer_analysis.py` | `outputs/tables/table2_seven_layer_bifolium_classification.json`, `table2_folds.csv` |
| §2.4 | 2--5gram bifolium comparison | `03_ngram_bifolium_classification.py` | `ngram_bifolium_classification_summary.json`, `ngram_bifolium_classification_runs.csv` |
| §2.4 | 38,547 next-state predictions | `04_next_state_prediction.py` | `next_state_prediction_summary.json`, `next_state_prediction_folds.csv` |
| Appendix B | exact 600+8 inventory | `01_prepare_data.py` | `A2_main_shelf_inventory_600.csv`, `A2_paragraph_start_inventory_8.csv` |
| §3.5.2 | empirical fitting events | `08_a2_fitting_event_extraction.py` | `A2_empirical_fitting_events*.csv/json` |
| §3.5.2 / A.6 | 475--650 sensitivity | `09_budget_sensitivity_reconstructed.py` | `outputs/budget_sensitivity/*` — reconstructed, not original optimizer |
| Table 3 | 1,000 shelf fit runs | `06_a2_shelf_simulation.py` | `A2_shelf_fit_assessment_runs.csv`, `...summary.json` |
| §3.5.3 | 5,000 shelf attestation runs | `06_a2_shelf_simulation.py` | `A2_shelf_attestation_runs.csv`, `...summary.json` |
| Table 4 | matched n-gram nulls | `10_a2_ngram_null_models.py` | `outputs/null/A2_ngram_null_attestation_5000runs.csv`, `...summary.csv` |
| §3.7 | D--G reassignment | `07_cross_currier_reassignment.py` | `cross_currier_DG_180_allocations.csv`, `cross_currier_DG_summary.json` |
| Appendix audit | reachability/dead states | `05_inventory_reachability.py` | `inventory_and_reachability_summary.json`, detailed CSVs |
| Overall | target-vs-recomputed audit | `11_build_result_comparison.py` | `paper_results_comparison.csv` |
| Overall | automated package verification | `13_verify_package.py` | `package_verification.json` |
