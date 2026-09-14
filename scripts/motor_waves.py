import logging
import random
import time

import numpy as np
import pandas as pd

import motor_state as state
from motor_utils import cm_to_step, net_wave_diff, sleep_delay_count, time_elapsed, wait_for_motors, wait_until_idle
from paths import WAVE_STATUS_CSV
from runtime import LOGGER_MOTORS, sleep_interruptible

log = logging.getLogger(LOGGER_MOTORS)


def create_wave(
    first_motor=None,
    second_motor=None,
    wave_height=250,
    wave_diff=25,
    max_count=10,
    current_count=0,
    sleep_delay=0.2,
    speed=40,
):
    first_motor = first_motor or state.Motor0
    second_motor = second_motor or state.Motor1

    first_motor.setMaxSpeed(speed)
    second_motor.setMaxSpeed(speed)

    while current_count < max_count:
        current_count += 1
        wait_until_idle(first_motor)
        first_motor.move(wave_height)
        if current_count >= 1:
            time.sleep(sleep_delay)
        wait_until_idle(second_motor)
        second_motor.move(wave_height)
        wait_until_idle(first_motor)
        first_motor.move(-1 * (wave_height - wave_diff))
        time.sleep(sleep_delay)
        wait_until_idle(second_motor)
        second_motor.move(-1 * (wave_height - wave_diff))
        wait_until_idle(first_motor)


def _correct_to_position(expected):
    pos0 = state.Motor0.getPosition()
    pos1 = state.Motor1.getPosition()
    if pos0 == expected and pos1 == expected:
        return
    log.info(
        "Correcting motor position: Motor0=%s Motor1=%s expected=%s",
        pos0,
        pos1,
        expected,
    )
    state.Motor0.goTo(expected)
    state.Motor1.goTo(expected)
    wait_for_motors()


def wave_sequence(tide_distance, number_of_waves=1):
    loop_count = 0
    start_position = state.Motor0.getPosition()
    holding = tide_distance == 0

    if holding:
        log.info(
            "Holding wave at current position Motor0=%s Motor1=%s",
            start_position,
            state.Motor1.getPosition(),
        )

    while True:
        try:
            wave_data = pd.read_csv(WAVE_STATUS_CSV)
            max_wave_height = round(cm_to_step(float(wave_data["max_wave_height"][0])) * 0.8) * state.multiplier
            sig_wave_height = round(cm_to_step(float(wave_data["sig_wave_height"][0])) * 0.8) * state.multiplier
            period_damper = 0.5
            peak_wave_period = float(wave_data["peak_wave_period"][0]) * (
                1 if state.multiplier * period_damper <= 1 else state.multiplier * period_damper
            )
            diff_per_wave = round(tide_distance / number_of_waves)
            wave_timing = []
            log.info("peak wave period (secs): %s", peak_wave_period)
            log.info("max wave height (m): %s", float(wave_data["max_wave_height"][0]))
            log.info("sig wave height (m): %s", float(wave_data["sig_wave_height"][0]))
            break
        except (OSError, KeyError, IndexError, ValueError) as error:
            log.warning("Waiting for wave data: %s", error)
            sleep_interruptible(5)

    while loop_count < number_of_waves:
        start_time = time.time()

        create_wave(
            wave_height=max_wave_height,
            wave_diff=net_wave_diff(tide_distance, round(max_wave_height * 0.2)),
            max_count=1,
            current_count=0,
            sleep_delay=sleep_delay_count(max_wave_height),
            speed=state.speed_steps_per_minute,
        )
        if time.time() - start_time > peak_wave_period:
            create_wave(
                wave_height=round(sig_wave_height * float(random.randint(80, 150) / 100)),
                wave_diff=net_wave_diff(
                    tide_distance, diff_per_wave - round(max_wave_height * 0.2)
                ),
                max_count=1,
                current_count=0,
                sleep_delay=sleep_delay_count(
                    max(max_wave_height, round(sig_wave_height * float(random.randint(80, 150) / 100)))
                ),
                speed=state.speed_steps_per_minute,
            )
            loop_count += 1
            wave_timing.append(time_elapsed(start_time))
            continue

        create_wave(
            wave_height=round(max_wave_height * 0.8),
            wave_diff=net_wave_diff(tide_distance, -(round(max_wave_height * 0.2 * 0.8))),
            max_count=1,
            current_count=0,
            sleep_delay=sleep_delay_count(round(max_wave_height * 0.8)),
            speed=state.speed_steps_per_minute,
        )
        if time.time() - start_time > peak_wave_period:
            create_wave(
                wave_height=round(sig_wave_height * float(random.randint(80, 150) / 100)),
                wave_diff=net_wave_diff(
                    tide_distance, diff_per_wave - (round(max_wave_height * 0.2 * 0.2))
                ),
                max_count=1,
                current_count=0,
                sleep_delay=sleep_delay_count(
                    max(max_wave_height, round(sig_wave_height * float(random.randint(80, 150) / 100)))
                ),
                speed=state.speed_steps_per_minute,
            )
            loop_count += 1
            wave_timing.append(time_elapsed(start_time))
            continue

        create_wave(
            wave_height=sig_wave_height,
            wave_diff=net_wave_diff(tide_distance, -(round(max_wave_height * 0.2 * 0.2))),
            max_count=1,
            current_count=0,
            sleep_delay=sleep_delay_count(sig_wave_height),
            speed=state.speed_steps_per_minute,
        )
        if time.time() - start_time > peak_wave_period:
            create_wave(
                wave_height=round(sig_wave_height * float(random.randint(80, 150) / 100)),
                wave_diff=net_wave_diff(tide_distance, diff_per_wave),
                max_count=1,
                current_count=0,
                sleep_delay=sleep_delay_count(
                    max(max_wave_height, round(sig_wave_height * float(random.randint(80, 150) / 100)))
                ),
                speed=state.speed_steps_per_minute,
            )
            loop_count += 1
            wave_timing.append(time_elapsed(start_time))
            continue

        create_wave(
            wave_height=round(sig_wave_height * float(random.randint(80, 150) / 100)),
            wave_diff=net_wave_diff(tide_distance, diff_per_wave),
            max_count=1,
            current_count=0,
            sleep_delay=sleep_delay_count(
                max(max_wave_height, round(sig_wave_height * float(random.randint(80, 150) / 100)))
            ),
            speed=state.speed_steps_per_minute,
        )

        wave_timing.append(time_elapsed(start_time))

        if time_elapsed(start_time) < (peak_wave_period - 0.8):
            time_to_kill = peak_wave_period - time_elapsed(start_time)
            time_killing_start = time.time()
            while (time_to_kill * 0.8) > time_elapsed(time_killing_start):
                create_wave(
                    wave_height=round(sig_wave_height * float(random.randint(80, 150) / 100)),
                    wave_diff=0,
                    max_count=1,
                    current_count=0,
                    sleep_delay=sleep_delay_count(
                        round(sig_wave_height * float(random.randint(80, 150) / 100))
                    ),
                    speed=state.speed_steps_per_minute,
                )

        loop_count += 1
        log.info(
            "Position update Motor0=%s Motor1=%s",
            state.Motor0.getPosition(),
            state.Motor1.getPosition(),
        )
        log.info("Wave sequence duration: %s mean=%s", wave_timing, np.mean(wave_timing))
        state.global_wave_timing.append(wave_timing)

    expected = start_position + tide_distance
    _correct_to_position(expected)
