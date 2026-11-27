# Energy Forecasting Challenge

**Introduction to Time Series Analysis · FINKI, Ss. Cyril and Methodius University in Skopje**
Prof. Eftim Zdravevski

> **Draft.** Items marked **[TBD]** are filled in before release.

---

## 1. The challenge in one paragraph

You will forecast real energy time series **1 to 5 days ahead**, using only the information
that would have been available at the moment the forecast is made. You choose one track:
**solar power per inverter** (15-minute data from Macedonian PV plants), **day-ahead
electricity prices** (hourly, North Macedonia), or **your own dataset** with a similar
structure. For four weeks you develop against a public leaderboard. At the same time you
submit forecasts for a **hold-out set** — other plants, other inverters or other markets in
the same period — whose scores stay hidden until the end. The hold-out decides the final
ranking, so the goal is a model that **generalises**, not one that fits the leaderboard.

Work is **individual**.

---

## 2. Timeline

| When | What |
|---|---|
| Week 0 — December 1 | Data, starter kit and rules released. Leaderboard opens |
| End of week 1 | **Own-dataset proposals due** (Track C). Checkpoint: beat baseline B0 on the leaderboard |
| End of week 3 | Optional: ensemble-validation forecasts due (bonus, section 9) |
| End of week 4 — Mid January | **Final deadline**: leaderboard CSV, hold-out CSV, code + model, report |
| Week 5 | Reproducibility check, hold-out scores revealed, presentations |
| After week 5 (optional) | Live forecasting rounds (bonus, agreed together in class) |

---

## 3. Rules common to all tracks

### 3.1 When a forecast is made

Every forecast has an **issue time**: **08:00 Central European time on day D0**, shortly
before the day-ahead electricity auction for the next day. From that moment you forecast
**every step of the calendar days D+1, D+2, D+3, D+4 and D+5** (local time).

```
D0 00:00        D0 10:00 (issue)     D+1 00:00                                  D+5 24:00
   |---- known ------|---- not scored ----|=========== forecast window ===========|
```

### 3.2 What you may use

Each input belongs to one of two groups. Use it only as described.

| Group | Meaning | Examples |
|---|---|---|
| **Past** | Known only up to the issue time | Measured power, current, voltage, measured irradiance, actual prices, actual load, fuel prices **published** by 08:00 on D0 |
| **Future** | Known at the issue time for the whole forecast window | Weather forecasts from the ECMWF IFS run of **00 UTC on D0**, solar geometry, clear-sky irradiance, calendar, holidays, load forecasts published before 10:00 |

**Not allowed**, anywhere in your pipeline:

- actual target values (power, prices) for the forecast window, from any source;
- measured or reanalysis weather (e.g. pyranometers, ERA5) for the forecast window;
- weather forecasts from runs later than 00 UTC on D0;
- trying to find out the dates or locations hidden in the PV data.

Using any of these is treated as academic dishonesty and the hold-out score becomes zero.

### 3.3 External data

You may use extra public data **for training only** (data dated before the training
cut-off), if you document the source. At prediction time your code may use only the inputs
we provide and the files in your model folder (section 10.2).

### 3.4 Tools

Any language and library. Foundation models (Chronos, TimesFM, Moirai, Yug, …), deep
learning and GPUs are allowed; there is no compute limit. AI use welcomed, just make sure you understand it.]

---

## 4. Choose your track

| | Track A — PV inverters | Track B — Day-ahead prices | Track C — Your own dataset |
|---|---|---|---|
| Target | Energy per 15 min per inverter, **kWh per kWp** | Day-ahead price, **EUR/MWh**, hourly | Your choice |
| Values per forecast | 480 per inverter (5 days × 96) | 120 per market (5 days × 24) | ≥ 2 horizons |
| Leaderboard | Unseen plant, hidden dates | North Macedonia, later period | Your later period |
| Hold-out | Other plants and inverters, same period, hidden dates | Hungary (HUPX) and Serbia (SEEPEX), same period | Your unseen site/market |
| Bonus | Anomaly detection, quantiles, ensemble, live | Quantiles, ensemble, live | Quantiles |

Tell us your track by **end of week 1** (the form in the starter kit).

---

## 5. Track A — Solar power per inverter

### 5.1 Data

Data come from 3–5 PV plants in North Macedonia. Plant and inverter ids are anonymous,
coordinates are removed, and power is divided by the inverter's DC capacity (kWp).

**Training data** (`train/`, from 2024-03-14 to the training cut-off [TBD date]):

| File | Group | Columns (main) |
|---|---|---|
| `inverters.csv` | static | `inverter_id`, `plant_id`, `ac_kw`, `dc_kwp`, `n_mppt`, `mount` (fixed/tracker), `orientation_class` |
| `inverter_measurements.parquet` | past | `time_utc`, `inverter_id`, `energy_kwh_per_kwp` (**target**), `ac_power`, `dc_current_*`, `dc_voltage_*`, `inverter_temp`, `status_code` |
| `plant_measurements.parquet` | past | `time_utc`, `plant_id`, `ghi_measured`, `poa_measured`, `module_temp`, `ambient_temp`, `wind_speed` |
| `nwp_ifs.parquet` | future | `init_time_utc`, `valid_time_utc`, `plant_id`, `ghi`, `dni`, `dhi`, `gti`, `cloud_cover`, `temp_2m`, `wind_10m` (hourly, one 00 UTC run per day) |
| `solar_geometry.parquet` | future | `time_utc`, `plant_id`, `sun_elevation`, `sun_azimuth`, `clearsky_ghi`, `clearsky_poa` (15 min) |
| `flags.parquet` | past | `inverter_id` or `plant_id`, `start`, `end`, `type` (curtailment, outage, maintenance) |

The data are real: expect **gaps**, frozen values, outages and curtailment. Dealing with them
is part of the work.

**Leaderboard and hold-out data** come as **episodes**. One episode = one inverter at one
issue time:

```
leaderboard/episode_0017/
  context.parquet   7 days of measurements before the issue time (inverter + plant columns),
                    column `step` from −671 to 0 (0 = issue time), `local_time_of_day`
  future.parquet    IFS forecast (00 UTC run of D0) and solar geometry from the issue time to
                    the end of D+5: `step`, `horizon_day` (0 = rest of D0, 1…5), `local_time_of_day`,
                    weather and geometry columns
  meta.json         episode_id, inverter_id, plant_id, dc_kwp, mount
```

Episodes have **no dates** and come in random order. The season is in the solar geometry
and clear-sky columns. Episodes are spaced in time so that no episode's forecast window
appears inside another episode's context.

### 5.2 Task

For every episode, forecast `energy_kwh_per_kwp` for every 15-min step with
`horizon_day` 1 to 5. Night steps may be 0.

### 5.3 Scoring

Only **daylight** steps (sun elevation > 5°) with an available measurement and no
curtailment/outage are scored. The same mask applies to everyone.

**Primary score — relative MAE (lower is better):**

1. For each inverter *i*, over all its scored steps in all episodes:
   `RelMAE_i = Σ |y − ŷ| / Σ |y − ŷ_B0|`, where `ŷ_B0` is baseline B0.
2. Combine inverters with a geometric mean, each ratio clipped to [0.01, 100]:
   `Score = exp( mean_i log RelMAE_i )`.
3. **Skill = 1 − Score.** Skill > 0 means you beat B0.

Also shown (not ranked): nMAE (MAE in kWh/kWp), nRMSE, and error of daily energy, each per
horizon day D+1 … D+5.

### 5.4 Baselines (in the starter kit)

| Name | Idea |
|---|---|
| **B0** naive | Repeat the profile of the last full day (D−1) for every forecast day |
| B1 clear-sky persistence | Yesterday's clear-sky index × clear-sky production of each forecast step |
| B2 regression on forecast irradiance | Linear model of energy on IFS GTI, per inverter |
| B3 gradient boosting | LightGBM on IFS weather, solar geometry and recent production |

### 5.5 Bonus: anomaly detection

File `anomaly/inverter_days.parquet` contains inverter-days from the training plants. Some
contain faults we injected (lost strings, soiling, clipping, frozen telemetry, shading,
sensor drift, time shifts); some contain real events from the plant logs.

Submit `anomaly_submission.csv` with columns `inverter_id, day_id, score, flag` (`flag` = 0/1).
Scored by **F1** (flags) and **PR-AUC** (scores) on injected faults, and **recall** on real
logged events.

---

## 6. Track B — Day-ahead electricity prices

### 6.1 Data

All prices are from the **ENTSO-E Transparency Platform**, hourly. Where the market uses
15-minute prices (Hungary since 1 Oct 2025), the hourly value is the **mean of the four
quarter-hours**.

**Training data** (`train/`, up to the training cut-off [TBD date]):

| File | Group | Content |
|---|---|---|
| `prices.parquet` | past | `time_utc`, `zone`, `price_eur_mwh`: MK from 2023-05-10 (start of the MEMO day-ahead market), plus longer history of neighbouring zones |
| `system.parquet` | past / future | Actual load (past); day-ahead and week-ahead load forecasts, day-ahead wind/solar forecasts, each with `published_utc` (future, if published before 10:00); generation per type and cross-border flows (past) |
| `weather_ifs.parquet` | future | `init_time_utc`, `valid_time_utc`, `location`: temperature, irradiance, wind, precipitation for ~6 locations in North Macedonia |
| `fuels.parquet` | past | `value_date`, `published_date`, `ttf_eur_mwh`, `brent_usd_bbl`. Use a value only if `published_date` ≤ D0 |
| `calendar.parquet` | future | Date, weekday, public holidays per country, DST flags |

**Leaderboard** (`leaderboard/`): issue dates in North Macedonia after the training cut-off,
each with its inputs frozen at 10:00 on D0. **Hold-out** (`holdout/`): the same issue dates
for **Hungary and Serbia**, with weather for locations in those countries. Dates are visible
in this track.

### 6.2 Task

For every issue date and market, forecast the 120 hourly prices of D+1 … D+5. ENTSO-E wind
and solar forecasts exist only for D+1; for later days you must derive them yourself, e.g.
from the weather forecasts.

### 6.3 Scoring

**Primary score — relative MAE against `naive_weekly`** (the price at the same hour one
week earlier), lower is better:

1. Per market *m*: `RelMAE_m = Σ |y − ŷ| / Σ |y − ŷ_naive_weekly|` over all issue dates and hours.
2. Geometric mean over markets (clipped to [0.01, 100]); **Skill = 1 − Score**.

This makes markets with different price levels comparable. Also shown: MAE (EUR/MWh) and
RMSE per horizon day. MAPE is not used: prices can be zero or negative.

### 6.4 Baselines (in the starter kit)

| Name | Idea |
|---|---|
| **naive_weekly** | Same hour one week earlier |
| naive_last_day | Repeat the price profile of D0 |
| LEAR | LASSO-regularised autoregression from epftoolbox |
| LightGBM | Lags, calendar, fuel prices, load forecasts |

### 6.5 Re-run check

Because prices are public, your **hold-out predictions must be reproducible**: we run your
`predict.py` (section 10.2) on the hold-out inputs **without internet access**. The output
must match your submitted CSV (absolute difference ≤ 0.01 EUR/MWh per value). If it does not,
your hold-out score is zero.

---

## 7. Track C — Your own dataset

Submit a one-page proposal by **end of week 1**. It must show that the dataset:

- [ ] has at least 3 years of data, or at least ~20 000 time steps at hourly or finer resolution;
- [ ] is multivariate: at least two inputs besides the target, at least one of them known in
      advance for the forecast window (forecast, calendar, schedule) and available as it was
      at issue time;
- [ ] has a clear target, unit, issue time and at least two horizons;
- [ ] has an unseen test set: a later period and, if possible, another site, city or market.
      **You give the test targets to the instructor before you start modelling**;
- [ ] has simple baselines that can be beaten but are not trivial;
- [ ] may be used for the course (licence) and can be downloaded by a script.

Ideas: Elia (Belgium) solar/wind with official week-ahead forecasts; Predico's open targets;
ENTSO-E load for North Macedonia or neighbours; Skopje air quality (pulse.eco) with weather
forecasts; district heating; EV charging.

Track C uses the same rules (section 3), metrics (relative MAE against a seasonal naive) and
deliverables. The leaderboard is replaced by your own validation; the instructor scores your
test set.

---

## 8. Bonuses

| Bonus | What to do | How it is scored |
|---|---|---|
| **MLflow** | Track experiments | Aid in reproducability. |
| **Quantiles** | Add columns `q10` and `q90` | Mean Winkler score of [q10, q90] (α = 0.2) relative to a baseline interval, and 80 % coverage; separate board |
| **Anomaly detection** (Track A) | Section 5.5 | F1, PR-AUC, recall on real events |
| **Ensemble** | Submit forecasts for the ensemble-validation set by end of week 3, plus your hold-out | We combine all participants (median, skill-weighted mean, stacking). Your contribution = loss of the ensemble without you − loss with you, on the hold-out. A positive contribution earns the bonus, so a model that is **different** and good helps most |
| **Live rounds** | After week 5, if agreed in class: daily forecasts at 10:00 for real days, from a data snapshot we publish | Same metrics on days that had not happened when you forecast. A missed day gets the 75th-percentile score of the other participants |

---

## 10. What to submit

### 10.1 Prediction files

Start from `sample_submission_leaderboard.csv` and `sample_submission_holdout.csv`; they list
every required row.

**Track A**

```
episode_id,step,q50[,q10,q90]
ep_0017,57,0.000
ep_0017,58,0.000
...
```

**Track B**

```
issue_date,zone,delivery_time_utc,horizon_day,q50[,q10,q90]
2026-02-03,HU,2026-02-03T23:00:00Z,1,104.21
...
```

### 10.2 Code and model

A Git repository (or zip) with:

```
predict.py          python predict.py --input-dir holdout/ --model-dir model/ --output predictions.csv
train.py            how the model in model/ was produced
model/              trained model files (and any training-only external data you need)
environment.yml     or requirements.txt, with versions
README.md           how to reproduce training and prediction
```

`predict.py` must run **without internet access** and produce exactly your submitted hold-out
file. This is required for Track B and checked on a sample in Track A.

### 10.3 Report (max 8 pages, PDF)

1. **Task definition**: issue time, horizons, which inputs are past and which future.
2. **Data**: gaps, outliers, anomalies, how you handled them.
3. **Evaluation setup**: your rolling-origin validation, and why it imitates the hold-out.
4. **Models**: everything you tried, with validation scores per horizon day against the baselines.
5. **Final model** and why you chose it.
6. **Error analysis**: by horizon day, time of day, weather or price regime.
7. **Expected hold-out performance** and what could go wrong when moving to other plants or markets.
8. What did not work.

### 10.4 Presentation (week 5)

5 minutes + 3 minutes questions: your task definition, best idea, and one error you learned from.

---

## 11. Grading

The challenge counts can be used to pass the exam with a grade up to 10. Traditional form of the exam is possible but for a grade up to 8.

| Component | Indicative Weight |
|---|---|
| Report: task definition, leakage-free evaluation, analysis | 25 % |
| Leaderboard skill vs baselines | 10 % |
| **Hold-out skill vs baselines** | 35 % |
| Reproducibility (code, re-run check, environment) | 20 % |
| Presentation | 10 % |
| Bonuses (section 9) | up to +15 % |

Thresholds (indicatve, to be tuned for each challenge)

| Hold-out skill |
|---|---|
| Below baseline B0 / naive_weekly |
| Beats B0 / naive_weekly |
| Beats B2 / LEAR |
| Beats B3 / LightGBM |

---

## 12. Starter kit

- `starter.ipynb`: loads the data, plots an inverter / a market, builds an episode, runs a
  baseline, writes a valid submission.
- `baselines/`: B0–B3 (Track A), naive_weekly, naive_last_day, LEAR, LightGBM (Track B).
- `score.py`: **the official scoring code**; run it on your own validation folds.
- `make_episodes.py`: turns training data into episodes for your own validation, with the
  same format as the leaderboard.
- `predict_template.py`: the required command-line interface.

Recommended reading before you start: the resource guide [resources.md](resources.md),
in particular "Live benchmarks and platforms" and "How to evaluate time series models
properly". Course lectures: L4 (splits, benchmarks, metrics), L7 (exogenous inputs),
L8 (outliers), L9 (lag features, leakage, direct vs recursive multi-step), L10 (known-future
covariates, multi-output networks).

---

## 13. FAQ

**Can I use the leaderboard and hold-out context windows for training?**
Yes. They contain only measurements from before each issue time, and no context window
contains another episode's forecast days.

**Can I use other weather forecasts (e.g. GFS, ICON)?**
For training, yes, if you can show the forecasts are archived as they were issued (with
issue time). At prediction time only the provided inputs are available, so the model must
work with the IFS forecasts we provide.

**Why no MAPE?**
PV production is zero at night and prices can be zero or negative, so percentage errors
explode or are undefined. Relative MAE against a naive forecast is scale-free and stable.

**Why are the hold-out scores hidden?**
So that you choose your model with your own validation, as in real forecasting, and not by
probing the final test set.

**How do daylight saving changes work?**
Forecast days are local calendar days, so they have 92 or 100 quarter-hours (23 or 25 hours)
on change days. The sample submissions already contain the right rows.

**Can I work with a colleague?**
Discussing ideas is fine; code, features, predictions and reports must be your own.
Name anyone you discussed with in the report.

**My model failed on some episodes. What happens?**
Missing rows are filled with the baseline, so you lose skill on those rows but are not
disqualified.
