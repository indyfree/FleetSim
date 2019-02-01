# flake8: noqa
from .simulation import Simulation

# PHYSICAL CONSTANTS
CHARGING_SPEED = 3.6  # 3.6 kWh per hour
MAX_EV_CAPACITY = 17.6  # kWh
MAX_EV_RANGE = 160  # km
TIME_UNIT = 15  # Minutes
TIME_UNIT_CHARGE = CHARGING_SPEED / (60 / TIME_UNIT)  # kwh
