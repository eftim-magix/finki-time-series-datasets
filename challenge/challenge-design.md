# Course challenge: design proposal (draft)

**Status:** design decisions taken (section 0). Student-facing text drafted in
[challenge-description.md](challenge-description.md); details still open are in section 9
and marked **[TBD]** there.
Background on metrics, splits, leakage and the live benchmarks this design borrows from
(EnergyBench, Energy-Arena, Predico, open-predico): [resources.md](resources.md).

## 0. Decisions

| # | Topic | Decision | Consequence for the design |
|---|---|---|---|
| 1 | Participants | **40 students, individual work** | 40 submissions split over tracks; enough members for a class ensemble per track |
| 2 | Scope | **Each student chooses one track**: PV, prices, or an approved own dataset | Anomaly detection is a **bonus** for PV students |
| 3 | Duration | **4 weeks** of development on the **validation / leaderboard** set; **hold-out predictions submitted in the same 4 weeks, scores hidden** until the end | Leaderboard = feedback; hold-out = final ranking (section 3.3, 4.3) |
| 4 | Hold-out | **Overlapping time period, different plants / inverters / markets** | Requires episode design with non-overlapping time slots (PV) and a code re-run check (prices, public data) |
| 5 | Live forecasts | **Bonus**, scope to be agreed with students | Optional daily rounds after week 4 (section 8) |
| 6 | PV leaderboard semantics | **Forecasting**, not estimation | Split **by plant**; forecast irradiance only; hidden dates (section 3.3) |
| 7 | Weather forecasts | **Open-Meteo Single Runs API, ECMWF IFS HRES 9 km, 00 UTC run** | Full runs by init time from **2024-03-14**, 15 days long: forecasts exactly as available at issue time. Hourly radiation interpolated to 15 min with one fixed rule |
| 8 | Horizons | **D+1 … D+5** | IFS covers 15 days, so D+6 … D+7 can be added later without new data |
| 9 | PV data | **3–5 plants, 20–100 inverters**, anonymised, no NDA, daily export available | Anonymous ids, no coordinates (solar geometry columns instead), power per kWp |
| 10 | Anomaly labels | **Partial logs** | Synthetic fault injection for scoring; real logged events as a separate recall check |
| 11 | Price markets and source | Target **MK**; hold-out **HU (HUPX)** and **RS (SEEPEX)**; all prices from **ENTSO-E** | One consistent, attributable source |
| 12 | Price resolution | **Hourly mean** of quarter-hour prices where 15-min MTU exists (HU since 1 Oct 2025) | Same rule for all markets and all periods |
| 13 | Fuel prices | **Free daily sources** (Brent from FRED, TTF from a free market feed) | Only values **published by issue time** may be used (FRED Brent arrives days late) |
| 14 | Forecast type | **Q50 required**; **Q10/Q90 bonus** | Point board (MAE, Rel. MAE) + separate probabilistic board (Winkler) |
| 15 | Platform | **Hugging Face**: private datasets + Space with leaderboard (open-predico style) | Hugging Face Competitions provides public/private boards on top of this (section 8) |
| 16 | Compute | **No limits** | Foundation models and deep learning allowed; inference script must still run for the check in decision 4 |
| 17 | Ensemble | **Optional bonus** | Students opting in submit validation-set forecasts |
| 18 | Bring your own | **Allowed; proposal by end of week 1** | Checklist in section 7 |

---

## 1. Learning goals

1. State a forecasting task precisely: issue time, horizon, resolution, information set.
2. Build a leakage-free rolling-origin evaluation and beat honest benchmarks.
3. Use multivariate inputs correctly: **past** covariates (measurements, fuel prices) vs
   **future** covariates known at issue time (weather forecasts, calendar, solar geometry).
4. Forecast several horizons (D+1 … D+5) and explain how error grows with lead time.
5. Generalise to unseen plants, inverters and markets.
6. (Bonus) Detect anomalies, produce quantiles, contribute to an ensemble, forecast live.

---

## 2. Tracks and common timing

| Track | Target | Resolution | Horizons | Main inputs |
|---|---|---|---|---|
| **A. PV inverters** | Inverter energy, kWh per kWp | 15 min | D+1 … D+5 | Inverter DC current/voltage, AC power, temperatures, status; plant measured irradiance (past only); IFS forecast irradiance, cloud cover, temperature; solar geometry; capacity |
| **B. Day-ahead prices** | Price, EUR/MWh (hourly mean) | 1 h | D+1 … D+5 | Past prices (MK, HU, RS and neighbours), ENTSO-E load and RES forecasts, IFS weather for ~6 MK locations, TTF, Brent, calendar and holidays |
| **C. Own dataset** | Student-defined | ≤ 1 h or comparable size | ≥ 2 horizons | Multivariate |

**Gate-aligned timing** (EnergyBench practice):

- **Issue time:** 10:00 CET/CEST on day D0, before the day-ahead auction for D+1
  (confirm MEMO's gate time).
- **Weather:** the IFS **00 UTC** run of D0 (published 4–6 h after initialisation). No later runs.
- **Forecast window:** calendar days D+1 … D+5, local time.
- **Inputs frozen at issue time** and stored per origin, so every forecast is reproducible.

---

## 3. Track A — PV inverters

### 3.1 Data package

| File | Tag | Content |
|---|---|---|
| `inverters.csv` | static | Anonymous inverter id, anonymous plant id, rated AC kW, DC kWp, MPPTs/strings, fixed or tracker, tilt/azimuth class |
| `train/inverter_measurements.parquet` | past | Timestamp (UTC), inverter id, AC energy per 15 min (**target**), AC power, DC current and voltage per MPPT, inverter temperature, status/alarm code |
| `train/plant_measurements.parquet` | past | Measured GHI/POA irradiance, module and ambient temperature, wind |
| `train/nwp_ifs.parquet` | future | **Init time**, valid time, plant id: GHI, DNI, DHI, GTI (plant tilt/azimuth), cloud cover, temperature, wind |
| `train/solar_geometry.parquet` | future | Sun elevation/azimuth, clear-sky GHI and POA (pvlib), per 15 min |
| `train/flags.parquet` | past | Known curtailment, outages, maintenance |
| `leaderboard/episode_*/`, `holdout/episode_*/` | — | Episodes (section 3.4) |

Gaps stay as they occur in SCADA. A data dictionary documents units and how 15-min energy
is integrated.

### 3.2 Task A1: forecasting

- **Forecast:** all 15-min steps of D+1 … D+5 (480 values per inverter per origin), Q50
  required, Q10/Q90 optional.
- **Not allowed:** measured irradiance or other inverters' measurements inside the forecast
  window; weather runs later than 00 UTC of D0.
- **Scoring mask:** daylight steps (sun elevation > 5°), actual present, no known
  curtailment/outage. Same mask for every submission.
- **Metrics:**
  - primary **Rel. MAE** = MAE / MAE of baseline B0 on the same steps, per inverter, then
    geometric mean over inverters (skill = 1 − geometric mean);
  - also nMAE (MAE / DC kWp), nRMSE, error of daily energy (WAPE), per horizon day;
  - quantile bonus: Winkler score of [Q10, Q90] (α = 0.2) and 80 % coverage.
- **Baselines provided:** B0 last full day's profile repeated; B1 clear-sky persistence;
  B2 linear regression on IFS GTI; B3 LightGBM with IFS + geometry features.

### 3.3 Splits: same period, different plants

```
                 2024-03-14 ─────────── T₁ ─────────────────── T₂
training plants  [ measurements released ][ withheld (only inside hold-out episodes) ]
plant D          [      not released     ][ LEADERBOARD episodes                     ]
plant E (+ D')   [      not released     ][ HOLD-OUT episodes (scores hidden)        ]
```

| Set | Plants / inverters | Period | Purpose |
|---|---|---|---|
| Training | Plants A, B (, C), all inverters | 2024-03-14 → T₁ | Model building; students cut their own validation folds |
| **Validation / leaderboard** | Plant D | T₁ → T₂ (e.g. 2026-01 → 2026-10), episodes, hidden dates | Feedback during the 4 weeks |
| **Hold-out** | Plant E + reserved inverters of D + training plants | Same slots as the leaderboard, episodes, hidden dates | Final ranking; scores hidden until the end |

With only 3 plants: A train, B leaderboard (half of its inverters), C + other half of B hold-out.

**Leakage rules for an overlapping period.** All plants in Macedonia share regional weather.
If any measurement from T₁ → T₂ were released outside the episodes, a student could find the
date of a hold-out episode (by matching its IFS forecast) and read the real cloudiness from a
neighbouring plant. Therefore:

1. No measurements after T₁ are released except inside episode context windows.
2. Episodes use a **common schedule of origins** for all plants, spaced so that no episode's
   forecast days fall inside any other episode's context window: with a 7-day context and
   D+1 … D+5, origins at least 13 days apart → ~23 origins in 10 months, times all
   leaderboard and hold-out inverters.
3. Dates and coordinates are hidden; episode order is shuffled.

### 3.4 Episode format

```
episode_017/
  context.parquet   last 7 days of measurements (inverter + plant), relative index,
                    step 0 = issue time
  future.parquet    IFS 00 UTC run of D0 and solar geometry for D+1 … D+5; day-of-week
  meta.json         inverter kWp, plant type, anonymous ids; NO date, NO coordinates
```

Solar geometry and clear-sky irradiance carry the season, so the calendar date is not needed.

### 3.5 Bonus A2: anomaly detection

- **Data:** a separate file of inverter-days from training plants. Some contain injected
  faults (string loss = −1/n of DC current, soiling drift, clipping, frozen telemetry,
  shading at fixed hours, pyranometer drift, timestamp shift), some contain real logged events.
- **Submission:** anomaly score and flag per **inverter-day**.
- **Metrics:** event-level F1 and PR-AUC on injected faults; recall on real logged events
  (logs are incomplete, so no precision there). No point-adjust.

---

## 4. Track B — Day-ahead prices

### 4.1 Data package

| File | Tag | Content |
|---|---|---|
| `prices.parquet` | past | Hourly day-ahead prices from ENTSO-E: MK (target), auxiliary BG, GR, RO, … up to T₁ |
| `system.parquet` | past / future | Load actual (past); day-ahead and week-ahead load forecasts, wind/solar day-ahead forecasts (future, only if published before 10:00); generation per type, cross-border flows (past) |
| `weather_ifs.parquet` | future | Init time, valid time, location: temperature, GHI, wind, precipitation for ~6 MK locations |
| `fuels.parquet` | past | Daily TTF and Brent with **value date and publication date** |
| `calendar.parquet` | future | Weekday, public holidays per country, DST flags |
| `leaderboard/`, `holdout/` | — | Origins with frozen inputs (section 4.3) |

### 4.2 Task B1: forecasting

- **Forecast:** hours of D+1 … D+5 (120 values per origin), Q50 required, Q10/Q90 optional.
- **Information set at 10:00 on D0:** prices to the end of D0; load and RES forecasts
  published by 10:00 (ENTSO-E RES forecasts exist only for D+1, so D+2 … D+5 must come from
  weather forecasts); fuel values published by 10:00; calendar.
- **Metrics:** primary **Rel. MAE vs `naive_weekly`** (same hour one week earlier), pooled
  per market, geometric mean across markets; also MAE (EUR/MWh) and RMSE (spikes), per
  horizon day. Winkler score for the quantile bonus. No MAPE (zero and negative prices).
- **Baselines provided:** naive_weekly; EPF naive (yesterday for Tue–Fri, last week
  otherwise); LEAR (epftoolbox); LightGBM with lags, calendar, fuels.

### 4.3 Splits and the public-data problem

| Set | Market | Period | Purpose |
|---|---|---|---|
| Training | MK (from 2023-05-10) + auxiliary markets | → T₁ | Model building |
| **Validation / leaderboard** | MK | T₁ → T₂, origins with frozen inputs | Feedback |
| **Hold-out** | HU, RS (weather from HU/RS locations) | Same origins as the leaderboard | Final ranking; scores hidden |

Prices are public on ENTSO-E, so hiding dates does not protect the hold-out: 7 days of
context prices or a single TTF value identify the date. Integrity therefore comes from:

1. **Code + model artefacts submitted with the CSV** (`predict.py`, environment file, saved
   model). The instructor re-runs inference on the hold-out inputs; predictions must match
   the CSV within a small tolerance. A mismatch means no hold-out score.
2. Dates stay **visible** in the price track (holidays and fuel alignment need them).
3. An explicit rule: using actual prices of the forecast window from any source is
   disqualifying.

### 4.4 Data facts

- **MEMO** started on 10 May 2023 → ~3.5 years of MK history, illiquid at first. Auxiliary
  markets give longer history.
- **15-min MTU in SDAC since 1 Oct 2025**: HU hourly target = mean of four quarter-hours.
- Confirm MK and RS day-ahead price coverage on ENTSO-E before release.

---

## 5. Generalisation

| Level | PV | Prices | Set |
|---|---|---|---|
| G0 | Training plants, later period | — | Hold-out |
| G1 | Unseen plant D, same period | MK, later period | Leaderboard |
| G2 | Unseen plant E | HU, RS | Hold-out |
| G3 | Live days | Live days | Bonus |

**Final score** = skill on the hold-out (1 − geometric-mean Rel. MAE), with G0 and G2
reported separately. The gap between leaderboard and hold-out skill is shown as a diagnostic.
The instructor adds a zero-shot foundation model (Chronos-Bolt, TimesFM or
[Yug](https://huggingface.co/birlaailabs/yug)) as a reference row.

---

## 6. Ensemble bonus (after Predico and EnergyBench)

1. Students who opt in submit forecasts for a common **ensemble-validation** set
   (out-of-sample rolling origins before T₁) plus their leaderboard and hold-out forecasts.
2. Per track the instructor builds: **median** of members; **skill-weighted mean** with
   weights from validation errors (Predico); a stacked combination fitted on validation only.
3. Contribution of student i: `Δᵢ = loss(ensemble without i) − loss(ensemble)` on the
   hold-out. Positive Δ earns the bonus, which rewards diverse models.
4. The ensemble appears on the boards as a reference row, not ranked.

---

## 7. Own dataset (Track C): acceptance checklist (proposal by end of week 1)

- [ ] At least 3 years of data, or at least ~20 000 time steps at hourly or finer resolution.
- [ ] Multivariate: at least 2 inputs beside the target, including at least one **future**
      covariate (forecast, calendar, schedule) with a known vintage.
- [ ] Well-defined target, unit, issue time and at least 2 horizons.
- [ ] Objective test on unseen data: a later period and another site, city or market; the
      student hands the hold-out targets to the instructor before modelling starts.
- [ ] Simple baselines beatable but not trivial (shown in the proposal).
- [ ] Licence allows course use; retrieval is scripted.

Examples: Elia (BE) PV/wind with official week-ahead forecasts; Predico's open targets
(Elia solar, 50Hertz wind/solar); ENTSO-E load for MK or neighbours; Skopje air quality
(pulse.eco) with IFS weather; district heating; EV charging.

---

## 8. Logistics

### Platform: Hugging Face

- **Data:** private Hugging Face datasets (gated: students accept course terms of use).
- **Submissions and boards:** Hugging Face Competitions (built on Spaces + private datasets:
  public board from one split, private board from another, custom metric script, daily
  submission limit), or a custom Gradio Space that writes uploads to a private dataset and
  renders a static leaderboard (open-predico dashboard style).
- **Boards:** PV point, PV quantile, prices point, prices quantile, anomaly (bonus).
  Leaderboard scores visible immediately; hold-out stored and scored, shown only at the end.
- **Limits:** e.g. 3 leaderboard submissions per day; the last hold-out file counts.

### Timeline (4 weeks + presentations)

| Week | Milestone |
|---|---|
| 0 | Release data, baselines, starter notebook, rules, own-dataset template |
| 1 | Own-dataset proposals approved; checkpoint: beat B0 on the leaderboard |
| 1–4 | Leaderboard open; hold-out submissions accepted (scores hidden) |
| 3 | Optional: ensemble-validation forecasts due |
| end of 4 | Final: leaderboard CSV, hold-out CSV, `predict.py` + model, report |
| 5 | Re-run check (prices); hold-out scores revealed; presentations; ensemble results |
| after 5 (bonus) | Live daily rounds, if agreed with students |

### Live rounds (bonus, to agree with students)

- Each working day at 10:00 CET the instructor publishes a frozen snapshot (PV measurements to
  issue time + IFS 00 UTC run; prices to end of D0, published forecasts and fuels). Deadline
  10:45. Daily SCADA export makes this possible for PV too.
- Missed day = 75th-percentile score of participants (Predico rule). Fewer than 12 scored days
  = provisional (EnergyBench rule). Intervals from a bootstrap over issue days.

### Grading sketch (individual)

| Component | Weight |
|---|---|
| Task definition and leakage-free evaluation (report) | 25 % |
| Leaderboard skill vs baselines (thresholds) | 10 % |
| **Hold-out skill vs baselines** (thresholds + rank) | 35 % |
| Reproducibility (code, re-run check, environment) | 20 % |
| Presentation | 10 % |
| *Bonuses (cap +15 %):* anomaly detection, Q10/Q90 quantiles, ensemble contribution, live rounds | each +5 % |

---

## 9. Remaining details

1. Share of the final course grade for the challenge.
2. Cut dates T₁ and T₂, and which plants go to training / leaderboard / hold-out (needs the
   plant list with data start dates).
3. MEMO gate closure time (to confirm the 10:00 issue time).
4. Grading thresholds (proposed in the description: below B0 → up to 10/35, beats B0 → 15,
   beats B2/LEAR → 22, beats B3/LightGBM → 28, top 5 → 35).
5. Course policy on AI coding assistants.
6. Calendar dates of weeks 0–5 and the Hugging Face link.

### Choices made while drafting the description (review)

- `predict.py` must run **offline**; the re-run check is mandatory for prices and done on a
  sample for PV.
- Re-run tolerance: 0.01 EUR/MWh per value.
- Missing rows are filled with the baseline (no disqualification).
- Report max 8 pages; presentation 5 + 3 minutes.
- Extra external data allowed for training only; at prediction time only provided inputs.
- Track A episodes: step 0 = issue time, 7-day context (steps −671 … 0), forecast rows
  tagged `horizon_day` 0 (not scored) to 5; D+1 starts at step 57.
