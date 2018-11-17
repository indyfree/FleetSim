from datetime import datetime
import simpy

import vppsim


class EV:
    def __init__(self, env, vpp, name, soc):
        self.battery = simpy.Container(env, init=soc , capacity=100)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle(env))
        self.soc = soc

    def log(self, message):
        print('[%s] - %s(%s/%s)' % (datetime.fromtimestamp(self.env.now), self.name, self.battery.level, self.battery.capacity), message)

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

        # self.vpp.log('Adding capacity %s' % self.battery.level)
        # yield self.vpp.capacity.put(self.battery.level)
        # self.vpp.log('Added capacity %s' % self.battery.level)

        while True:
            try:
                # TODO: Investigate timeout
                yield env.timeout(1)
            except simpy.Interrupt as i:
                self.log('Charging interrupted! %s' % i.cause)

                self.log('Last SoC: %s%%, current SoC: %s%%' % (self.battery.level, self.soc))
                charged_amount = self.soc - self.battery.level
                # TODO: Fix SoC
                if charged_amount != 0:
                    yield self.battery.put(charged_amount)
                    self.log('Charged battery for %s%%' % charged_amount)

                break

        # self.vpp.log('Removing capacity %s' % self.battery.level)
        # yield self.vpp.capacity.get(self.battery.level)
        # self.vpp.log('Removed capacity %s' % self.battery.level)

    def drive(self, env, rental, duration, trip_charge, start_soc, dest_charging_station):
        if self.battery.level > trip_charge:
            print('\n ---------- RENTAL %d ----------' % rental)

            # Interrupt Charging or Parking
            if not self.action.triggered:
                # HACK: Pass value how much is charged
                self.soc = start_soc
                self.action.interrupt("Start driving")

            if self.battery.level != start_soc:
                self.log('WARNING: Data inconsistency. SoC is %s%%, but should be %s%%' % (start_soc, self.battery.level))

            yield env.timeout(duration * 60)  # seconds

            print('\n -------- END RENTAL %d --------' % rental)
            self.log('Drove for %.2f minutes and consumed %s%% charge' % (duration, trip_charge))

            if trip_charge > 0:
                self.log('Trying to adjust battery level')
                yield self.battery.get(trip_charge)
                self.log('Battery level has been decreased by %s%%' % trip_charge)
            elif trip_charge < 0:
                self.log('WARNING: Battery has been charged on the trip')
                yield self.battery.put(-trip_charge)
                self.log('Battery level has been increased by %s%%' % -trip_charge)
            else:
                self.log('WARNING: No battery has been consumed on the trip')

        else:
            self.log('WARNING: Not enough battery for the planned trip.')

        if bool(dest_charging_station):
            self.action = env.process(self.charge(self.env))
        else:
            self.action = env.process(self.idle(self.env))
