from datetime import datetime
from random import randint
import simpy

import vppsim


class EV:
    def __init__(self, env, vpp, name, soc):
        self.battery = simpy.Container(env, init=vppsim.MAX_EV_CAPACITY * soc / 100, capacity=vppsim.MAX_EV_CAPACITY)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle(env))

    def log(self, message):
        print('[%s] - %s(%.2f/%.2f)' % (datetime.fromtimestamp(self.env.now), self.name, self.battery.level, self.battery.capacity), message)

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
                    increment = vppsim.CHARGING_SPEED / 60
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

    def drive(self, env, duration):
        trip_distance = randint(5, 15)  # km
        trip_time = duration * 60       # seconds
        trip_capacity = (vppsim.MAX_EV_CAPACITY / vppsim.MAX_EV_RANGE) * trip_distance  # kWh

        self.log('Customer arrived.')
        if self.battery.level > trip_capacity:
            self.log('Start driving.')

            # Interrupt Charging or Parking
            if not self.action.triggered:
                self.action.interrupt("")

            yield env.timeout(trip_time)

            if trip_charge > 0:
                yield self.battery.get(trip_charge)
            elif trip_charge < 0:
                self.log('WARNING: Battery has been charged on the trip')
                yield self.battery.put(-trip_charge)
            else:
                self.log('WARNING: No battery has been consumed on the trip')

            self.log('Drove for %.2f minutes and consumed %.2f kWh' % (trip_time / 60, trip_charge))
        else:
            self.log('Not enough battery for the planned trip.')
