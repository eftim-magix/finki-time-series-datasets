"""Download ENTSO-E Power Statistics CSV files (https://www.entsoe.eu/data/power-stats/).

    python scripts/fetch_power_stats.py                      # default selection below
    python scripts/fetch_power_stats.py --datasets monthly_hourly_load_values --years 2025 2026

Files are saved to raw/<dataset>_<year>.csv in the dataset folder. Existing files are skipped.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

BASE = "https://www.entsoe.eu/publications/data/power-stats/{year}/{dataset}_{year}.csv"
RAW = Path(__file__).resolve().parents[1] / "raw"      # datasets/energy-volumes/raw (not in git)

DEFAULT = {
    "monthly_hourly_load_values": [2023, 2024, 2025, 2026],   # ~35-45 MB per year
    "monthly_domestic_values": list(range(2019, 2027)),
    "physical_energy_power_flows": [2024, 2025, 2026],
    "net_generation_capacity": [2024, 2025],
}


def fetch(dataset: str, year: int) -> None:
    out = RAW / f"{dataset}_{year}.csv"
    if out.exists():
        print(f"skip  {out.name}")
        return
    # curl uses the operating system's certificate store (Python's ssl may not)
    subprocess.run(["curl", "-sSfL", "-A", "Mozilla/5.0", "--max-time", "600",
                    "-o", str(out), BASE.format(year=year, dataset=dataset)], check=True)
    print(f"saved {out.name} ({out.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="*")
    ap.add_argument("--years", nargs="*", type=int)
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    plan = ({d: a.years or DEFAULT.get(d, [2025]) for d in a.datasets} if a.datasets else DEFAULT)
    for dataset, years in plan.items():
        for y in years:
            fetch(dataset, y)


if __name__ == "__main__":
    main()
