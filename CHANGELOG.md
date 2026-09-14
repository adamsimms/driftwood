# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- `SECURITY.md`, `CONTRIBUTING.md`, and `CHANGELOG.md`
- `scripts/check_apis.py` for verifying tide and wave data sources
- `deploy/install.sh` for Pi setup
- `deploy/systemd/` service units
- Motor control split into `motor_state.py`, `motor_utils.py`, `motor_waves.py`, `motor_session.py`
- `config/gallery_hours.py` for gallery schedule
- Rotating file logs in `logs/` for the data stream and motor controller (#11)
- Motor busy timeout, then home the log and reboot the Pi on unrecoverable errors (#12)
- Remote graceful stop via `systemctl stop driftwood-motors`, SIGTERM, or `scripts/graceful_stop.py` (#14)

### Changed
- Migrated tide fetching from tides.gc.ca HTML scraping to CHS IWLS REST API (Bonavista)
- Migrated wave fetching from deprecated SmartAtlantic PHP endpoint to ERDDAP (Holyrood Buoy 2)
- Standardized project naming to **Driftwood** with Pi install path `~/driftwood`
- Reorganized repository: `config/`, `data/`, `viz/`, `deploy/`
- Holding/blank waves stay at the current motor position and correct leftover drift (#16)

### Removed
- Committed secrets and machine-specific config (`scratchpad.md`, `concordia-wifi/`)
- Duplicate files (`resources/snippets.txt`, `scripts/logberry`)
- Stale committed runtime CSVs

### Security
- Rewrote git history to purge previously committed credentials and network config

## [Historical]

Earlier commits cover the original 2017 gallery installation, SlushEngine motor control, and live data integration.
