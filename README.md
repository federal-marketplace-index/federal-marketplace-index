# The Federal Marketplace Index
Measured. Reconciled. Public.

Independent, reproducible measures of the federal small-business marketplace,
built entirely from public federal data. Powered by The American Small Business
Chamber of Commerce. Not a U.S. government website.

## Repository layout
- `data/` — the published tables (CSV), the data dictionary, and the data_as_of stamp
- `scripts/` — the analysis scripts that produce the tables from public data
- `build_site.py` — generates the entire website into `docs/` from `data/`
- `docs/` — the built website (served by GitHub Pages; never edit by hand)
- `changelog.md` — every update and correction, permanently
- `RUNBOOK.md` — the quarterly update procedure
- `SETUP.md` — one-time setup (GitHub, Pages, domain)

## Rebuild the site
    python build_site.py
Then open `docs/index.html` locally to review, and publish with GitHub Desktop.

## Licenses
Data and text: CC BY 4.0 (reuse freely with attribution to the Federal
Marketplace Index). Code: MIT.
