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

    def at_charger(self):
        self.log("At a charging station!")

        # Only add to VPP if enough battery cpacity to charge next timeslot
        capacity_left = (
            (self.battery.capacity - self.battery.level) * vppsim.MAX_EV_CAPACITY / 100
        )
        if capacity_left >= vppsim.CHARGING_SPEED / (60 / vppsim.TIME_UNIT_CHARGE):
            self.vpp.log(
                "Adding EV %s to VPP: Increase capacity by %skW..."
                % (self.name, vppsim.CHARGING_SPEED)
            )
            yield self.vpp.capacity.put(vppsim.CHARGING_SPEED)
            self.vpp.log("Added capacity %skWh" % vppsim.CHARGING_SPEED)
        else:
            self.vpp.log(
                "Not adding EV %s to VPP, not enough free battery capacity(%.2f)"
                % (self.name, capacity_left)
            )

        while True:
            try:
                # TODO: Charge with timesteps
                if self.battery.level < 100:
                    self.battery.put(self.battery.capacity - self.battery.level)

                # END_TODO
                yield self.env.timeout(1)
            except simpy.Interrupt as i:
                self.log("Charging interrupted! %s" % i.cause)
                break

        # TODO: Check if EV is in VPP, see above condition
        self.vpp.log(
            "Removing EV %s from VPP: Decrease capacity by %skW"
            % (self.name, vppsim.CHARGING_SPEED)
        )
        yield self.vpp.capacity.get(vppsim.CHARGING_SPEED)
        self.vpp.log("Removed capacity %skW" % vppsim.CHARGING_SPEED)

    def drive(self, rental, duration, trip_charge, end_charger):
        self.logger.info(
            "[%s] - --------- RENTAL %d of %s--------"
            % (datetime.fromtimestamp(self.env.now), rental, self.name)
        )

        # Interrupt Charging or Parking
        if not self.action.triggered:
            self.action.interrupt("Start trip %d.")
        else:
            self.log.warning("Something weird happened :o")

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
            "End Trip %d : Drove for %.2f minutes and consumed %s%% charge."
            % (rental, duration, trip_charge)
        )

        self.log("Adjusting battery level...")
        yield self.battery.get(trip_charge)
        self.log("Battery level has been decreased by %s%%." % trip_charge)

        if bool(end_charger):
            self.action = self.env.process(self.at_charger())
        else:
            self.action = self.env.process(self.idle())
