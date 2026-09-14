#!/usr/bin/env python3
"""Ask the motor controller to home the log and exit.

Writes data/STOP. project_log_live.py notices on the next wait or loop
iteration, runs closing_action(), then exits.

If motors are running under systemd, this is equivalent to:
  sudo systemctl stop driftwood-motors
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paths import STOP_FLAG
from runtime import write_stop_flag


def main():
    write_stop_flag()
    print(f"Wrote {STOP_FLAG}. Motors will home and exit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
