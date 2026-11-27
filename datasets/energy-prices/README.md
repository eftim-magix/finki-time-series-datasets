# Day-ahead electricity prices: HUPX, MEMO, SEEPEX and neighbours (Ember)

Hourly day-ahead electricity prices for **Hungary (HUPX)**, **North Macedonia (MEMO)**,
**Serbia (SEEPEX)** and eight neighbouring markets, from Ember's cleaned copy of the ENTSO-E
Transparency Platform. Evaluated 2026-11-26.

Used by **problem C** of the [challenge](../../challenge/simplified-challenge.md) (target and
hold-out exchange), as the day-ahead price `P` of the **imbalance cost** (problems A, B) and as
an input of **problem D** (VAA prices are set from HUPX).

## At a glance

| | |
|---|---|
| Source | Ember, European wholesale electricity price data (from ENTSO-E): <https://ember-energy.org/data/european-wholesale-electricity-price-data/> |
| Raw | Hourly ZIP (one CSV per country, 35 files, ~380 MB unzipped), daily and monthly CSV. **Not in git**: re-download with the script |
| Processed | [`processed/day_ahead_prices_hourly.csv`](processed/day_ahead_prices_hourly.csv): **104,351 rows** (one per UTC hour, 2015-01-01 → 2026-11-26), 13 columns, 10 MB |
| Columns | `timestamp_utc`, `local_timestamp` (Europe/Skopje), `price_<code>_eur_per_mwh` for HU, MK, RS, BG, GR, RO, HR, SI, ME, AL, XK |
| Hours with a price | HU 104,327 · MK 31,008 (from 2023-05-10) · RS 87,551 · BG 89,015 · GR 104,303 · RO 104,327 · HR 79,825 · SI 104,351 · ME 31,441 · AL 20,327 · XK 10,872 |
| Unit | EUR/MWh, day-ahead (15-min products after 1 Oct 2025 already averaged to the hour by Ember) |
| Licence | Ember publishes the data under CC BY 4.0: credit Ember and the ENTSO-E Transparency Platform |

## Folder layout

```
energy-prices/
├── README.md
├── scripts/
│   ├── fetch_ember_prices.py      download the Ember files into raw/ and unzip raw/hourly/
│   ├── build_ember_prices.py      raw/hourly/*.csv → processed/day_ahead_prices_hourly.csv
│   └── evaluate_ember_prices.py   quality checks, correlations, naive baselines → summary/
├── raw/                           (not in git) Ember ZIP, daily and monthly CSV, hourly/<Country>.csv
├── processed/day_ahead_prices_hourly.csv
└── summary/                       price_quality.csv, yearly_*.csv, correlation_2024_on.csv,
                                   naive_baselines_2025_on.csv, prices_hu_mk_rs.html/.png, evaluation_output.txt
```

## Rebuild

```bash
cd datasets/energy-prices
python scripts/fetch_ember_prices.py       # ~43 MB download, unzips to raw/hourly/
python scripts/build_ember_prices.py       # processed/day_ahead_prices_hourly.csv
python scripts/evaluate_ember_prices.py    # summary/ (needs plotly and kaleido for the chart)
```

| What | URL |
|---|---|
| Hourly, all countries (ZIP, 43 MB → 380 MB) | <https://files.ember-energy.org/public-downloads/price/outputs/european_wholesale_electricity_price_data_hourly.zip> |
| Daily (CSV) | <https://files.ember-energy.org/public-downloads/price/outputs/european_wholesale_electricity_price_data_daily.csv> |
| Monthly (CSV) | <https://files.ember-energy.org/public-downloads/price/outputs/european_wholesale_electricity_price_data_monthly.csv> |
| Ember API | <https://api.ember-energy.org/v1/docs> (free key). **No price endpoints**: only generation, demand, emissions, carbon intensity and capacity |

No account or key is needed for the files. Raw format: `Country, ISO3 Code, Datetime (UTC),
Datetime (Local), Price (EUR/MWhe)`, one row per hour. The processed file copies the values
unchanged: the zero days and gaps below are **not** cleaned there.

## Potential targets

| Target | Problem | Notes |
|---|---|---|
| `price_MK_eur_per_mwh` (MEMO) | C | Short history (since May 2023), never negative |
| `price_HU_eur_per_mwh` (HUPX) | C | Long history (2015), negative prices at sunny middays |
| `price_RS_eur_per_mwh` (SEEPEX) | C, hold-out H | Correlated with MK (0.94) but different level and floor: a good **unseen exchange** |
| Other markets | C inputs, E | Neighbours as covariates (known for D+1 after the auction only) |
| `P` of the imbalance cost | A, B | HUPX for the hour the PV forecast is for |

Setup in the challenge: daily t0 before the day-ahead auction, horizon D+1 … D+7. Baselines:
same hour last week (seasonal naive, m = 168), same hour yesterday (only fair for D+1), SMA,
EMA. MAPE is unusable (zero and negative prices).

## Coverage (UTC, to 2026-11-26 22:00)

| Market | Ember file | From | Hours | Missing hours | Zero hours | Negative hours | Median | Max |
|---|---|---|---|---|---|---|---|---|
| **Hungary (HUPX)** | `Hungary.csv` | 2015-01-01 | 104,327 | 24 (20–21 Nov 2026) | 177 | 863 | 61.0 | 1,047 |
| **North Macedonia (MEMO)** | `North Macedonia.csv` | 2023-05-10 22:00 (first MEMO auction) | 31,008 | 97 (8 days in Jul–Nov 2024) | 129 | 0 | 102.8 | 813 |
| **Serbia (SEEPEX)** | `Serbia.csv` | 2016-12-01 | 87,551 | 0 | 490 | 42 (2026 only) | 71.7 | 900 |
| Bulgaria · Greece · Romania | | 2015–2016 | ~89–104 k | 0–48 | 360–765 | 388–629 | 59–68 | 942–3,120 |
| Croatia · Slovenia | | 2015–2017 | 80–104 k | 0–24 | 151–165 | 885–918 | 60–80 | ~1,000 |
| Montenegro | | 2023-04 | 31,441 | 0 | 241 | 0 | 104.8 | 1,151 |
| Albania · Kosovo | | 2023-10 · 2024-01 | 20 k · 11 k | **7,344 · 13,848** | | | | |

Full table: [summary/price_quality.csv](summary/price_quality.csv). Chart (2022 on):
[summary/prices_hu_mk_rs.html](summary/prices_hu_mk_rs.html)
(PNG [summary/prices_hu_mk_rs.png](summary/prices_hu_mk_rs.png)).

## Quality findings

- **Hourly values only.** After the switch to 15-min MTU (1 Oct 2025) Hungary still has 24
  rows per day: Ember already averages the quarter-hours. That matches our hourly target rule.
- **Time zones are correct.** `Datetime (Local)` is UTC+1/+2 for HU, MK, RS and UTC+2/+3 for
  BG, GR, RO, so DST is handled. No duplicate hours.
- **Ember's daily file averages UTC days, not local days.** The mean of the hourly values
  per UTC day matches it (median difference 0.002 EUR/MWh); per local day it does not.
  Compute daily values yourself if local days are needed.
- **No visible interpolation.** Almost no sloped straight-line runs; gaps stay as missing rows.
- **Suspicious stretches to clean:**
  - MK: 4 whole days at exactly 0 EUR/MWh (2023-05-25, 2023-06-05, 2023-08-04, 2024-01-31)
    and 8 missing days in 2024 → treat as missing.
  - RS: the first ~3 weeks (from 2016-12-01) are one constant value (53.14) → start Serbia in 2017.
  - HU: 20–21 Nov 2026 missing (recent; may be filled in a later update).
- **Price floors differ.** HU, RO, BG, GR, HR, SI go negative (HU down to −500, the SDAC
  minimum); **MK never goes below 0**; RS only from 2026. Zero and negative prices sit around
  midday (solar), so **MAPE is unusable** for all of these markets.
- **Prices per year (HU):** ~35–51 EUR/MWh in 2015–2020, 272 in 2022 (crisis), ~100–110 in
  2023–2025, 151 so far in 2026, with more negative hours each year (74 → 262 → 281 → 226).

## How close the markets are (2024 onwards)

| Correlation | HU | MK | RS | BG | GR | RO |
|---|---|---|---|---|---|---|
| **MK** | 0.88 | 1 | **0.94** | 0.91 | 0.89 | 0.90 |
| **HU** | 1 | 0.88 | 0.90 | 0.93 | 0.84 | **0.96** |

- MK, RS (not in European market coupling) almost never have exactly the same price as
  their neighbours (≤ 0.6 % of hours). BG = RO in 81 % of hours, BG = GR in 69 % (coupled).
- **For the challenge:** HU or RS as a hold-out market for a model trained on MK is a real
  test: highly correlated (0.88–0.94) but with different levels, floors and negative prices.

## Naive baselines (test from 2025-01-01, every hour)

| Market | Naive daily MAE (same hour yesterday) | Naive weekly MAE (same hour last week) | MASE of naive daily (scale: weekly naive on training data) |
|---|---|---|---|
| Hungary | 28.45 | 33.77 | 1.35 |
| North Macedonia | 22.12 | 30.02 | 0.89 |
| Serbia | 26.89 | 33.05 | 1.25 |

Errors are in EUR/MWh. The daily naive forecast uses yesterday's prices, which at a 10:00
issue time are only known for D+1 forecasts (D+1's "yesterday" is D0); for D+2 … D+7 the
weekly naive is the fair baseline.

## Verdict

Ember is the quickest source for the price track: free, no key, one file per country,
HU / MK / RS and all neighbours, hourly, UTC and local time, 15-min already averaged.
Clean the few zero days and gaps listed above. For traded volumes, load and RES forecasts
(needed as inputs) use the ENTSO-E Transparency Platform or the exchanges; Ember has prices only.
