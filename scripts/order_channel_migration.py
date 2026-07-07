#!/usr/bin/env python3
"""
order_channel_migration.py (v2, pre-fitted) — FY-by-FY order-channel share.

Pre-fitted to the USWCC base table schema (from the band_rule_of_two_exposure
--list-columns run): fiscal_year, federal_action_obligation, is_small, is_wosb,
is_edwosb, award_type. No editing required.

Produces, for FY2022-FY2026 and for four categories (all / small / wosb /
edwosb): dollars and actions through the order channel vs. standalone, per FY.
Fills Exhibit 7's [INSERT: exact % by FY] and upgrades the comment's pooled
order shares to a year-by-year series.

TWO reconciliation checks print at the end — both must pass before any number
is used:
  1. Category dollar totals vs. the exposure run:
       all $3,445.7B | small $759.9B | WOSB $118.2B | EDWOSB $44.1B
  2. POOLED order share vs. the exposure run (validates order classification):
       all 56.70% | small 67.83% | WOSB 73.22% | EDWOSB 72.93%
If either is off beyond rounding, STOP and send Claude the output.

Usage:
  python order_channel_migration.py --input "..\\USWCC_FedData\\base\\usaspending"
Optional: --out-dir reports   --batch-rows 500000   --list-columns
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.dataset as ds

COLUMNS = {
    "fiscal_year": "fiscal_year",
    "dollars": "federal_action_obligation",
    "is_small": "is_small",
    "is_wosb": "is_wosb",
    "is_edwosb": "is_edwosb",
    "order_flag": None,                 # not used; classification via award_type
    "award_type": "award_type",
}
# USAspending award_type values that are orders under a vehicle.
# (FPDS records task orders under IDIQs as DELIVERY ORDER; BPA calls are orders.)
ORDER_TYPE_VALUES = {"DELIVERY ORDER", "TASK ORDER", "BPA CALL"}

TRUTHY = {"1", "true", "t", "y", "yes", "x"}
FY_MIN, FY_MAX = 2022, 2026
EXPECT_TOTALS_B = {"all": 3445.7, "small": 759.9, "wosb": 118.2, "edwosb": 44.1}
EXPECT_ORDER_SHARE = {"all": 56.70, "small": 67.83, "wosb": 73.22, "edwosb": 72.93}


def truthy(v) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    return str(v).strip().lower() in TRUTHY


def open_dataset(path: Path) -> ds.Dataset:
    if path.is_dir():
        try:
            d = ds.dataset(str(path), format="parquet")
            _ = d.schema  # force schema resolution
            return d
        except Exception:
            return ds.dataset(str(path), format=ds.CsvFileFormat())
    fmt = "parquet" if path.suffix.lower() in (".parquet", ".pq") else "csv"
    if fmt == "csv":
        return ds.dataset(str(path), format=ds.CsvFileFormat())
    return ds.dataset(str(path), format="parquet")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", "--base-table", dest="input", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("reports"))
    ap.add_argument("--batch-rows", type=int, default=500_000)
    ap.add_argument("--list-columns", action="store_true")
    args = ap.parse_args()

    dataset = open_dataset(args.input)
    if args.list_columns:
        print(f"Columns in {args.input}:")
        for name in dataset.schema.names:
            print(f"  {name}")
        return 0

    needed = [COLUMNS["fiscal_year"], COLUMNS["dollars"], COLUMNS["is_small"],
              COLUMNS["is_wosb"], COLUMNS["is_edwosb"], COLUMNS["award_type"]]
    missing = [c for c in needed if c not in dataset.schema.names]
    if missing:
        print(f"ERROR: columns not found: {missing}", file=sys.stderr)
        print("Run with --list-columns and send Claude the output.", file=sys.stderr)
        return 2

    acc = defaultdict(lambda: [0.0, 0.0, 0, 0])  # (fy,cat) -> [$order, $standalone, n_order, n_standalone]
    categories = ("all", "small", "wosb", "edwosb")
    rows_seen = rows_skipped_fy = 0

    scanner = dataset.scanner(columns=needed, batch_size=args.batch_rows)
    for bi, batch in enumerate(scanner.to_batches(), start=1):
        cols = [batch.column(j).to_pylist() for j in range(len(needed))]
        fy_l, dl, sm, wo, ed, at = cols
        for k in range(len(fy_l)):
            try:
                fy = int(str(fy_l[k])[:4])
            except (TypeError, ValueError):
                rows_skipped_fy += 1
                continue
            if fy < FY_MIN or fy > FY_MAX:
                rows_skipped_fy += 1
                continue
            d = float(dl[k]) if dl[k] is not None else 0.0
            is_order = (str(at[k]).strip().upper() if at[k] is not None else "") in ORDER_TYPE_VALUES
            slot = 0 if is_order else 1
            for cat, on in zip(categories, (True, truthy(sm[k]), truthy(wo[k]), truthy(ed[k]))):
                if on:
                    a = acc[(fy, cat)]
                    a[slot] += d
                    a[2 + slot] += 1
            rows_seen += 1
        if bi % 10 == 0:
            print(f"  ...batch {bi}, {rows_seen:,} rows accumulated")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / "order_channel_share_by_fy.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fiscal_year", "category", "total_dollars", "order_dollars",
                    "standalone_dollars", "order_share_pct",
                    "order_actions", "standalone_actions", "order_action_share_pct"])
        for fy in range(FY_MIN, FY_MAX + 1):
            for cat in categories:
                do, dsa, no, nsa = acc[(fy, cat)]
                tot = do + dsa
                w.writerow([fy, cat, round(tot, 2), round(do, 2), round(dsa, 2),
                            round(100 * do / tot, 2) if tot else "",
                            no, nsa,
                            round(100 * no / (no + nsa), 2) if (no + nsa) else ""])

    print(f"\nRows in FY window: {rows_seen:,}  |  outside/blank FY skipped: {rows_skipped_fy:,}")
    print("\nOrder-channel share of DOLLARS by fiscal year (%):")
    print("  FY     " + "".join(f"{c:>10}" for c in categories))
    for fy in range(FY_MIN, FY_MAX + 1):
        line = f"  {fy}  "
        for cat in categories:
            do, dsa, _, _ = acc[(fy, cat)]
            tot = do + dsa
            line += f"{(100 * do / tot):>9.1f}%" if tot else f"{'—':>10}"
        print(line + ("   (partial FY)" if fy == 2026 else ""))

    print("\nRECONCILIATION 1 — category totals across FYs ($B) vs exposure run:")
    pooled = {}
    for cat in categories:
        do = sum(acc[(fy, cat)][0] for fy in range(FY_MIN, FY_MAX + 1))
        dsa = sum(acc[(fy, cat)][1] for fy in range(FY_MIN, FY_MAX + 1))
        pooled[cat] = (do, dsa)
        print(f"  {cat:>7}: {(do + dsa)/1e9:>9,.1f}   (expected {EXPECT_TOTALS_B[cat]:,.1f})")
    print("\nRECONCILIATION 2 — POOLED order share (%) vs exposure run:")
    for cat in categories:
        do, dsa = pooled[cat]
        share = 100 * do / (do + dsa) if (do + dsa) else 0.0
        print(f"  {cat:>7}: {share:>8.2f}   (expected {EXPECT_ORDER_SHARE[cat]:.2f})")
    print(f"\nWrote {out_csv}")
    print("Both checks must match within rounding before any number is used.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
