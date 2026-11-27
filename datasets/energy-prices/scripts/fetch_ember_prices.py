"""Download Ember's European wholesale (day-ahead) electricity price data.

Page:  https://ember-energy.org/data/european-wholesale-electricity-price-data/
Files: https://files.ember-energy.org/public-downloads/price/outputs/
         european_wholesale_electricity_price_data_hourly.zip   (~43 MB; all countries + one CSV per country)
         european_wholesale_electricity_price_data_daily.csv
         european_wholesale_electricity_price_data_monthly.csv
The Ember API (https://api.ember-energy.org/v1/docs) has no price endpoints, only generation,
demand, emissions and capacity, so prices are downloaded as files.

    python scripts/fetch_ember_prices.py          # downloads into raw/ and unzips into raw/hourly/
"""
from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

BASE = "https://files.ember-energy.org/public-downloads/price/outputs/"
FILES = ["european_wholesale_electricity_price_data_hourly.zip",
         "european_wholesale_electricity_price_data_daily.csv",
         "european_wholesale_electricity_price_data_monthly.csv"]
RAW = Path(__file__).resolve().parents[1] / "raw"      # datasets/energy-prices/raw (not in git)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        out = RAW / name
        # curl uses the operating system's certificate store (Python's ssl may not)
        subprocess.run(["curl", "-sSfL", "-A", "Mozilla/5.0", "--max-time", "600",
                        "-o", str(out), BASE + name], check=True)
        print(f"saved {name} ({out.stat().st_size / 1e6:.1f} MB)")
    dest = (RAW / "hourly").resolve()
    with zipfile.ZipFile(RAW / FILES[0]) as z:
        for m in z.infolist():                       # refuse paths that leave the folder
            if not (dest / m.filename).resolve().is_relative_to(dest):
                raise ValueError(f"unsafe path in zip: {m.filename}")
        z.extractall(dest)
        print(f"extracted {len(z.infolist())} entries to raw/hourly/")


if __name__ == "__main__":
    main()
