from datetime import datetime
import logging
import simpy

import vppsim


class EV:
    def __init__(self, env, vpp, name, soc):
        self.logger = logging.getLogger('vppsim.ev')

        self.battery = simpy.Container(env, init=soc , capacity=100)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle(env))
        self.soc = soc

    def log(self, message):
        self.logger.info('[%s] - %s(%s/%s) %s' % (datetime.fromtimestamp(self.env.now), self.name, self.battery.level, self.battery.capacity, message))

    def warning(self, message):
        self.logger.warning('[%s] - %s(%s/%s) %s' % (datetime.fromtimestamp(self.env.now), self.name, self.battery.level, self.battery.capacity, message))


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
                yield env.timeout(1)
            except simpy.Interrupt as i:
                self.log('Charging interrupted! %s' % i.cause)

                self.log('Last SoC: %s%%, current SoC: %s%%' % (self.battery.level, self.soc))
                charged_amount = self.soc - self.battery.level
                if charged_amount > 0:
                    yield self.battery.put(charged_amount)
                    self.log('Charged battery for %s%%' % charged_amount)
                elif charged_amount < 0:
                    self.warning('Data inconsistency. SoC is > %s%%, but should have been charging. Adjusting...' % self.battery.level)
                    yield self.battery.get(-charged_amount)
                    self.log('Charged battery for %s%%' % charged_amount)
                else:
                    self.warning('Battery has been charged on the trip')

                break

        # self.vpp.log('Removing capacity %s' % self.battery.level)
        # yield self.vpp.capacity.get(self.battery.level)
        # self.vpp.log('Removed capacity %s' % self.battery.level)

    def drive(self, env, rental, duration, trip_charge, start_soc, dest_charging_station):
        # Remeber SoC on the begging of rental to fix inconsistencies
        # between simulated SoC and the the data.
        self.soc = start_soc

        self.logger.info('[%s] - ----------- RENTAL %d ----------' % (datetime.fromtimestamp(self.env.now), rental))

        # Interrupt Charging or Parking
        if not self.action.triggered:
            self.action.interrupt("Start driving")

        # Adjust changes in SoC while beeing idle
        yield env.timeout(1)  # seconds
        if self.battery.level != start_soc:
            self.warning('Data inconsistency. SoC is %s%%, but should be %s%%. Adjusting...' % (start_soc, self.battery.level))
            diff = start_soc - self.battery.level
            if diff < 0:
                yield self.battery.get(-diff)
                self.warning('EV lost %s%% battery while beeing idle. How much can a EV loose standing around?' % diff)
            else:
                yield self.battery.put(diff)
                self.warning('EV gained %s%% battery while beeing idle. At charging station?' % diff)


        if self.battery.level < trip_charge:
            self.error('Not enough battery for the planned trip.')
            # TODO: Previous action
            # self.action =
            return

        # Drive for the trip duration
        yield env.timeout((duration * 60) - 1)  # seconds

        # Adjust SoC
        self.logger.info('[%s] - --------- END RENTAL %d --------' % (datetime.fromtimestamp(self.env.now), rental))
        self.log('Drove for %.2f minutes and consumed %s%% charge' % (duration, trip_charge))
        if trip_charge > 0:
            self.log('Trying to adjust battery level')
            yield self.battery.get(trip_charge)
            self.log('Battery level has been decreased by %s%%' % trip_charge)
        elif trip_charge < 0:
            self.warning('Battery has been charged on the trip')
            yield self.battery.put(-trip_charge)
            self.log('Battery level has been increased by %s%%' % -trip_charge)
        else:
            self.warning('No battery has been consumed on the trip')

        if bool(dest_charging_station):
            self.action = env.process(self.charge(self.env))
        else:
            self.action = env.process(self.idle(self.env))
