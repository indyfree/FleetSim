from datetime import datetime
import logging
import simpy

import vppsim


class EV:
    def __init__(self, env, vpp, name, soc):
        self.logger = logging.getLogger("vppsim.ev")

        # Battery capacity in percent
        self.battery = simpy.Container(env, init=soc, capacity=100)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = env.process(self.idle())
        self.soc = soc

    def log(self, message):
        self.logger.info(
            "[%s] - %s(%s/%s) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                self.name,
                self.battery.level,
                self.battery.capacity,
                message,
            )
        )

    def warning(self, message):
        self.logger.warning(
            "[%s] - %s(%s/%s) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                self.name,
                self.battery.level,
                self.battery.capacity,
                message,
            )
        )

    def idle(self):
        self.log("At a parking lot. Waiting for rental...")
        while True:
            try:
                yield self.env.timeout(5 * 60)
            except simpy.Interrupt as i:
                self.log("Idle interrupted! %s" % i.cause)
                break

    def charge(self):
        self.log("At a charging station! Charging...")

        capacity = (
            vppsim.MAX_EV_CAPACITY * (self.battery.capacity - self.battery.level) / 100
        )
        if capacity != 0:
            self.vpp.log(
                "Adding EV %s to VPP: Increase capacity by %skWh..."
                % (self.name, capacity)
            )
            yield self.vpp.capacity.put(capacity)
            self.vpp.log("Added capacity %skWh" % capacity)

        while True:
            try:
                yield self.env.timeout(1)
            except simpy.Interrupt as i:
                self.log("Charging interrupted! %s" % i.cause)
                self.log(
                    "Last SoC: %s%%, current SoC: %s%%" % (self.battery.level, self.soc)
                )

                charged_amount = self.soc - self.battery.level
                if charged_amount > 0:
                    yield self.battery.put(charged_amount)
                    self.log("Charged battery for %s%%" % charged_amount)
                elif charged_amount < 0:
                    self.warning(
                        "Data inconsistency."
                        " Battery lost %s%% but should have been charging. Adjusting..."
                        % charged_amount
                    )
                    yield self.battery.get(-charged_amount)
                    self.log("Charged battery for %s%%" % charged_amount)
                else:
                    self.warning(
                        "Battery level did not change, but should have been charging."
                    )

                break

        # TODO: Adjust VPP capacity during charging?
        if capacity != 0:
            self.vpp.log(
                "Removing EV %s from VPP: Decrease capacity by %skWh"
                % (self.name, capacity)
            )
            yield self.vpp.capacity.get(capacity)
            self.vpp.log("Removed capacity %skWh" % capacity)

    def drive(self, rental, duration, trip_charge, start_soc, dest_charging_station):
        # Remeber SoC on the begging of rental to fix inconsistencies
        # between simulated SoC and the the data.
        self.soc = start_soc

        self.logger.info(
            "[%s] - --------- RENTAL %d of %s--------"
            % (datetime.fromtimestamp(self.env.now), rental, self.name)
        )

        # Interrupt Charging or Parking
        if not self.action.triggered:
            self.action.interrupt("Customer starts driving.")

        # Pause 1 second to allow charging station to adjust battery levels
        # before we correct based on data
        yield self.env.timeout(1)
        # Fix battery levels based on real data
        if self.battery.level != start_soc:
            self.warning(
                "SoC is %s%% at start of trip %d."
                "It should be %s%% based on previous trip. Adjusting..."
                % (start_soc, rental, self.battery.level)
            )
            diff = start_soc - self.battery.level
            if diff < 0:
                yield self.battery.get(-diff)
                self.warning(
                    "EV lost %s%% battery while beeing idle."
                    "How much can a EV loose standing around?"
                    % diff
                )
            else:
                yield self.battery.put(diff)
                self.warning(
                    "EV gained %s%% battery while beeing idle. At charging station?"
                    % diff
                )

        if self.battery.level < trip_charge:
            self.error("Not enough battery for the planned trip %d!" % rental)
            return

        # Drive for the trip duration
        yield self.env.timeout((duration * 60) - 2)  # seconds

        # Adjust SoC
        self.logger.info(
            "[%s] - --------- END RENTAL %d --------"
            % (datetime.fromtimestamp(self.env.now), rental)
        )
        self.log(
            "Drove for %.2f minutes on trip %s and consumed %s%% charge."
            % (duration, rental, trip_charge)
        )
        if trip_charge > 0:
            self.log("Adjusting battery level...")
            yield self.battery.get(trip_charge)
            self.log("Battery level has been decreased by %s%%." % trip_charge)
        elif trip_charge < 0:
            self.warning(
                "Battery has been charged for %s%% on trip %d which lasted %s minutes."
                % (-trip_charge, rental, duration)
            )
            yield self.battery.put(-trip_charge)
            self.log("Battery level has been increased by %s%%." % -trip_charge)
        else:
            self.warning(
                "No battery has been consumed on trip %d which lasted %s minutes."
                % (rental, duration)
            )

        if bool(dest_charging_station):
            self.action = self.env.process(self.charge())
        else:
            self.action = self.env.process(self.idle())
