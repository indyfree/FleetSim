import gym

# from gym import error, spaces, utils
# from gym.utils import seeding


class FleetEnv(gym.Env):
    """
    Environment wrapper for simulation to be compatible with openai gym
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self):
        pass

    def step(self, action):
        pass

    def reset(self):
        pass

    def render(self, mode="human"):
        pass

    def close(self):
        pass
