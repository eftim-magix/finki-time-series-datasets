"""Collate Ember's hourly day-ahead prices (raw/hourly/<Country>.csv) into one table.

    python scripts/build_ember_prices.py

Writes processed/day_ahead_prices_hourly.csv: one row per UTC hour, one price column per
market, EUR/MWh. The grid is complete (every hour from the first to the last timestamp of any
market); hours a market did not publish are blank. Values are copied unchanged: zero days
and gaps listed in README.md are not cleaned, so that the cleaning stays a visible modelling
choice.

Columns: timestamp_utc (interval start, ISO 8601 with Z), local_timestamp (Europe/Skopje,
with offset), price_<ISO2>_eur_per_mwh.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]          # the dataset folder (datasets/energy-prices)
RAW, OUT = HERE / "raw" / "hourly", HERE / "processed"
MARKETS = {  # Ember file name -> ISO 3166 alpha-2 code used in column names
    "Hungary": "HU", "North Macedonia": "MK", "Serbia": "RS", "Bulgaria": "BG", "Greece": "GR",
    "Romania": "RO", "Croatia": "HR", "Slovenia": "SI", "Montenegro": "ME", "Albania": "AL", "Kosovo": "XK",
}


def load(country: str) -> pd.Series:
    df = pd.read_csv(RAW / f"{country}.csv")
    utc = pd.to_datetime(df["Datetime (UTC)"]).dt.tz_localize("UTC")
    s = pd.Series(df["Price (EUR/MWhe)"].to_numpy(), index=utc, name=f"price_{MARKETS[country]}_eur_per_mwh")
    if s.index.duplicated().any():
        raise ValueError(f"duplicate hours in {country}.csv")
    return s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prices = pd.concat([load(c) for c in MARKETS], axis=1).sort_index()
    grid = pd.date_range(prices.index.min(), prices.index.max(), freq="h", tz="UTC")
    prices = prices.reindex(grid)
    out = pd.DataFrame({
        "timestamp_utc": grid.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local_timestamp": [t.isoformat() for t in grid.tz_convert("Europe/Skopje")],
    })
    out = pd.concat([out, prices.reset_index(drop=True)], axis=1)
    path = OUT / "day_ahead_prices_hourly.csv"
    out.to_csv(path, index=False, float_format="%.2f")
    print(f"wrote {path.relative_to(HERE)}: {len(out):,} rows, {out['timestamp_utc'].iloc[0]} .. {out['timestamp_utc'].iloc[-1]}")
    print(prices.notna().sum().rename("hours with a price").to_string())


if __name__ == "__main__":
    main()
