from datetime import datetime
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np

from evsim.controller import Controller, strategy
from evsim.simulation import Simulation, SimulationConfig


class FleetEnv(gym.Env):
    """
    Environment wrapper for simulation to be compatible with openai gym
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self):

        # Initialize evsim
        self.init_sim()

        # Define what the agent can do:
        #    Set Risk factors from lambda = [0.0, 0.1, ..., 1.0]
        #    for both markets
        self.action_space = spaces.Tuple((spaces.Discrete(11), spaces.Discrete(11)))

        # Define what the agent can observe:
        #    Current time in hours [0-23]
        low = np.array([0])
        high = np.array([23])
        self.observation_space = spaces.Box(low, high, dtype=np.int64)

        self.curr_balance = 0
        self._realtime = self.sim.env.now

        self.episode = 0

    @property
    def realtime(self):
        return datetime.fromtimestamp(self._realtime)

    def init_sim(self):
        cfg = SimulationConfig()
        self.controller = Controller(
            cfg, strategy.integrated, accuracy=(80, 95), imbalance_costs=3000
        )
        self.sim = Simulation(cfg, self.controller)

    def imbalance_costs(self, cost):
        self.controller.imbalance_costs = cost

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        # Transform "flat" action back to tuple
        risk = ((action // 11) / 10, (action % 11) / 10)

        balance, done = self.sim.step(risk=risk, minutes=15)
        reward = balance - self.curr_balance

        self.curr_balance = balance
        self._realtime = self.sim.env.now

        hour = self.realtime.hour
        ob = [hour]

        return ob, reward, done, {}

    def reset(self):
        """ Returns observation """

        # Save simulation results
        if self.episode > 0:
            self.save_results("./results/sim_result_ep_{}.csv".format(self.episode))

        self.episode += 1
        self.curr_balance = 0

        del self.sim
        self.init_sim()

        self._realtime = self.sim.env.now
        ob = self.realtime.hour
        return [ob]

    def save_results(self, filename):
        self.sim.results.write(filename)

    def render(self, mode="human", close=False):
        print(self.sim.env.now)

    def close(self):
        pass

    def prediction_accuracy(self, accuracy):
        self.controller.accuracy = accuracy
