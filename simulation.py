#!/usr/bin/env python
import simpy
from random import random, seed, randint
#seed(20)

MAX_EV_CAPACITY=16.5  # kWh
MAX_EV_RANGE=20       # km
CHARGING_SPEED=300.6    # 3.6 kWh per hour
NUM_EVS=1

class VPP:
    def __init__(self, env, name):
        self.capacity = simpy.Container(env, init=0, capacity=MAX_EV_CAPACITY*NUM_EVS)
        self.env = env
        self.name = name
        self.mon_proc = env.process(self.monitor_capacity(env))

    def log(self, message):
        print('[%s] - VPP-%s(%.2f/%.2f)'% (self.env.now, self.name, self.capacity.level, self.capacity.capacity), message)

    def monitor_capacity(self, env):
        level = 0
        while True:
            if level != self.capacity.level:
                self.log('Change %.2f capacity' % (self.capacity.level - level))
                level = self.capacity.level

            yield env.timeout(1)


class EV:
    def __init__(self, env, vpp, name):
        self.battery = simpy.Container(env, init=MAX_EV_CAPACITY, capacity=MAX_EV_CAPACITY)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle(env))

    def log(self, message):
        print('[%s] - EV-%s(%.2f/%.2f)'% (self.env.now, self.name, self.battery.level, self.battery.capacity), message)

    def idle(self, env):
        self.log('At a parking lot. Waiting for rental...')
        while True:
            try:
                yield env.timeout(1)
            except simpy.Interrupt as i:
                self.log('Idle interrupted! %s' % i.cause)
                break

    def charge(self, env):
        self.log('At a charging station! Charging...')
        while True:
            try:
                yield self.vpp.capacity.put(self.battery.level)
                if self.battery.level < self.battery.capacity - (CHARGING_SPEED / 60):
                    yield self.battery.put(CHARGING_SPEED / 60)
                    yield self.vpp.capacity.put(CHARGING_SPEED / 60)
                    self.log('Charging...')
                    yield env.timeout(1)
                elif 0 < self.battery.capacity - self.battery.level < (CHARGING_SPEED / 60):
                    rest = self.battery.capacity - self.battery.level
                    yield self.battery.put(rest)
                    yield self.vpp.capacity.put(rest)
                    yield env.timeout(1)
                else:
                    self.log('Fully charged. Waiting for rental...')
                    break
            except simpy.Interrupt as i:
                # yield self.vpp.capacity.get(self.battery.level)
                self.log('Charging interrupted! %s' % i.cause)


    def drive(self, env):
        avg_speed = randint(30, 60) # km/h
        trip_distance = randint(5, 10) # km
        trip_time = int(trip_distance / avg_speed * 60) # minutes
        trip_capacity = MAX_EV_CAPACITY / MAX_EV_RANGE * trip_distance # kWh

        if self.battery.level > trip_capacity:
            self.log('Start driving.')

            # Interrupt Charging or Parking
            if not self.action.triggered:
                self.action.interrupt('Customer arrived')

            yield env.timeout(trip_time)
            yield self.battery.get(trip_capacity)
            self.log('Drove %d kilometers in %d minutes and consumed %.2f kWh'% (trip_distance, trip_time, trip_capacity))
        else:
            self.log('Not enough battery for the planned trip')


def lifecycle(env, vpp):
    ev = EV(env, vpp, 1)

    while True:
        if ev.action.triggered:
            if (random() <= 0.5):
                ev.action = env.process(ev.idle(env))
            else:
                ev.action = env.process(ev.charge(env))

        # Wait for customer
        yield env.timeout(randint(60,360))

        yield env.process(ev.drive(env))


env = simpy.Environment()
vpp = VPP(env, 1)
life = env.process(lifecycle(env, vpp))
env.run(3000)
