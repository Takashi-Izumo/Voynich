#!/usr/bin/env python3
"""Core implementation of the published A-2 shelf state machine.

The implementation follows Appendix A of the submitted paper:
- draws are with replacement from the fixed compartment inventory;
- the selected output is written before the stopping threshold is tested;
- ordinary stops enter [output, SPACE] and reset the word length to zero;
- paragraph starts use the separate START inventory;
- noninitial lines use the supplied neutral restart [SPACE, SPACE].
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from voynich_common import boundary_counter, jsd_counts, ngram_counter, segment

SPACE = "SPACE"
GALLOWS = frozenset({"p", "f", "k", "t"})


@dataclass(frozen=True)
class Tablet:
    output: str
    stop_number: int
    multiplicity: int
    tablet_class: str
    safety: int


@dataclass
class GeneratedRun:
    lines: list[list[str]]
    line_modes: list[str]
    dead_ends: int = 0

    @property
    def words(self) -> list[str]:
        return [w for line in self.lines for w in line]


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_main_inventory(path: str | Path) -> dict[tuple[str, str], list[Tablet]]:
    inv: dict[tuple[str, str], list[Tablet]] = defaultdict(list)
    for r in read_csv_rows(path):
        inv[(r["state_1"], r["state_2"])].append(
            Tablet(
                output=r["output"],
                stop_number=int(r["stop_number"]),
                multiplicity=int(r["multiplicity"]),
                tablet_class=r["class"],
                safety=int(r["safety"]),
            )
        )
    return dict(inv)


def load_start_inventory(path: str | Path) -> list[Tablet]:
    rows = read_csv_rows(path)
    return [
        Tablet(
            output=r["output"],
            stop_number=int(r["stop_number"]),
            multiplicity=int(r["multiplicity"]),
            tablet_class=r.get("class", "START"),
            safety=int(r.get("safety", 0)),
        )
        for r in rows
    ]


def load_schedule(path: str | Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for r in read_csv_rows(path):
        rows.append(
            {
                "page": r["page"],
                "locus": r["locus"],
                "paragraph": int(r["paragraph"]),
                "line_in_paragraph": int(r["line_in_paragraph"]),
                "start_mode": r["start_mode"],
                "token_count": int(r["token_count"]),
                "observed_tokens": r["observed_tokens"].split(),
            }
        )
    return rows


def _weighted_draw(tablets: Sequence[Tablet], rng: np.random.Generator) -> Tablet:
    total = sum(t.multiplicity for t in tablets)
    if total <= 0:
        raise RuntimeError("Cannot draw from an empty/zero-weight tablet inventory")
    x = int(rng.integers(total))
    running = 0
    for t in tablets:
        running += t.multiplicity
        if x < running:
            return t
    raise AssertionError("weighted draw fell outside cumulative multiplicity")


def generate_run(
    inventory: dict[tuple[str, str], list[Tablet]],
    start_inventory: Sequence[Tablet],
    schedule: Sequence[dict[str, object]],
    rng: np.random.Generator,
    *,
    max_draws_per_word: int = 100,
) -> GeneratedRun:
    """Generate one A-2-sized run conditional on the supplied line schedule."""
    lines: list[list[str]] = []
    modes: list[str] = []
    dead_ends = 0
    for row in schedule:
        target = int(row["token_count"])
        mode = str(row["start_mode"])
        modes.append(mode)
        words: list[str] = []

        if mode == "PARAGRAPH_START":
            t = _weighted_draw(start_inventory, rng)
            current = [t.output]
            state = (SPACE, t.output)
            word_length = 1
        elif mode == "NEUTRAL_RESTART":
            current = []
            state = (SPACE, SPACE)
            word_length = 0
        else:
            raise ValueError(f"Unknown start mode: {mode}")

        draws_this_word = 0
        while len(words) < target:
            tablets = inventory.get(state)
            if not tablets:
                dead_ends += 1
                raise RuntimeError(
                    f"Unrecoverable empty state {state} at line {row['locus']}, "
                    f"word_length={word_length}, generated_words={len(words)}"
                )
            tablet = _weighted_draw(tablets, rng)
            draws_this_word += 1
            if draws_this_word > max_draws_per_word:
                raise RuntimeError(f"Exceeded {max_draws_per_word} draws in one word")

            current.append(tablet.output)
            word_length += 1
            if tablet.stop_number <= word_length:
                words.append("".join(current))
                state = (tablet.output, SPACE)
                current = []
                word_length = 0
                draws_this_word = 0
                if len(words) >= target:
                    break
            else:
                state = (state[1], tablet.output)
        lines.append(words)
    return GeneratedRun(lines=lines, line_modes=modes, dead_ends=dead_ends)


def run_statistics(run: GeneratedRun, observed_lines: Sequence[Sequence[str]]) -> dict[str, float]:
    words = run.words
    lengths = np.asarray([len(segment(w) or []) for w in words], dtype=float)
    counts = Counter(words)
    bigram_jsd = jsd_counts(ngram_counter([w for line in observed_lines for w in line], 2), ngram_counter(words, 2))
    trigram_jsd = jsd_counts(ngram_counter([w for line in observed_lines for w in line], 3), ngram_counter(words, 3))
    observed_boundary = boundary_counter(observed_lines, include_line_boundaries=False)
    generated_boundary = boundary_counter(run.lines, include_line_boundaries=False)
    boundary_jsd = jsd_counts(observed_boundary, generated_boundary)

    paragraph_first = []
    neutral_first = []
    for line, mode in zip(run.lines, run.line_modes):
        if not line:
            continue
        gs = segment(line[0]) or []
        if not gs:
            continue
        (paragraph_first if mode == "PARAGRAPH_START" else neutral_first).append(gs[0])

    return {
        "word_types": float(len(counts)),
        "hapax_legomena": float(sum(v == 1 for v in counts.values())),
        "mean_word_length": float(lengths.mean()),
        "word_length_sd": float(lengths.std(ddof=0)),
        "one_character_rate": float(np.mean(lengths == 1)),
        "eight_plus_rate": float(np.mean(lengths >= 8)),
        "bigram_jsd": float(bigram_jsd),
        "trigram_jsd": float(trigram_jsd),
        "word_boundary_jsd": float(boundary_jsd),
        "paragraph_start_gallows": float(np.mean([g in GALLOWS for g in paragraph_first])) if paragraph_first else float("nan"),
        "neutral_restart_gallows": float(np.mean([g in GALLOWS for g in neutral_first])) if neutral_first else float("nan"),
        "dead_ends": float(run.dead_ends),
    }


def attestation_statistics(
    words: Sequence[str],
    a2_vocab: set[str],
    herbal_a_vocab: set[str],
    vm_vocab: set[str],
) -> dict[str, float]:
    n = len(words)
    token_counts = [0, 0, 0, 0]
    type_counts = [0, 0, 0, 0]

    def category(w: str) -> int:
        if w in a2_vocab:
            return 0
        if w in herbal_a_vocab:
            return 1
        if w in vm_vocab:
            return 2
        return 3

    for w in words:
        token_counts[category(w)] += 1
    for w in set(words):
        type_counts[category(w)] += 1
    nt = len(set(words))
    return {
        "A2": token_counts[0] / n,
        "HerbalA_outside_A2": token_counts[1] / n,
        "VM_outside_HerbalA": token_counts[2] / n,
        "Unattested": token_counts[3] / n,
        "VM_total": sum(token_counts[:3]) / n,
        "Outside_A2_total": sum(token_counts[1:3]) / n,
        "Generated_types": float(nt),
        "Hapax": float(sum(v == 1 for v in Counter(words).values())),
        "A2_type_rate": type_counts[0] / nt,
        "HerbalA_type_rate": sum(type_counts[:2]) / nt,
        "VM_type_rate": sum(type_counts[:3]) / nt,
    }


def summarize_numeric_rows(rows: Sequence[dict[str, float]]) -> dict[str, dict[str, float]]:
    if not rows:
        return {}
    result: dict[str, dict[str, float]] = {}
    for key in rows[0]:
        vals = np.asarray([float(r[key]) for r in rows], dtype=float)
        result[key] = {
            "mean": float(np.nanmean(vals)),
            "sd_across_runs": float(np.nanstd(vals, ddof=0)),
            "p2_5": float(np.nanquantile(vals, 0.025)),
            "p50": float(np.nanquantile(vals, 0.5)),
            "p97_5": float(np.nanquantile(vals, 0.975)),
        }
    return result


def observed_lines_from_schedule(schedule: Sequence[dict[str, object]]) -> list[list[str]]:
    return [list(row["observed_tokens"]) for row in schedule]
