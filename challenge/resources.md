# Energy forecasting challenges: resources, where to start, how to evaluate

> Part of the [forecasting challenge](../README.md). The challenge itself is described in
> [simplified-challenge.md](simplified-challenge.md); the data in [datasets/](../datasets/README.md).

Reference material for designing the course challenge (see
[challenge-design.md](challenge-design.md)) and for students who want to learn how
energy forecasting competitions are run and scored.

---

## 0. Live benchmarks and platforms (the starting links)

These are **live, operational** benchmarks: forecasts are submitted before a deadline and
scored only after the actuals exist, so leakage and retroactive tuning are impossible.
This is the model for the live rounds of our challenge.

| Site | What it is | Targets, resolution, horizon | Scoring | Take-away for the course |
|---|---|---|---|---|
| [EnergyBench by Foretec](https://energybench.foretec.co/methodology.html#gate-aligned) — **start here** | Daily live benchmark of models (statistical, ML, foundation models, TSO forecasts) | Day-ahead price, wind, solar, load in BE, NL, FR, DE-LU, DK1, DK2; 96 quarter-hours of day D | MAE, RMSE, **Rel. MAE / Rel. RMSE vs `naive_weekly`**, WIS (pinball), Winkler, 80 % coverage, skill score (fev-bench), forecast value of a virtual 100 MW asset; Elo / win rate / average rank with **bootstrap over issue days** | Clearest written methodology: **gate-aligned** issue time (11:30 CET on D−1, before the 12:00 SDAC gate), inputs **frozen at the cut-off** (only weather runs already published: 06 UTC ICON-EU, 00 UTC GFS and IFS), fuel closes count only from the end of their date, actuals scored only when final |
| [Energy-Arena](https://energy-arena.org/) ([paper, arXiv 2604.24705](https://arxiv.org/abs/2604.24705)) | Open, API-driven "dynamic benchmark" for operational energy forecasting | Prices, load, renewables (Europe; ENTSO-E ground truth) | Rolling evaluation windows (1, 7, 30, 90, 365 days), persistent leaderboards | Ex-ante submission via API, ex-post scoring. Teams could submit to it as a stretch goal |
| [Predico](https://predico.inesctec.pt/) (INESC TEC; [docs](https://predico-elia.inesctec.pt/docs/), [FAQ](https://predico-elia.inesctec.pt/docs/faq/)) | **Collaborative forecasting market**: market owners (Elia, 50Hertz, EDP) publish challenges, forecasters are paid on performance | Belgian offshore wind and solar (Elia), 15-min, intraday / D+1 / D+N | **Q50 scored by RMSE, Q10–Q90 by Mean Winkler Interval**, ranked separately; skill-weighted ensemble of all submissions (pinball-based weights for quantiles) | Direct template for our **ensemble goal**: combine many forecasters, reward contribution. Useful rules: latest submission before gate counts; a missed day gets the **75th-percentile score of peers** |
| [open-predico](https://github.com/arnaud-vs/open-predico) + [dashboard](https://huggingface.co/spaces/open-predico/dashboard) | Open-source pipeline that submits to Predico with time series foundation models (TSFMs) | Spanish mFRR energy/price, German (50Hertz) wind/solar, Belgian solar; 15-min, day-ahead, q10/q50/q90 | RMSE (q50) + Winkler (q10/q90), rolling-origin backtest over a test year | Reference code: each input column tagged **`past` or `future`** (`configs/groups.toml`) and the backtest enforces it; weather vintages from Open-Meteo; benchmark + live data as Hugging Face datasets; leaderboard as a **static Hugging Face Space** (cheap way to host ours) |
| [Yug](https://huggingface.co/birlaailabs/yug) (Birla AI Labs) | 271.8M-parameter TSFM for zero-shot probabilistic forecasting | Generic; quantiles 0.1–0.9; context up to 2048 steps; supports covariates | GIFT-Eval CRPS 0.529, MASE 0.744 (self-reported) | Zero-shot baseline for the **generalisation** goal. Model card notes covariate forecasts degrade faster with horizon. Weights are CC-BY-NC (fine for teaching) |
| [milloin.energy](https://www.milloin.energy/) | Commercial price forecasting service | Day-ahead prices for Nordics, Baltics, PL, DE, SYS; **12 days ahead, updated 6× per day**; reserve (mFRR/aFRR) | No public accuracy figures | Industry reference for multi-day horizons: inputs are weather, plant and grid status, fuel prices, hydro; accuracy best for 1–2 days, usable to ~3–7 days. Contrast with transparent benchmarks above |

### Lessons that shape our challenge

1. **Gate-aligned issue time.** Fix the issue time to when a real decision is made (before the
   day-ahead auction), not "one step ahead".
2. **Frozen information set.** Store the inputs as they were at the cut-off (weather run,
   published load forecast, fuel close of the previous day). Backtests must use archived
   vintages, never today's revised data.
3. **Relative error vs a seasonal-naive baseline** (Rel. MAE) is the common currency across
   series, zones and plants; aggregate with a geometric mean of ratios.
4. **Point + quantiles.** Q50 by MAE/RMSE, Q10–Q90 by Winkler or pinball, ranked separately.
5. **Many days, with uncertainty.** Leaderboards need enough issue days (EnergyBench marks a
   model provisional below 12 races) and bootstrap intervals over whole days.
6. **Rules for missed submissions** (Predico: peer 75th-percentile score) keep live rounds fair.
7. **Ensembles of many forecasters** beat single models (Predico reports 6–8 % RMSE
   improvement over Elia's operational forecasts in its CIGRE paper).

---

## 1. Competitions and benchmarks worth knowing

| # | Competition / benchmark | Problem | Data and granularity | Scoring | Why it matters for us |
|---|---|---|---|---|---|
| 1 | **GEFCom2014** (Global Energy Forecasting Competition) — [overview paper](https://doi.org/10.1016/j.ijforecast.2016.02.001), [Tao Hong's blog](https://blog.drhongtao.com/2016/01/probabilistic-energy-forecasting-gefcom2014.html) | 4 tracks: load, **price**, wind, **solar** | Solar: 3 PV farms, hourly, ECMWF NWP forecasts as inputs. Rolling weekly tasks | Pinball loss averaged over 99 quantiles | Template for "NWP forecast → PV power" and for a rolling, multi-round competition |
| 2 | **HEFTCom2024** (IEEE Hybrid Energy Forecasting and Trading Competition) — [IEEE DataPort](https://ieee-dataport.org/competitions/hybrid-energy-forecasting-and-trading-competition), [report, arXiv 2507.01579](https://arxiv.org/abs/2507.01579) | Day-ahead wind + solar for a GB portfolio, plus trading | Half-hourly; DWD and NCEP NWP inputs; live, prospective rounds | Pinball loss (quantiles 10–90 %) + trading revenue | Shows a **live** evaluation phase (truly unseen data) and a second "value" metric beside accuracy. Winning student team used stacked GBMs |
| 3 | **Kaggle Enefit — Predict Energy Behavior of Prosumers** (2023–24) — [Kaggle](https://www.kaggle.com/competitions/predict-energy-behavior-of-prosumers) | Hourly PV production and consumption of Estonian prosumers | ECMWF forecast weather (as available at forecast time), historical weather, installed capacity, **electricity and gas prices** | MAE | Closest public analogue of our multivariate setup: forecasted weather + prices + gas as inputs, a time-series API that prevents look-ahead, and a forecasting phase scored on data collected after submissions closed |
| 4 | **Kaggle AMS 2013–2014 Solar Energy Prediction** — [Kaggle](https://www.kaggle.com/competitions/ams-2014-solar-energy-prediction-contest) | Daily solar energy at 98 Oklahoma Mesonet stations | GEFS ensemble forecasts as inputs | MAE | Spatial generalisation: forecast for stations from gridded NWP |
| 5 | **epftoolbox** (Lago, Marcjasz, De Schutter, Weron 2021) — [GitHub](https://github.com/jeslago/epftoolbox), [paper, arXiv 2008.08004](https://arxiv.org/abs/2008.08004) | Day-ahead electricity price forecasting (EPF) benchmark | 5 markets (Nord Pool, PJM, EPEX-BE/FR/DE), 6 years hourly each, 2 exogenous variables (load / generation forecasts) | MAE, **rMAE**, sMAPE, RMSE; Diebold–Mariano and Giacomini–White tests | **Best methodological template for the price track**: strong baselines (LEAR, DNN), recalibration protocol, metric choice and significance testing |
| 6 | **M4 / M5** forecasting competitions — [M4 results](https://doi.org/10.1016/j.ijforecast.2019.04.014), [M5 accuracy](https://doi.org/10.1016/j.ijforecast.2021.11.013) | Many series, many domains | Yearly → daily | sMAPE + MASE (OWA in M4), WRMSSE in M5 | Why scale-free metrics (MASE) are used to rank across many series; benchmarks first; simple combinations are hard to beat |
| 7 | **Monash Forecasting Archive** — [forecastingdata.org](https://forecastingdata.org/); **GIFT-Eval** — [leaderboard](https://huggingface.co/spaces/Salesforce/GIFT-Eval) | Cross-dataset benchmarks | Includes solar, wind, electricity, prices | MASE, CRPS | Measuring **generalisation to unseen datasets**; zero-shot evaluation of foundation models |

### Datasets close to the planned challenge

| Dataset | What it contains | Fit |
|---|---|---|
| [Kaggle "Solar Power Generation Data"](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data) | 2 Indian PV plants, ~34 days, **15-min, inverter-level** DC/AC power and yield, plant-level irradiation, ambient and module temperature | Same schema as our inverter data. Too short for 2–7 day forecasting, good for an anomaly detection warm-up (underperforming inverters) |
| [PVOD](https://research-collection.ethz.ch/handle/20.500.11850/515012) (Yao et al., Solar Energy 2021) | 10 PV stations in Hebei, China, ~1 year, **15-min, NWP forecast + local measurements** (irradiance, temperature, humidity, wind) | Same "forecasted vs measured irradiance" design as our plan |
| [NREL PVDAQ](https://data.openei.org/submissions/4568) | Many US PV systems over many years, 10 s – 15 min, inverter metadata, Solar Data Prize systems | Long histories for anomaly detection and degradation studies |
| [Elia open data](https://opendata.elia.be/) (Belgium) | Measured and forecast PV and wind (including week-ahead forecasts), load, imbalance prices | Good "bring your own dataset" option with official 2–7 day forecasts |

### Data sources for the planned tracks

| Source | Use |
|---|---|
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) + [entsoe-py](https://github.com/EnergieID/entsoe-py) | Day-ahead prices, load and load forecasts (day-, week-ahead), wind/solar day-ahead forecasts, generation per type, cross-border flows, for MK, HU, RS, BG, GR, ... Free API token |
| [ENTSO-E Power Statistics](https://www.entsoe.eu/data/power-stats/) | Hourly load per country (2006 → 2026 H1), monthly generation by fuel, monthly flows, yearly capacity. **No prices.** Evaluated in [datasets/energy-volumes/](../datasets/energy-volumes/README.md) |
| [Ember wholesale prices](https://ember-energy.org/data/european-wholesale-electricity-price-data) | Hourly/daily/monthly day-ahead prices per European country incl. HU, MK, RS, cleaned from ENTSO-E; free download, no key. Evaluated in [datasets/energy-prices/](../datasets/energy-prices/README.md) |
| MEMO (North Macedonia, memo.mk) | Day-ahead market since **10 May 2023** ([news](https://balkangreenenergynews.com/north-macedonias-memo-launches-domestic-day-ahead-power-market)), so only ~3.5 years of history. Intraday market launched later |
| [HUPX](https://hupx.hu/) (Hungary) | Long hourly history. Part of SDAC, which switched to **15-minute MTU on 1 Oct 2025** ([HUPX](https://hupx.hu/2025/10/01/15-minute-mtu-implemented-sdac)) |
| SEEPEX (Serbia) | Hourly day-ahead prices; check current MTU and coupling status |
| [Open-Meteo](https://open-meteo.com/) | ERA5 reanalysis (measured-like weather since 1940); [Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api) (stitched short lead times); [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) (value predicted 24 h, 48 h, … 7 days **before the valid time**, most models from January 2024); [**Single Runs API**](https://open-meteo.com/en/docs/single-runs-api) (a full run by its UTC init time: **ECMWF IFS HRES 9 km from 2024-03-14**, 4 runs/day, 15 days; most other models from 2026-04-02). Hourly radiation (GHI, DNI, DHI, GTI) for Macedonia; 15-min radiation only in Central Europe / North America. CC BY 4.0, free API is non-commercial |
| [pvlib](https://pvlib-python.readthedocs.io/) | Solar position, clear-sky irradiance, transposition to plane-of-array, PV models |
| [PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en) | Typical-year irradiance and expected yield for locations in Macedonia |
| [FRED](https://fred.stlouisfed.org/) | Brent crude daily (`DCOILBRENTEU`), EU natural gas monthly (`PNGASEUUSDM`). Daily TTF gas and EU ETS carbon prices need another source (EEX/ICE are licensed) |
| [pulse.eco](https://pulse.eco/) | Hourly air quality for Skopje and other cities: a local "bring your own dataset" option |

### Tooling

- **Classical and ML baselines at scale:** Nixtla [statsforecast / mlforecast / neuralforecast / utilsforecast](https://nixtlaverse.nixtla.io/), [Darts](https://unit8co.github.io/darts/), [sktime](https://www.sktime.net/), [skforecast](https://skforecast.org/).
- **Price forecasting:** epftoolbox (LEAR, DNN, metrics, DM/GW tests).
- **Foundation models for zero-shot baselines:** Chronos/Chronos-Bolt, TimesFM, Moirai. Useful as a "generalisation" reference point.
- **Hosting a challenge:** [Codabench](https://www.codabench.org/) ([docs](https://docs.codabench.org/)), [Kaggle Community Competitions](https://www.kaggle.com/c/about/community), [Hugging Face Competitions](https://huggingface.co/docs/competitions).

---

## 2. Where to start (suggested path for students)

1. **Read the EnergyBench methodology page** (30 min) — gate alignment, information sets,
   relative metrics and leaderboard statistics in one place. Browse the open-predico repo for
   how a real pipeline tags `past` / `future` inputs.
2. **Read two overviews** (2–3 hours):
   - Hong et al. 2016, *Probabilistic energy forecasting: GEFCom2014 and beyond* (IJF 32(3)) — how energy competitions are designed and what won.
   - Lago et al. 2021, *Forecasting day-ahead electricity prices: a review of state-of-the-art algorithms, best practices and an open-access benchmark* (Applied Energy 293) — sections on best practices and evaluation.
3. **Reproduce a benchmark** before building anything new:
   - Prices: run epftoolbox `naive` and `LEAR` on one market and compute MAE and rMAE.
   - Solar: on PVOD (or the course data when released) build *clear-sky persistence* and a linear regression on NWP irradiance.
4. **Define the task precisely** (section 3.1) and write it down before writing model code.
5. **Build the evaluation harness first**: rolling origins, horizons, metrics and baselines (section 3.2–3.4). Every model then plugs into the same loop.
6. **Climb the ladder**: seasonal naive → regression with exogenous inputs (SARIMAX, L7) → gradient boosting with lags and calendar features (L9) → neural nets (L10) → ensembles.
7. **Check generalisation**: leave-one-plant-out / leave-one-market-out, and look at error by horizon, hour of day and weather regime.

The course lectures map directly: L4 (temporal splits, benchmarks, MAE/RMSE/MAPE/MASE),
L6–L7 (SARIMA, SARIMAX, regression with exogenous inputs), L8 (outliers, interventions),
L9 (lag features, leakage, `TimeSeriesSplit`, recursive vs direct multi-step),
L10 (known-future covariates, multi-output networks).

---

## 3. How to evaluate time series models properly

### 3.1 Define the forecasting task

A forecast is only meaningful with these four items fixed:

| Item | Example (solar) | Example (prices) |
|---|---|---|
| **Issue time** (when the forecast is made) | Day D, 06:00 local | Day D, 10:00 CET (before the D+1 auction at 12:00) |
| **Target and resolution** | Inverter energy per 15 min, kWh/kWp | Hourly day-ahead price, EUR/MWh |
| **Horizons** | All 15-min steps of D+2 … D+7 | All hours of D+2 … D+7 |
| **Information set** (what is known at issue time) | Measurements up to issue time; NWP forecasts **issued before** issue time; solar geometry; capacity | Prices up to D+1? (only if issue time is after the auction); load/RES forecasts published by issue time; fuel prices at close of D-1; calendar |

Anything not in the information set is **leakage**. Common sources in energy data:

- Using **measured** irradiance or weather for the forecast window instead of the forecast
  that was available at issue time ("perfect prognosis"). It inflates skill a lot.
- Using archived NWP with the **wrong lead time**. Open-Meteo's Historical Forecast API
  stitches the first hours of each run, so it behaves like a 0–1 day forecast. The Previous
  Runs API offsets are relative to the *valid* time: `previous_day1` for 23:00 on D+1 comes
  from a run ~24 h earlier, i.e. *after* a 10:00 issue time on D. Safest: the **Single Runs
  API**, taking the last run published before the issue time (e.g. the 00 UTC ECMWF IFS run
  for a 10:00 CET issue time). If Previous Runs is used, take `previous_day(k+1)` for day D+k.
- Gas, oil and carbon prices for days after the issue date.
- Normalisation, imputation or feature selection fitted on the whole dataset, centred rolling
  windows, interpolating gaps across the train/test boundary.
- Neighbouring inverters' measurements for the same period as the target (turns forecasting
  into spatial estimation).

### 3.2 Split data in time: rolling-origin evaluation

Never shuffle. Use several forecast origins and score every horizon:

```
origin 1: [=========== train ===========][issue]..gap..[ D+2 ... D+7 ]
origin 2: [============= train =============][issue]..gap..[ D+2 ... D+7 ]
origin 3: [=============== train ===============][issue]..gap..[ D+2 ... D+7 ]
```

- Expanding or sliding window; retrain every origin, or every k origins ("recalibration" in EPF).
- Enough origins to cover all seasons (at least one full year for prices and PV).
- Keep a final hold-out that is never used for model selection.

A minimal multi-horizon evaluation loop:

```python
import numpy as np
import pandas as pd

def rolling_origin(y, X_future, fit_predict, origins, horizon_steps, gap_steps):
    """y: target Series; X_future: covariates *as known at each origin*;
    fit_predict(y_hist, X_hist, X_fut) -> array of len(horizon_steps)."""
    rows = []
    for t0 in origins:
        i0 = y.index.get_loc(t0)
        fut = y.index[i0 + gap_steps : i0 + gap_steps + horizon_steps]
        yhat = fit_predict(y.iloc[: i0 + 1], X_future.loc[: t0], X_future.loc[fut])
        rows.append(pd.DataFrame({"origin": t0, "time": fut,
                                  "step": np.arange(1, len(fut) + 1),
                                  "y": y.loc[fut].to_numpy(), "yhat": yhat}))
    return pd.concat(rows, ignore_index=True)

# score per horizon day:
# res["day"] = (res["time"].dt.normalize() - res["origin"].dt.normalize()).dt.days
# res.groupby("day").apply(lambda d: np.mean(np.abs(d.y - d.yhat)))
```

### 3.3 Always report benchmarks

| Track | Benchmarks |
|---|---|
| Solar | Seasonal naive (same 15-min slot yesterday, m = 96); **clear-sky persistence** (yesterday's clear-sky index × today's clear-sky power); climatology for that time of year; linear regression on NWP irradiance |
| Prices | Seasonal naive (same hour last week, m = 168); EPF "naive" (yesterday for Tue–Fri, last week for Sat–Mon); LEAR (epftoolbox); gradient boosting with lags + calendar + fuel prices |

Report every model as a **skill score** against the benchmark: `skill = 1 − metric_model / metric_benchmark`.

### 3.4 Pick metrics that suit the target

| Metric | Formula | Use | Watch out |
|---|---|---|---|
| MAE | mean \|y − ŷ\| | Primary point metric for both tracks; optimal forecast = median | Scale-dependent: cannot average across plants/markets |
| RMSE | √mean (y − ŷ)² | Penalises large errors (price spikes, missed cloudy days) | Dominated by a few spikes |
| **nMAE / nRMSE** (PV) | MAE / installed capacity | Standard in PV forecasting; comparable across inverters and plants | Report the normaliser; score daylight steps only |
| WAPE | Σ\|y − ŷ\| / Σ\|y\| | A percentage that still works with zeros | Not a mean of per-step percentages |
| **MASE** | MAE / in-sample MAE of seasonal naive (m) | Scale-free; ranks across series (M4) | Choose m and say whether night steps are included in the scale |
| **rMAE** (EPF) | MAE / MAE of a naive benchmark on the same test period | Scale-free across markets and periods (Lago et al. 2021) | Benchmark must be fixed in advance |
| MAPE | mean \|(y − ŷ)/y\| | Only for strictly positive, non-tiny targets (e.g. daily PV energy in summer) | **Undefined for PV at night; explodes for prices near zero or negative** (negative prices now occur in HU/SEE at midday) |
| sMAPE | mean 2\|y − ŷ\|/(\|y\|+\|ŷ\|) | Legacy; used in M4 and EPF papers | Asymmetric, unstable near zero |
| Pinball loss / CRPS | max(τ(y − q), (τ − 1)(y − q)) over quantiles | Probabilistic forecasts (GEFCom2014, HEFTCom2024) | Requires quantile submissions |
| Event F1, PR-AUC | — | Anomaly detection | See 3.7 |

Recommendation for the course: **MAE (or nMAE) as primary, RMSE secondary, MASE/rMAE
for anything aggregated across inverters or markets**. Keep MAPE only for daily totals and
explain why it fails at 15-min / hourly resolution.

### 3.5 Break the error down

Score per horizon day (D+2 … D+7), per hour of day, per month/season, and per weather regime
(clear, partly cloudy, overcast; low/normal/high price). A model that wins on average can
lose badly on the cases that matter (cloudy days, price spikes).

### 3.6 Test whether differences are real

- **Diebold–Mariano** test on loss differentials between two models (epftoolbox has a
  multivariate version per day for EPF).
- Giacomini–White or Model Confidence Set when comparing many models.
- On a leaderboard, report ranks with ties for models that are not significantly different.

### 3.7 Anomaly detection evaluation

- Prefer **event-level** precision/recall/F1 with a time tolerance, or range-based
  precision/recall (Tatbul et al., NeurIPS 2018, [arXiv 1803.03639](https://arxiv.org/abs/1803.03639)).
- Avoid **point-adjust** F1: it rewards random detectors (Kim et al., AAAI 2022,
  [arXiv 2109.05257](https://arxiv.org/abs/2109.05257)). Threshold-free alternatives: PR-AUC, VUS-PR (Paparrizos et al., PVLDB 2022).
- For PV, compare inverters against peers at the same plant (they share the weather):
  performance ratio and per-inverter residuals from a peer or physical model.

### 3.8 Ensembles

- Simple average or median of diverse models is a strong baseline (the "forecast
  combination puzzle"; M4 and GEFCom winners used combinations).
- Weighted/stacked combinations need **out-of-sample** predictions (from the rolling
  origins), never in-sample fits.
- Quantile Regression Averaging (Nowotarski & Weron, 2015) turns several point forecasts
  into probabilistic ones; widely used in EPF.

---

## 4. Further reading

- Hyndman & Koehler (2006), *Another look at measures of forecast accuracy*, IJF 22(4) — MASE. [doi](https://doi.org/10.1016/j.ijforecast.2006.03.001)
- Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (3rd ed.), chapters 5 and 13 — evaluation, time series cross-validation. [otexts.com/fpp3](https://otexts.com/fpp3/)
- Yang et al. (2020), *Verification of deterministic solar forecasts*, Solar Energy 210 — skill scores and reference forecasts for PV.
- Weron (2014), *Electricity price forecasting: a review of the state-of-the-art*, IJF 30(4).
- Hong et al. (2016), GEFCom2014 overview; HEFTCom2024 report ([arXiv 2507.01579](https://arxiv.org/abs/2507.01579)).
- Diebold & Mariano (1995), *Comparing predictive accuracy*, JBES 13(3).
- Pinson (2013), *Wind energy: forecasting challenges for its operational management*, Statistical Science 28(4).
