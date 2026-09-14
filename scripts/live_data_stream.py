import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import data_input

import tide_data as tide
import wave_data as wave
from runtime import LOGGER_DATA, setup_logging

REFRESH_INTERVAL = data_input.data_refresh_interval


def main():
    log = setup_logging(LOGGER_DATA)
    log.info("Starting data stream (interval=%ss)", REFRESH_INTERVAL)

    while True:
        try:
            tide_info = tide.get_tide_data()
            wave_info = wave.get_wave_data()
            log.info("New tide data: %s", tide_info)
            log.info("New wave data: %s", wave_info)
            time.sleep(REFRESH_INTERVAL)
        except KeyboardInterrupt:
            log.info("Ending data stream")
            return 0
        except Exception as error:
            log.exception("Error in data refresh: %s", error)
            time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
