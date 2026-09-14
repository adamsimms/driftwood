import time

from config import data_input
import motor_state as state
from runtime import MotorTimeoutError, StopRequested, should_stop


def cm_to_step(cm):
    return round(cm * 200 / 9)


def sleep_delay_count(step):
    step = abs(step)
    if step < cm_to_step(1.67):
        return 0.15
    if step < cm_to_step(3.33):
        return 0.25
    if step < cm_to_step(3.83):
        return 0.35
    if step < cm_to_step(4.67):
        return 0.45
    if step < cm_to_step(5.83):
        return 0.55
    if step < cm_to_step(6.67):
        return 0.6
    if step < cm_to_step(7.5):
        return 0.7
    return 0.8


def time_elapsed(time_value):
    return time.time() - time_value


def net_wave_diff(tide_distance, planned_diff):
    """Blank/holding waves (tide_distance=0) must not net-move the log."""
    if tide_distance == 0:
        return 0
    return planned_diff


def tide_control(value):
    if value > 1.1:
        return float(1.1)
    if value < -0.1:
        return float(-0.1)
    return float(value)


def motor_reset(motor=None):
    motor = motor or state.Motor0
    motor.resetDev()
    motor.setMicroSteps(1)


def wait_until_idle(motor, timeout=None, ignore_stop=False):
    timeout = data_input.motor_busy_timeout_seconds if timeout is None else timeout
    start = time.time()
    while motor.isBusy():
        if not ignore_stop and should_stop():
            raise StopRequested()
        if time.time() - start > timeout:
            raise MotorTimeoutError(f"Motor stayed busy for {timeout}s")
        time.sleep(0.01)


def wait_for_motors(timeout=None, ignore_stop=False):
    timeout = data_input.motor_busy_timeout_seconds if timeout is None else timeout
    start = time.time()
    while state.Motor0.isBusy() or state.Motor1.isBusy():
        if not ignore_stop and should_stop():
            raise StopRequested()
        if time.time() - start > timeout:
            raise MotorTimeoutError(f"Motors stayed busy for {timeout}s")
        time.sleep(0.01)
