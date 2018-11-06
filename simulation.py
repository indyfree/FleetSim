#!/usr/bin/env python
import simpy
from random import seed, randint

MAX_EV_CAPACITY=16.5 # kWh
MAX_EV_RANGE=20     # km
NUM_EVS=2

class VPP:
    def __init__(self, env, name):
        self.capacity = simpy.Container(env, init=0, capacity=MAX_EV_CAPACITY*NUM_EVS)
        self.mon_proc = env.process(self.monitor_capacity(env))
        self.name = name

    def monitor_capacity(self, env):
        level = 0
        while True:
            if level != self.capacity.level:
                level = self.capacity.level
                print('[%s] - %s VPP: Capacity level: %.2f' % (env.now, self.name, self.capacity.level))
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
                yield vpp.capacity.put(self.battery.level)
                yield env.timeout(idle_time)
                print('[%s] - EV %s was idle for %d minutes' % (env.now, name, idle_time))
                self.idle = False
            else:
                avg_speed = randint(30, 60) # km/h
                trip_distance = randint(5, 10) # km
                trip_time = int(trip_distance / avg_speed * 60) # minutes
                trip_capacity = MAX_EV_CAPACITY / MAX_EV_RANGE * trip_distance # kWh
                print('[%s] - EV %s starts driving' % (env.now, name))
                yield vpp.capacity.get(self.battery.level)
                yield env.timeout(trip_time + idle_time)
                yield self.battery.get(trip_capacity)
                print('[%s] - EV %s drove %d kilometers in %d minutes and consumed %.2f kWh' % (env.now, name, trip_distance, trip_time, trip_capacity))
                self.idle = True


def car_generator(env, vpp):
    for i in range(NUM_EVS):
        print('[%s] - EV %s joined the fleet' % (env.now, i))
        ev = EV(env, vpp, i)
        yield env.timeout(1)


env = simpy.Environment()
vpp = VPP(env, "Balancing")
# ev = EV(env, vpp, "1")
car_gen = env.process(car_generator(env, vpp))
env.run(200)
