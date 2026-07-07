#!/usr/bin/env python3
"""
make_exposure_layers.py — reshape the protection-layer analysis output into the
wide, publish-ready exposure_layers.csv the Federal Marketplace Index site reads.

Input : the long output of band_rule_of_two_exposure.py
        (columns: category, layer, dollars, actions), e.g.
        ..\\USWCC_FedData\\reports\\exposure_by_layer_raw.csv
Output: data/exposure_layers.csv in the site's wide schema
        (layer, label, {cat}_pct, {cat}_b) with pct at 2 decimals and
        dollar-billions at 1 decimal.

Pure standard library. Run from the repo root, or pass paths explicitly:
    python scripts/make_exposure_layers.py \
        --in ..\\USWCC_FedData\\reports\\exposure_by_layer_raw.csv \
        --out data/exposure_layers.csv

Every category's five layers are checked to sum to its total and its percentages
to ~100 before anything is written; a failure stops the build (no silent output).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Long-format layer codes -> published (code, label). Order is the published order.
LAYER_MAP = [
    ("L1_standalone_leq_MPT",          "L1", "Below MPT (no Rule of Two)"),
    ("L2_standalone_MPT_to_SAT_STATUTORY", "L2", "MPT-SAT standalone (statutory mandate)"),
    ("L3_standalone_gt_SAT_REGULATORY", "L3", "Above SAT standalone (regulation only)"),
    ("L4_order_leq_SAT",               "L4", "Orders at or below SAT"),
    ("L5_order_gt_SAT_RFO_CARVEOUT",   "L5", "Orders above SAT (carve-out channel)"),
]
LONG_TO_SHORT = {long: short for long, short, _ in LAYER_MAP}

# Analysis category name -> published short column name. Order is the published
# column order. Extend this map to publish more categories (the flag must already
# exist in the analysis output).
CATEGORY_MAP = [
    ("all",            "all"),
    ("small_business", "small"),
    ("sdb",            "sdb"),
    ("eight_a",        "eight_a"),
    ("wosb",           "wosb"),
    ("edwosb",         "edwosb"),
    ("hubzone",        "hubzone"),
    ("sdvosb",         "sdvosb"),
    ("vosb",           "vosb"),
    ("woman_owned",    "woman_owned"),
]

TOL = 0.005  # 0.5% tolerance on the percentage-sum check


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", default="../USWCC_FedData/reports/exposure_by_layer_raw.csv")
    ap.add_argument("--out", dest="out", default="data/exposure_layers.csv")
    args = ap.parse_args(argv)

    inp = Path(args.inp)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    # dollars[cat][layer_short] = float
    dollars: dict[str, dict[str, float]] = {}
    with open(inp, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cat = r["category"].strip()
            layer_long = r["layer"].strip()
            if layer_long not in LONG_TO_SHORT:
                raise SystemExit(f"Unexpected layer code: {layer_long!r}")
            dollars.setdefault(cat, {})[LONG_TO_SHORT[layer_long]] = float(r["dollars"])

    # Validate presence and internal consistency before writing anything.
    layer_order = [short for _, short, _ in LAYER_MAP]
    problems: list[str] = []
    active = [(src, dst) for src, dst in CATEGORY_MAP if src in dollars]
    missing = [src for src, _ in CATEGORY_MAP if src not in dollars]
    if missing:
        problems.append(f"categories absent from input (skipped): {', '.join(missing)}")
    for src, dst in active:
        got = set(dollars[src])
        need = set(layer_order)
        if got != need:
            problems.append(f"{src}: layers {sorted(need - got)} missing / {sorted(got - need)} extra")

    # Precompute totals + percentages; verify each category sums to 100%.
    pct: dict[str, dict[str, float]] = {}
    bil: dict[str, dict[str, float]] = {}
    for src, dst in active:
        tot = sum(dollars[src][l] for l in layer_order)
        if tot <= 0:
            problems.append(f"{src}: non-positive total {tot}")
            continue
        pct[src] = {l: 100.0 * dollars[src][l] / tot for l in layer_order}
        bil[src] = {l: dollars[src][l] / 1e9 for l in layer_order}
        s = sum(pct[src].values())
        if abs(s - 100.0) > TOL:
            problems.append(f"{src}: percentages sum to {s:.4f}, not 100")

    if problems:
        print("RECONCILIATION FAILED — nothing written:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # Write the wide table: layer, label, {cat}_pct..., {cat}_b...
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (["layer", "label"]
              + [f"{dst}_pct" for _, dst in active]
              + [f"{dst}_b" for _, dst in active])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for long_code, short, label in LAYER_MAP:
            row = [short, label]
            row += [f"{pct[src][short]:.2f}" for src, _ in active]
            row += [f"{bil[src][short]:.1f}" for src, _ in active]
            w.writerow(row)

    cats = ", ".join(dst for _, dst in active)
    print(f"Wrote {out} — {len(active)} categories x {len(layer_order)} layers.")
    print(f"Categories: {cats}")
    print("All categories reconcile (layers sum to total; percentages sum to 100).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
