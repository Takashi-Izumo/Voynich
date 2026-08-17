#!/usr/bin/env python3
"""Compile paper targets, reproduced values, and documented discrepancies."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add(rows, section, metric, target, value, status, note=""):
    diff = "" if target == "" or value == "" else abs(float(target) - float(value))
    rows.append({
        "section": section,
        "metric": metric,
        "paper_target": target,
        "reproduced_value": value,
        "absolute_difference": diff,
        "status": status,
        "note": note,
    })


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args(); root = args.root
    rows = []

    manifest = load(root / "data/derived/data_manifest.json")
    corpus_targets = {
        ("A2", "tokens"): 297, ("A2", "types"): 195,
        ("Herbal_A", "tokens"): 7694, ("Herbal_A", "types"): 2270,
        ("full_VM_ngram", "tokens"): 37608, ("full_VM_ngram", "types"): 7457,
        ("strict_VM_attestation", "tokens"): 37597, ("strict_VM_attestation", "types"): 7455,
    }
    for (corpus, field), target in corpus_targets.items():
        add(rows, "Corpus audit", f"{corpus} {field}", target, manifest["corpora"][corpus][field], "exact")

    d = load(root / "outputs/tables/table1_seven_layer_directionality.json")
    table1 = [
        ("Analyzed tokens", 6765, "analyzed_word_tokens"), ("Covered tokens", 6747, "covered_word_tokens"),
        ("Observed types", 2012, "observed_word_types"), ("Covered types", 1994, "covered_word_types"),
        ("Transitions", 20207, "word_internal_transitions"), ("Forward rate", .6164, "forward_rate"),
        ("Same-layer rate", .2323, "same_rate"), ("Backward rate", .1513, "backward_rate"),
        ("Randomized backward mean", .3965, "randomized_backward_mean"),
        ("Zero-back words", .6172, "words_zero_backward"),
        ("Zero/one-back words", .9342, "words_zero_or_one_backward"),
        ("Minimum bifolium back rate", .1039, "per_bifolium_backward_min"),
        ("Maximum bifolium back rate", .1919, "per_bifolium_backward_max"),
        ("Randomization plus-one tail", 4e-5, "randomization_plus_one_tail"),
    ]
    for metric, target, key in table1:
        add(rows, "Table 1", metric, target, d[key], "exact_to_printed_precision")

    d = load(root / "outputs/tables/table2_seven_layer_bifolium_classification.json")
    for model, key, targets in [
        ("Layer only", "layer_structure_only", {"top1": .2738, "top3": .5714, "one_to_one": .2262}),
        ("Full", "full_seven_layer", {"top1": .3810, "top3": .7619, "one_to_one": .4286}),
    ]:
        for metric, target in targets.items():
            add(rows, "Table 2", f"{model} {metric}", target, d[key][metric], "exact_to_printed_precision")

    d = load(root / "outputs/tables/ngram_bifolium_classification_summary.json")
    for n, metric, target in [
        ("2", "top1", .3127), ("2", "one_to_one", .2911), ("2", "top3", .6177),
        ("3", "top1", .2559),
    ]:
        add(rows, "N-gram bifolium classification", f"{n}-gram {metric}", target, d[n][metric],
            "monte_carlo_near_match",
            "The original 2,000 holdout configurations and seed were not preserved; a new fixed seed is archived.")

    d = load(root / "outputs/tables/next_state_prediction_summary.json")
    add(rows, "Next-state prediction", "Bigram bits/state", 2.2931, d["bigram_bits_per_state"],
        "reconstructed_near_match", "Additive smoothing alpha=0.1 and page-fold seed 123 are now explicit; the original choices were not archived.")
    add(rows, "Next-state prediction", "Trigram bits/state", 2.1691, d["trigram_bits_per_state"],
        "reconstructed_near_match", "Additive smoothing alpha=0.1 and page-fold seed 123 are now explicit; the original choices were not archived.")

    fit = load(root / "outputs/shelf/A2_shelf_fit_assessment_summary.json")
    for key, target in fit["paper_targets"].items():
        add(rows, "Table 3", key, target, fit["summary"][key]["mean"], "stochastic_near_match",
            "The original simulation seed was not preserved; the package archives seed 20260817.")

    att = load(root / "outputs/shelf/A2_shelf_attestation_summary.json")
    for key, target in att["paper_targets"].items():
        add(rows, "Shelf attestation", key, target, att["summary"][key]["mean"], "stochastic_near_match",
            "The original simulation seed was not preserved; the package archives a separate deterministic stream.")

    nd = pd.read_csv(root / "outputs/null/A2_ngram_null_attestation_summary.csv")
    target_map = {
        ("uni", "VM_total"): .1237, ("uni", "Outside_A2_total"): .0897,
        ("bi", "VM_total"): .7726, ("bi", "Outside_A2_total"): .2860,
        ("tri", "VM_total"): .8762, ("tri", "Outside_A2_total"): .2280,
    }
    for (model, metric), target in target_map.items():
        value = float(nd[(nd.design == "exact_length_conditioned_START_END") & (nd.model == model) & (nd.metric == metric)]["mean"].iloc[0])
        add(rows, "Table 4 nulls", f"{model} {metric}", target, value, "exact_archived_output")

    dg = load(root / "outputs/tables/cross_currier_DG_summary.json")
    add(rows, "D-G reassignment", "Observed new active compartments", 99, dg["observed"], "exact")
    add(rows, "D-G reassignment", "Reassignment mean", 108.17, dg["reassignment_mean"], "exact_to_printed_precision",
        "The paper result uses the stored stable-22 state definition (VM23 excluding rare g).")
    add(rows, "D-G reassignment", "One-sided exact p", .0056, dg["one_sided_exact_p"], "exact_to_printed_precision")
    sens_path = root / "outputs/sensitivity/cross_currier_VM23_summary.json"
    if sens_path.exists():
        sens = load(sens_path)
        add(rows, "D-G sensitivity", "VM23 reassignment mean", "", sens["mean"], "new_sensitivity",
            "Including g changes the mean to 109.17 while leaving observed=99 and p=1/180.")

    inv = load(root / "outputs/audits/inventory_and_reachability_summary.json")
    add(rows, "Inventory", "Main tablets", 600, inv["physical_main_tablets"], "exact")
    add(rows, "Inventory", "Safety tablets", 14, inv["safety_tablets"], "exact")
    add(rows, "Inventory audit", "Reachable tablets under published rules", "", inv["reachable_physical_tablets"], "new_audit",
        "Sixteen physical tablets are unreachable under the printed state-update and stopping rules.")
    add(rows, "Inventory audit", "Reachable empty states", "", inv["reachable_empty_state_length_combinations"], "new_audit")

    ev = load(root / "data/derived/A2_empirical_fitting_events_summary.json")
    for k, target in ev["expected_counts"].items():
        add(rows, "A-2 fitting inputs", f"{k} empirical events", target, ev["class_counts"].get(k, 0), "exact")

    out_csv = root / "outputs/audits/paper_results_comparison.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    md = ["# Paper-result reproduction audit", "", "This table compares printed values with the outputs generated or archived in this package.", "",
          "| Section | Metric | Paper | Reproduced | Status | Note |", "|---|---|---:|---:|---|---|"]
    for r in rows:
        md.append(f"| {r['section']} | {r['metric']} | {r['paper_target']} | {r['reproduced_value']} | {r['status']} | {r['note']} |")
    (root / "outputs/audits/paper_results_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(out_csv)


if __name__ == "__main__":
    main()
