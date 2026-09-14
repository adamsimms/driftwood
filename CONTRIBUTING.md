# Contributing to Driftwood

Thank you for your interest in contributing. Driftwood is kinetic installation software: a Raspberry Pi reads live tide and wave data and drives stepper motors through a SlushEngine board.

## Before you start

Read these docs:

- [README.md](README.md) — install, architecture, and operations
- [SECURITY.md](SECURITY.md) — what must not be committed
- [CHANGELOG.md](CHANGELOG.md) — recent changes

## Development setup

### Without hardware (data scripts only)

You can work on tide/wave fetching and gallery scheduling on any machine with Python 3.10+:

```bash
git clone https://github.com/adamsimms/driftwood.git
cd driftwood
pip3 install -r requirements.txt
python3 scripts/check_apis.py
```

This verifies connectivity to the [CHS IWLS API](https://api-iwls.dfo-mpo.gc.ca) and [SmartAtlantic ERDDAP](https://www.smartatlantic.ca/erddap/index.html).

To run the data stream locally:

```bash
cd scripts
python3 live_data_stream.py
```

CSV output is written to `data/` (gitignored).

### With hardware (motor scripts)

Motor control requires:

- Raspberry Pi with GPIO access
- [SlushEngine](https://roboteurs.com/products/slushengine) driver board
- Stepper motors wired per the hardware list in the README

```bash
./deploy/install.sh --from-source
cd ~/driftwood/scripts
python3 play_test.py          # manual calibration
python3 project_log_live.py   # full motor loop
```

## Project structure

```
config/          Install parameters and gallery hours (edit on the Pi)
scripts/         Python control software
  motor_*.py     Motor logic (refactored from project_log_live.py)
  check_apis.py  Health check for external data sources
data/            Runtime CSV output (not committed)
logs/            Rotating service logs (not committed)
deploy/          install.sh, systemd units, sudoers rule
tests/           Unit tests that do not need motor hardware
viz/             Optional browser visualization (not used by the Pi)
```

## Making changes

1. Fork the repository and create a branch from `master`.
2. Make focused changes. One concern per pull request.
3. Run `python3 scripts/check_apis.py` if you touch `tide_data.py` or `wave_data.py`.
4. Run `python3 -m unittest tests/test_runtime.py` if you touch logging, stop, recovery, or blank-wave math.
5. Do not commit secrets, runtime CSVs, or machine-specific config (see [SECURITY.md](SECURITY.md)).
6. Open a pull request with:
   - What changed and why
   - How you tested it
   - Whether hardware testing was performed (if motor code changed)

## Configuration guidelines

| File | Purpose |
|------|---------|
| `config/data_input.py` | Motor tuning, API station IDs, refresh interval |
| `config/gallery_hours.py` | Gallery open/close schedule |

Default wave data comes from **Holyrood Buoy 2** because the original Mouth of Placentia buoy was decommissioned in 2022. If you change `WAVE_ERDDAP_DATASET`, document why in the PR and verify with `check_apis.py`.

Default tide data comes from **Bonavista** (CHS station 00990).

## Code style

- Match the existing Python style in the file you edit.
- Prefer specific exception types over bare `except:`.
- Use `and` / `or` for boolean logic, not bitwise `&` / `|`.
- Keep motor timing behavior changes explicit in the PR description — subtle changes affect the physical installation.

## Questions

Open a [GitHub issue](https://github.com/adamsimms/driftwood/issues) for bugs, questions, or feature ideas. Use the bug report template when applicable.
