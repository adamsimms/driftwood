"""Shared logging, stop signaling, and Pi recovery helpers."""

import logging
import signal
import subprocess
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import data_input
from paths import LOG_DIR, STOP_FLAG

LOGGER_DATA = "live_data_stream"
LOGGER_MOTORS = "project_log_live"

_stop_requested = False


class MotorTimeoutError(Exception):
    """A motor stayed busy longer than motor_busy_timeout_seconds."""


class StopRequested(Exception):
    """Graceful stop was requested via SIGTERM or the STOP flag file."""


def setup_logging(name):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=1_000_000,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def request_stop(*_args):
    global _stop_requested
    _stop_requested = True


def clear_stop_flag():
    global _stop_requested
    _stop_requested = False
    try:
        STOP_FLAG.unlink()
    except FileNotFoundError:
        pass


def write_stop_flag():
    STOP_FLAG.parent.mkdir(parents=True, exist_ok=True)
    STOP_FLAG.write_text("stop\n")
    request_stop()


def should_stop():
    return _stop_requested or STOP_FLAG.exists()


def install_stop_signal_handler():
    signal.signal(signal.SIGTERM, request_stop)


def is_raspberry_pi():
    model = Path("/proc/device-tree/model")
    if not model.exists():
        return False
    try:
        return b"raspberry" in model.read_bytes().lower()
    except OSError:
        return False


def sleep_interruptible(seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if should_stop():
            raise StopRequested()
        time.sleep(min(1, max(0, deadline - time.time())))


def reboot_pi(log):
    if not data_input.reboot_on_unrecoverable_error:
        log.warning("reboot_on_unrecoverable_error is off; exiting instead of rebooting")
        raise SystemExit(1)
    if not is_raspberry_pi():
        log.warning("Not a Raspberry Pi; skipping reboot")
        raise SystemExit(1)

    log.error("Rebooting Raspberry Pi")
    result = subprocess.run(
        ["sudo", "-n", "/sbin/reboot"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.error("reboot failed (%s): %s%s", result.returncode, result.stdout, result.stderr)
        raise SystemExit(1)
    time.sleep(120)
    raise SystemExit(0)
