#!/usr/bin/env python3
"""Rule-of-Two exposure banding — which protection layer covers the money?

Classifies every FY2022-FY2026 base-table action into a protection layer and
reports dollars/actions by layer for ALL socioeconomic categories the base
table carries (all dollars, small business, and every set-aside category you
map below). The headline output is the share of each category's dollars that
would remain under a MANDATORY Rule of Two if the regulatory layers go away —
i.e., standalone awards in the MPT-to-SAT statutory band (15 U.S.C. 644(j)(1);
FAR 19.502-2(a)).

Layers:
  L1  standalone, <= MPT          micro-purchase; no Rule of Two
  L2  standalone, MPT-SAT         STATUTORY mandatory set-aside (644(j))
  L3  standalone, > SAT           REGULATORY Rule of Two (FAR 19.502-2(b))
  L4  order (MAC/FSS/BPA), <=SAT  order-level; discretionary by 644(r)
  L5  order (MAC/FSS/BPA), > SAT  order-level; the RFO carve-out channel

Thresholds are era-appropriate (FAC 2025-06 took effect 2025-10-01 = FY2026):
  FY2022-FY2025: MPT $10,000 / SAT $250,000
  FY2026:        MPT $15,000 / SAT $350,000

Banding modes (--band-by):
  action  each action banded by its own obligation (fast; crude; counts
          deobligations at face value)
  award   obligations aggregated per award key first, the award is banded by
          its total, then all its dollars land in that band (DEFAULT; closer
          to how an acquisition's size is judged at set-aside time)

The script never guesses your schema silently. Edit COLUMNS (structural fields)
and CATEGORIES (socioeconomic flags) below to point at your base table's actual
column names, or run with --list-columns first to print the schema and exit.
Derived boolean flags from your pipeline (e.g., an is_wosb you already trust
from the goaling work) are BETTER inputs than raw FPDS fields — plug them in.
Set any category's column to None to skip that category cleanly.

Usage:
  python band_rule_of_two_exposure.py --input "..\\USWCC_FedData\\base_table" --list-columns
  python band_rule_of_two_exposure.py --input "..\\USWCC_FedData\\base_table" \
      --out-dir "..\\USWCC_FedData\\exhibits" [--band-by award] [--csv-fallback]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# EDIT ME (1/2): structural columns -> your base table's real column names.
# These are the fields the banding logic itself needs. Set a value to None to
# skip cleanly only where the code tolerates it (agency_code is optional when
# award_id is globally unique).
COLUMNS = {  # fitted to the USWCC base table schema, 2026-07-01
    "fiscal_year":   "fiscal_year",
    "obligation":    "federal_action_obligation",
    "award_id":      "contract_award_unique_key",  # already globally unique
    "agency_code":   None,                         # not needed with the above
    "award_type":    "award_type",
}

# If a flag points at a raw text column, these values count as true.
SMALL_VALUES = {"S", "SMALL BUSINESS", "SMALL", "TRUE", "T", "1", "Y", "YES"}
TRUE_VALUES = {"TRUE", "T", "1", "Y", "YES"}

# ---------------------------------------------------------------------------
# EDIT ME (2/2): socioeconomic categories to band.
# Each entry maps a DISPLAY LABEL (used in the output CSV and headline) to the
# pipeline-derived boolean flag column and the value-set counted as true.
#   - Run --list-columns FIRST, then point each "col" at the real derived flag.
#   - Set "col" to None to skip a category cleanly (no silent drop).
#   - A mapped-but-missing column is a LOUD error, same as structural fields.
# "all" (the whole universe) is always reported and is not listed here.
CATEGORIES = {
    # --- Group 1: the eight small-business set-aside PROGRAM categories.
    # For these, the L2 statutory-band headline reads natively (dollars sitting
    # in the standalone MPT-SAT band that rests on the 644(j) floor).
    "small_business": {"col": "is_small",   "true": SMALL_VALUES},
    "sdb":            {"col": "is_sdb",     "true": TRUE_VALUES},   # small disadvantaged business
    "eight_a":        {"col": "is_8a",      "true": TRUE_VALUES},   # 8(a) program
    "wosb":           {"col": "is_wosb",    "true": TRUE_VALUES},   # women-owned small business
    "edwosb":         {"col": "is_edwosb",  "true": TRUE_VALUES},   # economically disadvantaged WOSB
    "hubzone":        {"col": "is_hubzone", "true": TRUE_VALUES},   # HUBZone
    "sdvosb":         {"col": "is_sdvosb",  "true": TRUE_VALUES},   # service-disabled veteran-owned
    "vosb":           {"col": "is_vosb",    "true": TRUE_VALUES},   # veteran-owned small business
    # --- Group 2: broad WOMAN-OWNED descriptor (wider than the WOSB program —
    # women-owned regardless of size). Documented in the methodology paper's
    # Appendix A, so it ships in this deposit edition. For this row read L2 as
    # "share of the category's dollars in the statutorily-protected band," not
    # "WOSB-eligible."
    "woman_owned":    {"col": "is_woman_owned",  "true": TRUE_VALUES},
    # NOTE: the six race/ethnicity descriptors (is_minority_owned, is_black_owned,
    # is_hispanic_owned, is_native_american_owned, is_asian_pacific_owned,
    # is_asian_indian_owned) are intentionally HELD from this edition — their
    # flags are not yet documented in the methodology paper's Appendix A, and the
    # paper places race/ethnicity in the forthcoming availability-and-utilization
    # (disparity) edition (§7). Document them in Appendix A before publishing them
    # here; the pipeline already derives all six.
}

# Substrings identifying order-level actions in award_type (upper-cased match):
ORDER_TYPES = ("DELIVERY ORDER", "TASK ORDER", "BPA CALL", "BOA ORDER")
# Everything else (DEFINITIVE CONTRACT, PURCHASE ORDER, ...) = standalone.

# Era-appropriate thresholds by FY (FAC 2025-06 effective 2025-10-01 = FY2026):
def thresholds_for_fy(fy: int) -> tuple[float, float]:
    return (15_000.0, 350_000.0) if fy >= 2026 else (10_000.0, 250_000.0)

LAYERS = ["L1_standalone_leq_MPT", "L2_standalone_MPT_to_SAT_STATUTORY",
          "L3_standalone_gt_SAT_REGULATORY", "L4_order_leq_SAT",
          "L5_order_gt_SAT_RFO_CARVEOUT"]


def classify(is_order: bool, band_value: float, fy: int) -> str:
    mpt, sat = thresholds_for_fy(fy)
    v = abs(band_value)
    if is_order:
        return LAYERS[3] if v <= sat else LAYERS[4]
    if v <= mpt:
        return LAYERS[0]
    if v <= sat:
        return LAYERS[1]
    return LAYERS[2]


def _truthy(val, value_set) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().upper() in value_set


def open_dataset(input_path: str, csv_fallback: bool):
    """Return an iterator of pyarrow record batches with only needed columns."""
    import pyarrow.dataset as ds
    p = Path(input_path)
    fmt = "csv" if csv_fallback else "parquet"
    dataset = ds.dataset(str(p), format=fmt)
    return dataset


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Band Rule-of-Two exposure.")
    ap.add_argument("--input", required=True,
                    help="base table: a parquet file, directory, or (with "
                         "--csv-fallback) csv path/directory")
    ap.add_argument("--out-dir", default=".", help="where to write the CSVs")
    ap.add_argument("--band-by", choices=("award", "action"), default="award")
    ap.add_argument("--csv-fallback", action="store_true",
                    help="read csv instead of parquet")
    ap.add_argument("--list-columns", action="store_true",
                    help="print the dataset schema and exit (do this first)")
    args = ap.parse_args(argv)

    try:
        dataset = open_dataset(args.input, args.csv_fallback)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"Could not open dataset at {args.input}: {e}")

    schema_names = set(dataset.schema.names)
    if args.list_columns:
        print("Columns in dataset:")
        for n in dataset.schema.names:
            print(f"  {n}")
        print("\nEdit COLUMNS and CATEGORIES at the top of this script to "
              "match, then re-run.")
        return 0

    # Validate the mapping loudly before touching data.
    structural_needed = {k: v for k, v in COLUMNS.items() if v is not None}
    category_mapped = {label: spec["col"]
                       for label, spec in CATEGORIES.items()
                       if spec["col"] is not None}

    missing = {f"COLUMNS[{k!r}]": v for k, v in structural_needed.items()
               if v not in schema_names}
    missing.update({f"CATEGORIES[{label!r}]": col
                    for label, col in category_mapped.items()
                    if col not in schema_names})
    if missing:
        lines = "\n".join(f"  {k} -> '{v}' (not found)"
                          for k, v in missing.items())
        raise SystemExit(
            "Column mapping doesn't match the dataset. Fix these entries "
            "(or set a category's col to None to skip it):\n"
            f"{lines}\n\nRun with --list-columns to see what's available.")

    for label, spec in CATEGORIES.items():
        if spec["col"] is None:
            print(f"  note: CATEGORIES[{label!r}] col is None -> "
                  f"'{label}' summary skipped.")

    # Ordered list of active category labels (mapping already validated).
    categories = [label for label, spec in CATEGORIES.items()
                  if spec["col"] is not None]

    proj = sorted(set(structural_needed.values()) | set(category_mapped.values()))
    scanner_cols = proj

    # ------------------------------------------------------------------
    # Pass 1 (award mode only): total obligation per award key per FY-era.
    # Keyed by (agency_code, award_id); banded on total across all its actions.
    # ------------------------------------------------------------------
    award_totals: dict[tuple, float] = defaultdict(float)
    award_fy: dict[tuple, int] = {}       # first FY seen (era for thresholds)

    def rows(batch):
        cols = {name: batch.column(name).to_pylist() for name in scanner_cols}
        n = len(next(iter(cols.values()))) if cols else 0
        for i in range(n):
            yield {name: cols[name][i] for name in scanner_cols}

    if args.band_by == "award":
        print("  pass 1/2: aggregating obligations per award ...", flush=True)
        for batch in dataset.to_batches(columns=scanner_cols):
            for r in rows(batch):
                try:
                    ob = float(r[COLUMNS["obligation"]] or 0.0)
                    fy = int(r[COLUMNS["fiscal_year"]])
                except (TypeError, ValueError):
                    continue
                key = (str(r.get(COLUMNS["agency_code"], "")),
                       str(r.get(COLUMNS["award_id"], "")))
                award_totals[key] += ob
                award_fy.setdefault(key, fy)
        print(f"    {len(award_totals):,} distinct award keys.", flush=True)

    # ------------------------------------------------------------------
    # Pass 2: classify and accumulate dollars/actions by layer x category.
    # ------------------------------------------------------------------
    print("  pass 2/2: classifying actions into protection layers ...", flush=True)
    dollars = defaultdict(float)   # (category, layer) -> $
    actions = defaultdict(int)     # (category, layer) -> count
    skipped = 0
    for batch in dataset.to_batches(columns=scanner_cols):
        for r in rows(batch):
            try:
                ob = float(r[COLUMNS["obligation"]] or 0.0)
                fy = int(r[COLUMNS["fiscal_year"]])
            except (TypeError, ValueError):
                skipped += 1
                continue
            at = str(r.get(COLUMNS["award_type"], "") or "").upper()
            is_order = any(t in at for t in ORDER_TYPES)
            if args.band_by == "award":
                key = (str(r.get(COLUMNS["agency_code"], "")),
                       str(r.get(COLUMNS["award_id"], "")))
                band_value = award_totals.get(key, ob)
                fy_era = award_fy.get(key, fy)
            else:
                band_value, fy_era = ob, fy
            layer = classify(is_order, band_value, fy_era)

            dollars[("all", layer)] += ob
            actions[("all", layer)] += 1
            for label in categories:
                spec = CATEGORIES[label]
                if _truthy(r.get(spec["col"]), spec["true"]):
                    dollars[(label, layer)] += ob
                    actions[(label, layer)] += 1
    if skipped:
        print(f"    skipped {skipped:,} rows with unparseable FY/obligation.")

    # ------------------------------------------------------------------
    # Write outputs + print the headline.
    # ------------------------------------------------------------------
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Published-table name matches the methodology paper (§5). Award banding is
    # the published cut (§5.1); action mode gets a suffix so it can't clobber it.
    detail = out / ("exposure_by_layer_raw.csv" if args.band_by == "award"
                    else f"exposure_by_layer_raw_{args.band_by}.csv")
    with detail.open("w", encoding="utf-8", newline="") as f:
        f.write("category,layer,dollars,actions\n")
        for cat in ["all"] + categories:
            for layer in LAYERS:
                f.write(f"{cat},{layer},{dollars[(cat, layer)]:.2f},"
                        f"{actions[(cat, layer)]}\n")
    print(f"\n  wrote {detail}")

    print("\n  ===== HEADLINE: where does the mandatory Rule of Two survive? =====")
    print("  (share of each category's dollars in L2 = standalone, MPT-SAT,")
    print("   the only layer resting on the statutory floor, 15 U.S.C. 644(j))\n")
    _w = max(len(c) for c in ["all"] + categories)
    for cat in ["all"] + categories:
        tot = sum(dollars[(cat, l)] for l in LAYERS)
        if tot == 0:
            continue
        l2 = dollars[(cat, LAYERS[1])]
        l5 = dollars[(cat, LAYERS[4])]
        l45 = dollars[(cat, LAYERS[3])] + l5
        print(f"  {cat:<{_w}s} total ${tot/1e9:,.1f}B | statutory-band (L2): "
              f"{100*l2/tot:5.2f}% | order-level (L4+L5): {100*l45/tot:5.2f}% "
              f"| above-SAT orders (L5): {100*l5/tot:5.2f}%")
    print("\n  Interpretation: everything outside L2 relies on the regulatory")
    print("  Rule of Two (19.502-2(b)) or discretionary order-level set-asides")
    print("  (644(r)) - the layers the RFO makes discretionary or removes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
