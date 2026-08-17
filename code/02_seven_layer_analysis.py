#!/usr/bin/env python3
"""Reproduce Tables 1 and 2: seven-layer directionality and bifolium classification."""
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

from voynich_common import (
    LAYER_MAP23,
    VM23,
    controlled_page_order,
    dump_json,
    load_zl3b,
    page_tokens,
    segment,
)


def bkt(n: int, cap: int = 4) -> str:
    return str(n) if n < cap else f"{cap}+"


def extract_features(words: list[str], mapping: dict[str, int], mode: str) -> Counter[str]:
    c: Counter[str] = Counter()
    for w in words:
        gs = segment(w)
        if not gs or any(g not in mapping for g in gs):
            continue
        ls = [mapping[g] for g in gs]
        runs: list[tuple[int, list[str]]] = []
        st = 0
        for i in range(1, len(ls) + 1):
            if i == len(ls) or ls[i] != ls[st]:
                runs.append((ls[st], gs[st:i]))
                st = i
        collapsed = [r[0] for r in runs]
        desc = sum(b < a for a, b in zip(ls, ls[1:]))
        same = sum(b == a for a, b in zip(ls, ls[1:]))
        forward = sum(b > a for a, b in zip(ls, ls[1:]))
        rounds = 1 + desc
        returns = sum(1 for z in ls[1:] if z == ls[0])
        if mode in ("entry_exit", "layer_core", "disk_full", "disk_no_ports"):
            c[f"EE:start:L{ls[0]}"] += 1
            c[f"EE:end:L{ls[-1]}"] += 1
            c[f"EE:pair:L{ls[0]}>L{ls[-1]}"] += 1
            c[f"EE:closure:{int(ls[0] == ls[-1])}"] += 1
        if mode in ("layer_usage", "layer_core", "disk_full", "disk_no_ports"):
            for z in ls:
                c[f"U:glyph:L{z}"] += 1
            for z in set(ls):
                c[f"U:word_has:L{z}"] += 1
            rc = Counter(collapsed)
            for z, n in rc.items():
                c[f"U:runs:L{z}"] += n
            c[f"U:length:{bkt(len(ls), 8)}"] += 1
            c[f"U:distinct:{len(set(ls))}"] += 1
        if mode in ("layer_transitions", "layer_core", "disk_full", "disk_no_ports"):
            for a, b in zip(ls, ls[1:]):
                c[f"T:L{a}>L{b}"] += 1
            for a, b in zip(collapsed, collapsed[1:]):
                c[f"CT:L{a}>L{b}"] += 1
            c["DIR:forward"] += forward
            c["DIR:same"] += same
            c["DIR:back"] += desc
        if mode in ("rounds_blocks", "layer_core", "disk_full", "disk_no_ports"):
            c[f"R:rounds:{bkt(rounds, 5)}"] += 1
            c[f"R:desc:{bkt(desc, 4)}"] += 1
            c[f"R:same:{bkt(same, 4)}"] += 1
            c[f"R:returns:{bkt(returns, 3)}"] += 1
            c[f"R:n_runs:{bkt(len(runs), 7)}"] += 1
            for layer, seg in runs:
                c[f"B:L{layer}:len:{bkt(len(seg), 4)}"] += 1
                c[f"B:L{layer}:uniq:{bkt(len(set(seg)), 3)}"] += 1
                c[f"B:L{layer}:allsame:{int(len(set(seg)) == 1)}"] += 1
        if mode in ("glyph_choice", "disk_full", "disk_no_ports"):
            for g, z in zip(gs, ls):
                c[f"G:all:L{z}:{g}"] += 1
            c[f"G:start:L{ls[0]}:{gs[0]}"] += 1
            c[f"G:end:L{ls[-1]}:{gs[-1]}"] += 1
            for layer, seg in runs:
                c[f"G:run_start:L{layer}:{seg[0]}"] += 1
                c[f"G:run_end:L{layer}:{seg[-1]}"] += 1
        if mode in ("ports", "disk_full"):
            for g1, g2, l1, l2 in zip(gs, gs[1:], ls, ls[1:]):
                if l1 != l2:
                    c[f"P:L{l1}:{g1}>L{l2}:{g2}"] += 1
    return c


def build_raw(page_words: dict[str, list[str]], pages: list[str], mapping: dict[str, int], mode: str):
    ds = [extract_features(page_words[p], mapping, mode) for p in pages]
    dv = DictVectorizer(sparse=True)
    x = dv.fit_transform(ds).astype(np.float64).tocsr()
    fn = np.array(dv.get_feature_names_out())
    if mode in ("glyph_choice", "ports", "disk_no_ports", "disk_full"):
        df = np.asarray((x > 0).sum(axis=0)).ravel()
        tot = np.asarray(x.sum(axis=0)).ravel()
        keep = (df >= 6) & (tot >= 15)
        x, fn = x[:, keep], fn[keep]
    return x, fn


def tfidf(raw, train_idx):
    x = raw.copy().astype(np.float64)
    x.data = np.log1p(x.data)
    df = np.asarray((raw[train_idx] > 0).sum(axis=0)).ravel()
    idf = np.log((1 + len(train_idx)) / (1 + df)) + 1
    return normalize(x.multiply(idf).tocsr(), norm="l2").tocsr()


def similarity_for_fold(raws, groups_idx, h):
    test = [g[h] for g in groups_idx]
    train = [i for g in groups_idx for j, i in enumerate(g) if j != h]
    sims = []
    for raw in raws:
        x = tfidf(raw, train)
        protos = []
        for g in groups_idx:
            inds = [i for j, i in enumerate(g) if j != h]
            v = sparse.csr_matrix(np.asarray(x[inds].mean(axis=0)))
            protos.append(normalize(v, norm="l2"))
        p = sparse.vstack(protos).tocsr()
        sims.append((x[test] @ p.T).toarray())
    return np.mean(sims, axis=0)


def metrics(s):
    n = s.shape[0]
    order = np.argsort(-s, axis=1)
    top1 = float(np.mean(order[:, 0] == np.arange(n)))
    top3 = float(np.mean([i in order[i, :3] for i in range(n)]))
    r, c = linear_sum_assignment(-s)
    assign = float(np.mean(c[r] == r))
    ranks = np.array([np.where(order[i] == i)[0][0] + 1 for i in range(n)])
    return top1, top3, assign, float(ranks.mean())


def directionality(page_words, pages, groups_idx, rng_seed, permutations):
    words = [w for p in pages for w in page_words[p]]
    covered = [(w, segment(w, VM23)) for w in words]
    covered = [(w, gs) for w, gs in covered if gs is not None]
    types = set(words)
    covered_types = {w for w, _ in covered}
    transitions = Counter()
    word_back = []
    for _, gs in covered:
        ls = [LAYER_MAP23[g] for g in gs]
        d = sum(b < a for a, b in zip(ls, ls[1:]))
        word_back.append(d)
        for a, b in zip(ls, ls[1:]):
            if b > a:
                transitions["forward"] += 1
            elif b == a:
                transitions["same"] += 1
            else:
                transitions["back"] += 1
    total_t = sum(transitions.values())
    observed_back = transitions["back"] / total_t

    # Directed glyph transition matrix permits fast random layer reassignments.
    glyph_idx = {g: i for i, g in enumerate(VM23)}
    m = np.zeros((23, 23), dtype=np.int64)
    for _, gs in covered:
        for a, b in zip(gs, gs[1:]):
            m[glyph_idx[a], glyph_idx[b]] += 1
    layer_template = np.array([0] * 1 + [1] * 6 + [2] * 5 + [3] * 4 + [4] * 3 + [5] * 1 + [6] * 3)
    rng = np.random.default_rng(rng_seed)
    # Generate random assignments in reproducible vectorized batches.  A random
    # permutation specifies which glyph receives each position in the fixed
    # layer-size template.  This is the archived randomization stream used for
    # the reported descriptive benchmark.
    batches = []
    remaining = permutations
    nonzero_i, nonzero_j = np.nonzero(m)
    while remaining:
        size = min(10000, remaining)
        permutation = np.argsort(rng.random((size, 23)), axis=1)
        layers = np.empty_like(permutation)
        layers[np.arange(size)[:, None], permutation] = layer_template[None, :]
        back_counts = np.zeros(size, dtype=float)
        for gi, gj in zip(nonzero_i, nonzero_j):
            back_counts += m[gi, gj] * (layers[:, gj] < layers[:, gi])
        batches.append(back_counts / total_t)
        remaining -= size
    perm_rates = np.concatenate(batches)
    count_le = int(np.sum(perm_rates <= observed_back + 1e-15))

    per_leaf = []
    for leaf_idx, g in enumerate(groups_idx):
        lt = Counter()
        for i in g:
            for w in page_words[pages[i]]:
                gs = segment(w, VM23)
                if not gs:
                    continue
                ls = [LAYER_MAP23[x] for x in gs]
                for a, b in zip(ls, ls[1:]):
                    lt["back" if b < a else "same" if b == a else "forward"] += 1
        per_leaf.append(lt["back"] / sum(lt.values()))

    return {
        "complete_bifolia": 21,
        "surfaces": 84,
        "analyzed_word_tokens": len(words),
        "covered_word_tokens": len(covered),
        "token_coverage": len(covered) / len(words),
        "observed_word_types": len(types),
        "covered_word_types": len(covered_types),
        "type_coverage": len(covered_types) / len(types),
        "word_internal_transitions": total_t,
        "forward_rate": transitions["forward"] / total_t,
        "same_rate": transitions["same"] / total_t,
        "backward_rate": observed_back,
        "randomized_backward_mean": float(perm_rates.mean()),
        "randomized_count_le_observed": count_le,
        "randomization_plus_one_tail": (count_le + 1) / (permutations + 1),
        "words_zero_backward": sum(x == 0 for x in word_back) / len(word_back),
        "words_zero_or_one_backward": sum(x <= 1 for x in word_back) / len(word_back),
        "per_bifolium_backward_min": min(per_leaf),
        "per_bifolium_backward_max": max(per_leaf),
        "per_bifolium_backward_rates": per_leaf,
        "permutation_seed": rng_seed,
        "permutations": permutations,
    }, perm_rates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zl3b", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20260817)
    ap.add_argument("--permutations", type=int, default=50000)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    _, records = load_zl3b(args.zl3b)
    pages, groups_idx, leaves = controlled_page_order()
    pw = page_tokens(records, pages, paragraph_only=False, require23=False)

    table1, rates = directionality(pw, pages, groups_idx, args.seed, args.permutations)
    dump_json(table1, args.outdir / "table1_seven_layer_directionality.json")
    np.savetxt(args.outdir / "table1_randomization_rates.csv", rates, delimiter=",", header="backward_rate", comments="")

    raw_layer, layer_features = build_raw(pw, pages, dict(LAYER_MAP23), "layer_core")
    raw_full, full_features = build_raw(pw, pages, dict(LAYER_MAP23), "disk_full")
    results = {}
    fold_rows = []
    for name, raw in (("layer_structure_only", raw_layer), ("full_seven_layer", raw_full)):
        vals = []
        for h in range(4):
            v = metrics(similarity_for_fold([raw], groups_idx, h))
            vals.append(v)
            fold_rows.append({"model": name, "heldout_position": h + 1, "top1": v[0], "top3": v[1], "one_to_one": v[2], "mean_rank": v[3]})
        mean = np.mean(vals, axis=0)
        results[name] = {"top1": float(mean[0]), "top3": float(mean[1]), "one_to_one": float(mean[2]), "mean_rank": float(mean[3]), "folds": vals}
    results["chance"] = {"top1": 1 / 21, "top3": 3 / 21, "one_to_one": 1 / 21}
    results["feature_dimensions"] = {"layer_structure_only": int(raw_layer.shape[1]), "full_seven_layer": int(raw_full.shape[1])}
    dump_json(results, args.outdir / "table2_seven_layer_bifolium_classification.json")
    with (args.outdir / "table2_folds.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fold_rows[0])); w.writeheader(); w.writerows(fold_rows)
    (args.outdir / "table2_layer_features.txt").write_text("\n".join(layer_features) + "\n", encoding="utf-8")
    (args.outdir / "table2_full_features.txt").write_text("\n".join(full_features) + "\n", encoding="utf-8")

    print(json.dumps({"table1": table1, "table2": results}, indent=2))

if __name__ == "__main__":
    main()
