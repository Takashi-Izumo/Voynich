#!/usr/bin/env python3
"""Audit the exact A-2 inventory and reachability under the published rules."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, deque
from pathlib import Path

from a2_shelf_core import SPACE, load_main_inventory, load_start_inventory
from voynich_common import dump_json


def write_csv(rows, path: Path, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and fieldnames is None:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0]) if rows else list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--start-inventory", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args(); args.outdir.mkdir(parents=True, exist_ok=True)

    inv = load_main_inventory(args.inventory)
    start = load_start_inventory(args.start_inventory)

    # A state includes the active compartment and the current word length.
    initial = {(SPACE, SPACE, 0)}
    for t in start:
        initial.add((SPACE, t.output, 1))
    q = deque(sorted(initial))
    reachable_states = set(initial)
    reachable_rows = set()
    reachable_physical = 0
    empty_reachable_states = set()

    while q:
        s1, s2, k = q.popleft()
        tablets = inv.get((s1, s2), [])
        if not tablets:
            empty_reachable_states.add((s1, s2, k))
            continue
        for j, t in enumerate(tablets):
            reachable_rows.add((s1, s2, t.output, t.stop_number, t.tablet_class, t.safety))
            new_k = k + 1
            if t.stop_number <= new_k:
                nxt = (t.output, SPACE, 0)
            else:
                nxt = (s2, t.output, new_k)
            if nxt not in reachable_states:
                reachable_states.add(nxt); q.append(nxt)

    all_rows = []
    unreachable = []
    state_totals = Counter()
    class_totals = Counter()
    class_rows = Counter()
    physical_total = 0
    safety_total = 0
    for state, tablets in sorted(inv.items()):
        for t in tablets:
            key = (state[0], state[1], t.output, t.stop_number, t.tablet_class, t.safety)
            is_reach = key in reachable_rows
            physical_total += t.multiplicity
            state_totals[state] += t.multiplicity
            class_totals[t.tablet_class] += t.multiplicity
            class_rows[t.tablet_class] += 1
            safety_total += t.multiplicity * t.safety
            row = {
                "state_1": state[0], "state_2": state[1], "output": t.output,
                "stop_number": t.stop_number, "multiplicity": t.multiplicity,
                "class": t.tablet_class, "safety": t.safety,
                "reachable_under_published_rules": int(is_reach),
            }
            all_rows.append(row)
            if not is_reach:
                unreachable.append(row)
            else:
                reachable_physical += t.multiplicity

    reachable_compartments = sorted({(s1, s2) for s1, s2, _ in reachable_states if (s1, s2) in inv})
    unreachable_active_compartments = sorted(set(inv) - set(reachable_compartments))
    summary = {
        "distinct_main_inventory_rows": len(all_rows),
        "physical_main_tablets": physical_total,
        "active_compartments": len(inv),
        "class_tablets": dict(class_totals),
        "class_distinct_rows": dict(class_rows),
        "safety_tablets": safety_total,
        "start_tablets": sum(t.multiplicity for t in start),
        "reachable_state_length_combinations": len(reachable_states),
        "reachable_active_compartments": len(reachable_compartments),
        "unreachable_active_compartments": len(unreachable_active_compartments),
        "reachable_distinct_inventory_rows": len(reachable_rows),
        "unreachable_distinct_inventory_rows": len(unreachable),
        "reachable_physical_tablets": reachable_physical,
        "unreachable_physical_tablets": physical_total - reachable_physical,
        "reachable_empty_state_length_combinations": len(empty_reachable_states),
        "published_inventory_invariants": {
            "main_tablets_expected": 600,
            "start_tablets_expected": 8,
            "safety_tablets_expected": 14,
        },
        "interpretation": (
            "Reachability is computed from [SPACE,SPACE] at word length 0 and from "
            "the three Paragraph START outputs at word length 1, using exactly the "
            "state update and stopping rules printed in Appendix A."
        ),
    }
    dump_json(summary, args.outdir / "inventory_and_reachability_summary.json")
    write_csv(all_rows, args.outdir / "inventory_rows_with_reachability.csv")
    write_csv(unreachable, args.outdir / "unreachable_inventory_rows.csv")
    write_csv(
        [{"state_1": a, "state_2": b, "total_tablets": state_totals[(a,b)]}
         for a,b in unreachable_active_compartments],
        args.outdir / "unreachable_active_compartments.csv",
    )
    write_csv(
        [{"state_1": a, "state_2": b, "word_length": k}
         for a,b,k in sorted(empty_reachable_states)],
        args.outdir / "reachable_empty_states.csv",
        fieldnames=["state_1", "state_2", "word_length"],
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
