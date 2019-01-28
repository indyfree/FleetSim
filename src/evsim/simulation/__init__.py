# flake8: noqa
from .simulation import start

# PHYSICAL CONSTANTS
CHARGING_SPEED = 3.6  # 3.6 kWh per hour
MAX_EV_CAPACITY = 17.6  # kWh
MAX_EV_RANGE = 160  # km
TIME_UNIT = 15  # Minutes
TIME_UNIT_CHARGE = CHARGING_SPEED / (60 / TIME_UNIT)  # kwh

CHARGING_STEP_KWH = CHARGING_SPEED / (60 / 5)  # kwh in 5 minutes charging
CHARGING_STEP_SOC = (
    100 * CHARGING_STEP_KWH / MAX_EV_CAPACITY
)  # SoC in 5 minutes charging
