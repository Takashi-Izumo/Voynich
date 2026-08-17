#!/usr/bin/env python3
"""Run the complete reproducibility workflow from the package root."""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path


def run(cmd, root, env, log_name):
    log = root / "outputs/runs" / log_name
    log.parent.mkdir(parents=True, exist_ok=True)
    print("+", " ".join(map(str, cmd)), flush=True)
    with log.open("w", encoding="utf-8") as f:
        subprocess.run([str(x) for x in cmd], cwd=root, env=env, check=True, stdout=f, stderr=subprocess.STDOUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--full-null", action="store_true", help="regenerate all 30,000 null-model runs; otherwise use the archived 5,000-run outputs")
    ap.add_argument("--budget-runs", type=int, default=50)
    args = ap.parse_args(); root = args.root.resolve(); py = sys.executable
    env = os.environ.copy(); env["PYTHONPATH"] = str(root / "code")
    zl = root / "data/raw/ZL3b-n_2025-05-13_snapshot.txt"
    tex = root / "data/raw/Supplementary_Table_A1_A2_600_tablet_inventory_SIMPLE_MATH.tex"
    derived = root / "data/derived"

    run([py, "code/01_prepare_data.py", "--zl3b", zl, "--inventory-tex", tex, "--outdir", derived], root, env, "01_prepare_data.log")
    run([py, "code/02_seven_layer_analysis.py", "--zl3b", zl, "--outdir", "outputs/tables", "--seed", "30", "--permutations", "50000"], root, env, "02_seven_layer_analysis.log")
    run([py, "code/03_ngram_bifolium_classification.py", "--zl3b", zl, "--outdir", "outputs/tables", "--runs", "2000", "--seed", "20260817"], root, env, "03_ngram_bifolium_classification.log")
    run([py, "code/04_next_state_prediction.py", "--zl3b", zl, "--outdir", "outputs/tables", "--seed", "123", "--alpha", "0.1"], root, env, "04_next_state_prediction.log")
    run([py, "code/05_inventory_reachability.py", "--inventory", derived / "A2_main_shelf_inventory_600.csv", "--start-inventory", derived / "A2_paragraph_start_inventory_8.csv", "--outdir", "outputs/audits"], root, env, "05_inventory_reachability.log")
    run([py, "code/06_a2_shelf_simulation.py", "--inventory", derived / "A2_main_shelf_inventory_600.csv", "--start-inventory", derived / "A2_paragraph_start_inventory_8.csv", "--schedule", derived / "A2_boundary_schedule.csv", "--a2-vocab", derived / "A2_vocabulary.txt", "--herbal-a-vocab", derived / "Herbal_A_vocabulary.txt", "--vm-vocab", derived / "strict_VM_attestation_vocabulary.txt", "--outdir", "outputs/shelf", "--fit-runs", "1000", "--attestation-runs", "5000", "--seed", "20260817"], root, env, "06_a2_shelf_simulation.log")
    run([py, "code/07_cross_currier_reassignment.py", "--zl3b", zl, "--outdir", "outputs/tables"], root, env, "07_cross_currier_reassignment.log")
    run([py, "code/07b_cross_currier_vm23_sensitivity.py", "--zl3b", zl, "--outdir", "outputs/sensitivity"], root, env, "07b_cross_currier_vm23_sensitivity.log")
    run([py, "code/08_a2_fitting_event_extraction.py", "--zl3b", zl, "--outdir", derived], root, env, "08_a2_fitting_event_extraction.log")
    run([py, "code/09_budget_sensitivity_reconstructed.py", "--inventory", derived / "A2_main_shelf_inventory_600.csv", "--start-inventory", derived / "A2_paragraph_start_inventory_8.csv", "--schedule", derived / "A2_boundary_schedule.csv", "--outdir", "outputs/budget_sensitivity", "--runs-per-budget", str(args.budget_runs), "--seed", "20260817"], root, env, "09_budget_sensitivity_reconstructed.log")
    if args.full_null:
        run([py, "code/10_a2_ngram_null_models.py", zl, "--runs", "5000", "--seed", "20260817", "--out", "outputs/null/A2_ngram_null_attestation"], root, env, "10_a2_ngram_null_models.log")
    else:
        required = [root / "outputs/null/A2_ngram_null_attestation_5000runs.csv", root / "outputs/null/A2_ngram_null_attestation_summary.csv"]
        if not all(p.exists() for p in required):
            raise FileNotFoundError("Archived full null outputs are missing; rerun with --full-null")
        print("Using archived full 5,000-run null outputs. Pass --full-null to regenerate them.")
    run([py, "code/11_build_result_comparison.py", "--root", root], root, env, "11_build_result_comparison.log")
    run([py, "code/13_verify_package.py", "--root", root], root, env, "13_verify_package.log")
    print("Reproduction workflow completed.")


if __name__ == "__main__":
    main()
