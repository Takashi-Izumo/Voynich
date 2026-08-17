#!/usr/bin/env python3
"""Verify the integrity and headline numerical outputs of the package.

This verifier distinguishes exact deterministic/archived results from stochastic
reconstructions that are expected to agree only within stated tolerances because
some original random seeds or holdout streams were not preserved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks, name, observed, expected, tolerance=0.0, kind="exact", note=""):
    if isinstance(observed, (int, float)) and isinstance(expected, (int, float)):
        diff = abs(float(observed) - float(expected))
        ok = diff <= tolerance
    else:
        diff = None
        ok = observed == expected
    checks.append({
        "name": name,
        "kind": kind,
        "observed": observed,
        "expected": expected,
        "absolute_difference": diff,
        "tolerance": tolerance,
        "pass": bool(ok),
        "note": note,
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    checks = []

    required = [
        "data/raw/ZL3b-n_2025-05-13_snapshot.txt",
        "data/derived/A2_main_shelf_inventory_600.csv",
        "data/derived/A2_paragraph_start_inventory_8.csv",
        "data/derived/A2_boundary_schedule.csv",
        "outputs/tables/table1_seven_layer_directionality.json",
        "outputs/tables/table2_seven_layer_bifolium_classification.json",
        "outputs/tables/ngram_bifolium_classification_summary.json",
        "outputs/tables/next_state_prediction_summary.json",
        "outputs/shelf/A2_shelf_fit_assessment_summary.json",
        "outputs/shelf/A2_shelf_attestation_summary.json",
        "outputs/null/A2_ngram_null_attestation_summary.csv",
        "outputs/tables/cross_currier_DG_summary.json",
        "outputs/audits/inventory_and_reachability_summary.json",
    ]
    for rel in required:
        add(checks, f"file:{rel}", (root / rel).exists(), True, kind="integrity")

    manifest = load_json(root / "data/derived/data_manifest.json")
    add(checks, "A-2 tokens", manifest["corpora"]["A2"]["tokens"], 297)
    add(checks, "A-2 types", manifest["corpora"]["A2"]["types"], 195)
    add(checks, "Herbal A tokens", manifest["corpora"]["Herbal_A"]["tokens"], 7694)
    add(checks, "Herbal A types", manifest["corpora"]["Herbal_A"]["types"], 2270)
    add(checks, "Strict VM tokens", manifest["corpora"]["strict_VM_attestation"]["tokens"], 37597)
    add(checks, "Strict VM types", manifest["corpora"]["strict_VM_attestation"]["types"], 7455)
    add(checks, "Main-shelf tablets", manifest["inventory"]["main_tablets"], 600)
    add(checks, "Paragraph START tablets", manifest["inventory"]["start_tablets"], 8)
    add(checks, "Safety tablets", manifest["inventory"]["safety_tablets"], 14)
    add(checks, "A-2 schedule lines", manifest["A2_schedule"]["lines"], 40)
    add(checks, "A-2 schedule paragraphs", manifest["A2_schedule"]["paragraphs"], 8)
    add(checks, "A-2 neutral restarts", manifest["A2_schedule"]["neutral_restarts"], 32)

    t1 = load_json(root / "outputs/tables/table1_seven_layer_directionality.json")
    add(checks, "Table 1 analyzed tokens", t1["analyzed_word_tokens"], 6765)
    add(checks, "Table 1 covered tokens", t1["covered_word_tokens"], 6747)
    add(checks, "Table 1 transitions", t1["word_internal_transitions"], 20207)
    add(checks, "Table 1 forward", t1["forward_rate"], 0.6164, 5e-5, "printed-precision")
    add(checks, "Table 1 same", t1["same_rate"], 0.2323, 5e-5, "printed-precision")
    add(checks, "Table 1 backward", t1["backward_rate"], 0.1513, 5e-5, "printed-precision")
    add(checks, "Table 1 randomized mean", t1["randomized_backward_mean"], 0.3965, 1e-4, "seeded-randomization")
    add(checks, "Table 1 randomization tail", t1["randomization_plus_one_tail"], 4.0e-5, 1e-8, "seeded-randomization")

    t2 = load_json(root / "outputs/tables/table2_seven_layer_bifolium_classification.json")
    for model, vals in {
        "layer_structure_only": (0.2738, 0.5714, 0.2262),
        "full_seven_layer": (0.3810, 0.7619, 0.4286),
    }.items():
        obj = t2[model]
        add(checks, f"Table 2 {model} Top 1", obj["top1"], vals[0], 5e-5, "printed-precision")
        add(checks, f"Table 2 {model} Top 3", obj["top3"], vals[1], 5e-5, "printed-precision")
        add(checks, f"Table 2 {model} one-to-one", obj["one_to_one"], vals[2], 5e-5, "printed-precision")

    ng = load_json(root / "outputs/tables/ngram_bifolium_classification_summary.json")
    add(checks, "Bigram bifolium Top 1", ng["2"]["top1"], 0.3127, 0.003, "Monte-Carlo-reconstruction",
        "Original 2,000 holdout stream was not preserved.")
    add(checks, "Bigram bifolium one-to-one", ng["2"]["one_to_one"], 0.2911, 0.003, "Monte-Carlo-reconstruction")
    add(checks, "Bigram bifolium Top 3", ng["2"]["top3"], 0.6177, 0.003, "Monte-Carlo-reconstruction")
    add(checks, "Trigram bifolium Top 1", ng["3"]["top1"], 0.2559, 0.003, "Monte-Carlo-reconstruction")

    ns = load_json(root / "outputs/tables/next_state_prediction_summary.json")
    add(checks, "Next-state bigram bits", ns["bigram_bits_per_state"], 2.2931, 0.001, "method-reconstruction",
        "Original smoothing and fold seed were not preserved; alpha=0.1 and seed=123 are archived here.")
    add(checks, "Next-state trigram bits", ns["trigram_bits_per_state"], 2.1691, 0.001, "method-reconstruction")
    add(checks, "Next-state predictions", ns["next_state_predictions"], 38547)

    fit = load_json(root / "outputs/shelf/A2_shelf_fit_assessment_summary.json")
    paper_fit = {
        "word_types": (188.54, 0.3),
        "hapax_legomena": (136.17, 0.3),
        "mean_word_length": (4.0186, 0.002),
        "word_length_sd": (1.6186, 0.003),
        "one_character_rate": (0.0446, 0.001),
        "eight_plus_rate": (0.0117, 0.001),
        "bigram_jsd": (0.03892, 0.001),
        "trigram_jsd": (0.10608, 0.001),
        "word_boundary_jsd": (0.11462, 0.002),
        "paragraph_start_gallows": (1.0, 1e-12),
        "neutral_restart_gallows": (0.0277, 0.002),
    }
    for key, (target, tol) in paper_fit.items():
        add(checks, f"Table 3 {key}", fit["summary"][key]["mean"], target, tol, "stochastic-reconstruction",
            "Fresh archived seed; original seed was not preserved.")
    add(checks, "Shelf dead ends", fit["summary"]["dead_ends"]["mean"], 0)

    att = load_json(root / "outputs/shelf/A2_shelf_attestation_summary.json")
    paper_att = {
        "A2": 0.5500,
        "HerbalA_outside_A2": 0.1752,
        "VM_outside_HerbalA": 0.0453,
        "Unattested": 0.2295,
        "VM_total": 0.7705,
        "Outside_A2_total": 0.2205,
    }
    for key, target in paper_att.items():
        add(checks, f"Shelf attestation {key}", att["summary"][key]["mean"], target, 0.001, "stochastic-reconstruction")

    null_rows = list(csv.DictReader((root / "outputs/null/A2_ngram_null_attestation_summary.csv").open(encoding="utf-8")))
    null_map = {(r["design"], r["model"], r["metric"]): float(r["mean"]) for r in null_rows}
    for model, vm, outside in [
        ("uni", 0.1237, 0.0897),
        ("bi", 0.7726, 0.2860),
        ("tri", 0.8762, 0.2280),
    ]:
        design = "exact_length_conditioned_START_END"
        add(checks, f"Table 4 {model} VM total", null_map[(design, model, "VM_total")], vm, 5e-5, "archived-exact")
        add(checks, f"Table 4 {model} outside A-2", null_map[(design, model, "Outside_A2_total")], outside, 5e-5, "archived-exact")

    dg = load_json(root / "outputs/tables/cross_currier_DG_summary.json")
    add(checks, "D-G observed", dg["observed"], 99)
    add(checks, "D-G mean", dg["reassignment_mean"], 108.17, 0.005, "printed-precision")
    add(checks, "D-G exact p", dg["one_sided_exact_p"], 0.0056, 5e-5, "printed-precision")
    add(checks, "D-G allocations", dg["allocations"], 180)

    reach = load_json(root / "outputs/audits/inventory_and_reachability_summary.json")
    add(checks, "Reachability main tablets", reach["physical_main_tablets"], 600)
    add(checks, "Reachability reachable tablets", reach["reachable_physical_tablets"], 584)
    add(checks, "Reachability unreachable tablets", reach["unreachable_physical_tablets"], 16)
    add(checks, "Reachable empty states", reach["reachable_empty_state_length_combinations"], 0)

    failed = [c for c in checks if not c["pass"]]
    result = {
        "checks": checks,
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "overall_pass": not failed,
        "interpretation": (
            "All archived integrity and numerical-tolerance checks passed. Exact original random streams are not claimed where the archive did not preserve them."
            if not failed else
            "One or more package checks failed; inspect the failed entries before using the results."
        ),
    }
    out = root / "outputs/audits/package_verification.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"], "output": str(out)}, indent=2))
    if failed:
        for c in failed:
            print("FAIL", c)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
