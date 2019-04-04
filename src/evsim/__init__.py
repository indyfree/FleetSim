# flake8: noqa
import evsim.simulation
from evsim.simulation import statistic

from gym.envs.registration import register

register(id="evsim-v0", entry_point="evsim.envs:FleetEnv")
