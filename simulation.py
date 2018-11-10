#!/usr/bin/env python
from datetime import datetime
from random import random, seed, randint
import simpy

import ev


# CONSTANTS
START_DATE = datetime(2016, 1, 1)
END_DATE = datetime(2016, 1, 1, 8)
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour
NUM_EVS = 1
RUNTIME = 2000


class VPP:
    def __init__(self, env, name):
        self.capacity = simpy.Container(env, init=0, capacity=MAX_EV_CAPACITY * NUM_EVS)
        self.env = env
        self.name = name
        self.mon_proc = env.process(self.monitor_capacity(env))

    def log(self, message):
        print('[%s] - VPP-%s(%.2f/%.2f)' % (datetime.fromtimestamp(self.env.now), self.name, self.capacity.level, self.capacity.capacity), message)

    def monitor_capacity(self, env):
        while True:
            self.log('Capacity')
            yield env.timeout(10 * 60)


def lifecycle(env, vpp):
    EV = ev.EV(env, vpp, 1)

    while True:
        # print('Process %s, triggered: %s' % (EV.action, EV.action.triggered))
        if EV.action.triggered:
            if (random() <= 0.5):
                EV.action = env.process(EV.idle(env))
            else:
                EV.action = env.process(EV.charge(env))

        # Wait for customer
        yield env.timeout(randint(10, 30) * 60)

        yield env.process(EV.drive(env))


seed(21)
env = simpy.Environment(START_DATE.timestamp())
vpp = VPP(env, 1)
life = env.process(lifecycle(env, vpp))
env.run(END_DATE.timestamp())
