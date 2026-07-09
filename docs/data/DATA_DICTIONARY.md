# Data Dictionary — Federal Marketplace Index

## exposure\_layers.csv

Five-year (FY2022–FY2026) federal contract dollars by Rule of Two protection layer.

* layer: L1–L5 protection-layer code
* label: plain-language layer description
* {cat}\_pct: percent of that category's five-year dollars in the layer
* {cat}\_b: dollars in the layer, $ billions

Categories ({cat}): all (all federal dollars), small (small business),
sdb (small disadvantaged business), eight\_a (8(a) program),
wosb (women-owned small business), edwosb (economically disadvantaged WOSB),
hubzone (HUBZone), sdvosb (service-disabled veteran-owned), vosb (veteran-owned),
woman\_owned (women-owned firms of any size — broader than the WOSB program).

For the program categories the L2 (statutory-band) share reflects set-aside–eligible
dollars; for woman\_owned, read each layer as the share of that category's dollars in
the band, not as WOSB-program eligibility.

Banding is award-level with era-appropriate thresholds ($10K/$250K FY2022–FY2025;
$15K/$350K FY2026). Totals reconcile to SBA published goaling figures.

## order\_channel\_share\_by\_fy.csv

Order-channel (task orders, delivery orders, BPA calls) share of dollars by fiscal year and category.

* fiscal\_year: federal fiscal year (2026 is partial)
* category: all | small | wosb | edwosb
* order\_share\_pct: percent of the category's dollars obligated through the order channel that year
NOTE: this seed file carries the share column only. Replacing it with the full
reports\\order\_channel\_share\_by\_fy.csv produced by scripts/order\_channel\_migration.py
(which adds dollar and action columns) works without any site changes — the builder
reads columns by name.


\*\*`exposure\_layers\_dollars\_actions.csv`\*\* — Contract dollars and contract-action counts by Rule of Two protection layer and socioeconomic category, pooled FY2022–FY2026 (FY2026 partial), era-appropriate thresholds. Columns: `category` (see category key), `layer`, `dollars` (net obligations, USD; de-obligations included as negatives), `actions` (contract-action count). Layers: `L1\_standalone\_leq\_MPT` = standalone awards at or below the micro-purchase threshold; `L2\_standalone\_MPT\_to\_SAT\_STATUTORY` = standalone awards above the MPT up to the simplified acquisition threshold (the 15 U.S.C. § 644(j) statutory band); `L3\_standalone\_gt\_SAT\_REGULATORY` = standalone awards above the SAT (Rule of Two rests on regulation, FAR 19.502-2(b)); `L4\_order\_leq\_SAT` = task/delivery orders at or below the SAT; `L5\_order\_gt\_SAT\_RFO\_CARVEOUT` = orders above the SAT (the channel the proposed redefinition excludes). Category key: `all`, `small\_business`, `sdb`, `eight\_a`, `wosb` (WOSB program flag), `edwosb`, `hubzone`, `sdvosb`, `vosb`, `woman\_owned` (broader women-owned flag; not limited to the WOSB program — do not sum with `wosb`). Categories are non-exclusive; do not sum across categories. This is the long-format source behind `exposure\_layers.csv`: within each category, `dollars` as a share of that category's five-year total reproduces the site file's `{category}\_pct` columns, and `dollars ÷ 1e9` its `{category}\_b` columns (the chart file abbreviates `small\_business` to `small`).



