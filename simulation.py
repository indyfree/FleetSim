#!/usr/bin/env python
import simpy
from random import seed, randint

MAX_EV_CAPACITY=16.5 # kWh
MAX_EV_RANGE=106     # km
NUM_EVS=20

class VPP:
    def __init__(self, env):
        self.capacity = simpy.Container(env, init=MAX_EV_CAPACITY*NUM_EVS, capacity=MAX_EV_CAPACITY*NUM_EVS)
        self.mon_proc = env.process(self.monitor_capacity(env))

    def monitor_capacity(self, env):
        while True:
            print('Capacity level: %d  at %s' % (self.capacity.level, env.now))
            yield env.timeout(1)

class EV:
    def __init__(self, env, vpp, name):
        self.idle = True
        self.battery = simpy.Container(env, init=MAX_EV_CAPACITY, capacity=MAX_EV_CAPACITY)
        self.drive_proc = env.process(self.drive(env, vpp, name))
    
    def drive(self, env, vpp, name):
        while True:
            if self.idle:
                idle_time = randint(5, 20)
                yield env.timeout(idle_time)
                print('EV %s was idle for %d minutes' % (name, idle_time))
                self.idle = False
            else:
                avg_speed = randint(30, 60) # km/h
                trip_distance = randint(5, 10) # km
                trip_time = int(trip_distance / avg_speed * 60) # minutes
                trip_capacity = MAX_EV_CAPACITY / MAX_EV_RANGE * trip_distance # kWh
                print('EV %s started driving at %s' % (name, env.now))
                yield env.timeout(trip_time + idle_time)
                yield vpp.capacity.get(trip_capacity)
                print('EV %s drove %d kilometers in %d minutes and consumed %f kWh' % (name, trip_distance, trip_time, trip_capacity))
                self.idle = True


def car_generator(env, vpp):
    for i in range(NUM_EVS):
        print('EV %s joined the VPP at %s' % (i, env.now))
        ev = EV(env, vpp, i)
        yield env.timeout(1)


env = simpy.Environment()
vpp = VPP(env)
# ev = EV(env, vpp, "1")
car_gen = env.process(car_generator(env, vpp))
env.run(200)
