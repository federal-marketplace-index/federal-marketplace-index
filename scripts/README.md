# Analysis scripts

These are the scripts that produce the published Federal Marketplace Index
tables. They live in the repo alongside the data and the site so that code,
data, and site travel together and the Zenodo snapshot captures the complete,
reproducible package.

## Pipeline and run order

The exposure table is built in two stages, then the order-channel series is
built separately:

1. `band_rule_of_two_exposure.py` — the engine. Reads the FY2022-FY2026 base
   table, classifies ("bands") every action into one of five Rule-of-Two
   protection layers (L1-L5) by dollar threshold and award/order type, and
   writes a long table (`category, layer, dollars, actions`) as
   **`exposure_by_layer_raw.csv`**. Award-mode banding is the published cut.

2. `make_exposure_layers.py` — the formatter. Reads
   `exposure_by_layer_raw.csv` and reshapes it into the wide, publish-ready
   **`data/exposure_layers.csv`** the site reads (`layer, label, {cat}_pct,
   {cat}_b`), for all nine socioeconomic categories plus "all."

3. `order_channel_migration.py` — produces **`data/order_channel_share_by_fy.csv`**
   (the order-channel migration series).

## Naming note

The engine's raw long output is named `exposure_by_layer_raw.csv` — deliberately
distinct from the published wide `data/exposure_layers.csv`, so the two never
collide, and matching the input name the formatter already expects.

## Reconciliation

Each script prints reconciliation checks (layers sum to category totals;
percentages sum to 100). Publication requires all checks to pass — a failure
stops the build with no file written.
