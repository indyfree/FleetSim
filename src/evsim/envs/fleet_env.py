from datetime import datetime
import gym
from gym import spaces
import numpy as np

from evsim.controller import Controller, strategy
from evsim.simulation import Simulation, SimulationConfig


class FleetEnv(gym.Env):
    """
    Environment wrapper for simulation to be compatible with openai gym
    """

    def __init__(self):

        # Initialize evsim
        cfg = SimulationConfig()
        self.controller = Controller(cfg, strategy.integrated)
        self.sim = Simulation(cfg, self.controller)

        # Define what the agent can do:
        # Set Risk factors from lambda = [0.0, 0.1, ..., 1.0]
        self.action_space = spaces.Discrete(11)

        # Define what the agent can observe:
        # Current time in hours [0-23]
        low = np.array([0])
        high = np.array([23])
        self.observation_space = spaces.Box(low, high, dtype=np.int64)

        self.curr_balance = 0
        self._realtime = self.sim.env.now

    @property
    def realtime(self):
        return datetime.fromtimestamp(self._realtime)

    def step(self, action):
        """
        The agent takes a step in the environment.
        Parameters
        ----------
        action : int
        Returns
        -------
        ob, reward, episode_over, info : tuple
            ob (object) :
                an environment-specific object representing your observation of
                the environment.
            reward (float) :
                amount of reward achieved by the previous action. The scale
                varies between environments, but the goal is always to increase
                your total reward.
            episode_over (bool) :
                whether it's time to reset the environment again. Most (but not
                all) tasks are divided up into well-defined episodes, and done
                being True indicates the episode has terminated. (For example,
                perhaps the pole tipped too far, or you lost your last life.)
            info (dict) :
                 diagnostic information useful for debugging. It can sometimes
                 be useful for learning (for example, it might contain the raw
                 probabilities behind the environment's last state change).
                 However, official evaluations of your agent are not allowed to
                 use this for learning.
        """
        balance, done = self.sim.step(action / 10, minutes=15)
        reward = balance - self.curr_balance

        self.curr_balance = balance
        self._realtime = self.sim.env.now

        hour = self.realtime.hour
        ob = [hour]

        return ob, reward, done, {}

    def reset(self):
        del self.sim
        self.sim = Simulation(SimulationConfig(), self.controller)
        self._realtime = self.sim.env.now
        self.curr_balance = 0
        return [self.realtime.hour]

    def render(self):
        print(self.sim.env.now)

    def close(self):
        pass
