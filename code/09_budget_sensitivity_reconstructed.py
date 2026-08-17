#!/usr/bin/env python3
"""Transparent fresh sensitivity analysis for 475--650 tablet budgets.

The original optimization code used to construct every budget in the paper is not
present in the archive. This script therefore performs a documented re-quantization
around the exact published 600-tablet inventory. At 600 tablets it reproduces the
published inventory exactly; other budgets are fresh sensitivity configurations and
must not be represented as the lost original optimizer's outputs.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from a2_shelf_core import (
    Tablet,
    generate_run,
    load_main_inventory,
    load_schedule,
    load_start_inventory,
    observed_lines_from_schedule,
    run_statistics,
)
from voynich_common import dump_json

BUDGETS = (475, 500, 525, 550, 575, 600, 625, 650)


def largest_remainder(weights: np.ndarray, total: int) -> np.ndarray:
    if total <= 0:
        return np.zeros(len(weights), dtype=int)
    if weights.sum() <= 0:
        weights = np.ones(len(weights), dtype=float)
    quota = weights / weights.sum() * total
    out = np.floor(quota).astype(int)
    remainder = total - int(out.sum())
    if remainder:
        order = np.argsort(-(quota - out), kind="stable")
        out[order[:remainder]] += 1
    return out


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def quantize_rows(rows, budget):
    final = np.array([int(r["multiplicity"]) for r in rows], dtype=int)
    n = len(rows)
    if budget < n:
        raise ValueError(f"Budget {budget} is smaller than {n} distinct branches")
    if budget <= int(final.sum()):
        extras = largest_remainder(np.maximum(final - 1, 0).astype(float), budget - n)
        mult = 1 + extras
    else:
        mult = final.copy()
        mult += largest_remainder(final.astype(float), budget - int(final.sum()))
    if budget == 600 and not np.array_equal(mult, final):
        raise AssertionError("600-budget re-quantization failed to recover the exact inventory")
    out = []
    for r, m in zip(rows, mult):
        z = dict(r); z["multiplicity"] = int(m); out.append(z)
    return out


def rows_to_inventory(rows):
    inv = {}
    for r in rows:
        state = (r["state_1"], r["state_2"])
        inv.setdefault(state, []).append(Tablet(
            output=r["output"], stop_number=int(r["stop_number"]),
            multiplicity=int(r["multiplicity"]), tablet_class=r["class"],
            safety=int(r["safety"]),
        ))
    return inv


def write_rows(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--start-inventory", type=Path, required=True)
    ap.add_argument("--schedule", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--runs-per-budget", type=int, default=250)
    ap.add_argument("--seed", type=int, default=20260817)
    args = ap.parse_args(); args.outdir.mkdir(parents=True, exist_ok=True)

    base_rows = read_rows(args.inventory)
    start = load_start_inventory(args.start_inventory)
    schedule = load_schedule(args.schedule)
    observed = observed_lines_from_schedule(schedule)
    summary_rows = []
    all_runs = []

    for bi, budget in enumerate(BUDGETS):
        rows = quantize_rows(base_rows, budget)
        write_rows(rows, args.outdir / "budget_inventories" / f"A2_inventory_{budget}.csv")
        inv = rows_to_inventory(rows)
        rng = np.random.default_rng(args.seed + budget * 1000)
        metrics = []
        for r in range(1, args.runs_per_budget + 1):
            run = generate_run(inv, start, schedule, rng)
            met = run_statistics(run, observed)
            metrics.append(met)
            all_runs.append({"budget": budget, "run": r, **met})
        for key in metrics[0]:
            vals = np.asarray([m[key] for m in metrics], dtype=float)
            summary_rows.append({
                "budget": budget, "metric": key, "mean": float(np.nanmean(vals)),
                "p2_5": float(np.nanquantile(vals, .025)),
                "p97_5": float(np.nanquantile(vals, .975)),
            })

    pd.DataFrame(all_runs).to_csv(args.outdir / "budget_sensitivity_runs.csv", index=False)
    pd.DataFrame(summary_rows).to_csv(args.outdir / "budget_sensitivity_summary.csv", index=False)
    payload = {
        "status": "fresh reconstructed sensitivity analysis; not the lost original optimizer",
        "budgets": list(BUDGETS),
        "runs_per_budget": args.runs_per_budget,
        "seed_rule": "20260817 + budget*1000",
        "quantization": (
            "Every one of the 430 published branches receives at least one tablet. "
            "For budgets below 600, additional tablets are apportioned by largest "
            "remainder in proportion to published multiplicity minus one. At 600 the "
            "exact published inventory is recovered. Above 600, added tablets are "
            "apportioned in proportion to the published multiplicities."
        ),
    }
    dump_json(payload, args.outdir / "budget_sensitivity_method.json")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
