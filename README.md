<p>
  <img src="assets/finki-logo.jpg" alt="FINKI, Ss. Cyril and Methodius University in Skopje" height="64">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://magix.ai"><img src="assets/magix-ai-logo.png" alt="Magix.AI" height="36"></a>
</p>

# Energy forecasting challenge: datasets and materials

A self-contained forecasting challenge on **energy time series** from North Macedonia and its
region: PV inverters and plants, day-ahead electricity prices, and balancing (imbalance prices,
activated reserves). It belongs to the course **Introduction to Time Series Analysis** at the
Faculty of Computer Science and Engineering (FINKI), Ss. Cyril and Methodius University in
Skopje, and is run together with [Magix.AI](https://magix.ai).

This repository holds everything needed to take part: the challenge text and slides, the
datasets with their download and processing scripts, and a guide to evaluating forecasts.

## Start here

| | |
|---|---|
| **Slides** | [slides/forecasting-challenge-slides.pdf](slides/forecasting-challenge-slides.pdf) (HTML: [slides/forecasting-challenge-slides.html](slides/forecasting-challenge-slides.html), source: [slides/slides.md](slides/slides.md)) |
| **The challenge** | [challenge/simplified-challenge.md](challenge/simplified-challenge.md): problems, timeline, pipeline contract, baselines, metrics, grading |
| Detailed variant | [challenge/challenge-description.md](challenge/challenge-description.md); design notes in [challenge/challenge-design.md](challenge/challenge-design.md) |
| Background | [challenge/resources.md](challenge/resources.md): live benchmarks, past competitions, data sources, how to evaluate time series models without leakage |
| **Datasets** | [datasets/README.md](datasets/README.md): catalogue, folder layout and conventions |

## The challenge in brief

Pick **one problem**, build a pipeline that trains, validates and forecasts **with an 80 %
prediction interval**, and show that it generalises to series it has never seen (hold-out
**H**) and to data published after the code freeze (**S3**). The same `run.py` runs unchanged
on all subsets. Individual work; dates are tentative.

| Problem | Target | Data |
|---|---|---|
| **A. PV inverters** | Energy per inverter, 5-min / 15-min / hourly, next 48 h | [solarmagix](datasets/solarmagix/README.md) |
| **B. PV plants** | Hourly production of a whole plant, next 48 h | [solarmagix](datasets/solarmagix/README.md) |
| **C. Electricity prices** | Hourly day-ahead price, MEMO and HUPX, D+1 … D+7; hold-out: another exchange | [energy-prices](datasets/energy-prices/README.md), [energy-volumes](datasets/energy-volumes/README.md) |
| **D. Balancing (MEPSO)** | Hourly imbalance price (WAPpos / WAPneg / VAA±), activated aFRR / mFRR, D+1 … D+2; each new month is a test | [mepso](datasets/mepso/README.md) |
| **E. Your own dataset** | Several years, covariates, time-based or leave-subjects-out test | e.g. [energy-volumes](datasets/energy-volumes/README.md) |

| When (tentative) | What |
|---|---|
| From 30 Nov 2026 | Core datasets released: S1 (train), S2 (validation), H (hold-out, targets withheld) |
| December 2026 | Short presentation of S2 results vs baselines |
| Mid-January 2027 | Forecasts for H and code freeze (tagged commit) |
| End of February 2027 | S3: newly published data; the frozen code is re-run |

Metrics: **MASE** (primary), MAE, RMSE, skill vs seasonal naive; coverage, width and Winkler
score of the 80 % interval; for PV also nMAE and the **imbalance cost** in EUR per MWh
produced. The PV and balancing problems are linked: MEPSO settles the imbalance of a whole
balancing group, so several plants (normalised per installed capacity) can share one
imbalance price ([details](datasets/mepso/README.md#link-to-pv-production-balancing-groups)).

## Repository layout

```
.
├── README.md                this file
├── requirements.txt         Python packages for all scripts
├── assets/                  logos used by this README and the slides
├── challenge/               challenge texts and the resource guide
├── slides/                  slides.md (source), forecasting-challenge-slides.pdf / .html, theme/
├── datasets/
│   ├── README.md            catalogue, layout and conventions
│   ├── solarmagix/          PV inverters and plants (problems A, B)
│   ├── mepso/               balancing data of North Macedonia (problem D)
│   ├── energy-prices/       day-ahead prices HU, MK, RS and neighbours (problem C)
│   └── energy-volumes/      hourly load, monthly generation, flows, capacity (C inputs, E)
└── tools/md2pdf.sh          render a Markdown file to PDF (pandoc + Chrome)
```

Each dataset folder has the same structure: `README.md`, `scripts/` (download, build,
evaluate), `raw/` (as downloaded), `processed/` (normalised, analysis-ready tables),
`summary/` (quality checks and charts) and optionally `docs/`.

## Quick start

```bash
git clone https://github.com/eftim-magix/finki-time-series-datasets.git
cd finki-time-series-datasets
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```python
import pandas as pd

prices = pd.read_csv("datasets/energy-prices/processed/day_ahead_prices_hourly.csv",
                     parse_dates=["timestamp_utc"], index_col="timestamp_utc")
mepso = pd.read_csv("datasets/mepso/processed/MEPSO_balancing_prices_hourly.csv",
                    parse_dates=["timestamp_utc"], index_col="timestamp_utc", low_memory=False)
imbalance = mepso[["imbalance_regime", "imbalance_price_surplus_eur_per_mwh",
                   "imbalance_price_deficit_eur_per_mwh"]].join(prices["price_HU_eur_per_mwh"])
```

All processed tables use `timestamp_utc` (start of the interval, UTC) as the key, so they join
directly. The processed MEPSO, price and load tables are in git; the large raw downloads of
prices and load are not and are fetched again with each dataset's `scripts/fetch_*.py`.

To rebuild the slides (Node.js 18+):

```bash
npx @marp-team/marp-cli@4.5.1 --theme-set slides/theme/finki.css --html --allow-local-files slides/slides.md -o slides/forecasting-challenge-slides.pdf --pdf
npx @marp-team/marp-cli@4.5.1 --theme-set slides/theme/finki.css --html --allow-local-files slides/slides.md -o slides/forecasting-challenge-slides.html
```

## How to cite

If you use the PV data (SolarMagix), please cite:

Daskalov, A., Dimitrova, M., Atanasovska, T., Lameski, P., Risteska Stojkoska, B., &
Zdravevski, E. (2026). SolarMagix: An integrated multi-station photovoltaic and weather
dataset for solar energy forecasting, fault detection, and anomaly analysis. *Data in Brief*,
67, 112830. <https://doi.org/10.1016/j.dib.2026.112830>
(open access: <https://pmc.ncbi.nlm.nih.gov/articles/PMC13264133/>)

```bibtex
@article{daskalov2026solarmagix,
  title   = {{SolarMagix}: An integrated multi-station photovoltaic and weather dataset for solar energy forecasting, fault detection, and anomaly analysis},
  author  = {Daskalov, Andrej and Dimitrova, Marija and Atanasovska, Tijana and Lameski, Petre and Risteska Stojkoska, Biljana and Zdravevski, Eftim},
  journal = {Data in Brief},
  volume  = {67},
  pages   = {112830},
  year    = {2026},
  doi     = {10.1016/j.dib.2026.112830},
  pmid    = {42293442},
  pmcid   = {PMC13264133},
  url     = {https://pmc.ncbi.nlm.nih.gov/articles/PMC13264133/}
}
```

The other datasets are republished from public sources; credit them as well: **MEPSO**
(balancing data), **Ember** and the **ENTSO-E Transparency Platform** (day-ahead prices), and
**ENTSO-E Power Statistics** (load and generation).

## Contact

**Prof. Eftim Zdravevski**
eftim.zdravevski@finki.ukim.mk
Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University in Skopje

**Magix.AI** · <https://magix.ai>
