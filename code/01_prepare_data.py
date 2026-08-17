#!/usr/bin/env python3
"""Extract audited corpora, A-2 schedule, and exact tablet inventory."""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from voynich_common import (
    A2_PAGES,
    VM23,
    extract_a2_schedule,
    extract_tokens,
    extract_tokens_attestation_strict,
    load_zl3b,
    segment,
    sha256,
    dump_json,
)

INV_RE = re.compile(
    r"^\\\(\\left\[\\mathrm\{([^}]+)\}, \\mathrm\{([^}]+)\}\\right\] "
    r"\\to \\mathrm\{([^}]+)\}\[(\d+)\] \\times (\d+)\\\); "
    r"class=([A-Z]+); safety=(\d+)\\par$"
)
START_RE = re.compile(
    r"^\\\(\\left\[\\mathrm\{PARAGRAPH\\ START\}\\right\] "
    r"\\to \\mathrm\{([^}]+)\}\[(\d+)\] \\times (\d+)\\\)\\par$"
)


def parse_inventory(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    main: list[dict[str, object]] = []
    start: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = INV_RE.match(line)
        if m:
            s1, s2, output, stop, mult, cls, safety = m.groups()
            main.append({
                "state_1": s1,
                "state_2": s2,
                "output": output,
                "stop_number": int(stop),
                "multiplicity": int(mult),
                "class": cls,
                "safety": int(safety),
            })
            continue
        m = START_RE.match(line)
        if m:
            output, stop, mult = m.groups()
            start.append({
                "state_1": "PARAGRAPH_START",
                "state_2": "PARAGRAPH_START",
                "output": output,
                "stop_number": int(stop),
                "multiplicity": int(mult),
                "class": "START",
                "safety": 0,
            })
    if sum(int(x["multiplicity"]) for x in main) != 600:
        raise RuntimeError("Inventory parser did not recover 600 main-shelf tablets")
    if sum(int(x["multiplicity"]) for x in start) != 8:
        raise RuntimeError("Inventory parser did not recover 8 Paragraph START tablets")
    return main, start


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zl3b", type=Path, required=True)
    ap.add_argument("--inventory-tex", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    meta, records = load_zl3b(args.zl3b)
    a2 = extract_tokens(records, pages=set(A2_PAGES), paragraph_only=True, require23=True)
    herbal_a_pages = {p for p, m in meta.items() if m.get("I") == "H" and m.get("L") == "A"}
    herbal_a = extract_tokens(records, pages=herbal_a_pages)
    full_vm_ngram = extract_tokens(records, pages=set(meta))
    strict_vm_attestation = extract_tokens_attestation_strict(records, pages=set(meta))

    corpora = {
        "A2": a2,
        "Herbal_A": herbal_a,
        "full_VM_ngram": full_vm_ngram,
        "strict_VM_attestation": strict_vm_attestation,
    }
    for name, words in corpora.items():
        (args.outdir / f"{name}_tokens.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
        (args.outdir / f"{name}_vocabulary.txt").write_text("\n".join(sorted(set(words))) + "\n", encoding="utf-8")

    audit_rows = []
    for name, words in corpora.items():
        segmented = [segment(w, VM23) for w in words]
        audit_rows.append({
            "corpus": name,
            "tokens": len(words),
            "types": len(set(words)),
            "tokens_covered_by_VM23": sum(x is not None for x in segmented),
            "types_covered_by_VM23": len({w for w, x in zip(words, segmented) if x is not None}),
        })
    write_csv(audit_rows, args.outdir / "corpus_audit.csv")

    glyph_counts = Counter()
    for w in full_vm_ngram:
        gs = segment(w)
        if gs:
            glyph_counts.update(gs)
    glyph_rows = [
        {"glyph": g, "count": n, "in_VM23": int(g in VM23), "meets_100_threshold": int(n >= 100)}
        for g, n in sorted(glyph_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    write_csv(glyph_rows, args.outdir / "whole_manuscript_glyph_counts.csv")

    schedule = extract_a2_schedule(records)
    write_csv(schedule, args.outdir / "A2_boundary_schedule.csv")
    if sum(int(x["token_count"]) for x in schedule) != 297:
        raise RuntimeError("A-2 schedule does not sum to 297 tokens")
    if sum(x["start_mode"] == "PARAGRAPH_START" for x in schedule) != 8:
        raise RuntimeError("A-2 schedule does not contain 8 paragraphs")

    main_inv, start_inv = parse_inventory(args.inventory_tex)
    write_csv(main_inv, args.outdir / "A2_main_shelf_inventory_600.csv")
    write_csv(start_inv, args.outdir / "A2_paragraph_start_inventory_8.csv")
    write_csv(main_inv + start_inv, args.outdir / "A2_full_inventory_608.csv")

    class_counts = Counter()
    safety_count = 0
    for row in main_inv:
        class_counts[str(row["class"])] += int(row["multiplicity"])
        safety_count += int(row["multiplicity"]) * int(row["safety"])
    manifest = {
        "input_sha256": sha256(args.zl3b),
        "inventory_tex_sha256": sha256(args.inventory_tex),
        "VM23": list(VM23),
        "corpora": {r["corpus"]: r for r in audit_rows},
        "A2_schedule": {
            "lines": len(schedule),
            "paragraphs": sum(x["start_mode"] == "PARAGRAPH_START" for x in schedule),
            "neutral_restarts": sum(x["start_mode"] == "NEUTRAL_RESTART" for x in schedule),
            "tokens": sum(int(x["token_count"]) for x in schedule),
        },
        "inventory": {
            "distinct_main_rows": len(main_inv),
            "main_tablets": sum(int(x["multiplicity"]) for x in main_inv),
            "start_tablets": sum(int(x["multiplicity"]) for x in start_inv),
            "class_counts": dict(class_counts),
            "safety_tablets": safety_count,
        },
    }
    dump_json(manifest, args.outdir / "data_manifest.json")
    print(manifest)


if __name__ == "__main__":
    main()
