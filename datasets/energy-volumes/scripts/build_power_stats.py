"""Collate the downloaded ENTSO-E Power Statistics files (raw/*.csv) into tidy tables.

    python scripts/build_power_stats.py

The yearly files change delimiter and column names from year to year; this script reads them
all with one set of names (see evaluate_power_stats.read) and writes to processed/:

    hourly_load_mw.csv              one row per UTC hour, load_<ISO2>_mw for MK and its region
                                    (complete hourly grid; hours a country did not report are blank)
    monthly_domestic_values_gwh.csv country, year, month, category, value_gwh (all countries)
    monthly_physical_flows_gwh.csv  year, month, from_country, to_country, direction, value_gwh
    net_generation_capacity_mw.csv  country, year, category, value_mw (all countries)

Values are copied unchanged. North Macedonia's load has whole days missing or reported as 0
from 2024 on (see README.md): zeros are kept, so treat them as missing when modelling.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_power_stats import HERE, RAW, REGION, read  # noqa: E402

OUT = HERE / "processed"


def hourly_load(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["CountryCode"].isin(REGION)].copy()
    df["time"] = pd.to_datetime(df["DateUTC"], format="%d-%m-%Y %H:%M").dt.tz_localize("UTC")
    wide = df.pivot_table(index="time", columns="CountryCode", values="Value", aggfunc="mean")
    grid = pd.date_range(wide.index.min(), wide.index.max(), freq="h", tz="UTC")
    wide = wide.reindex(grid)[[c for c in REGION if c in wide.columns]]
    wide.columns = [f"load_{c}_mw" for c in wide.columns]
    out = pd.DataFrame({"timestamp_utc": grid.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "local_timestamp": [t.isoformat() for t in grid.tz_convert("Europe/Skopje")]})
    return pd.concat([out, wide.reset_index(drop=True)], axis=1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = {}

    load = hourly_load(read("monthly_hourly_load_values_*.csv"))
    written["hourly_load_mw.csv"] = load
    load.to_csv(OUT / "hourly_load_mw.csv", index=False)

    mdv = read("monthly_domestic_values_*.csv")
    mdv = (mdv.rename(columns={"Country": "country", "Year": "year", "Month": "month", "Category": "category",
                               "ProvidedValue": "value_gwh"})[["country", "year", "month", "category", "value_gwh"]]
           .sort_values(["country", "category", "year", "month"]))
    written["monthly_domestic_values_gwh.csv"] = mdv
    mdv.to_csv(OUT / "monthly_domestic_values_gwh.csv", index=False)

    pepf = read("physical_energy_power_flows_*.csv")
    pepf = pepf[pepf["MeasureTime"].astype(str).str.contains("Monthly", case=False)]
    pepf = (pepf.rename(columns={"Year": "year", "Month": "month", "FromCountryMapCode": "from_country",
                                 "ToCountryMapCode": "to_country", "Direction": "direction", "Value": "value_gwh"})
            [["year", "month", "from_country", "to_country", "direction", "value_gwh"]]
            .sort_values(["from_country", "to_country", "direction", "year", "month"]))
    written["monthly_physical_flows_gwh.csv"] = pepf
    pepf.to_csv(OUT / "monthly_physical_flows_gwh.csv", index=False)

    ngc = read("net_generation_capacity_*.csv")
    ngc = (ngc.rename(columns={"Country": "country", "Year": "year", "Category": "category", "ProvidedValue": "value_mw"})
           [["country", "year", "category", "value_mw"]].sort_values(["country", "year", "category"]))
    written["net_generation_capacity_mw.csv"] = ngc
    ngc.to_csv(OUT / "net_generation_capacity_mw.csv", index=False)

    for name, df in written.items():
        print(f"wrote processed/{name}: {len(df):,} rows")
    print(f"hourly load: {load['timestamp_utc'].iloc[0]} .. {load['timestamp_utc'].iloc[-1]}")


if __name__ == "__main__":
    if not any(RAW.glob("*.csv")):
        raise SystemExit("raw/ is empty: run python scripts/fetch_power_stats.py first")
    main()
