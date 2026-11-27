"""Evaluate the downloaded ENTSO-E Power Statistics files (raw/*.csv).

    python scripts/evaluate_power_stats.py

Prints what each dataset contains, checks whether any prices are present, and assesses the
hourly load series of North Macedonia and neighbouring countries (coverage, gaps, duplicates).
Writes summary tables to summary/ and a chart to summary/hourly_load_mk_hu_rs.html (+ .png).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

HERE = Path(__file__).resolve().parents[1]          # the dataset folder (datasets/energy-volumes)
RAW, OUT = HERE / "raw", HERE / "summary"
REGION = ["MK", "HU", "RS", "BG", "GR", "RO", "AL", "ME", "BA", "HR", "SI", "XK"]


RENAME = {"Area": "Country", "FromAreaCode": "FromCountryMapCode", "ToAreaCode": "ToCountryMapCode"}


def read(pattern: str) -> pd.DataFrame:
    """Read all yearly files of one dataset. The delimiter (tab, ';' or ',') and some column
    names differ from year to year, so detect and harmonise them."""
    frames = []
    for f in sorted(RAW.glob(pattern)):
        header = f.open(encoding="utf-8-sig").readline()
        sep = max(["\t", ";", ","], key=header.count)
        df = pd.read_csv(f, sep=sep, encoding="utf-8-sig", low_memory=False).rename(columns=RENAME)
        df["source_file"] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def price_check(frames: dict[str, pd.DataFrame]) -> None:
    print("\n== Any price data?")
    for name, df in frames.items():
        text = " ".join(df.columns) + " " + " ".join(
            str(v) for c in df.columns if df[c].dtype == object for v in df[c].dropna().unique()[:500])
        hits = [w for w in ("price", "eur", "€", "mwh price", "day-ahead") if w in text.lower()]
        print(f"  {name:30s} columns: {', '.join(df.columns[:6])}{' …' if len(df.columns) > 6 else ''}")
        print(f"  {'':30s} price-related words: {hits or 'none'}")


def hourly_load(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["time"] = pd.to_datetime(df["DateUTC"], format="%d-%m-%Y %H:%M")
    rows = []
    for c in REGION:
        s = df[df["CountryCode"] == c]
        if s.empty:
            rows.append({"country": c, "rows": 0})
            continue
        t = s["time"]
        full = pd.date_range(t.min(), t.max(), freq="h")
        step = t.sort_values().diff().dropna().value_counts().index[0]
        rows.append({
            "country": c, "rows": len(s), "first_utc": t.min(), "last_utc": t.max(),
            "typical_step": str(step), "expected_hours": len(full),
            "missing_hours": len(full.difference(t)), "duplicate_hours": int(t.duplicated().sum()),
            "cov_ratio_min": s["Cov_ratio"].min(), "share_cov_lt_100_pct": round(100 * (s["Cov_ratio"] < 100).mean(), 2),
            "mean_MW": round(s["Value"].mean(), 1), "min_MW": round(s["Value"].min(), 1), "max_MW": round(s["Value"].max(), 1),
        })
    return pd.DataFrame(rows)


def chart(df: pd.DataFrame) -> None:
    df = df.copy()
    df["time"] = pd.to_datetime(df["DateUTC"], format="%d-%m-%Y %H:%M")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04)
    for i, c in enumerate(["MK", "HU", "RS"], start=1):
        s = df[df["CountryCode"] == c].set_index("time")["Value"].sort_index()
        fig.add_trace(go.Scattergl(x=s.index, y=s.values, mode="lines", line=dict(width=0.6, color="#0300c0"),
                                   name=f"{c} hourly"), row=i, col=1)
        w = s.rolling("7D").mean()
        fig.add_trace(go.Scatter(x=w.index, y=w.values, mode="lines", line=dict(width=1.6, color="#eb6834"),
                                 name=f"{c} 7-day mean"), row=i, col=1)
        fig.update_yaxes(title_text=f"{c} load (MW)", row=i, col=1)
    fig.update_layout(title="ENTSO-E Monthly Hourly Load Values: hourly load and 7-day mean",
                      template="plotly_white", height=650, width=1100, showlegend=False)
    fig.write_html(OUT / "hourly_load_mk_hu_rs.html", include_plotlyjs="cdn")
    try:
        fig.write_image(OUT / "hourly_load_mk_hu_rs.png", scale=1)
    except Exception as e:  # kaleido missing or no browser
        print("  (PNG not written:", e, ")")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    mhlv, mdv = read("monthly_hourly_load_values_*.csv"), read("monthly_domestic_values_*.csv")
    pepf, ngc = read("physical_energy_power_flows_*.csv"), read("net_generation_capacity_*.csv")
    frames = {"monthly_hourly_load_values": mhlv, "monthly_domestic_values": mdv,
              "physical_energy_power_flows": pepf, "net_generation_capacity": ngc}

    print("== Files and sizes")
    for name, df in frames.items():
        print(f"  {name:30s} {len(df):>9,d} rows")
    price_check(frames)

    print("\n== Hourly load (MHLV): countries", mhlv["CountryCode"].nunique(),
          "| measure:", mhlv["MeasureItem"].unique().tolist())
    hl = hourly_load(mhlv)
    hl.to_csv(OUT / "hourly_load_quality.csv", index=False)
    print(hl.to_string(index=False))

    print("\n== Monthly domestic values: categories for MK")
    mk = mdv[mdv["Country"] == "MK"]
    cats = mk.groupby("Category").agg(first_year=("Year", "min"), last_year=("Year", "max"),
                                      months=("Month", "size")).reset_index()
    cats.to_csv(OUT / "monthly_domestic_values_mk_categories.csv", index=False)
    print(cats.to_string(index=False))

    print("\n== Physical flows: MK borders (monthly)")
    fl = pepf[(pepf["FromCountryMapCode"] == "MK") | (pepf["ToCountryMapCode"] == "MK")]
    print(fl.groupby(["FromCountryMapCode", "ToCountryMapCode"]).size().to_string())
    print("  MeasureTime values:", pepf["MeasureTime"].unique().tolist())

    print("\n== Net generating capacity MK (MW)")
    cap = ngc[(ngc["Country"] == "MK") & (ngc["ProvidedValue"] > 0)][["Year", "Category", "ProvidedValue"]]
    cap.to_csv(OUT / "net_generation_capacity_mk.csv", index=False)
    print(cap.to_string(index=False))

    chart(mhlv)
    print(f"\nSummaries written to {OUT.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
