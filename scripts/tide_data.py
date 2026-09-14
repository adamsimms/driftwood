import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import data_input
from paths import TIDE_DATA_CSV

IWLS_API = "https://api-iwls.dfo-mpo.gc.ca/api/v1"


def get_tide_data():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    response = requests.get(
        f"{IWLS_API}/stations/{data_input.TIDE_STATION_ID}/data",
        params={
            "time-series-code": "wlp",
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "resolution": "FIFTEEN_MINUTES",
        },
        timeout=30,
    )
    response.raise_for_status()

    records = response.json()
    if not records:
        raise ValueError(f"No tide data returned for {data_input.TIDE_STATION_NAME}")

    tide_df = pd.DataFrame(records)
    tide_df["date_time"] = pd.to_datetime(tide_df["eventDate"])
    tide_df["Height"] = pd.to_numeric(tide_df["value"], errors="coerce")
    final_data = tide_df[["date_time", "Height"]].dropna()

    TIDE_DATA_CSV.parent.mkdir(parents=True, exist_ok=True)
    final_data.to_csv(TIDE_DATA_CSV, index=False)

    latest = final_data.iloc[-1]
    return {
        "station": data_input.TIDE_STATION_NAME,
        "rows": len(final_data),
        "latest_height_m": float(latest["Height"]),
        "latest_time": str(latest["date_time"]),
    }
