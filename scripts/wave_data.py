import sys
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import data_input
from paths import WAVE_STATUS_CSV

ERDDAP_BASE = "https://www.smartatlantic.ca/erddap/tabledap"


def get_wave_data():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=1)
    end = now

    url = (
        f"{ERDDAP_BASE}/{data_input.WAVE_ERDDAP_DATASET}.csv?"
        "time,latitude,longitude,wave_ht_max,wave_ht_sig,wave_period_max"
        f"&time>={start.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"&time<={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    if response.text.startswith("Error"):
        raise ValueError(response.text)

    wave_data = pd.read_csv(StringIO(response.text), skiprows=[1])
    if wave_data.empty:
        raise ValueError(f"No wave data returned for {data_input.WAVE_DATASET_NAME}")

    wave_data["time"] = pd.to_datetime(wave_data["time"])
    wave_data.columns = [
        "date_time",
        "latitude",
        "longitude",
        "max_wave_height",
        "sig_wave_height",
        "peak_wave_period",
    ]

    WAVE_STATUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    latest = wave_data.tail(1)
    latest.to_csv(WAVE_STATUS_CSV, index=False)

    row = latest.iloc[0]
    return {
        "dataset": data_input.WAVE_DATASET_NAME,
        "max_wave_height": float(row["max_wave_height"]),
        "sig_wave_height": float(row["sig_wave_height"]),
        "peak_wave_period": float(row["peak_wave_period"]),
        "latest_time": str(row["date_time"]),
    }
