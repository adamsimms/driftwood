from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"

TIDE_DATA_CSV = DATA_DIR / "tide_data.csv"
WAVE_STATUS_CSV = DATA_DIR / "wave_status.csv"
STOP_FLAG = DATA_DIR / "STOP"
