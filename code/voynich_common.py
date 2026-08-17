#!/usr/bin/env python3
"""Shared data parsing and VM-glyph utilities for the reproducibility package."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence

VM23 = ("q", "cfh", "ch", "cph", "cth", "p", "sh", "ckh", "f", "k", "o", "t", "a", "d", "e", "s", "i", "l", "y", "r", "m", "n", "g")
MULTI = tuple(sorted(("cfh", "cph", "cth", "ckh", "ch", "sh"), key=len, reverse=True))
LAYERS23 = (
    ("q",),
    ("cfh", "ch", "cph", "cth", "p", "sh"),
    ("ckh", "f", "k", "o", "t"),
    ("a", "d", "e", "s"),
    ("i", "l", "y"),
    ("r",),
    ("m", "n", "g"),
)
LAYER_MAP23 = {g: i for i, layer in enumerate(LAYERS23) for g in layer}
A2_PAGES = ("f2r", "f2v", "f7r", "f7v")
CONTROLLED_LEAVES = {
    "A-2": ("f2", "f7"), "A-3": ("f3", "f6"), "A-4": ("f4", "f5"),
    "A-5": ("f9", "f16"), "A-6": ("f10", "f15"), "A-7": ("f11", "f14"),
    "A-9": ("f17", "f24"), "A-10": ("f18", "f23"), "A-11": ("f19", "f22"),
    "A-12": ("f20", "f21"), "A-13": ("f25", "f32"), "A-14": ("f27", "f30"),
    "A-15": ("f28", "f29"), "A-16": ("f35", "f38"), "A-17": ("f36", "f37"),
    "A-18": ("f42", "f47"), "A-19": ("f44", "f45"), "A-20": ("f49", "f56"),
    "A-21": ("f51", "f54"), "A-22": ("f52", "f53"), "A-23": ("f93", "f96"),
}

@dataclass(frozen=True)
class LineRecord:
    page: str
    locus: str
    kind: str
    text: str
    meta: Mapping[str, str]


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def segment(word: str, allowed: Sequence[str] | None = None) -> list[str] | None:
    """Greedy EVA/VM segmentation, treating six multi-letter units as one glyph."""
    out: list[str] = []
    i = 0
    while i < len(word):
        match = next((g for g in MULTI if word.startswith(g, i)), None)
        if match is not None:
            out.append(match)
            i += len(match)
        elif word[i].isalpha() and word[i].islower():
            out.append(word[i])
            i += 1
        else:
            return None
    if allowed is not None and any(g not in allowed for g in out):
        return None
    return out


def load_zl3b(path: str | Path) -> tuple[dict[str, dict[str, str]], list[LineRecord]]:
    """Read ZL3b IVTFF page metadata and line/locus records."""
    page_meta: dict[str, dict[str, str]] = {}
    records: list[LineRecord] = []
    current_meta: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"<([^>.]+)>\s+<!\s*(.*?)>", raw)
        if m:
            page = m.group(1)
            current_meta = dict(re.findall(r"\$(\w+)=([^\s>]+)", m.group(2)))
            page_meta[page] = current_meta.copy()
            continue
        m = re.match(r"<([^,>]+),([^>]+)>\s+(.*)$", raw)
        if not m:
            continue
        locus, kind, text = m.groups()
        page = locus.split(".")[0]
        records.append(LineRecord(page, locus, kind, text, page_meta.get(page, current_meta).copy()))
    return page_meta, records


def clean_text(text: str, *, split_layout: bool = True) -> str:
    """Remove IVTFF annotations; preserve only token separators relevant to analysis."""
    text = text.replace("<%>", " ").replace("<$>", " ")
    text = re.sub(r"<!.*?>", " ", text)
    text = re.sub(r"<@H=.*?>", " ", text)
    text = text.replace("<~>", ".")
    text = text.replace("<->", "." if split_layout else "")
    return text


def tokens_from_text(text: str, *, require23: bool = False, split_layout: bool = True) -> list[str]:
    txt = clean_text(text, split_layout=split_layout)
    tokens = [x for x in re.split(r"[.,\s]+", txt) if x and re.fullmatch(r"[a-z]+", x)]
    if require23:
        tokens = [x for x in tokens if segment(x, VM23) is not None]
    return tokens


def extract_tokens(
    records: Iterable[LineRecord],
    *,
    pages: set[str] | None = None,
    paragraph_only: bool = False,
    require23: bool = False,
    meta_filter: Mapping[str, str] | None = None,
    split_layout: bool = True,
) -> list[str]:
    out: list[str] = []
    for rec in records:
        if pages is not None and rec.page not in pages:
            continue
        if paragraph_only and "P" not in rec.kind:
            continue
        if meta_filter and any(rec.meta.get(k) != v for k, v in meta_filter.items()):
            continue
        out.extend(tokens_from_text(rec.text, require23=require23, split_layout=split_layout))
    return out


def page_tokens(
    records: Iterable[LineRecord],
    pages: Iterable[str],
    *,
    paragraph_only: bool = True,
    require23: bool = False,
) -> dict[str, list[str]]:
    pset = set(pages)
    out: dict[str, list[str]] = {p: [] for p in pages}
    for rec in records:
        if rec.page in pset and (not paragraph_only or "P" in rec.kind):
            out[rec.page].extend(tokens_from_text(rec.text, require23=require23))
    return out


def controlled_page_order() -> tuple[list[str], list[list[int]], list[str]]:
    pages: list[str] = []
    groups: list[list[int]] = []
    leaves: list[str] = []
    for leaf, (f1, f2) in CONTROLLED_LEAVES.items():
        leaves.append(leaf)
        gpages = [f1 + "r", f1 + "v", f2 + "r", f2 + "v"]
        start = len(pages)
        pages.extend(gpages)
        groups.append(list(range(start, start + 4)))
    return pages, groups, leaves


def extract_a2_schedule(records: Iterable[LineRecord]) -> list[dict[str, object]]:
    """Return the supplied A-2 line/paragraph schedule used by the static shelf reconstruction.

    Each row records a paragraph line and its observed token count. The first line of a
    paragraph invokes Paragraph START; later lines invoke [SPACE,SPACE].
    """
    rows: list[dict[str, object]] = []
    paragraph_no = 0
    line_in_paragraph = 0
    for rec in records:
        if rec.page not in A2_PAGES or "P" not in rec.kind:
            continue
        is_start = rec.kind.startswith("@P") or "<%>" in rec.text
        if is_start:
            paragraph_no += 1
            line_in_paragraph = 1
        else:
            line_in_paragraph += 1
        toks = tokens_from_text(rec.text, require23=True)
        rows.append({
            "page": rec.page,
            "locus": rec.locus,
            "paragraph": paragraph_no,
            "line_in_paragraph": line_in_paragraph,
            "start_mode": "PARAGRAPH_START" if is_start else "NEUTRAL_RESTART",
            "token_count": len(toks),
            "observed_tokens": " ".join(toks),
        })
    return rows


def ngram_counter(words: Iterable[str], n: int) -> Counter[tuple[str, ...]]:
    c: Counter[tuple[str, ...]] = Counter()
    for w in words:
        gs = segment(w)
        if gs is None:
            continue
        c.update(tuple(gs[i : i + n]) for i in range(len(gs) - n + 1))
    return c


def boundary_counter(words_by_line: Iterable[Sequence[str]], *, include_line_boundaries: bool = False) -> Counter[tuple[str, str]]:
    """Count final-glyph -> initial-glyph pairs, by default only within each line."""
    c: Counter[tuple[str, str]] = Counter()
    previous: str | None = None
    for words in words_by_line:
        if not include_line_boundaries:
            previous = None
        for w in words:
            gs = segment(w)
            if not gs:
                continue
            if previous is not None:
                c[(previous, gs[0])] += 1
            previous = gs[-1]
    return c


def jsd_counts(a: Counter, b: Counter, *, base: float = 2.0) -> float:
    """Jensen-Shannon divergence between sparse count dictionaries."""
    import math
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    sa, sb = sum(a.values()), sum(b.values())
    if sa <= 0 or sb <= 0:
        return float("nan")
    div = 0.0
    log = lambda x: math.log(x, base)
    for k in keys:
        p = a.get(k, 0) / sa
        q = b.get(k, 0) / sb
        m = 0.5 * (p + q)
        if p:
            div += 0.5 * p * log(p / m)
        if q:
            div += 0.5 * q * log(q / m)
    return div


def dump_json(obj: object, path: str | Path) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tokens_from_text_attestation_strict(text: str) -> list[str]:
    """Token extraction used by the 5,000-run attestation/null comparison.

    This intentionally does not normalize <~>; it reproduces 37,597 tokens / 7,455
    types for the strict whole-manuscript comparison vocabulary.
    """
    txt = text.replace("<%>", "").replace("<$>", "")
    txt = re.sub(r"<!.*?>", "", txt).replace("<->", ".")
    return [x for x in re.split(r"[.,\s]+", txt) if x and re.fullmatch(r"[a-z]+", x)]


def extract_tokens_attestation_strict(
    records: Iterable[LineRecord], *, pages: set[str] | None = None, paragraph_only: bool = False, require23: bool = False
) -> list[str]:
    out: list[str] = []
    for rec in records:
        if pages is not None and rec.page not in pages:
            continue
        if paragraph_only and "P" not in rec.kind:
            continue
        for w in tokens_from_text_attestation_strict(rec.text):
            if require23 and segment(w, VM23) is None:
                continue
            out.append(w)
    return out
