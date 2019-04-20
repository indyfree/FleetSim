#!/usr/bin/env python

import gym

from evsim.experiments import setup_logger
from evsim.rl import DDQN

name = "DDDQN-100-100"
episodes = 2
episode_steps = 65334

setup_logger("sim-{}".format(name), write=True)
env = gym.make("evsim-v0")
env.imbalance_costs(5000)
env.prediction_accuracy((100, 100))

dqqn = DDQN(env, name, memory_limit=episode_steps, nb_eps=episode_steps, nb_warmup=1000)
dqqn.run(episodes * episode_steps)

dqqn.test()
