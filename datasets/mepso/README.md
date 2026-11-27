# MEPSO balancing data: imbalance price, aFRR, mFRR, ACE (North Macedonia)

Hourly balancing data published by **MEPSO**, the transmission system operator of North
Macedonia: the four imbalance price components, activated aFRR and mFRR balancing energy,
the area control error (ACE) and the MKD/EUR rate, **January 2020 – October 2026**, in a
preliminary and a final release. The dataset combines the price components into the
**imbalance price** that a market party actually pays or receives.

Used by **problem D** of the [challenge](../../challenge/simplified-challenge.md), and for the
**imbalance cost** metric of the PV problems A and B.

## At a glance

| | |
|---|---|
| Source | <https://www.mepso.com.mk/index.php/mk/pbee>, section "Цена на порамнување" (settlement price): one Excel workbook per month and release |
| Raw | 146 workbooks (2020–2026), 17 MB, in git: [`raw/<year>/`](raw/) |
| Processed | [`processed/MEPSO_balancing_prices_hourly.csv`](processed/MEPSO_balancing_prices_hourly.csv): **59,904 rows** (one per UTC hour, 2020-01-01 to 2026-10-31 local time), 68 columns, 41 MB |
| Resolution | Hourly, settlement intervals in local time (Europe/Skopje), stored by UTC start |
| Releases | `preliminary_*` and `final_*` columns side by side; the final list comes out weeks after the preliminary one |
| Imbalance price coverage | 56,735 of 59,904 hours (94.7 %): 54,765 from the final and 1,970 from the preliminary release |
| Gaps | March–June 2023 (not published), the repeated hour of 2022-10-30, prices for 22–31 October 2026 (not yet published) |
| Licence | Public data of MEPSO; cite MEPSO as the source |

## Folder layout

```
mepso/
├── README.md                  this file
├── scripts/
│   ├── fetch_mepso.py         download new or missing workbooks from the MEPSO page into raw/<year>/
│   ├── process_mepso.py       raw/ → processed/ (incremental: only new or changed workbooks are parsed)
│   ├── summarize_mepso_quality.py   processed/ → summary/ (coverage and consistency counts)
│   ├── build_applied_price_references.py   optional: reference prices from a plant settlement workbook
│   ├── test_process_mepso.py  unit tests (python3 -m unittest test_process_mepso.py, run in scripts/)
│   └── requirements.txt
├── raw/
│   ├── 2020/ … 2026/          MEPSO_balancing_prices_<YYYY-MM>_<preliminary|final>[_<day>].xlsx, byte-for-byte
│   ├── download-audit-2026-11-24/   manifest of the first download: every link, HTTP status, SHA-256
│   ├── fetch_log.csv          appended by fetch_mepso.py (created on its first download)
│   └── applied_price_references.csv   hourly price billed to one PV plant, January 2026 (anonymised)
├── processed/
│   ├── MEPSO_balancing_prices_hourly.csv           the dataset
│   ├── MEPSO_balancing_prices_hourly.status.json   inventory of source files, issues, schema
│   └── MEPSO_balancing_prices_hourly.overrides.json   cells replaced by the clock-change supplements
├── summary/                   quality tables (per month, per column), the January 2026 price check
└── docs/
    ├── README_mepso.txt       full column reference, timestamp rules, imbalance price rule
    ├── README_data_quality.md data quality and which columns to forecast (PDF copy alongside)
    └── MEPSO_simple_summary.md   one-page summary (PDF copy alongside)
```

## Rebuild

```bash
cd datasets/mepso
python3 -m pip install -r scripts/requirements.txt
python3 scripts/fetch_mepso.py --dry-run      # which new workbooks are on the MEPSO page?
python3 scripts/fetch_mepso.py                # download them into raw/<year>/
python3 scripts/process_mepso.py --rebuild    # first run in a fresh clone (no parsing cache yet)
python3 scripts/process_mepso.py              # later runs: only new or changed workbooks are parsed
python3 scripts/summarize_mepso_quality.py    # refresh summary/ and docs/README_data_quality.md
```

`fetch_mepso.py` names each file by the month found **inside** the workbook, because some
links on the page point to the wrong month, and tries the other spellings MEPSO has used when
a link returns 404. A workbook that MEPSO revised is kept aside (`*.xlsx.revised-<date>`)
unless `--replace` is given. `process_mepso.py` never fills gaps, converts currencies or
averages components; see [docs/README_mepso.txt](docs/README_mepso.txt).

## Columns you will use

| Column | Meaning |
|---|---|
| `timestamp_utc` | Start of the hour, ISO 8601 UTC (`2026-01-01T00:00:00Z`) |
| `local_timestamp`, `local_date`, `local_hour`, `local_fold` | Same hour in Europe/Skopje; `local_fold` = 1 for the second 02:00 hour in October |
| `imbalance_price_surplus_eur_per_mwh` | Price for a **positive** imbalance (more energy than scheduled), EUR/MWh |
| `imbalance_price_deficit_eur_per_mwh` | Price for a **negative** imbalance (less energy than scheduled), EUR/MWh |
| `imbalance_regime` | Which part applied: `wappos` (system short), `wapneg` (system long), `vaa` (nothing activated) |
| `imbalance_price_version` | `final` if the final release has the hour, else `preliminary` |
| `final_afrr_up_mwh`, `final_afrr_down_mwh`, `final_mfrr_up_mwh`, `final_mfrr_down_mwh` | Activated balancing energy per direction (also `preliminary_*`) |
| `final_ace_mwh_per_h` | Area control error |
| `final_price_wappos_eur_per_mwh`, `…_wapneg_…`, `…_vaa_plus_…`, `…_vaa_minus_…` | The four published price components, unchanged |
| `status`, `quality_flags` | Which releases have the hour; flags for missing parameters and derivation issues |

### The imbalance price has three parts

| Part | What it is | When it applies |
|---|---|---|
| **WAPpos** | Weighted average price of the upward aFRR + mFRR energy activated in the hour | More upward than downward energy activated: the system was **short** |
| **WAPneg** | Weighted average price of the downward energy activated in the hour | More downward energy activated: the system was **long** |
| **VAA+ / VAA−** | Price when no balancing energy was activated. VAA+ ≈ HUPX − 50 % for a surplus, VAA− ≈ HUPX + 50 % for a deficit | Net activated energy = 0 (≈ 10 % of hours) |

WAPneg applies in 26,323 hours, WAPpos in 24,536 and VAA in 5,876. "Positive" and
"negative" are directions, not signs: every part can itself be negative. The derived price
reproduces the "MEPSO Price" billed to a real PV plant in 99.3 % of the hours of
January–October 2026 (the rest differ between releases).

## Potential targets

| Target | Problem | Notes |
|---|---|---|
| `imbalance_price_surplus_eur_per_mwh` / `…_deficit_…` | D | Main target. Two-stage idea: forecast `imbalance_regime`, then the price within the regime; VAA hours follow from a HUPX forecast |
| `imbalance_regime` | D | Classification: will the system be short, long or neither? |
| `final_afrr_up_mwh`, `final_afrr_down_mwh`, `final_mfrr_*` | D | Activated balancing energy; many zero hours (intermittent demand) |
| `final_ace_mwh_per_h` | D | System imbalance signal; noisy, centred near 0 |
| Final minus preliminary | D | How much does the final release revise the preliminary one? |
| Imbalance cost of a PV forecast | A, B | `cost = −(actual − forecast) × (C − P)`, C from this dataset, P from [energy-prices](../energy-prices/README.md) |

Setup in the challenge: daily t0, horizon D+1 … D+2, as if data were available up to t0;
**S3** is each newly published month. Baselines: naive (t−1), seasonal naive (same hour
yesterday / last week), SMA, EMA. MAPE is unusable: prices and energies are often zero or negative.

## Link to PV production: balancing groups

MEPSO settles the imbalance of a **balancing group**, the portfolio of one balance
responsible party (BRP), not of each plant. This connects the balancing data to the PV
problems:

- **Several PV plants in one balancing group.** The group's imbalance in an hour is the sum of
  the plants' imbalances, so errors partly cancel. In WAPpos and WAPneg hours the price is the
  same for a surplus and a deficit, so the group's cost equals the sum of the plants' costs.
  In VAA hours the **sign of the group's total** decides whether VAA+ or VAA− applies: netting
  usually lowers the cost. This is also why a plant's own settlement can show VAA− in an hour
  in which the plant itself had a surplus.
- **A single plant as its own balancing group** (the extreme case). Its own imbalance decides
  the VAA price, and the per-plant imbalance cost of the challenge is exactly what it pays.
- **Normalise per installed capacity.** Inverters and plants differ in size. Forecast energy
  per kWp installed, so that one model serves every inverter or plant, and rebuild the group's
  imbalance as Σ capacityᵢ × (per-kWp actual − per-kWp forecast)ᵢ. Compare groups by cost per
  MWh produced or per MW installed, not by total EUR.
- **PV errors and the system regime.** On sunny days the forecast errors of many PV plants add
  up and can push the whole system long or short. Forecasting the regime (problem D) with
  weather and PV forecasts is a natural extension of problems A and B. Use only information
  available at t0: measured production of other plants after t0 is leakage.

Reference: one 975 kW PV plant that belongs to a trader's balancing group. Its day-ahead
schedules cost **4.81 EUR per MWh produced** over January–October 2026, and in its VAA hours
the price followed the group's sign, not the plant's. The imbalance price minus the day-ahead
price averaged about +78 EUR/MWh in short-system hours and −75 EUR/MWh in long-system hours.

## More detail

- [docs/README_mepso.txt](docs/README_mepso.txt): every column, timestamps and daylight saving,
  the imbalance price rule and flags, the imbalance cost, the applied-price columns.
- [docs/README_data_quality.md](docs/README_data_quality.md): coverage per month and column,
  preliminary vs final, recommended forecasting columns.
- [docs/MEPSO_simple_summary.md](docs/MEPSO_simple_summary.md): one-page summary.
