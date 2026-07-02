# Quarterly Update Runbook — Federal Marketplace Index
Anyone on the team can publish an update by following these steps exactly.
Total time: about 30 minutes plus script runtime.

1. REFRESH THE ANALYSIS. Run the analysis scripts against the updated base
   table (see scripts/README). Confirm every reconciliation check in the
   script output PASSES. If any check fails: STOP — do not publish; resolve first.
2. UPDATE THE DATA. Copy the fresh output CSVs into `data/`, replacing the old
   ones (same filenames). Update `data/data_as_of.txt` to the new data date.
3. RECORD IT. Add a dated entry to `changelog.md`: what data changed, the new
   coverage window, and any method changes or corrections (there are usually none).
4. REBUILD. From the repository folder run:  python build_site.py
5. REVIEW. Open `docs/index.html` in your browser. Check: the "data as of" date
   in the header, the reading strip numbers, both charts, and the changelog page.
6. PUBLISH. In GitHub Desktop: review the changed files, write a one-line
   summary (e.g., "Q3 2026 data update"), Commit to main, then Push origin.
   The site updates automatically within a few minutes.
7. VERIFY LIVE. Load the site, confirm the new "data as of" date appears.

Corrections follow the same steps, with the changelog entry explaining what was
wrong and what changed. Corrections are never silent.
