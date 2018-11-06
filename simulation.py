#!/usr/bin/env python
import simpy
from random import seed, randint

MAX_EV_CAPACITY=16.5
NUM_EVS=20

class VPP:
    def __init__(self, env):
        self.capacity = simpy.Container(env, init=MAX_EV_CAPACITY*NUM_EVS, capacity=MAX_EV_CAPACITY*NUM_EVS)
        self.mon_proc = env.process(self.monitor_capacity(env))

    def monitor_capacity(self, env):
        while True:
            print('Capacity level: %d  at %s' % (self.capacity.level, env.now))
            yield env.timeout(10)

def EV(name, env, vpp):
    print('EV %s started driving at %s' % (name, env.now))
    minutes = randint(5, 10)
    yield env.timeout(minutes)
    print('EV %s finished driving at %s and used %d kWh' % (name, env.now, minutes*2))
    yield vpp.capacity.get(minutes*2)


def car_generator(env, vpp):
    for i in range(NUM_EVS):
        env.process(EV(i, env, vpp))
        yield env.timeout(1)


env = simpy.Environment()
vpp = VPP(env)
car_gen = env.process(car_generator(env, vpp))
env.run(100)
