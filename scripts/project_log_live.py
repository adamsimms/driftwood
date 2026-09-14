import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gallery_timings
import motor_state as state
import tide_data as tide
import wave_data as wave
from motor_session import closing_action, starting_act, tide_data_refresh
from motor_utils import motor_reset, wait_for_motors
from runtime import (
    LOGGER_MOTORS,
    MotorTimeoutError,
    StopRequested,
    clear_stop_flag,
    install_stop_signal_handler,
    reboot_pi,
    setup_logging,
    should_stop,
    sleep_interruptible,
)


def recover_and_reboot(log, reason):
    log.error("Unrecoverable error: %s", reason)
    try:
        closing_action()
    except Exception:
        log.exception("Failed to home motors during recovery")
        try:
            if state.Motor0:
                state.Motor0.hardStop()
            if state.Motor1:
                state.Motor1.hardStop()
        except Exception:
            log.exception("hardStop failed")
    reboot_pi(log)


def main():
    log = setup_logging(LOGGER_MOTORS)
    install_stop_signal_handler()
    clear_stop_flag()
    log.info("Starting motor controller")

    try:
        tide_info = tide.get_tide_data()
        wave_info = wave.get_wave_data()
        log.info("Initial tide data: %s", tide_info)
        log.info("Initial wave data: %s", wave_info)
    except Exception:
        log.exception("Initial data fetch failed")
        raise

    state.init_motors()
    motor_reset(state.Motor0)
    motor_reset(state.Motor1)

    is_motor_on = 0

    while True:
        try:
            if should_stop():
                raise StopRequested()

            if gallery_timings.are_we_open_yet():
                if is_motor_on == 0:
                    starting_act()
                log.info("Gallery is open")
                tide_data_refresh()
                is_motor_on = 1
                continue

            if is_motor_on == 1:
                log.info("Gallery is closing now")
                closing_action()
                is_motor_on = 0
                continue

            state.Motor0.setCurrent(hold=0, run=0, acc=0, dec=0)
            state.Motor1.setCurrent(hold=0, run=0, acc=0, dec=0)
            log.info(gallery_timings.show_offline_message())
            sleep_interruptible(60)

        except StopRequested:
            log.info("Stop requested; running closing sequence")
            try:
                closing_action()
            except Exception:
                log.exception("closing_action failed during stop")
            log.info("Motor controller stopped")
            return 0

        except KeyboardInterrupt:
            next_step = input("Enter N for new or Q for Quit: ")
            if next_step == "N":
                state.Motor0.goTo(state.current_from_position)
                state.Motor1.goTo(state.current_from_position)
                wait_for_motors()
                log.info("Starting new session")
                continue

            closing_action()
            log.info("Ending now")
            return 0

        except MotorTimeoutError as error:
            recover_and_reboot(log, str(error))

        except Exception:
            log.exception("Unexpected error in motor loop")
            recover_and_reboot(log, "unexpected error")


if __name__ == "__main__":
    raise SystemExit(main())
