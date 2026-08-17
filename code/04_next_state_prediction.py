#!/usr/bin/env python3
"""Page-grouped five-fold bigram/trigram next-state prediction on Herbal A."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.model_selection import KFold

from voynich_common import dump_json, load_zl3b, page_tokens, segment


def natural_page_key(p: str):
    m = re.match(r"f(\d+)", p)
    return (int(m.group(1)) if m else 10**9, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zl3b", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20260817)
    ap.add_argument("--alpha", type=float, default=0.1)
    args = ap.parse_args(); args.outdir.mkdir(parents=True, exist_ok=True)

    meta, records = load_zl3b(args.zl3b)
    pages = sorted([p for p, m in meta.items() if m.get("I") == "H" and m.get("L") == "A"], key=natural_page_key)
    pw = page_tokens(records, pages, paragraph_only=False, require23=False)
    vocab = sorted({g for p in pages for w in pw[p] for g in (segment(w) or [])})
    next_states = vocab + ["END"]
    k = len(next_states)
    kf = KFold(n_splits=5, shuffle=True, random_state=args.seed)
    fold_rows = []
    total_ll1 = total_ll2 = 0.0; total_n = 0
    for fold, (train, test) in enumerate(kf.split(pages), 1):
        c1 = defaultdict(Counter); c2 = defaultdict(Counter)
        for i in train:
            for w in pw[pages[i]]:
                seq = ["START", "START"] + segment(w) + ["END"]
                for j in range(2, len(seq)):
                    c1[seq[j-1]][seq[j]] += 1
                    c2[(seq[j-2], seq[j-1])][seq[j]] += 1
        ll1 = ll2 = 0.0; nobs = 0
        for i in test:
            for w in pw[pages[i]]:
                seq = ["START", "START"] + segment(w) + ["END"]
                for j in range(2, len(seq)):
                    y = seq[j]
                    co1 = c1[seq[j-1]]
                    p1 = (co1[y] + args.alpha) / (sum(co1.values()) + args.alpha * k)
                    co2 = c2[(seq[j-2], seq[j-1])]
                    p2 = (co2[y] + args.alpha) / (sum(co2.values()) + args.alpha * k)
                    ll1 -= math.log2(p1); ll2 -= math.log2(p2); nobs += 1
        fold_rows.append({
            "fold": fold, "test_pages": " ".join(pages[i] for i in test), "predictions": nobs,
            "bigram_bits_per_state": ll1 / nobs, "trigram_bits_per_state": ll2 / nobs,
        })
        total_ll1 += ll1; total_ll2 += ll2; total_n += nobs
    summary = {
        "pages": len(pages), "words": sum(len(pw[p]) for p in pages), "next_state_predictions": total_n,
        "glyph_states": len(vocab), "alpha_additive": args.alpha, "fold_seed": args.seed,
        "bigram_bits_per_state": total_ll1 / total_n,
        "trigram_bits_per_state": total_ll2 / total_n,
        "improvement_bits_per_state": (total_ll1 - total_ll2) / total_n,
        "paper_targets": {"bigram_bits_per_state": 2.2931, "trigram_bits_per_state": 2.1691},
    }
    dump_json(summary, args.outdir / "next_state_prediction_summary.json")
    with (args.outdir / "next_state_prediction_folds.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(fold_rows[0]));w.writeheader();w.writerows(fold_rows)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
