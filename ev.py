#!/usr/bin/env python
from datetime import datetime, timezone
from random import random, seed, randint
import simpy

MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour

class EV:
    def __init__(self, env, vpp, name):
        self.battery = simpy.Container(env, init=MAX_EV_CAPACITY, capacity=MAX_EV_CAPACITY)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle(env))

    def log(self, message):
        print('[%s] - EV-%s(%.2f/%.2f)' % (datetime.fromtimestamp(self.env.now), self.name, self.battery.level, self.battery.capacity), message)

    def idle(self, env):
        self.log('At a parking lot. Waiting for rental...')
        while True:
            try:
                yield env.timeout(5 * 60)
            except simpy.Interrupt as i:
                self.log('Idle interrupted! %s' % i.cause)
                break

    def charge(self, env):
        self.log('At a charging station! Charging...')
        yield self.vpp.capacity.put(self.battery.level)
        while True:
            try:
                if self.battery.level < self.battery.capacity:
                    increment = CHARGING_SPEED / 60
                    rest = self.battery.capacity - self.battery.level
                    if rest < increment:
                        increment = rest
                    yield self.battery.put(increment)
                    yield self.vpp.capacity.put(increment)
                    yield env.timeout(5 * 60)
                else:
                    self.log('Fully charged. Waiting for rental...')
                    break
            except simpy.Interrupt as i:
                self.log('Charging interrupted! %s' % i.cause)
                break

        yield self.vpp.capacity.get(self.battery.level)

    def drive(self, env):
        avg_speed = randint(30, 60)                                     # km/h
        trip_distance = randint(5, 15)                                  # km
        trip_time = int((trip_distance / avg_speed) * 60 * 60)          # seconds
        trip_capacity = MAX_EV_CAPACITY / MAX_EV_RANGE * trip_distance  # kWh

        if self.battery.level > trip_capacity:
            self.log('Start driving.')

            # Interrupt Charging or Parking
            if not self.action.triggered:
                self.action.interrupt('Customer arrived')

            yield env.timeout(trip_time)
            yield self.battery.get(trip_capacity)
            self.log('Drove %d kilometers in %.2f minutes and consumed %.2f kWh' % (trip_distance, trip_time / 60, trip_capacity))
        else:
            self.log('Not enough battery for the planned trip')
