# Install-specific motor and wave parameters (values are in motor steps unless noted).

lowest_tide = 50
tide_range = 200
multiplier = 6
speed_multiplier = 2.5

# Seconds between successful tide/wave data refreshes in live_data_stream.py
data_refresh_interval = 300

# Seconds a motor may stay busy before the controller homes the log and recovers.
motor_busy_timeout_seconds = 45

# After an unrecoverable motor error, home the log then reboot the Pi (no-op off-Pi).
reboot_on_unrecoverable_error = True

# Canadian Hydrographic Service IWLS tide station (Bonavista, code 00990)
TIDE_STATION_ID = "5cebf1e33d0f4a073c4bc189"
TIDE_STATION_NAME = "Bonavista"

# SmartAtlantic ERDDAP wave dataset.
# The original Mouth of Placentia buoy was decommissioned in 2022; Holyrood Buoy 2 is the nearest active source.
WAVE_ERDDAP_DATASET = "SMA_Holyrood_Buoy2"
WAVE_DATASET_NAME = "Holyrood Buoy 2"
