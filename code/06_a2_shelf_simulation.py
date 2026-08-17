#!/usr/bin/env python3
"""Re-run the exact 608-tablet A-2 shelf fit and attestation experiments."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from a2_shelf_core import (
    attestation_statistics,
    generate_run,
    load_main_inventory,
    load_schedule,
    load_start_inventory,
    observed_lines_from_schedule,
    run_statistics,
    summarize_numeric_rows,
)
from voynich_common import dump_json

PAPER_TABLE3 = {
    "word_types": 188.54,
    "hapax_legomena": 136.17,
    "mean_word_length": 4.0186,
    "word_length_sd": 1.6186,
    "one_character_rate": 0.0446,
    "eight_plus_rate": 0.0117,
    "bigram_jsd": 0.03892,
    "trigram_jsd": 0.10608,
    "word_boundary_jsd": 0.11462,
    "paragraph_start_gallows": 1.0,
    "neutral_restart_gallows": 0.0277,
}
PAPER_ATTEST = {
    "A2": 0.5500,
    "HerbalA_outside_A2": 0.1752,
    "VM_outside_HerbalA": 0.0453,
    "Unattested": 0.2295,
    "VM_total": 0.7705,
    "Outside_A2_total": 0.2205,
}


def load_vocab(path: Path) -> set[str]:
    return {x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()}


def write_sample(run, path: Path):
    with path.open("w", encoding="utf-8") as f:
        for i, (line, mode) in enumerate(zip(run.lines, run.line_modes), 1):
            f.write(f"{i:02d}\t{mode}\t{' '.join(line)}\n")


def comparison(summary, targets):
    rows = []
    for metric, target in targets.items():
        fresh = summary.get(metric, {}).get("mean")
        if fresh is None:
            continue
        rows.append({
            "metric": metric,
            "paper_value": target,
            "fresh_value": fresh,
            "fresh_minus_paper": fresh - target,
            "absolute_difference": abs(fresh - target),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--start-inventory", type=Path, required=True)
    ap.add_argument("--schedule", type=Path, required=True)
    ap.add_argument("--a2-vocab", type=Path, required=True)
    ap.add_argument("--herbal-a-vocab", type=Path, required=True)
    ap.add_argument("--vm-vocab", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--fit-runs", type=int, default=1000)
    ap.add_argument("--attestation-runs", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260817)
    args = ap.parse_args(); args.outdir.mkdir(parents=True, exist_ok=True)

    inv = load_main_inventory(args.inventory)
    start = load_start_inventory(args.start_inventory)
    schedule = load_schedule(args.schedule)
    observed_lines = observed_lines_from_schedule(schedule)
    a2_vocab = load_vocab(args.a2_vocab)
    ha_vocab = load_vocab(args.herbal_a_vocab)
    vm_vocab = load_vocab(args.vm_vocab)

    # Fit-assessment runs.
    rng = np.random.default_rng(args.seed)
    fit_rows = []
    first_sample = None
    for run_no in range(1, args.fit_runs + 1):
        generated = generate_run(inv, start, schedule, rng)
        if first_sample is None:
            first_sample = generated
        row = {"run": run_no, **run_statistics(generated, observed_lines)}
        fit_rows.append(row)
    pd.DataFrame(fit_rows).to_csv(args.outdir / "A2_shelf_fit_assessment_runs.csv", index=False)
    fit_summary = summarize_numeric_rows([{k: v for k, v in r.items() if k != "run"} for r in fit_rows])
    fit_payload = {
        "settings": {
            "runs": args.fit_runs,
            "seed": args.seed,
            "tokens_per_run": sum(int(x["token_count"]) for x in schedule),
            "lines": len(schedule),
            "paragraphs": sum(x["start_mode"] == "PARAGRAPH_START" for x in schedule),
            "neutral_restarts": sum(x["start_mode"] == "NEUTRAL_RESTART" for x in schedule),
            "sampling": "with replacement from fixed multiplicities",
            "word_boundary_jsd": "ordinary within-line boundaries only",
        },
        "summary": fit_summary,
        "paper_targets": PAPER_TABLE3,
    }
    dump_json(fit_payload, args.outdir / "A2_shelf_fit_assessment_summary.json")
    pd.DataFrame(comparison(fit_summary, PAPER_TABLE3)).to_csv(
        args.outdir / "A2_shelf_fit_assessment_paper_comparison.csv", index=False
    )
    if first_sample is not None:
        write_sample(first_sample, args.outdir / "A2_shelf_sample_run.txt")

    # Independent attestation runs, with a separate deterministic stream.
    rng2 = np.random.default_rng(args.seed + 1_000_000)
    att_rows = []
    for run_no in range(1, args.attestation_runs + 1):
        generated = generate_run(inv, start, schedule, rng2)
        att_rows.append({
            "run": run_no,
            **attestation_statistics(generated.words, a2_vocab, ha_vocab, vm_vocab),
        })
    pd.DataFrame(att_rows).to_csv(args.outdir / "A2_shelf_attestation_runs.csv", index=False)
    att_summary = summarize_numeric_rows([{k: v for k, v in r.items() if k != "run"} for r in att_rows])
    att_payload = {
        "settings": {
            "runs": args.attestation_runs,
            "seed": args.seed + 1_000_000,
            "tokens_per_run": 297,
            "hierarchy": "A2; Herbal A outside A2; VM outside Herbal A; unattested",
        },
        "summary": att_summary,
        "paper_targets": PAPER_ATTEST,
    }
    dump_json(att_payload, args.outdir / "A2_shelf_attestation_summary.json")
    pd.DataFrame(comparison(att_summary, PAPER_ATTEST)).to_csv(
        args.outdir / "A2_shelf_attestation_paper_comparison.csv", index=False
    )

    print(json.dumps({"fit": fit_payload, "attestation": att_payload}, indent=2))


if __name__ == "__main__":
    main()
