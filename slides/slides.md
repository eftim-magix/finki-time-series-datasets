---
marp: true
theme: finki
paginate: true
math: mathjax
footer: 'Introduction to Time Series Analysis · Forecasting challenge'
---

<style>
.part { position: absolute; top: 5px; left: 56px; font-size: 14px; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); }
.mid table { font-size: 20px; }
.mid th { padding: 5px 10px; }
.mid td { padding: 4px 10px; vertical-align: top; }
.card.small ul { margin: 0; }
.card.small li { margin: 0.12em 0; }
/* subset diagram */
.row { display: grid; grid-template-columns: 200px 1fr; gap: 12px; align-items: center; margin: 9px 0; }
.row .lbl { font-size: 20px; font-weight: 700; color: var(--finki-blue); line-height: 1.2; }
.row .lbl span { display: block; font-weight: 400; font-size: 16px; color: var(--ink2); }
.bar { display: flex; gap: 6px; height: 62px; }
.blk { border-radius: 6px; display: flex; flex-direction: column; justify-content: center; padding: 0 12px; font-size: 18px; line-height: 1.2; }
.blk b { font-size: 21px; }
.train { background: var(--finki-blue); color: #fff; }
.train b { color: #fff; }
.pred { background: var(--finki-light); color: #fff; }
.pred b { color: #fff; }
.hidden { background: #fff; border: 2px dashed var(--muted); color: var(--muted); }
.hidden b { color: var(--muted); }
/* t0 timeline */
.tl { display: flex; height: 64px; margin: 6px 0 4px 0; position: relative; }
.tl .past { flex: 1.25; background: var(--surface-2); border: 2px solid var(--finki-blue); border-radius: 6px 0 0 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: var(--finki-blue); font-weight: 600; }
.tl .fut { flex: 1; background: #f5f3fc; border: 2px solid #4a3aa7; border-left: none; border-radius: 0 6px 6px 0; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #4a3aa7; font-weight: 600; }
.tl .t0 { position: absolute; left: 55.5%; top: -12px; bottom: -12px; width: 4px; background: #eb6834; }
.tl .t0::after { content: 't0'; position: absolute; top: -26px; left: -8px; font-size: 20px; font-weight: 700; color: #eb6834; }
.kv table { font-size: 19px; }
.kv th { padding: 4px 10px; }
.kv td { padding: 3px 10px; vertical-align: top; }
.kv td:first-child { font-weight: 700; color: var(--finki-blue); white-space: nowrap; }
pre { font-size: 17px; }
/* logos on the title and closing slides */
.logos { display: flex; align-items: center; gap: 56px; margin-bottom: 6px; }
.logos img { display: block; }
section.title .contact { margin-top: 22px; font-size: 21px; }
section.title .contact p { font-size: 21px; }
</style>
<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="logos">
<img src="../assets/finki-logo.jpg" alt="FINKI" style="height:96px">
<img src="../assets/magix-ai-logo.png" alt="Magix.AI" style="height:52px">
</div>

# Forecasting Challenge
### Energy time series: PV inverters and plants, electricity prices, balancing. One pipeline, forecasts with uncertainty, tested on data you have not seen

**Prof. Eftim Zdravevski**
eftim.zdravevski@finki.ukim.mk
Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University in Skopje, Macedonia
**Magix.AI** · [magix.ai](https://magix.ai)

---

<div class="part">Overview</div>

## The challenge in one slide

<div class="cols-3">
<div class="card small">

#### What
- Pick **one problem**: PV inverters, PV plants, electricity prices, balancing (MEPSO), or **your own dataset**
- Forecast from an origin **t0** over a **horizon window**, e.g. 24–48 h ahead
- Give a **prediction interval** with every forecast
- Individual work

</div>
<div class="card small">

#### How
- **S1** train, **S2** validate (targets given)
- **H**: hold-out files, targets withheld
- **S3**: data published **after** you freeze your code
- The **same Python code** runs on all of them, from a **common GitHub** repository

</div>
<div class="card small">

#### Goal: generalise
- **To unseen series** (H): other inverters, other plants, another exchange
- **Over time** (S3): newer data than you trained on
- **Beat simple baselines**, honestly: no information from after t0

</div>
</div>

<div class="note small">

Builds on: <b>L2</b> SMA, EMA · <b>L4</b> temporal splits, benchmarks, MAE / RMSE / MASE · <b>L6</b> prediction intervals, coverage · <b>L7</b> exogenous inputs · <b>L9</b> lag features, leakage, multi-step · <b>L10</b> known-future covariates.

</div>

---

<div class="part">Overview</div>

## Data subsets and timeline (tentative)

<div class="row">
<div class="lbl">Next week<span>core data released</span></div>
<div class="bar">
<div class="blk train" style="flex:2.6"><b>S1</b>train</div>
<div class="blk pred" style="flex:1.3"><b>S2</b>validate, targets given</div>
<div class="blk hidden" style="flex:1.7"><b>H</b>hold-out, no targets</div>
</div>
</div>

<div class="row">
<div class="lbl">December<span>presentation</span></div>
<div class="bar">
<div class="blk" style="flex:1; display:block; padding-top:8px; background: var(--surface-2); color: var(--ink);">Short presentation of your <strong>S2 results vs baselines</strong>, per horizon, with intervals</div>
</div>
</div>

<div class="row">
<div class="lbl">Mid-January<span>preliminary results</span></div>
<div class="bar">
<div class="blk train" style="flex:3.9"><b>S1 + S2</b>train and validate</div>
<div class="blk pred" style="flex:1.7"><b>H</b>forecast + code freeze</div>
</div>
</div>

<div class="row">
<div class="lbl">End of February<span>new unseen data</span></div>
<div class="bar">
<div class="blk train" style="flex:3.9"><b>S1 + S2</b>same frozen code, re-run by the instructor</div>
<div class="blk pred" style="flex:1.7"><b>S3</b>newly published period</div>
</div>
</div>

<div class="note small">

<b>H</b> tests unseen series (other inverters, plants, exchange); <b>S3</b> tests time: it does not exist yet when you freeze the code. The re-run trains on <b>S1 + S2 only</b>, never on H. Other external data (weather, fuels, ENTSO-E, …) you fetch yourself, with a script in your folder.

</div>

---

<div class="part">Overview</div>

## What is known at t0

<div class="tl">
<div class="past">past: measured values up to t0</div>
<div class="fut">future: forecasts and calendar only</div>
<div class="t0"></div>
</div>

<div class="cols">
<div class="small">

**Past inputs** (only up to t0)
- measured production, AC / DC current, voltage, inverter status
- measured plant weather: temperature, wind, irradiance
- actual prices, traded volumes, balancing values
- crude oil and gas prices (daily)

</div>
<div class="small">

**Future inputs** (known at t0 for the whole horizon)
- **weather forecasts** issued before t0, up to D+2
- calendar: weekday, holidays, events
- anything scheduled in advance

</div>
</div>

<div class="warn small">

<b>Leakage.</b> Measured weather of a plant predicts every inverter in that plant almost perfectly. After t0 use only the <b>forecast</b> weather, never measured weather or other inverters' production. Fit scalers, imputers and feature selection on the training part only.

</div>

---

<div class="part">Overview</div>

## Horizon window and prediction intervals

<div class="cols">
<div>

<svg viewBox="0 0 560 270" width="560" height="270" xmlns="http://www.w3.org/2000/svg" style="font-family:'Source Sans 3',sans-serif">
<line x1="20" y1="190" x2="545" y2="190" stroke="#7d7b76" stroke-width="1.5"/>
<polygon points="300,106 540,38 540,182 300,120" fill="#40adff" fill-opacity="0.25"/>
<polyline points="20,140 45,120 70,135 95,100 120,115 145,90 170,110 195,95 220,125 245,105 270,118 300,112" fill="none" stroke="#0300c0" stroke-width="3"/>
<polyline points="300,112 340,104 380,114 420,100 460,112 500,104 540,110" fill="none" stroke="#40adff" stroke-width="3" stroke-dasharray="7 5"/>
<line x1="300" y1="26" x2="300" y2="196" stroke="#eb6834" stroke-width="3"/>
<text x="300" y="18" text-anchor="middle" fill="#eb6834" font-size="17" font-weight="700">t0</text>
<text x="150" y="58" text-anchor="middle" fill="#0300c0" font-size="16">measured (past)</text>
<text x="430" y="30" text-anchor="middle" fill="#1d2126" font-size="16">80 % interval widens with the horizon</text>
<line x1="353" y1="212" x2="400" y2="212" stroke="#eb6834" stroke-width="7"/>
<text x="290" y="217" text-anchor="end" fill="#eb6834" font-size="16" font-weight="700">minimum: hours 16–30</text>
<line x1="380" y1="236" x2="460" y2="236" stroke="#0300c0" stroke-width="7"/>
<text x="290" y="241" text-anchor="end" fill="#0300c0" font-size="16">recommended: 24–48 h</text>
<line x1="380" y1="260" x2="540" y2="260" stroke="#0300c0" stroke-width="7"/>
<text x="290" y="265" text-anchor="end" fill="#0300c0" font-size="16">24–72 h, prices up to 7 days</text>
</svg>

</div>
<div class="small">

- The window does **not** have to start at t0: forecast at least **t+16 … t+30** hours (the day-ahead window)
- Try **longer windows**: 24–48 h, 24–72 h; prices up to D+7
- Every value gets an **80 % prediction interval** `[y_lo80, y_hi80]`
- The further ahead, the **wider** the interval should be. Too narrow = overconfident (low coverage); too wide = useless

<div class="def">

<b>How to get intervals:</b> empirical quantiles of validation errors per horizon (simplest) · quantile regression (e.g. LightGBM with quantile loss) · conformal prediction · model-based intervals (ARIMA, ETS).

</div>

</div>
</div>

---

<!-- _class: divider -->

# Part 1
### The problems: choose one

---

<div class="part">Problems</div>

## A. PV inverters

<div class="kv">

| | |
|---|---|
| Target | Energy produced per inverter, **5-min** (A1). Variants: aggregated to **15-min** (A2) or **1-hour** (A3) |
| Inverter inputs | AC or DC current, voltage, power, temperature, status, other inverter series (past) |
| Auxiliary | Plant weather up to t0 (past): temperature, wind, irradiance · forecast weather from t0 up to D+2 (future) |
| Train | Inverters from **several plants**. Sizes differ: normalise (e.g. per kWp) or use scale-free metrics |
| Hold-out H | Other inverters of seen plants · **unseen plants** |
| S3 | Newer data of the same inverters and plants |
| t0 and horizon | Daily at 00:00; next **48 h** (at least hours 16–30); report hours 1–24 and 25–48 |
| Extra | Gaps, frozen sensors, outages, curtailment: part of the data |

</div>

<div class="note small">

Ideas: clear-sky irradiance and sun position as features (pvlib) · model the <b>clear-sky index</b> instead of raw power · one global model for all inverters vs one per inverter.

</div>

---

<div class="part">Problems</div>

## B. PV plants

<div class="cols">
<div>

- Target: **hourly production of the whole plant** (sum of its inverters)
- Same inputs as A, aggregated to the plant and the hour
- Hold-out H: **unseen plants**; S3: newer data
- Daily t0, next 48 h
- Smoother than single inverters: one inverter's outage is a small dip, not a zero

</div>
<div>

<div class="def">

<b>A or B?</b> A has more, noisier series and asks you to generalise to new inverters. B has few, smoother series and asks you to generalise to new plants. Both use the same weather forecasts.

</div>

<div class="note small">

Plants differ in size: compare them with MASE or with error per kWp of installed capacity, not with raw kWh.

</div>

</div>
</div>

---

<div class="part">Problems</div>

## C. Electricity prices

<div class="kv">

| | |
|---|---|
| Target | Day-ahead price, **hourly** (15-min less likely), **MEMO** (North Macedonia) and **HUPX** (Hungary), several years |
| Inputs (past) | Prices · **traded volumes** (MWh, hourly; normalise per exchange when combining) · actual weather · crude oil (daily) · European gas (daily) |
| Inputs (future) | Weather forecasts (first days only) · calendar events (holidays, weekends) |
| Validation | Step-wise (rolling-origin) or another time-based split |
| Hold-out H | **Another exchange**: correlated but different, less history |
| S3 | **Newer period**, published after the code freeze |
| t0 and horizon | Daily, before the day-ahead auction; **D+1 … D+7** (at least hours 16–30) |

</div>

<div class="warn small">

Prices can be <b>zero or negative</b> (sunny spring middays), and spike during scarcity. Do not use MAPE; look at RMSE for spikes.

</div>

---

<div class="part">Problems</div>

## D. Balancing (MEPSO): imbalance price, aFRR, mFRR

<div class="cols">
<div class="small">

- Targets: the hourly **imbalance price** (next slide) or activated **aFRR / mFRR** energy; other published parameters can be **inputs or targets**
- Published **once a month**: a **preliminary** list first, a **final** list later
- Use final values when available; **analyse the differences** between preliminary and final
- Same auxiliary data: crude oil, European gas, calendar events
- **Daily t0, D+1 … D+2**, as if data were available up to t0
- S3: each **newly published month**

</div>
<div>

<div class="def">

<b>aFRR / mFRR</b>: automatic and manual <b>frequency restoration reserves</b>, the energy the system operator activates to keep supply and demand balanced. <b>Imbalance</b>: actual minus scheduled energy of a market party, settled at the <b>imbalance price</b>.

</div>

<div class="note small">

Goal: <b>time-sensitive generalisation</b>. A model trained on data up to month M must still work in month M+1, M+2. Very different from day-ahead prices.

</div>

</div>
</div>

---

<div class="part">Problems</div>

## D. The imbalance price has three parts

<div class="mid">

| Part | What it is | Applies when |
|---|---|---|
| **WAPpos** | Weighted average price of the **upward** aFRR + mFRR energy activated in the hour | More upward than downward energy activated: system **short** |
| **WAPneg** | Weighted average price of the **downward** energy activated in the hour | More downward energy activated: system **long** |
| **VAA+ / VAA−** | Fallback: VAA+ ≈ HUPX − 50 % for a **surplus**, VAA− ≈ HUPX + 50 % for a **deficit** | **Nothing** activated (≈ 10 % of hours) |

</div>

<div class="cols">
<div class="small">

- The dataset combines the parts into `imbalance_price_surplus` and `imbalance_price_deficit` (EUR/MWh). They are equal except in VAA hours
- `imbalance_regime` says which part applied
- Final release if available, else preliminary · 2020–2026, 94.7&nbsp;% of hours

</div>
<div class="note small">

Idea: forecast the <b>regime</b> (short / long / none), then the <b>price</b> within it. "Positive" and "negative" are directions, not signs: every part can be negative.

</div>
</div>

---

<div class="part">Problems</div>

## D meets A and B: balancing groups

<div class="cols">
<div class="small">

MEPSO settles the imbalance of a **balancing group** (the portfolio of one market party), not of each plant.

- **Several PV plants, one group**: imbalances add up and partly cancel
  - WAPpos / WAPneg hours: one price, so the group's cost = the sum of the plants' costs
  - VAA hours: the **sign of the group's total** picks VAA+ or VAA−, so netting usually lowers the cost
- **One plant = one group** (the extreme case): its own sign decides; the imbalance cost metric is exactly what it pays

</div>
<div class="small">

<div class="def">

<b>Normalise per installed capacity.</b> Forecast kWh per kWp, so that one model serves inverters and plants of any size. The group's imbalance is then rebuilt from the per-kWp errors:

</div>

$$I_{\text{group},t}=\sum_i c_i\left(y_{i,t}-\hat y_{i,t}\right)$$

with $c_i$ the capacity (kWp) and $y_{i,t}$, $\hat y_{i,t}$ per kWp. Compare groups in EUR per MWh produced.

<div class="note">

On sunny days the errors of many PV plants can push the <b>whole system</b> long or short: forecasting the regime with weather and PV forecasts links D to A and B.

</div>

</div>
</div>

---

<div class="part">Problems</div>

## E. Your own dataset

<div class="cols">
<div>

A dataset is accepted if it has:

- **several years** of data, granularity and size comparable to A–D
- **multiple covariates**, and **external data** for enrichment
- a **well-defined target** and at least two horizons
- a test that is **time-based**, **leaves out subjects** (sites, plants, markets), or both
- **simple baselines** that can be evaluated

</div>
<div>

<div class="card small">

#### Where to look
- **ENTSO-E power statistics**: entsoe.eu/data/power-stats (load and generation per country)
- ENTSO-E Transparency Platform: prices, load, generation forecasts
- Elia (Belgium): solar and wind with official forecasts
- Skopje air quality (pulse.eco) with weather forecasts

</div>

<div class="note small">

Send a one-paragraph proposal by the end of week 1: target, inputs, horizons, how S1 / S2 / H / S3 are split.

</div>

</div>
</div>

---

<!-- _class: divider -->

# Part 2
### Evaluation: baselines, metrics, validation

---

<div class="part">Evaluation</div>

## Baselines: every model must beat them

<div class="mid">

| Baseline | Forecast for step $h$ after $t_0$ | Typical use |
|---|---|---|
| **Naive** ($t-1$) | $\hat y_{t_0+h} = y_{t_0}$ | Slow series, balancing parameters |
| **Seasonal naive** | $\hat y_{t_0+h} = y_{t_0+h-km}$, the same time one season earlier | PV: yesterday ($m$ = 1 day) · prices: last week ($m$ = 168 h) |
| **SMA** | $\hat y_{t_0+h} = \frac1k \sum_{j=0}^{k-1} y_{t_0-j}$ | Smooth level; for PV take the same time of day over the last $k$ days |
| **EMA** | $\ell_t = \alpha y_t + (1-\alpha)\ell_{t-1}$, $\hat y_{t_0+h} = \ell_{t_0}$ | Level that adapts; $\alpha$ chosen on S1 |

</div>

<div class="say">

$m$ = steps per season: 288 (5-min, one day), 96 (15-min), 24 (hourly, one day), 168 (hourly, one week). $k$ = how many seasons back, so that the value is known at $t_0$. For PV use the <b>seasonal</b> versions (one per time of day). Baseline intervals: the 10 % and 90 % quantiles of its errors on S1, per horizon.

</div>

---

<div class="part">Evaluation</div>

## Metrics: point forecasts

<div class="cols">
<div>

$$\text{MASE}=\frac{\frac1H\sum_{h=1}^{H}\left|y_{t_0+h}-\hat y_{t_0+h}\right|}{\frac{1}{n-m}\sum_{t=m+1}^{n}\left|y_t-y_{t-m}\right|}$$

<div class="say">

<b>Primary.</b> Your error divided by the error of the seasonal naive forecast on the training data. Scale-free: compares a 50 kW inverter with a 5 MW plant, MEMO with HUPX. Below 1 beats seasonal naive.

</div>

</div>
<div class="small">

- **MAE**: error in the original unit (kWh, EUR/MWh)
- **RMSE**: penalises large errors: cloud fronts, price spikes
- **Skill** vs seasonal naive on the test period: $1 - \text{MAE}/\text{MAE}_{\text{snaive}}$
- PV: also **nMAE** = MAE / installed capacity
- Report every metric **per horizon**: e.g. hours 1–24 and 25–48, or per day

<div class="warn">

<b>No MAPE.</b> PV is zero at night; prices and balancing values can be zero or negative: percentage errors explode or are undefined.

</div>

</div>
</div>

---

<div class="part">Evaluation</div>

## Metrics: prediction intervals

<div class="cols">
<div>

$$W_\alpha = (u-\ell) + \frac{2}{\alpha}(\ell-y)\,\mathbb 1[y<\ell] + \frac{2}{\alpha}(y-u)\,\mathbb 1[y>u]$$

<div class="say">

<b>Winkler score</b> of an interval $[\ell, u]$ with $\alpha = 0.2$ (80 %): its width, plus a penalty of $2/\alpha = 10$ times the distance by which the actual value falls outside. Lower is better: rewards intervals that are narrow <b>and</b> contain the actual value.

</div>

</div>
<div class="small">

- **Coverage**: share of actual values inside $[\ell, u]$. Target: **80 %**
  - well below 80 %: overconfident
  - well above 80 %: too cautious, intervals too wide
- **Width**: mean $u-\ell$, per horizon. Should **grow** with the horizon
- Report coverage, width and Winkler **per horizon**, next to the point metrics

<div class="note">

A plot of coverage and width against the horizon tells more than one number.

</div>

</div>
</div>

---

<div class="part">Evaluation</div>

## Metrics: imbalance cost (PV)

<div class="cols">
<div>

$$\text{cost}=\sum_{t\,\in\,D+1}-\left(y_t-\hat y_t\right)\left(C_t-P_t\right)$$

<div class="say">

What the forecast error costs a producer, in EUR.

- It sells $\hat y_t$ at the day-ahead price $P_t$ (HUPX).
- The imbalance $y_t-\hat y_t$ is settled at the imbalance price $C_t$: the **surplus** price if $y_t>\hat y_t$, the **deficit** price otherwise.
- A perfect forecast costs 0.

</div>

</div>
<div class="small">

- Hours of the **next day** (lead 24–48 h from t0 = 00:00), energy in **MWh**
- Report **EUR per MWh produced**, so that sizes compare; lower is better
- Can be negative: an error that helps the system earns money
- Reported **next to MASE**, not instead of it. Do not bias forecasts to bet on the system's direction

<div class="note">

Reference: the real day-ahead schedules of a 975 kW PV plant cost <b>4.81 EUR per MWh</b> produced (Jan–Oct 2026). $C-P$ is about +78 EUR/MWh when the system is short and about −75 when it is long.

</div>

</div>
</div>

---

<div class="part">Evaluation</div>

## Validation inside S1: rolling origins

<div class="cols-wide-left">
<div>

```
origin 1: [======= train =======]t0[ h=1 … H ]
origin 2: [========= train =========]t0[ h=1 … H ]
origin 3: [=========== train ===========]t0[ h=1 … H ]
origin 4: [============= train =============]t0[ h=1 … H ]
```

- Many origins, covering all seasons
- Retrain every origin, or every $k$ origins
- Score every horizon step, then average per horizon
- Calibrate intervals on validation errors, not training errors

</div>
<div>

<div class="def">

<b>Leave-subjects-out</b> imitates H: train on some inverters, plants or markets, validate on <b>others</b>. For prices: train on MEMO, validate on HUPX (or the other way round).

</div>

<div class="note small">

Your validation should look like the test: if H has unseen plants, your validation needs unseen plants too.

</div>

</div>
</div>

---

<!-- _class: divider -->

# Part 3
### Code, timeline, grading

---

<div class="part">Logistics</div>

## Code: one command, one repository

<div class="cols">
<div>

Python, dependencies pinned in `requirements.txt`:

```bash
python run.py --train data/S1 data/S2 \
              --test  data/H \
              --out   predictions_H.csv
```

The same command with `--test data/S3` at the end of February.
One row per forecast value, with the interval:

```
series_id,origin,timestamp,lead_h,y_pred,y_lo80,y_hi80
inv_017,2026-12-14T00:00,2026-12-15T12:00,36.0,4.21,2.95,5.10
```

</div>
<div class="small">

**Common GitHub repository**
- One folder per student: `run.py`, `requirements.txt`, `README.md`, data download scripts, report
- Everyone can **read** everyone's code
- **Code freeze mid-January**: tag your commit; that commit is re-run on S3
- Fixed random seeds; no internet access needed when predicting
- Scoring script is shared: run it on S2 yourself

</div>
</div>

---

<div class="part">Logistics</div>

## Timeline and grading

<div class="cols">
<div>

<div class="mid">

| When (tentative) | What |
|---|---|
| Next week | Core datasets: S1, S2, H |
| End of week 1 | Problem chosen · own-dataset proposal |
| December | **Presentation** of S2 results |
| **Mid-January** | **H forecasts + code freeze** |
| **End of February** | **S3** re-run: final results |
| In parallel | Paper, ensembles, anomalies |

</div>

</div>
<div>

<div class="mid">

| Component | Weight |
|---|---|
| Setup without leakage, baselines, validation | 20 % |
| S2 results and presentation | 25 % |
| **H + S3: generalisation** (points and intervals) | 30 % |
| Reproducibility: runs unchanged on S3 | 15 % |
| Report | 10 % |
| Optional tasks | bonus |

</div>

</div>
</div>

---

<div class="part">Logistics</div>

## Optional tasks

<div class="cols-3">
<div class="card small">

#### Ensembles of forecasts
- Combine the **forecasts** of different models, yours or other students' (all code and predictions are shared)
- Mean, median, or weights from S2 errors
- Not an ensemble **learner** (XGBoost, random forest): combine finished forecasts

</div>
<div class="card small">

#### Paper
- Write a **conference or journal paper**, in parallel with the challenge
- Strong candidates: generalisation to unseen plants, preliminary vs final balancing data, ensembles across many models

</div>
<div class="card small">

#### Beyond forecasting
- **Anomaly detection** on inverters: underperforming strings, frozen sensors, outages, clipping
- Compare an inverter with its neighbours in the same plant: they share the weather

</div>
</div>

---

<div class="part">Logistics</div>

## Where to start

<div class="cols">
<div class="small">

#### Read
- **EnergyBench methodology** (energybench.foretec.co): forecasts made at a fixed time, inputs frozen at that time, errors relative to a naive forecast
- **epftoolbox** (Lago et al., 2021): price forecasting benchmark, LEAR model, metrics
- **open-predico** (GitHub): inputs tagged *past* or *future*, rolling backtests, quantile forecasts
- **Predico**, **Energy-Arena**: live forecasting, ensembles of many forecasters

</div>
<div class="small">

#### Do, in this order
1. Load S1, plot a few series, find gaps and outliers
2. Write the evaluation loop: origins, horizon windows, metrics
3. Score the four baselines, with intervals
4. Add weather forecasts and other covariates (L7, L9)
5. Try one ML or deep model (L9, L10)
6. Validate the way H and S3 test: unseen series, newer data

</div>
</div>

<div class="note small">

Everything is in one repository: <code>challenge/</code> (texts, resource guide), <code>datasets/</code> (data, download scripts, READMEs), <code>slides/</code>. External data: Open-Meteo (weather), ENTSO-E Transparency Platform, FRED (oil), gas price feeds.

</div>

---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="logos">
<img src="../assets/finki-logo.jpg" alt="FINKI" style="height:80px">
<img src="../assets/magix-ai-logo.png" alt="Magix.AI" style="height:44px">
</div>

# Questions and contact

**Prof. Eftim Zdravevski** · eftim.zdravevski@finki.ukim.mk
Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University in Skopje
**Magix.AI** · [magix.ai](https://magix.ai)

<div class="contact">

**Materials and datasets:** [github.com/eftim-magix/finki-time-series-datasets](https://github.com/eftim-magix/finki-time-series-datasets)

**Using the PV data? Please cite:** Daskalov, A., Dimitrova, M., Atanasovska, T., Lameski, P., Risteska Stojkoska, B., Zdravevski, E. (2026). SolarMagix: An integrated multi-station photovoltaic and weather dataset for solar energy forecasting, fault detection, and anomaly analysis. *Data in Brief*, 67, 112830. doi:10.1016/j.dib.2026.112830

</div>
