# SolarMagix: PV inverters, plants and weather

The core dataset of the PV problems: production and telemetry of **inverters at several PV
stations** of different manufacturers and locations, fused with **weather data**. Published
as a data article in *Data in Brief* (2026); the challenge subsets are cut from it.

Used by **problem A** (PV inverters) and **problem B** (PV plants) of the
[challenge](../../challenge/simplified-challenge.md), and by the optional anomaly-detection task.

> **Status:** the challenge subsets **S1** (train), **S2** (validation, targets included) and
> **H** (hold-out, targets withheld) are released from **30 November 2026** (tentative);
> **S3** (newer data) follows at the end of February 2027. This folder will receive them, in
> the same layout as the other datasets.

## At a glance (from the data article)

| | |
|---|---|
| Content | PV system performance data of multiple stations fused with weather data; cleaned and aggregated views plus raw telemetry |
| Station level | 13,193 rows of station-level production and weather |
| Inverter level | 88,285 rows of inverter-level production and weather |
| Raw telemetry | More than 1.2 million rows of granular, unfiltered telemetry |
| Quality work | Timestamp alignment, inconsistent granularity across manufacturers, cleaning and aggregation |
| Article | <https://doi.org/10.1016/j.dib.2026.112830>, open access at <https://pmc.ncbi.nlm.nih.gov/articles/PMC13264133/>; its data availability section links the public files |

## Challenge subsets (planned layout)

```
solarmagix/
├── README.md
├── raw/            the published files, unchanged
├── processed/      S1/, S2/, H/ (and S3/ later), one file per subset and resolution
└── summary/        coverage per inverter and plant, gaps, capacities
```

| Subset | Contents | Targets |
|---|---|---|
| S1 | Training period: inverters of several plants | Included |
| S2 | Validation period of the same inverters | Included |
| H | Other inverters of seen plants, and unseen plants | **Withheld** |
| S3 | Newer data of the same inverters and plants (after the code freeze) | Withheld until scoring |

## Potential targets

| Target | Problem | Notes |
|---|---|---|
| Energy per inverter, 5-min (A1), aggregated to 15-min (A2) or 1-hour (A3) | A | Inverters differ in size: forecast **per kWp installed** or use MASE / nMAE |
| Hourly production of a whole plant (sum of its inverters) | B | Smoother than single inverters; hold-out = unseen plants |
| Imbalance cost of the day-ahead forecast | A, B | Needs the MEPSO imbalance price ([mepso](../mepso/README.md)) and HUPX ([energy-prices](../energy-prices/README.md)) |
| Underperforming inverters, frozen sensors, outages, clipping | optional | Compare an inverter with its neighbours in the same plant: they share the weather |

Inputs known at t0: past production, AC/DC current and voltage, inverter temperature and
status, measured plant weather up to t0. For the horizon only **forecast** weather (issued
before t0) and solar geometry are allowed: measured weather and other inverters' production
after t0 are leakage. Baselines: seasonal naive (same time yesterday), SMA and EMA over the
same time of day, clear-sky persistence.

**Normalise per installed capacity.** Several inverters of one plant, or several plants in
one balancing group, are combined by summing capacity × per-kWp forecast. That is how a PV
forecast becomes the schedule of a balancing group (see
[MEPSO: link to PV production](../mepso/README.md#link-to-pv-production-balancing-groups)).

## Cite

If you use this dataset, please cite:

Daskalov, A., Dimitrova, M., Atanasovska, T., Lameski, P., Risteska Stojkoska, B., &
Zdravevski, E. (2026). SolarMagix: An integrated multi-station photovoltaic and weather
dataset for solar energy forecasting, fault detection, and anomaly analysis. *Data in Brief*,
67, 112830. <https://doi.org/10.1016/j.dib.2026.112830>

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
