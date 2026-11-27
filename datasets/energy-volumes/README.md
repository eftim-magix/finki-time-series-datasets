# Load and generation volumes: ENTSO-E Power Statistics

Hourly electricity **load per country** for North Macedonia and its region, plus monthly
generation by fuel, monthly cross-border flows and yearly net generating capacity, from the
ENTSO-E Power Statistics. Evaluated 2026-11-26. **No prices** (those are in
[energy-prices](../energy-prices/README.md)).

Used as **inputs for problem C** (load drives prices) and as a ready dataset for **problem E**
(your own dataset: hourly load forecasting with a leave-one-country-out test) of the
[challenge](../../challenge/simplified-challenge.md).

## At a glance

| | |
|---|---|
| Source | <https://www.entsoe.eu/data/power-stats/> (aggregations of the ENTSO-E Transparency Platform since 2019) |
| Raw | Yearly CSV files per dataset, ~150 MB. **Not in git**: re-download with the script |
| Processed | [`hourly_load_mw.csv`](processed/hourly_load_mw.csv): **30,648 rows** (UTC hours 2023-01-01 → 2026-06-30), 14 columns: `timestamp_utc`, `local_timestamp`, `load_<code>_mw` for MK, HU, RS, BG, GR, RO, AL, ME, BA, HR, SI, XK |
| | [`monthly_domestic_values_gwh.csv`](processed/monthly_domestic_values_gwh.csv): 33,745 rows (country, year, month, category, GWh), 2019 → 2026 H1 |
| | [`monthly_physical_flows_gwh.csv`](processed/monthly_physical_flows_gwh.csv): 10,356 rows (border, direction, month, GWh), 2024 → 2026 H1 |
| | [`net_generation_capacity_mw.csv`](processed/net_generation_capacity_mw.csv): 769 rows (country, year, fuel, MW), 2024–2025 |
| Unit | MW (hourly mean load), GWh (monthly energy), MW (capacity) |
| Licence | ENTSO-E data, free reuse with attribution: credit ENTSO-E |

## Folder layout

```
energy-volumes/
├── README.md
├── scripts/
│   ├── fetch_power_stats.py       download the yearly CSV files into raw/ (existing files are skipped)
│   ├── build_power_stats.py       raw/ → processed/ (one set of column names for all years)
│   └── evaluate_power_stats.py    what each file contains, load quality per country → summary/
├── raw/                           (not in git) <dataset>_<year>.csv
├── processed/                     the four tidy tables above
└── summary/                       hourly_load_quality.csv, net_generation_capacity_mk.csv,
                                   monthly_domestic_values_mk_categories.csv, hourly_load_mk_hu_rs.html/.png
```

## Rebuild

```bash
cd datasets/energy-volumes
python scripts/fetch_power_stats.py         # default selection, ~150 MB
python scripts/fetch_power_stats.py --datasets monthly_hourly_load_values --years 2019 2020 2021 2022   # more years
python scripts/build_power_stats.py         # processed/
python scripts/evaluate_power_stats.py      # summary/ (needs plotly and kaleido for the chart)
```

The processed tables copy the values unchanged. **North Macedonia's load has whole days
missing or reported as 0 from 2024 on**: treat 0 as missing before modelling (see below).

## Potential targets

| Target | Problem | Notes |
|---|---|---|
| `load_HU_mw`, `load_RS_mw`, `load_BG_mw`, `load_GR_mw`, `load_RO_mw`, `load_HR_mw` | E | Clean hourly series; leave one country out as the hold-out H |
| `load_MK_mw` | E | Needs cleaning (9.6 % of hours missing, whole days at 0): a gap-handling exercise |
| Hourly load of the region | C inputs | Covariate for day-ahead prices (use load **forecasts** for the future part, e.g. from the Transparency Platform) |
| Monthly generation by fuel | context | Monthly only: background, normalisation |

Baselines: same hour yesterday or last week (seasonal naive, m = 24 or 168), SMA, EMA.

## Short answer: no prices

The Power Statistics page has **no electricity prices** — not hourly, not daily, for no
exchange (HUPX, SEEPEX, MEMO, …). None of the downloaded files has a price column or a
price-related category. The page publishes six datasets, aggregated **per country**:

| Dataset | Resolution | Years on the page | Useful for the challenge? |
|---|---|---|---|
| **Monthly Hourly Load Values** (MHLV) | **hourly**, MW, per country | 2006–2015, 2015–2019 (xlsx); 2019 … 2026 H1 (csv) | **Yes**: hourly load of MK and neighbours as a target (own-dataset track) or as a covariate for prices |
| Monthly Domestic Values (MDV) | monthly, GWh, per country and fuel; imports/exports | 1991–2015; 2019 … 2026 H1 | Background only (monthly) |
| Physical Energy & Power Flows (PEPF) | monthly per border (+ two snapshot hours per month) | 2015 … 2026 H1 | Background only |
| Net Generating Capacity (NGC) | yearly per country and fuel | 2010 … 2025 | Normalising, context |
| Inventory of generation / transmission | yearly lists | 2019 … 2025 | No |
| Statistical factsheets | PDF | 2013 … 2025 | No |

"2026 data" includes only Q1 and Q2. Since 2019 the statistics are aggregations of
Transparency Platform data.

## Where hourly day-ahead prices are

| Source | What | Access |
|---|---|---|
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) | Day-ahead prices per bidding zone (HU, RS, BG, GR, RO, … and check MK), hourly; 15-min where the market uses it (SDAC since 1 Oct 2025) | Free account; REST API with a security token; Python: [entsoe-py](https://github.com/EnergieID/entsoe-py) |
| [Ember: European wholesale electricity price data](https://ember-energy.org/data/european-wholesale-electricity-price-data) | Hourly, daily and monthly day-ahead prices per European country, from ENTSO-E, cleaned (gaps interpolated; 15-min and 60-min products averaged) | Free download (zip of CSVs); check the country list and the last update date |
| Exchanges: [HUPX](https://hupx.hu/), SEEPEX, MEMO | Official results, volumes | Websites; check terms for redistribution |

Recommendation: prices from the **Transparency Platform** (one source, raw, all zones incl.
volumes and load/RES forecasts), with Ember as a quick, pre-cleaned alternative for the
countries it covers.

## What was downloaded (raw/)

| File(s) | Rows (all years) |
|---|---|
| `monthly_hourly_load_values_2023 … 2026.csv` | 1,100,370 (38 countries) |
| `monthly_domestic_values_2019 … 2026.csv` | 33,745 |
| `physical_energy_power_flows_2024 … 2026.csv` | 21,114 |
| `net_generation_capacity_2024, 2025.csv` | 769 |

**Format traps** (handled in `scripts/evaluate_power_stats.py` and therefore in `build_power_stats.py`):

- The delimiter changes from year to year: tab (most years), `;` (MDV 2021, PEPF 2024),
  `,` (MDV 2023, MHLV 2023–2024).
- Column names change: `Country` → `Area` (MDV from 2024), `FromAreaCode` →
  `FromCountryMapCode` (PEPF from 2025). Some files start with a UTF-8 byte-order mark.
- Dates are `dd-mm-yyyy HH:MM`, in **UTC**.

## Hourly load quality, 2023-01-01 → 2026-06-30 (30,648 hours)

| Country | Missing hours | Zero values | Comment |
|---|---|---|---|
| **MK** | **2,928 (9.6 %)** | 356 | Clean in 2023. From spring 2024 whole days are missing (up to 18 days a month in May–June 2025 and May 2026) and whole days are reported as 0. The series is also much noisier from 2024 on |
| HU | 2 | 0 | Very clean |
| RS | 9 | 8 | Clean; a few single-hour drops to 0 |
| BG | 0 | 0 | Clean |
| GR | 4 | 0 | Clean |
| RO | 5 | 0 | Clean |
| AL | 1,322 | 1 | Long gaps (Jan 2024, Nov–Dec 2025) |
| BA | 231 | 813 | Many zero hours: treat 0 as missing |
| HR, ME | 0 | 0 | Clean |
| SI | 81 | 0 | Short gaps |
| XK | 7 | 0 | Clean |

Gaps in MK are whole days (every hour of the day equally affected), not missing daytime
hours. Chart: [summary/hourly_load_mk_hu_rs.html](summary/hourly_load_mk_hu_rs.html)
(PNG: [summary/hourly_load_mk_hu_rs.png](summary/hourly_load_mk_hu_rs.png)).

**For the challenge:** HU, RS, BG, GR, RO, HR load are good hourly covariates (or targets
for the own-dataset track). MK load needs cleaning (0 → missing, whole-day gaps) and is a
good real-world exercise in gap handling, but should not be used as a clean target for
2024–2026 without checking it against the Transparency Platform.

## Other findings for North Macedonia

- **Monthly generation (MDV)**: lignite, gas, oil, hydro reservoir, wind (and run-of-river up
  to 2022); imports/exports from 2025. **No solar** category is reported.
- **Net generating capacity 2025**: lignite 824 MW, hydro reservoir 644 MW, gas 251 MW,
  oil 165 MW, solar 67 MW, wind 37 MW, biomass 7 MW (as reported to ENTSO-E; reported solar
  looks low compared with installed PV in the country).
- **Physical flows**: monthly per border with BG, GR, RS, XK.
