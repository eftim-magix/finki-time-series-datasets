# Forecasting Challenge (simplified version)

**Introduction to Time Series Analysis · FINKI, Ss. Cyril and Methodius University in Skopje**
Prof. Eftim Zdravevski

> Slides: [slides/forecasting-challenge-slides.pdf](../slides/forecasting-challenge-slides.pdf)
> (HTML: [slides/forecasting-challenge-slides.html](../slides/forecasting-challenge-slides.html)).
> Datasets: [datasets/README.md](../datasets/README.md).
> A more detailed variant of the challenge is in [challenge-description.md](challenge-description.md).
> Dates are **tentative**.

---

## 1. Idea

Pick one forecasting problem, build a pipeline that **trains, validates and forecasts with
uncertainty**, and show that it **generalises**: to newer data (time) and to inverters,
plants or markets it has never seen. The same code runs several times: on the data you have,
on a hold-out set, and later on data that is published only after you submit your code.

Work is **individual**: one student, one problem.

---

## 2. Data and timeline

| When (tentative) | What |
|---|---|
| **Next week** (from 30 Nov 2026) | Core datasets released: **S1** (train), **S2** (validation, targets included) and **H** (hold-out, in **separate files**, targets withheld). Other external data you fetch yourself |
| End of week 1 | Problem chosen; own-dataset proposal |
| **December** | Short presentation of your S2 results vs baselines |
| **Mid-January 2027** | **Preliminary results on H** (your forecasts for the hold-out files) **and code**, tagged in the common GitHub repository (code freeze) |
| **End of February 2027** | **S3**: newly published data (newer period). Your frozen code is re-run: train on **S1 + S2 only** (H targets are not used for training), forecast S3. Final results |
| In parallel | Optional: paper writing, ensembles, anomaly detection |

- **H** contains other inverters of seen plants, unseen plants, or another exchange,
  depending on the problem: **generalisation to unseen series**.
- **S3** is newer data of the same series, published after the code freeze:
  **generalisation over time**.
- **External data** (weather, fuels, ENTSO-E, …) may be fetched individually. Put the
  download script in your folder and respect the information set (section 3).

### The pipeline contract

Python only, dependencies pinned in `requirements.txt`. Your code must run unchanged:

```bash
python run.py --train data/S1 data/S2 --test data/H  --out predictions_H.csv
python run.py --train data/S1 data/S2 --test data/S3 --out predictions_S3.csv
```

Output format (one row per forecast value; `lead_h` = hours between `origin` and `timestamp`; an **80 % prediction interval** for every value):

```
series_id,origin,timestamp,lead_h,y_pred,y_lo80,y_hi80
inv_017,2026-12-14T00:00,2026-12-15T12:00,36.0,4.21,2.95,5.10
```

### Common GitHub repository

- One repository for the course, **one folder per student**: `run.py`, `requirements.txt`,
  `README.md`, data download scripts, report.
- Everyone can read everyone's code.
- **Code freeze** mid-January: tag the commit; that commit is the one re-run on S3.
- Fixed random seeds; no internet access needed when predicting.
- The scoring script is shared: run it on S2 yourself.

---

## 3. Forecasting setup (all problems)

- **Origin t0**: the moment the forecast is made (once per day, see each problem).
- **Horizon window**: it does **not** have to start at t0. Minimum: forecast **hours 16–30
  after t0** (t+16 … t+30, the day-ahead window). Recommended: longer windows such as
  **24–48 h** or **24–72 h** (prices: up to 7 days).
- **Past inputs** (known only up to t0): measured production, currents, voltages, measured
  weather, actual prices and volumes, balancing values, fuel prices.
- **Future inputs** (known at t0 for the whole horizon): weather **forecasts** issued before
  t0, calendar events.
- **Uncertainty**: every forecast comes with an **80 % prediction interval**. The further
  ahead, the wider it should be.

> **Leakage warning.** Measured weather of a plant is an excellent predictor of every
> inverter in that plant. After t0 you may use only **forecast** weather, never measured
> weather or other inverters' production.

---

## 4. Problems (choose one)

### A. PV inverters

| | |
|---|---|
| Target | Energy produced per inverter, **5-min** (A1); variants aggregated to **15-min** (A2) or **1-hour** (A3) |
| Inverter inputs (past) | AC/DC current, voltage, power, temperature, status, other inverter series |
| Auxiliary (past) | Plant weather up to t0: temperature, wind, irradiance, … |
| Auxiliary (future) | Forecast weather from t0 up to D+2 (temperature, wind, irradiance, …) |
| Train | Inverters from several plants. **Different sizes**: normalise (e.g. by capacity) or use scale-free metrics |
| Hold-out H | Other inverters of seen plants; unseen plants |
| S3 | Newer data of the same inverters and plants |
| t0 and horizon | Daily at 00:00 local; next **48 h** (minimum hours 16–30; report hours 1–24 and 25–48) |

### B. PV plants

Same as A, but the target is **hourly production of the whole plant** (sum of its
inverters). Hold-out: unseen plants. S3: newer data. Daily t0, next 48 h.

### C. Electricity prices

| | |
|---|---|
| Target | Day-ahead price, **hourly**, MEMO (North Macedonia) and HUPX (Hungary), several years |
| Inputs (past) | Prices; **traded volumes** (MWh, hourly; normalise per exchange when combining); actual weather; crude oil (daily); European gas (daily) |
| Inputs (future) | Weather forecasts (first days only); calendar events (holidays, weekends) |
| Validation | Step-wise (rolling-origin) or another time-based split |
| Hold-out H | **Another exchange**: correlated but different, less history |
| S3 | **Newer period** published after the code freeze |
| t0 and horizon | Daily, before the day-ahead auction; **D+1 … D+7** (minimum hours 16–30) |

### D. Balancing (MEPSO): imbalance price, aFRR, mFRR and other parameters

| | |
|---|---|
| Target | The hourly **imbalance price** (EUR/MWh, see below), or activated aFRR / mFRR energy. **Other published parameters can be inputs or targets** |
| Publication | Monthly. A **preliminary** list first, a **final** list later. Use final values when available; analysing the differences is part of the task |
| Inputs | Other balancing parameters (activated energy, ACE); HUPX and MEMO day-ahead prices (known the day before); crude oil, European gas, calendar events |
| t0 and horizon | Daily t0, **D+1 … D+2**, as if data were available up to t0 |
| S3 | Each newly published month |
| Goal | **Time-sensitive generalisation**: does the model still work next month? |

**The imbalance price has three parts.** A producer sells its forecast on the day-ahead
market. MEPSO settles the difference between actual and scheduled energy (the
**imbalance**) at one price per hour. That price is one of three published components; the
balancing energy MEPSO activated in that hour decides which one applies:

| Part | What it is | When it applies |
|---|---|---|
| **WAPpos** | Weighted average price of the **upward** aFRR + mFRR balancing energy activated in the hour | More upward than downward energy activated: the system was **short** |
| **WAPneg** | Weighted average price of the **downward** balancing energy activated in the hour | More downward than upward energy activated: the system was **long** |
| **VAA+ / VAA−** | Fallback price when **no** balancing energy was activated. VAA+ ≈ HUPX − 50 % for a surplus; VAA− ≈ HUPX + 50 % for a deficit | Net activated energy = 0 (about 10 % of hours) |

- "Positive" and "negative" describe the direction of the energy, not the sign of the price:
  every part can itself be negative.
- The dataset already combines the three parts, using the activated energy of each hour:
  - `imbalance_price_surplus_eur_per_mwh` is the price for more energy than scheduled.
  - `imbalance_price_deficit_eur_per_mwh` is the price for less energy than scheduled.
  - The two are equal in every WAPpos and WAPneg hour and differ only in VAA hours.
  - `imbalance_regime` (`wappos` / `wapneg` / `vaa`) says which part applied.
  - The columns use the final release when available, otherwise the preliminary one
    (`imbalance_price_version`).
  - The raw components and per-release columns are kept too.
- A natural approach is two models: one for the regime (will the system be short, long or
  neither?) and one for the price within each regime. VAA hours follow from a HUPX forecast.
- Dataset description, rule and coverage (2020–2026, 94.7 % of hours):
  [`datasets/mepso/README.md`](../datasets/mepso/README.md).

**Balancing and PV production.** MEPSO settles the imbalance of a **balancing group**
(the portfolio of one balance responsible party), not of a single plant. That links problem D
to problems A and B:

- **Several PV plants in one balancing group.** The group's imbalance is the sum of the
  plants' imbalances, so errors of different plants partly cancel. In WAPpos and WAPneg hours
  the price is the same for a surplus and a deficit, so the group's cost is simply the sum of
  the plants' costs. In VAA hours the **sign of the group's total** decides whether VAA+ or
  VAA− applies, so netting usually lowers the cost.
- **A single plant as its own balancing group** (the extreme case). Its own imbalance decides
  the VAA price, and the imbalance cost below is exactly what it pays.
- **Normalise per installed capacity** (kWh per kWp) when inverters or plants of different
  sizes are combined. One model can then forecast every inverter or plant, and a group's
  imbalance is rebuilt as Σ capacityᵢ × per-kWp errorᵢ. Report group costs per MWh produced.
- **PV errors and the system regime.** On sunny days the forecast errors of many PV plants
  add up and can push the whole system long or short. Whether the system is short or long
  (WAPpos or WAPneg) is then partly a weather and PV question: the regime forecast of problem D
  is a natural extension of problems A and B.

### E. Your own dataset

Allowed if it has:

- [ ] several years of data, at a granularity and size comparable to the problems above;
- [ ] multiple covariates, and external data that can be used for enrichment;
- [ ] a well-defined target and at least two horizons;
- [ ] a test that is **time-based**, **leaves out subjects** (sites, plants, markets), or both;
- [ ] simple baselines that can be evaluated.

Good source of ideas: [ENTSO-E power statistics](https://www.entsoe.eu/data/power-stats/)
(load and generation per country), the ENTSO-E Transparency Platform, Elia open data,
pulse.eco air quality.

---

## 5. Baselines (you must report them)

| Baseline | Forecast for every horizon step |
|---|---|
| **Naive** (t−1) | The last observed value |
| **Seasonal naive** | The value one season earlier: same time yesterday (PV), same hour last week (prices) |
| **SMA** | Mean of the last k values (or of the same time over the last k days) |
| **EMA** | Exponentially weighted mean, smoothing α chosen on S1 |

Intervals for a baseline: empirical 10 % and 90 % quantiles of its errors on S1, per horizon.

---

## 6. Metrics

**Point forecasts**

| Metric | Use |
|---|---|
| **MASE** (primary) | MAE divided by the in-sample MAE of the seasonal naive forecast. Scale-free: compares inverters, plants and markets of different size. Below 1 beats seasonal naive |
| MAE | Error in the original unit (kWh, EUR/MWh) |
| RMSE | Penalises large errors (cloud fronts, price spikes) |
| Skill vs seasonal naive | 1 − MAE / MAE of seasonal naive on the same test period |

**Prediction intervals (80 %)**

| Metric | Use |
|---|---|
| **Coverage** | Share of actual values inside [y_lo80, y_hi80]; should be close to 80 % |
| Width | Mean width of the interval; narrower is better **at the right coverage** |
| **Winkler score** | Width + (2/0.2) × distance by which the actual falls outside the interval; lower is better |

**Imbalance cost (PV problems A and B; also E for producers)**

What a forecast error costs a producer in EUR. The producer sells its forecast `F` at the
day-ahead price `P`. The imbalance `I = actual − F` is settled at the imbalance price `C`
(problem D). Compared with a perfect forecast, each hour costs:

```
cost = −I × (C − P)      C = imbalance_price_surplus if I > 0, imbalance_price_deficit if I < 0
```

- **Units:** `I` in MWh (convert kWh), prices in EUR/MWh.
- **`P`** is the HUPX day-ahead price for the hour; **`C`** comes from the MEPSO imbalance
  price columns. Both are provided with the data.
- **Sign:** positive means a loss; a perfect forecast costs 0. A cost can be negative when an
  error happens to help the system.
- **Which hours:** the hours of the next day (D+1), i.e. **lead 24–48 h** from t0 = 00:00.
  That is the day a real producer schedules.
- **Report** the total in EUR and **EUR per MWh produced**, so that inverters and plants of
  different sizes can be compared. Lower is better.
- **Reference:** the real day-ahead schedules of one 975 kW PV plant cost **4.81 EUR per MWh
  produced** over January–October 2026 (8,746 EUR for 1,818 MWh). That figure uses the plant's
  own sale prices; its settlement data are not distributed. The imbalance price minus the
  day-ahead price averaged about +78 EUR/MWh when the system was short and −75 when it was long.
- **Balancing groups:** the formula assumes the plant is its own balancing group. For several
  plants in one group, sum their imbalances per hour first (problem D).
- The metric uses `y_pred` only. It is reported next to MASE, not instead of it: it
  rewards being right when imbalance is expensive. Do not bias forecasts on purpose to bet on
  the system's direction.

**General rules**

- Report every metric **per horizon** (e.g. hours 1–24 and 25–48, or per day).
- PV: also MAE normalised by capacity (nMAE), and the imbalance cost.
- **No MAPE**: PV is zero at night, and prices and balancing values can be zero or negative.

---

## 7. Grading

| Component | Weight |
|---|---|
| Correct setup (no leakage), baselines, validation | 20 % |
| S2 results and presentation | 25 % |
| Hold-out H and S3: generalisation to unseen series and over time (points and intervals) | 30 % |
| Reproducibility: code runs unchanged on S3 | 15 % |
| Report | 10 % |
| Optional tasks | bonus |

---

## 8. Optional tasks (bonus)

- **Ensembles of forecasts**: combine the **forecasts** of different models, yours or other
  students' for the same problem (all code and predictions are in the common repository):
  mean, median, or weights from S2 errors. This means combining finished forecasts, not using
  an ensemble learner such as XGBoost or a random forest as your model.
- **Paper**: write a conference or journal paper, in parallel with the challenge.
- **Beyond forecasting**: e.g. anomaly detection on inverters (underperforming strings,
  frozen sensors, outages).

---

## 9. Resources

[resources.md](resources.md): competitions and benchmarks (EnergyBench, Energy-Arena, Predico,
open-predico, epftoolbox, GEFCom), data sources, and how to evaluate forecasts properly.

Datasets ([overview](../datasets/README.md)):

- [SolarMagix PV data](../datasets/solarmagix/README.md): inverters and plants (problems A and B).
- [MEPSO balancing data](../datasets/mepso/README.md): the imbalance price, activated aFRR and
  mFRR, ACE (problem D).
- [Day-ahead prices](../datasets/energy-prices/README.md): HUPX, MEMO, SEEPEX and neighbours,
  from Ember (problem C; `P` in the imbalance cost).
- [Load and generation](../datasets/energy-volumes/README.md): ENTSO-E power statistics, hourly
  load per country (problem C inputs, problem E).
