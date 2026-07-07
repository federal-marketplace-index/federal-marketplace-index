#!/usr/bin/env python3
"""
build_site.py — generates the entire Federal Marketplace Index website
from the CSVs in /data. Pure Python standard library. No dependencies.

Usage (from the repository root):
    python build_site.py

Output: the /docs folder (served by GitHub Pages). Every run fully
regenerates the site from current data — there is nothing to edit by hand
in /docs. Edit data, methodology text below, or changelog.md instead.
"""

import csv
import json
import html
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — the only block most updates ever touch.
# If counsel's screen changes the name, edit SITE_NAME / DOMAIN / TAGLINE here.
# ---------------------------------------------------------------------------
SITE_NAME = "The Federal Marketplace Index"
SHORT_NAME = "Federal Marketplace Index"
DOMAIN = "federalmarketplaceindex.org"
TAGLINE = "Measured. Reconciled. Public."
STEWARD = "Powered by The American Small Business Chamber of Commerce"
STEWARD_FOOT = ('Powered by <a href="https://www.asbcc.org/" '
                'style="color:#fff;text-decoration:underline">'
                'The American Small Business Chamber of Commerce<sup>\u2122</sup></a>')
NOT_GOV = "An independent, privately produced resource. Not a U.S. government website."
LICENSE_LINE = ("Data and text: CC BY 4.0 &middot; Code: MIT &middot; "
                "Reuse freely with attribution to the Federal Marketplace Index<sup>\u2122</sup>.")

FAVICON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="12" fill="#14243D"/>'
    '<rect x="12" y="36" width="10" height="16" rx="2" fill="#0F6E56"/>'
    '<rect x="27" y="24" width="10" height="28" rx="2" fill="#EF9F27"/>'
    '<rect x="42" y="12" width="10" height="40" rx="2" fill="#D85A30"/>'
    '</svg>')

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

AS_OF = (DATA / "data_as_of.txt").read_text().strip() if (DATA / "data_as_of.txt").exists() else str(date.today())
BUILT = str(date.today())

# Semantic chart palette — identical to the organizations' printed exhibits.
C_TEAL = "#0F6E56"    # statutory mandate
C_AMBER = "#EF9F27"   # regulation only
C_CORAL_L = "#F0997B" # orders at/below SAT
C_CORAL = "#D85A30"   # orders above SAT (the carve-out channel)
C_GRAY = "#888780"    # below micro-purchase
CAT_COLORS = {"all": "#5B6470", "small": C_TEAL, "wosb": "#2E75B6", "edwosb": C_CORAL}
CAT_LABELS = {"all": "All federal dollars", "small": "Small business",
              "wosb": "Women-owned (WOSB)", "edwosb": "EDWOSB"}

# ---------------------------------------------------------------------------
# Data loading (defensive: reads only needed columns by name)
# ---------------------------------------------------------------------------
def read_csv(name):
    path = DATA / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

exposure = read_csv("exposure_layers.csv")
migration = read_csv("order_channel_share_by_fy.csv")

def exposure_value(layer, cat):
    for r in exposure:
        if r["layer"] == layer:
            return float(r[cat + "_pct"])
    return None

def latest_order_share(cat):
    rows = [r for r in migration if r["category"] == cat and r.get("order_share_pct")]
    rows.sort(key=lambda r: int(r["fiscal_year"]))
    return (rows[-1]["fiscal_year"], float(rows[-1]["order_share_pct"])) if rows else (None, None)

# Headline readings for the masthead strip
sb_floor = exposure_value("L2", "small")
wosb_floor = exposure_value("L2", "wosb")
fy_latest, sb_order_latest = latest_order_share("small")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
CSS = """
:root{
  --ink:#14243D; --rule:#2E75B6; --paper:#FAFBFC; --text:#22272E;
  --muted:#5B6470; --teal:#0F6E56; --coral:#D85A30; --line:#D7DEE8;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion: reduce){html{scroll-behavior:auto}}
body{font-family:'IBM Plex Sans',system-ui,sans-serif;background:var(--paper);
  color:var(--text);font-size:17px;line-height:1.65}
.mono{font-family:'IBM Plex Mono',ui-monospace,monospace}
a{color:var(--rule)}
a:focus-visible,button:focus-visible{outline:3px solid var(--rule);outline-offset:2px}
header.site{background:var(--ink);color:#fff;padding:0}
.wrap{max-width:1040px;margin:0 auto;padding:0 22px}
.brandbar{display:flex;align-items:baseline;justify-content:space-between;
  flex-wrap:wrap;gap:8px;padding:22px 0 14px}
.brand{font-size:1.35rem;font-weight:600;letter-spacing:.01em;color:#fff;text-decoration:none}
.brand .idx{color:#9FC3E8;font-weight:400}
.asof{font-family:'IBM Plex Mono',monospace;font-size:.8rem;color:#9FC3E8}
nav.site{display:flex;gap:22px;flex-wrap:wrap;padding-bottom:16px}
nav.site a{color:#D7E4F5;text-decoration:none;font-size:.92rem}
nav.site a:hover,nav.site a[aria-current]{color:#fff;border-bottom:2px solid var(--rule)}
/* Signature: the reading strip */
.strip{border-top:1px solid rgba(255,255,255,.18);background:#0E1B30}
.strip .wrap{display:flex;flex-wrap:wrap;gap:0;padding:0 22px}
.reading{padding:14px 26px 14px 0;margin-right:26px;border-right:1px solid rgba(255,255,255,.14)}
.reading:last-child{border-right:none}
.reading .val{font-family:'IBM Plex Mono',monospace;font-size:1.5rem;color:#fff;font-weight:500}
.reading .lbl{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#8FA6C4;margin-top:2px}
main{padding:44px 0 20px}
h1{font-size:1.9rem;font-weight:600;color:var(--ink);line-height:1.25;margin-bottom:14px;
  max-width:760px}
h2{font-size:1.25rem;font-weight:600;color:var(--ink);margin:38px 0 10px;
  padding-bottom:6px;border-bottom:2px solid var(--rule)}
p{margin:0 0 14px;max-width:760px}
p.lede{font-size:1.12rem;color:var(--muted);max-width:760px}
.figure{border:1px solid var(--line);background:#fff;padding:18px 18px 8px;margin:22px 0 8px}
.figure h3{font-size:1.02rem;font-weight:600;color:var(--ink);margin-bottom:2px}
.figure .sub{font-size:.85rem;color:var(--muted);margin-bottom:8px}
.figure .src{font-family:'IBM Plex Mono',monospace;font-size:.74rem;color:var(--muted);
  padding:8px 0 10px;border-top:1px solid var(--line);margin-top:6px}
.figure .src a{color:var(--muted)}
table.dl{border-collapse:collapse;width:100%;margin:14px 0;font-size:.95rem}
table.dl th{background:var(--ink);color:#fff;text-align:left;padding:9px 12px;font-weight:600}
table.dl td{border:1px solid var(--line);padding:9px 12px;background:#fff}
table.dl td.mono{font-size:.85rem}
.note{border-left:4px solid var(--rule);background:#EDF2F9;padding:12px 16px;margin:16px 0;
  max-width:760px;font-size:.95rem}
pre.log{font-family:'IBM Plex Mono',monospace;font-size:.85rem;background:#fff;
  border:1px solid var(--line);padding:16px;white-space:pre-wrap;max-width:860px}
footer.site{margin-top:52px;background:var(--ink);color:#B9C6D8;font-size:.85rem}
footer.site .wrap{padding:26px 22px;display:grid;gap:6px}
footer.site .steward{color:#fff;font-weight:600}
@media(max-width:640px){
  .reading{border-right:none;padding:8px 0;margin-right:0;width:100%}
  .strip .wrap{flex-direction:column;padding-bottom:8px}
}
"""

def layout(title, active, content, extra_head=""):
    nav_items = [("index.html", "Index"), ("methodology.html", "Methodology"),
                 ("downloads.html", "Downloads"), ("changelog.html", "Changelog"),
                 ("about.html", "About")]
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{lbl}</a>'
        for h, lbl in nav_items)
    strip = ""
    if active == "index.html":
        readings = []
        if sb_floor is not None:
            readings.append((f"{sb_floor:.2f}%", "of small-business dollars under the mandatory floor"))
        if wosb_floor is not None:
            readings.append((f"{wosb_floor:.2f}%", "of women-owned dollars under the mandatory floor"))
        if sb_order_latest is not None:
            readings.append((f"{sb_order_latest:.1f}%", f"SB dollars in the order channel, FY{fy_latest}"))
        cells = "".join(
            f'<div class="reading"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
            for v, l in readings)
        strip = f'<div class="strip"><div class="wrap">{cells}</div></div>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {SHORT_NAME}</title>
<meta name="description" content="{SHORT_NAME}: independent, reproducible measures of the federal small-business marketplace. {TAGLINE}">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SHORT_NAME}">
<meta property="og:title" content="{html.escape(title)} \u2014 {SHORT_NAME}">
<meta property="og:description" content="Independent, reproducible measures of the federal small-business marketplace. {TAGLINE}">
<meta property="og:url" content="https://{DOMAIN}/">
<meta property="og:image" content="https://{DOMAIN}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<header class="site">
  <div class="wrap">
    <div class="brandbar">
      <a class="brand" href="index.html">{SHORT_NAME}<span class="idx"> &middot; {TAGLINE}</span></a>
      <span class="asof">data as of {AS_OF} &middot; built {BUILT}</span>
    </div>
    <nav class="site" aria-label="Site">{nav}</nav>
  </div>
  {strip}
</header>
<main><div class="wrap">
{content}
</div></main>
<footer class="site"><div class="wrap">
  <div class="steward">{STEWARD_FOOT}</div>
  <div>{NOT_GOV}</div>
  <div>{LICENSE_LINE}</div>
  <div>Every figure on this site is reproducible from public federal data. Methods: <a href="methodology.html" style="color:#D7E4F5">methodology</a>. History of every change: <a href="changelog.html" style="color:#D7E4F5">changelog</a>.</div>
</div></footer>
</body></html>"""

# ---------------------------------------------------------------------------
# Charts (Plotly via CDN, data baked in at build time)
# ---------------------------------------------------------------------------
PLOTLY = '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>'

def chart_exposure():
    cats = ["all", "small", "wosb", "edwosb"]
    layers = [("L1", "Below MPT — no Rule of Two", C_GRAY),
              ("L2", "MPT–SAT standalone — statutory mandate", C_TEAL),
              ("L3", "Above SAT standalone — regulation only", C_AMBER),
              ("L4", "Orders ≤ SAT", C_CORAL_L),
              ("L5", "Orders > SAT — the carve-out channel", C_CORAL)]
    traces = []
    for lid, lbl, color in layers:
        traces.append({
            "type": "bar", "orientation": "h", "name": lbl,
            "y": [CAT_LABELS[c] for c in cats],
            "x": [exposure_value(lid, c) for c in cats],
            "marker": {"color": color},
            "hovertemplate": lbl + ": %{x:.2f}%<extra></extra>",
        })
    fig = {"data": traces, "layout": {
        "barmode": "stack", "height": 300,
        "margin": {"l": 150, "r": 10, "t": 6, "b": 34},
        "xaxis": {"range": [0, 100], "ticksuffix": "%", "gridcolor": "#E5EAF1"},
        "yaxis": {"autorange": "reversed"},
        "legend": {"orientation": "h", "y": -0.18, "font": {"size": 11}, "traceorder": "normal"},
        "font": {"family": "IBM Plex Sans, sans-serif", "size": 13, "color": "#22272E"},
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
    }}
    return fig

def chart_migration():
    cats = ["all", "small", "wosb", "edwosb"]
    traces = []
    for c in cats:
        rows = sorted([r for r in migration if r["category"] == c and r.get("order_share_pct")],
                      key=lambda r: int(r["fiscal_year"]))
        xs = [int(r["fiscal_year"]) for r in rows]
        ys = [float(r["order_share_pct"]) for r in rows]
        traces.append({
            "type": "scatter", "mode": "lines+markers", "name": CAT_LABELS[c],
            "x": xs, "y": ys, "line": {"color": CAT_COLORS[c], "width": 2.5},
            "hovertemplate": CAT_LABELS[c] + " FY%{x}: %{y:.1f}%<extra></extra>",
        })
    fig = {"data": traces, "layout": {
        "height": 340, "margin": {"l": 50, "r": 10, "t": 6, "b": 60},
        "yaxis": {"ticksuffix": "%", "gridcolor": "#E5EAF1", "title": {"text": "order-channel share of dollars", "font": {"size": 12}}},
        "xaxis": {"tickmode": "linear", "dtick": 1, "range": [2021.6, 2026.4]},
        "legend": {"orientation": "h", "y": -0.22, "font": {"size": 11}},
        "font": {"family": "IBM Plex Sans, sans-serif", "size": 13, "color": "#22272E"},
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "annotations": [{"x": 0.98, "xref": "paper", "y": 1.04, "yref": "paper", "showarrow": False,
                         "text": "FY2026 partial", "font": {"size": 10, "color": "#5B6470"}}],
    }}
    return fig

def figure(div_id, fig, title, sub, src_csv):
    return f"""<div class="figure">
<h3>{html.escape(title)}</h3>
<div class="sub">{html.escape(sub)}</div>
<div id="{div_id}" role="img" aria-label="{html.escape(title)}"></div>
<div class="src">source: <a href="data/{src_csv}">{src_csv}</a> &middot; FY2022–FY2026 &middot; reconciled to SBA goaling figures &middot; <a href="methodology.html">methodology</a></div>
<script>Plotly.newPlot("{div_id}", {json.dumps(fig["data"])}, {json.dumps(fig["layout"])}, {{displayModeBar:false, responsive:true}});</script>
</div>"""

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_index():
    content = f"""
<h1>Independent, reproducible measures of the federal small-business marketplace.</h1>
<p class="lede">The {SHORT_NAME}<sup>\u2122</sup> tracks where federal contract dollars actually flow, how much of the
marketplace mandatory small-business protections actually reach, and which way both are trending —
from roughly 30 million public contract records, reconciled against the government's own published totals.
Every number can be rebuilt by anyone, from public data, with the code on this site.</p>

<h2>Where the mandatory Rule of Two applies</h2>
<p>Share of five-year contract dollars (FY2022–FY2026) in each protection layer. The teal band —
standalone awards between the micro-purchase threshold and the simplified acquisition threshold —
is the only layer where small-business set-asides are mandated by statute.</p>
{figure("fig-exposure", chart_exposure(), "Contract dollars by Rule of Two protection layer",
        "Percent of each category's FY2022–FY2026 dollars", "exposure_layers.csv")}

<h2>The migration into the order channel</h2>
<p>Share of each category's dollars flowing through task and delivery orders, by fiscal year.
Small-business dependence on the order channel has risen every year of the window while the
overall market's share has held roughly stable — the migration is concentrated on the protected categories.</p>
{figure("fig-migration", chart_migration(), "Order-channel share of dollars by fiscal year",
        "FY2026 is a partial year", "order_channel_share_by_fy.csv")}

<div class="note"><strong>Version 0.</strong> This is the Index's first public release, published to
accompany formal comments filed in the FAR Overhaul rulemakings (FAR Cases 2026-001, -002, -005, -007).
Additional measures — new entrants, vendor concentration, and district-level views — join on the
quarterly schedule. See the <a href="changelog.html">changelog</a> for exactly what changed and when.</div>
"""
    return layout("Independent measures of the federal marketplace", "index.html", content, PLOTLY)

def page_methodology():
    content = f"""
<h1>Methodology</h1>
<p class="lede">Every figure the Index publishes is built from public federal data through documented, reproducible steps. This page states the sources, the definitions, and the checks &mdash; including the ones that could have gone against us. The full methodology paper travels with the data and code in the archived release.</p>

<div class="note">This edition (v0.2) is permanently archived, with a citable DOI, at <a href="https://doi.org/10.5281/zenodo.21247216">https://doi.org/10.5281/zenodo.21247216</a>. Formal citations should reference that archived release, not the working source, which lives in the <a href="https://github.com/federal-marketplace-index/federal-marketplace-index">public GitHub repository</a>.</div>

<h2>Sources</h2>
<p>All sources are public. No proprietary, licensed, or paywalled data enters any published measure.</p>
<table class="dl">
<tr><th>Source</th><th>Contents and role</th><th>Vintage / retrieval</th></tr>
<tr><td>USAspending.gov contract archives (FPDS-sourced)</td><td>Prime contract transaction records &mdash; the base table of ~30.1 million contract actions across 25.0 million distinct awards, FY2022&ndash;FY2026. Foundation of the exposure and migration measures.</td><td>Full-year FY2022&ndash;FY2025; FY2026 partial through the June 2026 archive. Retrieved June 27&ndash;28, 2026.</td></tr>
<tr><td>SAM.gov Public Monthly Entity Extract</td><td>All active federal registrants (758,617 entities, July 2026 baseline) with socioeconomic self-representations &mdash; the registered-availability universe.</td><td>July 1, 2026 extract, via the SAM Entity Extracts API.</td></tr>
<tr><td>U.S. Census Bureau, Annual Business Survey (ABS)</td><td>Employer-firm counts by industry and owner demographics &mdash; the economy-wide availability universe used by the forthcoming disparity measures.</td><td>2021 survey; reference years 2022&ndash;2023 (NAICS 2022 vintage), via the Census API, June 30, 2026.</td></tr>
<tr><td>SBA published reports (Goaling Report; Procurement Scorecard)</td><td>The government's official small-business achievement figures and eligible-dollar bases &mdash; calibration references for the Index's denominators and category totals.</td><td>Most recent published editions at time of release.</td></tr>
<tr><td>87 FR 15468, as updated by the November 17, 2022 NAICS-2022 notice</td><td>The Federal Register instruments identifying the WOSB program's designated industries (NAICS), from which the Index's reference list is regenerated. The 2022 notice recodes the list to the NAICS-2022 vintage.</td><td>Published March 18, 2022; NAICS-2022 update November 17, 2022.</td></tr>
</table>

<h2>Definitions</h2>
<p>Published table: <span class="mono">exposure_layers.csv</span>. Every contract dollar, FY2022&ndash;FY2026, is classified into one of five mutually exclusive layers defined by the legal footing of the small-business Rule of Two.</p>
<table class="dl">
<tr><th>Layer</th><th>Definition</th><th>Legal footing</th></tr>
<tr><td>L1</td><td>Standalone awards at or below the micro-purchase threshold</td><td>No Rule of Two applies</td></tr>
<tr><td>L2</td><td>Standalone awards above the micro-purchase threshold and at or below the simplified acquisition threshold</td><td>Statutory mandate &mdash; 15 U.S.C. &sect; 644(j)(1)</td></tr>
<tr><td>L3</td><td>Standalone awards above the simplified acquisition threshold</td><td>Regulation only &mdash; FAR 19.502-2(b)</td></tr>
<tr><td>L4</td><td>Task, delivery, and BPA-call orders at or below the simplified acquisition threshold</td><td>Order-level</td></tr>
<tr><td>L5</td><td>Task, delivery, and BPA-call orders above the simplified acquisition threshold</td><td>Order-level &mdash; the carve-out channel</td></tr>
</table>
<p>Banding is performed at the award level: obligations are aggregated per distinct award, and the award's total value determines its band, so a large award cannot be misclassified by its incremental funding actions. Thresholds are era-appropriate &mdash; $10,000 / $250,000 for FY2022&ndash;FY2025 and $15,000 / $350,000 for FY2026 (effective October 1, 2025, 90 FR 41872). An action belongs to the order channel (L4/L5) when its award type is a delivery order, task order, or BPA call; purchase orders and definitive contracts are standalone.</p>
<p>Each socioeconomic flag is a boolean derived from named FPDS representation columns, per the standardized definitions in the DoD Procurement Toolbox and GSA eLibrary &mdash; auditable rules, not summary fields taken on faith. Flags are non-exclusive by design: a dollar may count toward several categories at once, exactly as SBA reports categories, and overlaps are reported separately rather than silently double-counted.</p>
<table class="dl">
<tr><th>Pipeline flag</th><th>FPDS source column</th><th>Definition</th></tr>
<tr><td class="mono">is_small</td><td class="mono">contracting_officers_determination_of_business_size</td><td>Meets the NAICS size standard for its industry</td></tr>
<tr><td class="mono">is_wosb</td><td class="mono">women_owned_small_business</td><td>Majority owned and controlled by women</td></tr>
<tr><td class="mono">is_edwosb</td><td class="mono">economically_disadvantaged_women_owned_small_business</td><td>Economically disadvantaged subset of WOSB</td></tr>
<tr><td class="mono">is_woman_owned</td><td class="mono">woman_owned_business</td><td>Woman-owned, not necessarily small</td></tr>
<tr><td class="mono">is_sdb</td><td class="mono">self_certified_small_disadvantaged_business</td><td>Self-certified small disadvantaged business</td></tr>
<tr><td class="mono">is_8a</td><td class="mono">c8a_program_participant</td><td>SBA 8(a) program participant</td></tr>
<tr><td class="mono">is_vosb</td><td class="mono">veteran_owned_business</td><td>Veteran-owned</td></tr>
<tr><td class="mono">is_sdvosb</td><td class="mono">service_disabled_veteran_owned_business</td><td>Service-disabled veteran-owned</td></tr>
<tr><td class="mono">is_hubzone</td><td class="mono">historically_underutilized_business_zone_hubzone_firm</td><td>HUBZone-located firm meeting residency rules</td></tr>
</table>
<p>The full flag set (including completeness-only flags such as the WOSB joint-venture representation) appears in Appendix A of the archived methodology paper.</p>

<h2>Reconciliation</h2>
<p>Wherever an official published total exists, the pipeline is validated against it before any derived figure is published. Government-wide, the pipeline's FY2024 obligation total computes to $755.49 billion against GAO's published figure of approximately $755 billion &mdash; agreement to a fraction of one percent, establishing that the pull captures the complete government-wide universe.</p>
<p>SBA's published achievement figures sit atop a documented stack of adjustments, which the Index reproduces transparently and labels exactly where reproduction stops: the total prime universe (the transparent headline denominator &mdash; every published share states its denominator); the goaling-eligible base after SBA's statutory and policy exclusions; the FPDS-base category figures (the reconciliation target); and the SBA-enhanced scorecard layer, which applies a de-obligation screen and a statutory double-credit multiplier. The Index's headline figures report actual, un-multiplied dollars; a parallel SBA-replica computation exists solely to prove fidelity against the published figures.</p>
<p>Every category carries two named measures &mdash; a strict Index definition and an SBA-match definition &mdash; validated against SBA published goaling figures (awarding-agency lens, excluding de-obligations) for every year FY2022&ndash;FY2025:</p>
<table class="dl">
<tr><th>Category (SBA-match vs published)</th><th>FY2022</th><th>FY2023</th><th>FY2024</th><th>FY2025</th></tr>
<tr><td>Small business</td><td class="mono">-1.50%</td><td class="mono">-0.53%</td><td class="mono">-0.41%</td><td class="mono">-0.57%</td></tr>
<tr><td>WOSB</td><td class="mono">-1.80%</td><td class="mono">-1.82%</td><td class="mono">-1.87%</td><td class="mono">-2.37%</td></tr>
<tr><td>8(a) [order-inheritance lens]</td><td class="mono">-2.71%</td><td class="mono">-0.49%</td><td class="mono">+0.67%</td><td class="mono">+1.46%</td></tr>
<tr><td>VOSB</td><td class="mono">+0.32%</td><td class="mono">+1.93%</td><td class="mono">+0.37%</td><td class="mono">+0.81%</td></tr>
<tr><td>SDVOSB</td><td class="mono">-1.63%</td><td class="mono">-0.97%</td><td class="mono">-1.66%</td><td class="mono">-1.47%</td></tr>
<tr><td>SDB [union lens, documented]</td><td class="mono">+1.58%</td><td class="mono">+4.94%</td><td class="mono">+3.81%</td><td class="mono">+4.59%</td></tr>
<tr><td>HUBZone [source-data limit, documented]</td><td class="mono">-13.91%</td><td class="mono">-13.05%</td><td class="mono">-13.66%</td><td class="mono">-15.48%</td></tr>
</table>
<p class="note">&Delta; = (Index SBA-match &minus; SBA published) &divide; SBA published; SBA figures from the awarding-agency, excluding-de-obligations lens.</p>
<p>Four of the seven categories &mdash; small business, WOSB, VOSB, and SDVOSB &mdash; reconcile within &plusmn;2.4 percent every year, and 8(a) within &plusmn;2.8 percent, so five of the seven sit within &plusmn;2.8 percent every year. Two categories are documented exceptions rather than close reconciliations. HUBZone reconciles 13&ndash;15 percent below the SBA figure for a confirmed source-data reason &mdash; the public USAspending schema carries no HUBZone joint-venture column &mdash; a documented limitation of the public data, not a modeling error. SDB reconciles a few points above the SBA figure under a documented union-lens definition. Stated plainly: for the five reconciling categories the Index reproduces SBA's published figures to within roughly 3 percent every year, and it labels the two exceptions rather than smoothing them; it does not claim to reproduce SBA's exact internal eligible base, which depends on intermediate calculations SBA does not publish. The residual base gap (about $35 billion, roughly 5 percent) is catalogued as the boundary of public-data reproducibility rather than chased.</p>
<p>Every derived series must also reconcile against the base analysis it extends. The order-channel migration series, for example, reproduces the base table's five-year category totals to within 0.006 percent and matches the protection-layer analysis's pooled order-channel shares exactly (56.70 / 67.83 / 73.22 / 72.93 percent for all / small / WOSB / EDWOSB). A series that fails reconciliation is not published until the discrepancy is resolved.</p>

<h2>Limitations</h2>
<p>FY2026 is a partial fiscal year in this edition; all FY2026 figures are labeled partial, and trend claims rest on complete years. Dollars are net signed obligations (de-obligations included as negatives), not outlays, so obligation timing differs from spending timing. The Census availability universe covers employer firms only &mdash; the appropriate frame for contracting availability, since nonemployer firms rarely hold federal prime contracts, but a scope choice worth understanding.</p>
<p>SAM socioeconomic representations are self-representations except where a program requires certification; the Index distinguishes represented from certified status where a measure depends on it. Derived category flags follow the goaling-consistent treatment; alternative flag definitions can produce different category totals, which is precisely why the Index's flags are reconciled to published goaling figures. The government has retired FPDS.gov into SAM.gov and has proposed restructuring registration and representation data; any effect on field availability or series continuity will be disclosed in the changelog with the affected measures.</p>

<h2>Reproduction, licensing &amp; archiving</h2>
<p>The <a href="https://github.com/federal-marketplace-index/federal-marketplace-index">public repository</a> contains the published tables, the analysis scripts that produce them, the site generator, and the methodology paper. Analysis scripts print their reconciliation checks; a published figure implies its checks passed. Rebuilding any figure requires only public data and the released code.</p>
<p>Data and text are licensed CC BY 4.0 (attribute to the Federal Marketplace Index&trade;); code is MIT. Each release is archived as an immutable, DOI-referenced snapshot on Zenodo; formal citations should reference the archived release rather than the working repository.</p>
<div class="note">Archived release &mdash; cite this edition as: Federal Marketplace Index&trade; v0.2 (2026), Zenodo, <a href="https://doi.org/10.5281/zenodo.21247216">https://doi.org/10.5281/zenodo.21247216</a> (DOI 10.5281/zenodo.21247216). The concept DOI 10.5281/zenodo.21247215 always resolves to the latest version.</div>
<p>Corrections policy: errors are corrected promptly, disclosed in the <a href="changelog.html">changelog</a>, and never silently. Substantive method changes are versioned; prior archived releases remain available unchanged.</p>

<h2>Interest disclosure</h2>
<p>The Federal Marketplace Index&trade; is produced by <a href="https://www.asbcc.org/">The American Small Business Chamber of Commerce&trade;</a>, a member-funded organization (dues, events, and capped sponsorships) whose members range from small businesses &mdash; the large majority &mdash; to nonprofits, prime contractors, and government representatives. Sponsorships are held to modest thresholds so no single funder gains undue influence, and the Chamber takes no money from political activist organizations. The Index's independence rests on reproducibility: anyone can rebuild every figure from public data with the published code.</p>
<p>The Index reports measures across all acquisition methods and all socioeconomic categories and takes no position favoring any program, category, channel, or firm &mdash; it publishes what the data shows, whatever it shows.</p>
"""
    return layout("Methodology", "methodology.html", content)

def page_downloads():
    rows = ""
    for f in sorted(DATA.glob("*.csv")):
        rows += (f'<tr><td class="mono">{f.name}</td>'
                 f'<td>{CSV_DESCRIPTIONS.get(f.name, "")}</td>'
                 f'<td><a href="data/{f.name}">CSV</a></td></tr>')
    content = f"""
<h1>Downloads</h1>
<p class="lede">Every table behind every chart, in open formats, with no login — ever.
Column definitions are in the <a href="data/DATA_DICTIONARY.md">data dictionary</a>.
Cite as: {SHORT_NAME}, [table name], data as of {AS_OF}, {DOMAIN}.</p>
<table class="dl">
<tr><th>File</th><th>Contents</th><th>Download</th></tr>
{rows}
</table>
<p>The complete repository &mdash; data, analysis code, and this site's generator &mdash; is available on <a href="https://github.com/federal-marketplace-index/federal-marketplace-index">GitHub</a>, with an archived, DOI-referenced snapshot on Zenodo frozen at each release: <a href="https://doi.org/10.5281/zenodo.21247216">https://doi.org/10.5281/zenodo.21247216</a> (DOI 10.5281/zenodo.21247216).</p>
"""
    return layout("Downloads", "downloads.html", content)

CSV_DESCRIPTIONS = {
    "exposure_layers.csv": "Five-year contract dollars by Rule of Two protection layer and category (percent and $B).",
    "order_channel_share_by_fy.csv": "Order-channel share of dollars and actions by fiscal year and category.",
}

def page_changelog():
    log = (ROOT / "changelog.md").read_text(encoding="utf-8") if (ROOT / "changelog.md").exists() else "No entries yet."
    content = f"""
<h1>Changelog</h1>
<p class="lede">Every data update, method change, and correction — dated, in public, permanently.
This page is the Index's freshness guarantee.</p>
<pre class="log">{html.escape(log)}</pre>
"""
    return layout("Changelog", "changelog.html", content)

def page_about():
    content = f"""
<h1>About the Index</h1>
<p class="lede">{TAGLINE} The {SHORT_NAME}<sup>\u2122</sup> exists because the public record of the federal
marketplace is getting harder to see — and a constructed marketplace is kept honest by measurement.</p>

<h2>What this is</h2>
<p>An independent, continuously maintained set of measures of the federal contracting marketplace,
focused on small-business participation: where the dollars flow, what the protections actually reach,
who is entering and who is leaving, and how concentrated the supplier base is becoming. Updated
quarterly, with every figure reproducible from public data.</p>

<h2>Who produces it</h2>
<p>The Federal Marketplace Index&trade; is produced by <a href="https://www.asbcc.org/">The American Small Business Chamber of Commerce&trade;</a>, a member-funded organization (dues, events, and capped sponsorships) whose members range from small businesses &mdash; the large majority &mdash; to nonprofits, prime contractors, and government representatives. Sponsorships are held to modest thresholds so no single funder gains undue influence, and the Chamber takes no money from political activist organizations. The Index's independence rests on reproducibility: anyone can rebuild every figure from public data with the published code.</p>

<h2>What this is not</h2>
<p>{NOT_GOV} The Index takes no position favoring any program, category, channel, or firm, and it is built to permit unflattering findings &mdash; that openness, and the fact that every figure can be independently rebuilt from public data, is what makes its findings credible regardless of who funds the Chamber.</p>

<h2>Contact</h2>
<p><a href="mailto:charmagne@americansbcc.org">charmagne@americansbcc.org</a> &middot; Corrections and data questions welcome — see the corrections policy in the
<a href="methodology.html">methodology</a>.</p>
"""
    return layout("About", "about.html", content)

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def main():
    DOCS.mkdir(exist_ok=True)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page_index(), encoding="utf-8")
    (DOCS / "methodology.html").write_text(page_methodology(), encoding="utf-8")
    (DOCS / "downloads.html").write_text(page_downloads(), encoding="utf-8")
    (DOCS / "changelog.html").write_text(page_changelog(), encoding="utf-8")
    (DOCS / "about.html").write_text(page_about(), encoding="utf-8")
    (DOCS / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    (DOCS / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")
    assets = ROOT / "assets"
    if assets.exists():
        for f in assets.glob("*"):
            (DOCS / f.name).write_bytes(f.read_bytes())
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    for f in DATA.glob("*.csv"):
        (DOCS / "data" / f.name).write_bytes(f.read_bytes())
    if (DATA / "DATA_DICTIONARY.md").exists():
        (DOCS / "data" / "DATA_DICTIONARY.md").write_bytes((DATA / "DATA_DICTIONARY.md").read_bytes())
    print(f"Site built into /docs — {SHORT_NAME}, data as of {AS_OF}.")
    print("Pages: index, methodology, downloads, changelog, about")
    print("Review locally by opening docs/index.html in a browser, then publish with GitHub Desktop.")

if __name__ == "__main__":
    main()
