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
        self.action = None

        self.log("Added to fleet!")

    def error(self, message):
        self.logger.error(
            "[%s] - %s(%.2f/%s) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                self.name,
                self.battery.level,
                self.battery.capacity,
                message,
            )
        )

    def log(self, message):
        self.logger.info(
            "[%s] - %s(%.2f/%s) %s"
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
            "[%s] - %s(%.2f/%s) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                self.name,
                self.battery.level,
                self.battery.capacity,
                message,
            )
        )

    def at_charger(self):
        self.log("At a charging station!")

        # Only add to VPP if enough battery capacity to charge next timeslot
        if self.battery.capacity - self.battery.level >= vppsim.CHARGING_STEP_SOC:
            self.vpp.add(self)
        else:
            self.vpp.log(
                "Not adding EV %s to VPP, not enough free battery capacity(%.2f)"
                % (self.name, self.battery.capacity - self.battery.level)
            )

        while True:
            try:
                yield self.env.timeout(5 * 60)  # 5 Minutes

                self.log("Charging...")
                free_battery = self.battery.capacity - self.battery.level
                if free_battery >= vppsim.CHARGING_STEP_SOC:
                    self.battery.put(vppsim.CHARGING_STEP_SOC)
                    self.log("Charged battery for %.2f%%" % vppsim.CHARGING_STEP_SOC)
                else:
                    if free_battery > 0:
                        self.battery.put(free_battery)

                    self.log("Battery full")
                    break

            except simpy.Interrupt as i:
                self.log("Charging interrupted! %s" % i.cause)
                break

        if self.vpp.contains(self):
            self.vpp.remove(self)

    def drive(self, rental, duration, trip_charge, end_charger):

        self.log("Starting trip %d." % rental)
        # Interrupt Charging
        if self.action is not None and not self.action.triggered:
            self.action.interrupt("Customer wants to rent car")

        if trip_charge > 0 and self.battery.level < trip_charge:
            self.error("Not enough battery for the planned trip %d!" % rental)
            return

        # Drive for the trip duration
        yield self.env.timeout((duration * 60) - 1)  # seconds

        # Adjust SoC
        self.log(
            "End Trip %d: Drove for %.2f minutes and consumed %s%% charge."
            % (rental, duration, trip_charge)
        )

        self.log("Adjusting battery level...")
        # Special case: Battery has been charged without appearing in data
        if trip_charge < 0:
            self.warning(
                "EV was already at charging station. Battery level: %d. Trip charge: %d"
                % (self.battery.level, trip_charge)
            )

            free_battery = self.battery.capacity - self.battery.level
            if free_battery > 0 and -trip_charge >= free_battery:
                yield self.battery.put(self.battery.capacity - self.battery.level)
                self.warning(
                    "Battery charged more than available space. Filled up to 100."
                )
            elif -trip_charge < free_battery:
                yield self.battery.put(-trip_charge)
                self.log("Battery level has been increased by %s%%." % -trip_charge)
            else:
                self.log("Battery is still full")
        elif trip_charge > 0:
            yield self.battery.get(trip_charge)
            self.log("Battery level has been decreased by %s%%." % trip_charge)
        else:
            self.log("No consumed charge!")

        # TODO: Use real bool from data
        if end_charger == 1:
            self.action = self.env.process(self.at_charger())
