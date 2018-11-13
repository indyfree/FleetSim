#!/usr/bin/env python

from datetime import datetime
from random import random, seed, randint
import simpy

from vppsim.vpp import VPP
from vppsim.ev import EV

# SIMULATION CONSTANTS
START_DATE = datetime(2016, 1, 1)
END_DATE = datetime(2016, 1, 1, 8)
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour
RUNTIME = 2000
NUM_EVS = 1

# PHYSICAL CONSTANTS
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour


def lifecycle(env, vpp):
    ev = EV(env, vpp, 1)

    while True:
        if ev.action.triggered:
            if (random() <= 0.5):
                ev.action = env.process(ev.idle(env))
            else:
                ev.action = env.process(ev.charge(env))

        # Wait for customer
        yield env.timeout(randint(10, 30) * 60)

        yield env.process(ev.drive(env))


seed(21)
env = simpy.Environment(START_DATE.timestamp())
vpp = VPP(env, 1, NUM_EVS)
life = env.process(lifecycle(env, vpp))
env.run(END_DATE.timestamp())
