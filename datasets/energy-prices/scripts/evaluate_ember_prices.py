"""Evaluate Ember's hourly day-ahead prices for Hungary (HUPX), North Macedonia (MEMO), Serbia
(SEEPEX) and neighbours.

    python scripts/evaluate_ember_prices.py

Checks coverage, gaps, duplicates, DST handling, interpolated (straight-line) stretches,
zero/negative prices, spikes, agreement with Ember's daily file, how close the markets are,
and how good naive forecasts are (the baselines of the challenge). Writes tables and a chart
to summary/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

HERE = Path(__file__).resolve().parents[1]          # the dataset folder (datasets/energy-prices)
RAW, OUT = HERE / "raw", HERE / "summary"
MAIN = ["Hungary", "North Macedonia", "Serbia"]
NEIGHBOURS = ["Bulgaria", "Greece", "Romania", "Croatia", "Slovenia", "Albania", "Montenegro", "Kosovo"]


def load(country: str) -> pd.Series:
    df = pd.read_csv(RAW / "hourly" / f"{country}.csv")
    df["utc"] = pd.to_datetime(df["Datetime (UTC)"])
    df["local"] = pd.to_datetime(df["Datetime (Local)"])
    s = df.set_index("utc")["Price (EUR/MWhe)"].rename(country)
    s.attrs["local_offset_h"] = (df["local"] - df["utc"]).dt.total_seconds().div(3600).value_counts().to_dict()
    return s


def straight_runs(s: pd.Series, min_len: int = 6) -> tuple[int, int]:
    """Hours inside runs of >= min_len points lying on a straight line (constant first
    difference): the signature of linear interpolation over a gap (or of a flat price)."""
    d2 = s.diff().diff().abs() < 1e-6
    run_id = (~d2).cumsum()
    lengths = d2.groupby(run_id).transform("sum")
    flagged = d2 & (lengths >= min_len - 2)
    return int(flagged.sum()), int((lengths[flagged].groupby(run_id[flagged]).first() >= 0).sum())


def quality(s: pd.Series) -> dict:
    full = pd.date_range(s.index.min(), s.index.max(), freq="h")
    pts, runs = straight_runs(s)
    return {
        "country": s.name, "first_utc": s.index.min(), "last_utc": s.index.max(), "rows": len(s),
        "missing_hours": len(full.difference(s.index)), "duplicate_hours": int(s.index.duplicated().sum()),
        "nan_values": int(s.isna().sum()), "local_offsets_h": s.attrs["local_offset_h"],
        "straight_line_hours(>=6)": pts, "straight_line_runs": runs,
        "zero_hours": int((s == 0).sum()), "negative_hours": int((s < 0).sum()),
        "min": s.min(), "p01": round(s.quantile(0.01), 2), "median": s.median(),
        "p99": round(s.quantile(0.99), 2), "max": s.max(),
    }


def yearly(s: pd.Series) -> pd.DataFrame:
    g = s.groupby(s.index.year)
    return pd.DataFrame({"hours": g.size(), "mean": g.mean().round(1), "std": g.std().round(1),
                         "min": g.min(), "max": g.max(), "negative_hours": g.apply(lambda x: (x < 0).sum()),
                         "zero_hours": g.apply(lambda x: (x == 0).sum())})


def naive_scores(s: pd.Series, start: str) -> dict:
    """MAE of naive forecasts on the period from `start`, issued for each hour (h = 24 or 168)."""
    out = {"country": s.name, "period": f"{start} → {s.index.max():%Y-%m-%d}"}
    test = s[start:]
    for name, lag in [("naive_daily_MAE(lag24)", 24), ("naive_weekly_MAE(lag168)", 168)]:
        f = s.shift(lag, freq="h").reindex(test.index)
        out[name] = round(float((test - f).abs().mean()), 2)
    train = s[:start].iloc[:-1]
    scale = float((train - train.shift(168, freq="h").reindex(train.index)).abs().mean())
    out["MASE_scale_weekly(train)"] = round(scale, 2)
    out["MASE_naive_daily"] = round(out["naive_daily_MAE(lag24)"] / scale, 3)
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    series = {c: load(c) for c in MAIN + NEIGHBOURS}

    q = pd.DataFrame([quality(s) for s in series.values()])
    q.to_csv(OUT / "price_quality.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print("== Coverage and quality\n", q.to_string(index=False))

    for c in MAIN:
        y = yearly(series[c])
        y.to_csv(OUT / f"yearly_{c.replace(' ', '_').lower()}.csv")
        print(f"\n== {c}: per year\n", y.to_string())

    # 15-min MTU from 1 Oct 2025 (SDAC): are the hourly values still one per hour?
    hu = series["Hungary"]
    print("\n== Hungary around the 15-min switch (2025-09-30 / 10-01):",
          "rows per day:", hu["2025-09-28":"2025-10-04"].groupby(hu["2025-09-28":"2025-10-04"].index.date).size().to_dict())

    # agreement with Ember's daily file
    daily = pd.read_csv(RAW / "european_wholesale_electricity_price_data_daily.csv", parse_dates=["Date"])
    for c in MAIN:
        loc = load(c)
        h = pd.read_csv(RAW / "hourly" / f"{c}.csv", parse_dates=["Datetime (Local)"])
        hd = h.groupby(h["Datetime (Local)"].dt.normalize())["Price (EUR/MWhe)"].mean()
        dd = daily[daily["Country"] == c].set_index("Date")["Price (EUR/MWhe)"]
        j = pd.concat([hd, dd], axis=1, keys=["hourly_mean", "daily"]).dropna()
        print(f"   daily file vs mean of hourly ({c}): max |diff| = {np.abs(j.hourly_mean - j.daily).max():.3f} over {len(j)} days")
        del loc

    # how close are the markets? (2024 onwards, common hours)
    m = pd.concat([series[c] for c in MAIN + ["Bulgaria", "Greece", "Romania"]], axis=1)["2024":].dropna()
    corr = m.corr().round(3)
    equal = pd.DataFrame({a: {b: round(100 * float((m[a] - m[b]).abs().lt(0.01).mean()), 1) for b in m} for a in m})
    corr.to_csv(OUT / "correlation_2024_on.csv")
    equal.to_csv(OUT / "equal_price_share_2024_on.csv")
    print("\n== Correlation of hourly prices, 2024 onwards\n", corr.to_string())
    print("\n== % of hours with the same price (|diff| < 0.01), 2024 onwards\n", equal.to_string())

    # naive baselines (what the challenge's baselines would score)
    sc = pd.DataFrame([naive_scores(series[c], "2025-01-01") for c in MAIN])
    sc.to_csv(OUT / "naive_baselines_2025_on.csv", index=False)
    print("\n== Naive baselines, test from 2025-01-01\n", sc.to_string(index=False))

    # chart
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04)
    for i, c in enumerate(MAIN, start=1):
        s = series[c]["2022":]
        fig.add_trace(go.Scattergl(x=s.index, y=s.values, mode="lines", line=dict(width=0.5, color="#0300c0"),
                                   name=f"{c} hourly"), row=i, col=1)
        w = s.rolling("7D").mean()
        fig.add_trace(go.Scattergl(x=w.index, y=w.values, mode="lines", line=dict(width=2.2, color="#eb6834"),
                                   name=f"{c} 7-day mean"), row=i, col=1)
        fig.update_yaxes(title_text=f"{c} (EUR/MWh)", row=i, col=1)
    fig.update_layout(title="Ember hourly day-ahead prices (from ENTSO-E): hourly and 7-day mean, 2022 onwards",
                      template="plotly_white", height=700, width=1100, showlegend=False)
    fig.write_html(OUT / "prices_hu_mk_rs.html", include_plotlyjs="cdn")
    fig.write_image(OUT / "prices_hu_mk_rs.png", scale=1)
    print(f"\nWritten to {OUT.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
