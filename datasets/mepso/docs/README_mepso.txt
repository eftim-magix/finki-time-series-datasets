MEPSO HOURLY DATASET AND INCREMENTAL IMPORTER

Overview, targets and folder layout: see ../README.md. Data quality and forecasting column recommendations: see README_data_quality.md (this folder). Monthly and per-column counts are refreshed with python3 scripts/summarize_mepso_quality.py.

Folder layout (datasets/mepso):
    raw/<year>/MEPSO_balancing_prices_YYYY-MM_<version>.xlsx   source workbooks, byte-for-byte as published
    raw/download-audit-2026-11-24/                            manifest of the first download (URLs, HTTP status, SHA-256)
    processed/                                                importer output (below)
    summary/                                                  quality tables
    scripts/                                                  fetch_mepso.py, process_mepso.py, summarize_mepso_quality.py, tests

Run from datasets/mepso:
    python3 -m pip install -r scripts/requirements.txt
    python3 scripts/fetch_mepso.py        # optional: download new or missing workbooks into raw/<year>/
    python3 scripts/process_mepso.py      # raw/ -> processed/

The defaults are fixed relative to the script (raw/ as input, processed/ as output), regardless of the shell's working directory. In a fresh clone the parsing cache is absent: run python3 scripts/process_mepso.py --rebuild once. The importer scans the year subfolders of raw/ recursively for .xlsx files. Put new or revised files there using the existing MEPSO_balancing_prices_YYYY-MM_preliminary/final.xlsx naming convention, then rerun the same command. Do not place two conflicting monthly revisions of the same version/month in the folder. The importer stops on unknown hourly tables or conflicting monthly cells instead of silently choosing a file.

Files produced (processed/):
    MEPSO_balancing_prices_hourly.csv — one row per UTC hour
    MEPSO_balancing_prices_hourly.status.json — inventory, exclusions, issues, run counts and schema
    MEPSO_balancing_prices_hourly.overrides.json — cell changes made by dated DST supplements
    .mepso-import.sqlite3 — internal per-file parsing cache (not in git)

Incremental behavior:
SHA-256 content hashes identify new and changed workbooks, including revisions to old months. Only those workbooks are parsed. Unchanged parsed data are reused from SQLite, and deleted inputs are removed from the cache. The CSV is rebuilt atomically from cached and newly parsed data, so adding final data to an old preliminary month is safe. Incremental import does not mean append-only CSV output. A failed parse leaves the previous CSV intact. Successfully parsed files remain cached; failed files are not cached, so a retry can reuse the successful work. Parser version changes automatically invalidate cached parsing results. --rebuild forces all files to be parsed again. Keep the cache alongside the generated CSV; if it is lost, use --rebuild deliberately or choose a new output path.

Optional arguments:
    python3 scripts/process_mepso.py --start 2020-01 --end 2026-11
    python3 scripts/process_mepso.py --input /path/to/archive --output /path/to/output.csv --state /path/to/cache.sqlite3

--start and --end are local calendar months, inclusive. Defaults are the earliest and latest valid source months. Thus the initial dataset spans January 2020 through October 2026, including missing months within that range. It does not invent an open-ended future series. Use --end to extend the grid through an unpublished month.

TIMESTAMPS AND DAYLIGHT SAVING
timestamp_utc is the START of the settlement interval, in ISO 8601 UTC with Z. Source H1/1h means local 00:00–01:00, H24 means 23:00–24:00. Europe/Skopje timezone rules are applied through Python zoneinfo; a fixed offset is not used. local_timestamp includes its UTC offset, local_hour is zero-based, and local_fold distinguishes the repeated autumn hour (0 first, 1 second).

On spring transitions, nonexistent local H3 is omitted, yielding 23 actual hours. An explicitly marked H3B/Н3В/3Bh is the second autumn 02:00–03:00 interval, yielding 25 actual hours. A workbook with only H3 does not supply H3B: the absent second interval stays missing rather than copying or averaging another hour. Spurious extra-hour columns on ordinary days are ignored, and nonzero discarded cells are counted in file issues. The original values are not shifted to adjacent hours. Dated 2020 and 2021 supplements take priority over monthly values for the cells they actually supply. Their overrides are logged.

PRICES, CURRENCIES AND PARAMETERS
All version-dependent columns have preliminary_ or final_ prefixes.

price_wappos_eur_per_mwh, price_wapneg_eur_per_mwh,
price_vaa_plus_eur_per_mwh, price_vaa_minus_eur_per_mwh:
    Main EUR price components, kept exactly as reported in the workbook.
price_*_mkd_per_mwh:
    Separate matching MKD reference components, where the workbook provides them.
exchange_rate_mkd_per_eur:
    Published daily exchange rate, repeated on the corresponding local day's hours.
afrr_up_mwh, afrr_down_mwh, afrr_total_mwh:
    Published activated aFRR series, preserving their signs and reported totals.
mfrr_up_mwh, mfrr_down_mwh, mfrr_total_mwh:
    Published activated mFRR series, preserving their signs and reported totals.
afrr_net_mwh, mfrr_net_mwh:
    Earlier signed secondary/tertiary energy tables, retained separately from later directional tables.
ace_mwh_per_h:
    Published Area Control Error series.

No currency conversion, interpolation, economic formula, or imputation is applied. EUR is the main price currency; MKD is kept only as a separate reference. A missing currency stays blank. Earlier preliminary workbooks sometimes provide prices only. The source publishes four price components rather than one settlement-price series. The importer keeps all four unchanged and, separately, derives the imbalance settlement price from them (see IMBALANCE SETTLEMENT PRICE below); it never sums or averages components or equates an empty component with zero. Legitimate zero values remain zero. Daily totals/sums alongside hourly tables are not repeated into hourly energy columns; they aggregate existing hourly observations rather than introduce extra hourly parameters. Workbook formulas use their published cached values and are not recalculated.

MISSING DATA AND STATUS
status is both, preliminary_only, final_only, missing_price, or missing.
preliminary_status/final_status are available, missing_price, missing_hour, or missing_file.
available means at least one reported price component exists for that version/hour; it does not assert that every parameter exists. quality_flags identifies unavailable versions and missing non-price parameters within that version's published monthly schema. Empty price components are often structurally blank in MEPSO's source, so those individual blanks are preserved without assuming that they are an outage. No-price hours are flagged explicitly. Column availability changes across historical workbook formats; absent early directional/ACE data remain blank.

source_filename is a semicolon-delimited set of relative source paths contributing numeric values to the row. preliminary_source_filename and final_source_filename provide separate version provenance. Monthly and DST supplement filenames can both contribute to one row. Exact supplement cell replacements are in the overrides JSON. Rows with no contributed values have blank source fields. The known incorrectly linked original March 2020 preliminary file (renamed with __source-mart-preliminarna) is excluded and recorded in the status inventory, so it cannot masquerade as genuine March data or supersede June's true file. The misdirected September 2026 final link is already represented only as September 2025 data in the archive.

VALIDATION
    cd scripts && python3 -m unittest test_process_mepso.py

Tests cover winter/summer UTC offsets, spring's missing hour, both autumn folds, mixed-currency DST supplements, incremental reuse, new versions, changed existing sources, deleted sources, deterministic reruns and retained missing-month rows.

Initial archive coverage notes (2026-11-25): the generated grid has 59,904 rows and 48 columns. March–June 2023 contributes 2,927 missing hourly rows (March's spring transition has only 23 hours that day). One additional missing row is the second 02:00 interval on 2022-10-30. October 2026 has 241 hours with missing prices from October 22–31 while other workbook parameters remain available. These limitations are flagged in the CSV rather than filled with zero or interpolated.

Requires Python 3.9+ and openpyxl. tzdata provides timezone rules on systems without an OS timezone database. Scripts perform no network access and never modify source workbooks.

IMBALANCE SETTLEMENT PRICE (DERIVED COLUMNS)
MEPSO settles every balance responsible party (BRP) at one imbalance price per hour (balancing market rules, Articles 83-84). The four published price components are the candidates for that price:

    WAPpos   Weighted average price of the upward (positive) aFRR and mFRR balancing energy activated in the hour.
             Applies when more upward than downward energy was activated: the system was short.
    WAPneg   Weighted average price of the downward (negative) balancing energy activated in the hour.
             Applies when more downward than upward energy was activated: the system was long.
    VAA+/-   Price when no balancing energy was activated in the hour (VAA = price for inactive balancing energy).
             This is the only dual price, and it follows the sign of the BRP's own imbalance:
             VAA+  positive imbalance (surplus, MEPSO pays the BRP): HUPX day-ahead price - 50 %
                   (HUPX - 40 EUR/MWh when HUPX is below 40, never below -50 EUR/MWh);
             VAA-  negative imbalance (deficit, the BRP pays MEPSO): HUPX + 50 %, with a regulated minimum.
             In the data VAA- is 3 x VAA+ in most hours.

Positive and negative describe the direction of the balancing energy, not the sign of the price: every component can itself be positive, zero or negative.

Rule, applied to each release (preliminary, final) separately:
    net = |afrr_up| + |mfrr_up| - |afrr_down| - |mfrr_down|      (activated energy of that release)
    net > 0 -> WAPpos;  net < 0 -> WAPneg;  net = 0 -> VAA (surplus: VAA+, deficit: VAA-)
January 2020 (both releases) and February 2020 (preliminary) have no activation tables; there the single non-zero component decides.

Columns (EUR/MWh):
    preliminary_imbalance_regime, final_imbalance_regime        wappos | wapneg | vaa | blank
    preliminary_/final_imbalance_price_surplus_eur_per_mwh      price for a positive imbalance (more energy than scheduled)
    preliminary_/final_imbalance_price_deficit_eur_per_mwh      price for a negative imbalance (less energy than scheduled)
    imbalance_regime, imbalance_price_surplus_eur_per_mwh,
    imbalance_price_deficit_eur_per_mwh                         final release if available, else preliminary
    imbalance_price_version                                     final | preliminary
Surplus and deficit prices are identical in every WAPpos/WAPneg hour; they differ only in VAA hours.

Quality flags: <release>_imbalance_regime_from_prices (no activation data), <release>_imbalance_regime_ambiguous (no price derived), <release>_imbalance_price_component_missing (the selected component is blank), <release>_imbalance_unselected_component_nonzero (2 final and 6 preliminary hours where another WAP is also non-zero).

Coverage (2020-01 to 2026-10): 56,735 of 59,904 hours (94.71 %), 54,765 from final and 1,970 from preliminary data. Regimes: WAPneg 26,323 hours, WAPpos 24,536, VAA 5,876. No price for March-June 2023, the repeated hour on 2022-10-30 and 22-31 October 2026.

Validation: the settlement workbooks of one 975 kW PV plant for January-October 2026 (not distributed) list a "MEPSO Price" per hour. The derived price reproduces it in 7,007 of the 7,055 hours with a derived price (99.3 %); the other 48 hours differ between revisions. In the 250 VAA hours the workbook uses the deficit price 167 times and the surplus price 83 times: the sign of the whole balancing group (the trader's portfolio) decides, not the plant's own imbalance.

IMBALANCE COST OF A FORECAST
A producer sells its forecast (schedule) F at the day-ahead price P; the difference I = actual - F is settled at the imbalance price C. Compared with a perfect forecast, the cost of the forecast error in one hour is

    cost = -I * (C - P)          C = surplus price if I > 0, deficit price if I < 0;  positive cost = loss

This is column O ("Imbalance Amount") of the plant settlement workbooks. Over January-October 2026 the plant's real day-ahead nominations cost 4.81 EUR per MWh produced (8,746 EUR for 1,818 MWh). The imbalance price minus the day-ahead price averaged about +78 EUR/MWh in short-system hours and -75 EUR/MWh in long-system hours.

APPLIED EUR PRICE COLUMNS (added 2026-11-27)
The importer now adds preliminary_price_applied_eur_per_mwh and final_price_applied_eur_per_mwh, without removing the existing imbalance surplus/deficit columns. Prices retain their published signs and EUR/MWh units. No currency conversion or preliminary-to-final fallback is performed in these scalar columns.

Each release also has applied_price_component, applied_price_status, applied_price_source_filename, and applied_price_reference columns. Their prefixes are preliminary_ or final_. A blank scalar is explained by its selection status and an appended quality flag. The existing general status still describes raw component availability, not successful scalar selection.

Selection order:
1. If a timestamp has an explicit settlement reference, match its converted EUR value against this release's published components. Copy the matching published price, never the reference number. A mismatch stays blank and is flagged reference_mismatch; it is not replaced with another release's value.
2. Otherwise use a reported Cimb, a single reported EUR component (including zero), or a numeric value shared by all reported components. These source-driven selections are identified by status and are not independently validated against a plant settlement.
3. For multiple unequal components, use complete signed aFRR/mFRR directional activation data, or both legacy net series, to select WAPpos for net positive energy or WAPneg for net negative energy. Do not use potentially inconsistent total fields or treat a missing activation series as zero. Conflicting nonzero directional prices stay blank.
4. At zero net activation, use VAA only if the available fallback values are numerically identical. Different VAA-plus and VAA-minus values require an external applied-price reference or information about the relevant BRP/portfolio; they stay ambiguous_fallback otherwise. Never infer that choice from the plant's own imbalance or ACE.

Reference file: raw/applied_price_references.csv, loaded from the input folder automatically. The included 744 January 2026 observations come from the Settlement workbook of one PV plant, using J * 1000 / B10. The cell, exchange rate and workbook checksum are retained; the workbook filename is replaced by a neutral label (plant_settlement_2026-01.xlsx) because the original names the plant. Reference-based scalar values reproduce all 744 January observations in both releases; this does not establish a universal scalar selection for every portfolio or month. They are retrospective label evidence, not future-known model inputs.

To build a new explicit reference CSV (the command replaces the chosen output; it does not append):
    python3 scripts/build_applied_price_references.py --workbook /path/to/Settlement.xlsx --output /path/to/references.csv
Then use --applied-price-references /path/to/references.csv, or maintain the default applied_price_references.csv. An explicit missing reference path is an error; an absent default file is allowed and uses source-only selection.

Applied prices are derived on every CSV rebuild after cached raw workbooks are combined. Changes to reference evidence are therefore effective even when no Excel files changed. Raw parser version/cache stays compatible; applied_price_version is recorded separately in the status JSON. No --rebuild is needed for this upgrade. The quality summary script includes the numeric applied fields but excludes their text metadata.
