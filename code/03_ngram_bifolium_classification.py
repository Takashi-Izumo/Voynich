#!/usr/bin/env python3
"""Repeated bifolium holdout comparison for word-internal 2--5 grams."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import normalize

from voynich_common import controlled_page_order, dump_json, load_zl3b, page_tokens, segment


def surface_counts(words: list[str], n: int) -> Counter[str]:
    c: Counter[str] = Counter()
    for w in words:
        gs = segment(w)
        if not gs:
            continue
        c.update("|".join(gs[i : i + n]) for i in range(len(gs) - n + 1))
    return c


def build_matrix(page_words, pages, n):
    dv = DictVectorizer(sparse=True)
    raw = dv.fit_transform([surface_counts(page_words[p], n) for p in pages]).astype(float).tocsr()
    return raw, dv.get_feature_names_out()


def transform_tfidf(raw, train_idx):
    x = raw.copy().astype(float)
    x.data = 1.0 + np.log(x.data)  # standard sublinear tf
    df = np.asarray((raw[train_idx] > 0).sum(axis=0)).ravel()
    idf = np.log((1 + len(train_idx)) / (1 + df)) + 1.0
    return normalize(x.multiply(idf).tocsr(), norm="l2").tocsr()


def metrics(sim):
    n = sim.shape[0]
    order = np.argsort(-sim, axis=1)
    top1 = np.mean(order[:, 0] == np.arange(n))
    top3 = np.mean([i in order[i, :3] for i in range(n)])
    top5 = np.mean([i in order[i, :5] for i in range(n)])
    r, c = linear_sum_assignment(-sim)
    one = np.mean(c[r] == r)
    rank = np.mean([np.where(order[i] == i)[0][0] + 1 for i in range(n)])
    return top1, one, top3, top5, rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zl3b", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--runs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260817)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    _, records = load_zl3b(args.zl3b)
    pages, groups, leaves = controlled_page_order()
    # Match the stored classification analyses: all clean lowercase material on each surface.
    pw = page_tokens(records, pages, paragraph_only=False, require23=False)
    raw_matrices = {n: build_matrix(pw, pages, n)[0] for n in range(2, 6)}
    dimensions = {n: int(raw_matrices[n].shape[1]) for n in raw_matrices}
    # The stored repeated-holdout experiment used one sublinear TF-IDF representation
    # per n-gram order, followed by repeated prototype holdout on the fixed vectors.
    matrices = {}
    for n, raw in raw_matrices.items():
        x = raw.copy().astype(float)
        x.data = 1.0 + np.log(x.data)
        df = np.asarray((raw > 0).sum(axis=0)).ravel()
        idf = np.log((1 + raw.shape[0]) / (1 + df)) + 1.0
        matrices[n] = normalize(x.multiply(idf).tocsr(), norm="l2").tocsr()
    grams = {n: (x @ x.T).toarray() for n, x in matrices.items()}

    rng = np.random.default_rng(args.seed)
    configs = rng.integers(0, 4, size=(args.runs, len(groups)), endpoint=False)
    rows = []
    sums = {n: np.zeros(5) for n in matrices}
    wins_2_vs_3 = Counter()
    for run, hs in enumerate(configs, 1):
        test = np.array([g[int(h)] for g, h in zip(groups, hs)], dtype=int)
        train = np.array([idx for g, h in zip(groups, hs) for j, idx in enumerate(g) if j != int(h)], dtype=int)
        run_metrics = {}
        for n in matrices:
            gram = grams[n]
            train_groups = [[idx for j, idx in enumerate(g) if j != int(h)] for g, h in zip(groups, hs)]
            sim = np.empty((len(groups), len(groups)), dtype=float)
            for j, inds in enumerate(train_groups):
                denom = float(np.sqrt(gram[np.ix_(inds, inds)].sum()))
                sim[:, j] = gram[np.ix_(test, inds)].sum(axis=1) / denom if denom else 0.0
            met = metrics(sim)
            run_metrics[n] = met
            sums[n] += met
            rows.append({
                "run": run, "ngram": n, "top1": met[0], "one_to_one": met[1],
                "top3": met[2], "top5": met[3], "mean_rank": met[4],
                "heldout_positions": "".join(str(int(x) + 1) for x in hs),
            })
        if run_metrics[2][0] > run_metrics[3][0]: wins_2_vs_3["bigram"] += 1
        elif run_metrics[2][0] < run_metrics[3][0]: wins_2_vs_3["trigram"] += 1
        else: wins_2_vs_3["tie"] += 1

    summary = {}
    for n in sorted(sums):
        mean = sums[n] / args.runs
        summary[str(n)] = {
            "top1": float(mean[0]), "one_to_one": float(mean[1]), "top3": float(mean[2]),
            "top5": float(mean[3]), "mean_rank": float(mean[4]), "dimension": dimensions[n],
        }
    summary["settings"] = {"runs": args.runs, "seed": args.seed, "bifolia": 21, "surfaces": 84}
    summary["bigram_vs_trigram_top1_runs"] = dict(wins_2_vs_3)
    dump_json(summary, args.outdir / "ngram_bifolium_classification_summary.json")
    with (args.outdir / "ngram_bifolium_classification_runs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    np.savetxt(args.outdir / "ngram_holdout_configurations.csv", configs + 1, delimiter=",", fmt="%d")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
