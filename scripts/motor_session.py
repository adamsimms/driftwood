import logging
import time

import pandas as pd

import motor_state as state
from config import data_input
from motor_utils import tide_control, time_elapsed, wait_for_motors, wait_until_idle
from motor_waves import wave_sequence
from paths import TIDE_DATA_CSV
from runtime import LOGGER_MOTORS, MotorTimeoutError, sleep_interruptible

log = logging.getLogger(LOGGER_MOTORS)


def closing_action():
    log.info("Closing sequence started")
    state.Motor0.hardStop()
    state.Motor1.hardStop()
    time.sleep(1)
    sync_start = time.time()
    while state.Motor0.getPosition() != state.Motor1.getPosition():
        if time.time() - sync_start > data_input.motor_busy_timeout_seconds:
            raise MotorTimeoutError("Motors did not sync during closing")
        state.Motor1.goTo(state.Motor0.getPosition())
        wait_until_idle(state.Motor1, ignore_stop=True)
    log.info("Motors synced at %s", state.Motor0.getPosition())
    log.info("global_wave_timing=%s", state.global_wave_timing)
    time.sleep(1)
    state.Motor0.setMaxSpeed(state.speed_steps_per_minute)
    state.Motor1.setMaxSpeed(state.speed_steps_per_minute)
    state.Motor0.goHome()
    state.Motor1.goHome()
    wait_for_motors(ignore_stop=True)
    log.info(
        "Lowest tide at Motor0=%s Motor1=%s",
        state.Motor0.getPosition(),
        state.Motor1.getPosition(),
    )
    time.sleep(2)
    state.Motor0.goTo(-state.lowest_tide)
    state.Motor1.goTo(-state.lowest_tide)
    wait_for_motors(ignore_stop=True)
    state.Motor0.setCurrent(hold=0, run=0, acc=0, dec=0)
    state.Motor1.setCurrent(hold=0, run=0, acc=0, dec=0)
    log.info(
        "Motors home Motor0=%s Motor1=%s",
        state.Motor0.getPosition(),
        state.Motor1.getPosition(),
    )


def starting_act():
    log.info("Starting sequence")
    state.Motor0.setCurrent(hold=100, run=100, acc=100, dec=100)
    state.Motor1.setCurrent(hold=100, run=100, acc=100, dec=100)

    state.Motor0.setDecel(120)
    state.Motor1.setDecel(120)
    state.Motor0.setAccel(120)
    state.Motor1.setAccel(120)

    state.Motor0.setMaxSpeed(state.speed_steps_per_minute)
    state.Motor1.setMaxSpeed(state.speed_steps_per_minute)

    state.Motor0.move(state.lowest_tide)
    state.Motor1.move(state.lowest_tide)
    wait_for_motors()
    state.Motor0.setAsHome()
    state.Motor1.setAsHome()
    log.info("At lowest tide level")
    time.sleep(1.5)

    state.Motor0.move(state.tide_range)
    state.Motor1.move(state.tide_range)
    wait_for_motors()
    log.info("At highest tide level")
    time.sleep(1.5)

    state.global_wave_timing = []
    state.tide_data = pd.read_csv(TIDE_DATA_CSV)
    state.time_of_new_tide_data = time.time()
    current_from = float(state.tide_data.tail(2).head(1)["Height"])
    current_to = float(state.tide_data.tail(2).tail(1)["Height"])
    state.current_from_position = round(current_from * state.tide_range)
    state.current_to_position = round(current_to * state.tide_range)
    state.previous_from_position = state.current_from_position
    state.previous_to_position = state.current_to_position
    state.tide_distance_count = state.current_to_position - state.current_from_position
    time.sleep(0.5)
    state.Motor0.goTo(state.current_from_position)
    state.Motor1.goTo(state.current_from_position)
    wait_for_motors()
    time.sleep(0.5)
    wave_sequence(tide_distance=0, number_of_waves=1)
    time.sleep(1)


def tide_data_refresh():
    state.previous_from_position = state.current_from_position
    state.previous_to_position = state.current_to_position
    state.Motor0.setCurrent(hold=100, run=100, acc=100, dec=100)
    state.Motor1.setCurrent(hold=100, run=100, acc=100, dec=100)

    while True:
        try:
            state.tide_data = pd.read_csv(TIDE_DATA_CSV)
            break
        except (OSError, pd.errors.EmptyDataError) as error:
            log.warning("Waiting for tide data: %s", error)
            sleep_interruptible(5)

    current_from = tide_control(float(state.tide_data.tail(2).head(1)["Height"]))
    current_to = tide_control(float(state.tide_data.tail(2).tail(1)["Height"]))
    state.current_from_position = round(current_from * state.tide_range)
    state.current_to_position = round(current_to * state.tide_range)
    log.info("Actual From (m): %s Actual To (m): %s", current_from, current_to)
    log.info(
        "Motor position from=%s to=%s current Motor0=%s Motor1=%s",
        state.current_from_position,
        state.current_to_position,
        state.Motor0.getPosition(),
        state.Motor1.getPosition(),
    )
    state.tide_distance_count = state.current_to_position - state.current_from_position

    if (
        state.current_from_position != state.previous_from_position
        and state.current_to_position != state.previous_to_position
    ):
        state.time_of_new_tide_data = time.time()
        if abs(state.Motor0.getPosition() - state.current_from_position) != 0 or (
            abs(state.Motor1.getPosition() - state.current_from_position) != 0
        ):
            coverup_distance = state.current_from_position - state.Motor0.getPosition()
            log.info("New tide data; covering %s steps in 5 waves", coverup_distance)
            wave_sequence(number_of_waves=5, tide_distance=coverup_distance)
    elif state.current_to_position == state.previous_to_position:
        if (
            abs(state.Motor0.getPosition() - state.current_to_position) == 0
            or abs(state.Motor1.getPosition() - state.current_to_position) == 0
        ):
            log.info("Holding at current tide position")
            wave_sequence(tide_distance=0)
        else:
            try:
                target_distance = state.current_to_position - state.Motor0.getPosition()
                waves_in_remaining_time = round(
                    (900 - time_elapsed(state.time_of_new_tide_data))
                    / state.global_wave_timing[-1][-1]
                )
                tide_pace = round(target_distance / waves_in_remaining_time)
                log.info("Pacing %s steps over remaining waves (pace=%s)", target_distance, tide_pace)
                wave_sequence(tide_distance=tide_pace)
            except (IndexError, KeyError, ZeroDivisionError, TypeError):
                log.exception("Error in standard wave. Homing then restarting session")
                closing_action()
                time.sleep(30)
                starting_act()
