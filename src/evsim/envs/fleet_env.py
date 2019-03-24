import gym

from evsim.controller import Controller, strategy
from evsim.simulation import Simulation, SimulationConfig

# from gym import error, spaces, utils
# from gym.utils import seeding


class FleetEnv(gym.Env):
    """
    Environment wrapper for simulation to be compatible with openai gym
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self):

        cfg = SimulationConfig()
        controller = Controller(cfg, strategy.intraday)
        self.sim = Simulation(cfg, controller)

    def step(self, action):
        self.sim.step()

    def reset(self):
        pass

    def render(self, mode="human"):
        print(self.sim.env.now)

    def close(self):
        pass
