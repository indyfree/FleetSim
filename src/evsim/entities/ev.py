from datetime import datetime
import logging
import simpy


class EV:
    def __init__(self, env, vpp, name, soc, battery_capacity, charging_speed):
        self.logger = logging.getLogger(__name__)

        # Battery capacity in percent
        self.battery = simpy.Container(env, init=soc, capacity=100)
        self.env = env
        self.name = name
        self.vpp = vpp
        self.action = None

        self.charging_step = self._charging_step(battery_capacity, charging_speed, 5)

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

    def charge_full(self):
        timestep = 5
        while self.battery.capacity > self.battery.level:
            try:
                self.log("Charging...")
                yield self.env.timeout(timestep * 60)  # Minutes
                free = self.battery.capacity - self.battery.level
                self.battery.put(min(self.charging_step, free))
                self.log("Charged battery for %.2f%%." % self.charging_step)
            except simpy.Interrupt as i:
                self.log("Charging interrupted! %s" % i.cause)
                break

        self.log("Battery full!")
        # Remove from VPP when full or not charging anymore
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
            self.log("At a charging station!")

            # Only add to VPP if enough battery capacity to charge next timeslot
            if self.battery.capacity - self.battery.level >= self.charging_step:
                self.vpp.add(self)
            else:
                self.vpp.log(
                    "Not adding EV %s to VPP, not enough free battery capacity(%.2f)"
                    % (self.name, self.battery.capacity - self.battery.level)
                )

            self.action = self.env.process(self.charge_full())
        else:
            self.log("Parked where no charger around")

    def _charging_step(self, battery_capacity, charging_speed, control_period):
        """ Returns the SoC increase given the control period in minutes """

        kwh_per_control_period = (charging_speed / 60) * control_period
        soc_per_control_period = 100 * kwh_per_control_period / battery_capacity
        return soc_per_control_period
