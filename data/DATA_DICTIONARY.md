# Data Dictionary — Federal Marketplace Index

## exposure_layers.csv
Five-year (FY2022–FY2026) federal contract dollars by Rule of Two protection layer.
- layer: L1–L5 protection-layer code
- label: plain-language layer description
- {cat}_pct: percent of that category's five-year dollars in the layer
- {cat}_b: dollars in the layer, $ billions

Categories ({cat}): all (all federal dollars), small (small business),
sdb (small disadvantaged business), eight_a (8(a) program),
wosb (women-owned small business), edwosb (economically disadvantaged WOSB),
hubzone (HUBZone), sdvosb (service-disabled veteran-owned), vosb (veteran-owned),
woman_owned (women-owned firms of any size — broader than the WOSB program).

For the program categories the L2 (statutory-band) share reflects set-aside–eligible
dollars; for woman_owned, read each layer as the share of that category's dollars in
the band, not as WOSB-program eligibility.

Banding is award-level with era-appropriate thresholds ($10K/$250K FY2022–FY2025;
$15K/$350K FY2026). Totals reconcile to SBA published goaling figures.

## order_channel_share_by_fy.csv
Order-channel (task orders, delivery orders, BPA calls) share of dollars by fiscal year and category.
- fiscal_year: federal fiscal year (2026 is partial)
- category: all | small | wosb | edwosb
- order_share_pct: percent of the category's dollars obligated through the order channel that year
NOTE: this seed file carries the share column only. Replacing it with the full
reports\order_channel_share_by_fy.csv produced by scripts/order_channel_migration.py
(which adds dollar and action columns) works without any site changes — the builder
reads columns by name.
