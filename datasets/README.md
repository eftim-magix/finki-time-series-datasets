# Datasets

Every dataset of the [forecasting challenge](../README.md) lives in its own folder with the
same layout, so that new datasets can be added the same way.

## Catalogue

| Dataset | What | Resolution, period | Processed rows | Problems | Raw in git? |
|---|---|---|---|---|---|
| [solarmagix](solarmagix/README.md) | PV inverters and plants with weather (SolarMagix, *Data in Brief* 2026) | Released as S1 / S2 / H from 30 Nov 2026 | 13,193 station-level and 88,285 inverter-level rows in the article | A, B, anomalies | Release pending |
| [mepso](mepso/README.md) | MEPSO balancing: imbalance price (WAPpos, WAPneg, VAA±), activated aFRR / mFRR, ACE, preliminary and final | Hourly, 2020-01 → 2026-10 | 59,904 | D; imbalance cost of A, B | Yes (17 MB of workbooks) |
| [energy-prices](energy-prices/README.md) | Day-ahead prices HUPX, MEMO, SEEPEX and 8 neighbours (Ember, from ENTSO-E) | Hourly, 2015-01 → 2026-11 | 104,351 | C; `P` of the imbalance cost; D inputs | No (re-download, ~400 MB) |
| [energy-volumes](energy-volumes/README.md) | Hourly load per country, monthly generation, flows, capacity (ENTSO-E Power Statistics) | Hourly 2023-01 → 2026-06; monthly; yearly | 30,648 hourly + 3 monthly / yearly tables | C inputs, E | No (re-download, ~150 MB) |

## Layout of a dataset folder

```
<dataset>/
├── README.md     what it is, source, rows, columns, potential targets, how to rebuild
├── scripts/      fetch_*.py (download → raw/), build_*.py or process_*.py (raw/ → processed/),
│                 evaluate_*.py or summarize_*.py (→ summary/), tests, requirements
├── raw/          files exactly as downloaded, never edited by hand
├── processed/    normalised and collated, analysis-ready tables: load these
├── summary/      quality checks, coverage tables, charts
└── docs/         optional: longer documentation (column reference, data quality notes)
```

The scripts find their folders relative to their own location, so they can be run from
anywhere. Run them from the dataset folder for the shortest commands:

```bash
cd datasets/energy-prices
python scripts/fetch_ember_prices.py && python scripts/build_ember_prices.py
```

## Conventions of the processed tables

- **One row per time step.** Hourly tables have a complete grid from the first to the last
  hour; a missing value is a blank cell, never 0 and never interpolated.
- **`timestamp_utc`** is the **start** of the interval, ISO 8601 in UTC with `Z`
  (`2026-01-01T00:00:00Z`). **`local_timestamp`** is the same instant in Europe/Skopje with its
  offset (`2026-01-01T01:00:00+01:00`); use it for calendar features and for t0 = 00:00 local.
- **Column names** are snake_case and end with the unit: `_eur_per_mwh`, `_mw`, `_mwh`, `_gwh`.
  Countries use ISO 3166-1 alpha-2 codes (Kosovo: `XK`).
- **Values are copied, not cleaned.** Known problems (zero days, gaps, revisions) are listed
  in each README; cleaning them is part of the modelling and must be fitted on training data only.
- **Raw data stay reproducible.** Large re-downloadable raw files are not in git (see
  [.gitignore](../.gitignore)); small sources that may disappear from the web (the MEPSO
  workbooks) are kept in git with a download manifest.

## Adding a dataset

1. Create `datasets/<name>/` with the folders above and a `README.md` that states the source and
   licence, rows and period of each processed file, the columns, potential targets (which
   challenge problem, which baselines) and the rebuild commands.
2. Write `scripts/fetch_<name>.py` to download into `raw/` (skip existing files, never
   overwrite silently) and `scripts/build_<name>.py` to write `processed/` with the conventions
   above.
3. Add large raw files to [.gitignore](../.gitignore) and a row to the catalogue above and to the
   [root README](../README.md).

Downloaded files are untrusted input: run scripts that read them with `python -I` and keep
downloads inside `raw/`.
