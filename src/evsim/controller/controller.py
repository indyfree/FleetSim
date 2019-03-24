from datetime import datetime
import logging
from operator import attrgetter

from evsim.data import load
from evsim.market import Market


class Controller:
    def __init__(self, cfg, strategy, risk=0, refuse_rentals=True):
        self.logger = logging.getLogger(__name__)

        self.cfg = cfg

        self.balancing = Market(load.balancing_prices())
        self.balancing_plan = ConsumptionPlan("Balancing")

        self.intraday = Market(load.intraday_prices())
        self.intraday_plan = ConsumptionPlan("Intraday")

        self.fleet_capacity = load.simulation_baseline()
        self.strategy = strategy

        # Risk parameter set from outside
        self._risk = risk

        # Reference simulation objects
        self.env = None
        self.account = None
        self.vpp = None

        # Strategy specific optionals
        self.refuse_rentals = refuse_rentals

    def log(self, message, level=None):
        if level is None:
            level = self.logger.info

        level(
            "[%s] - %s(%s) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                type(self).__name__,
                self.strategy.__name__,
                message,
            )
        )

    def error(self, message):
        self.log(message, self.logger.error)

    def warning(self, message):
        self.log(message, self.logger.warning)

    @property
    def risk(self):
        return self._property

    @risk.setter
    def risk(self, value):
        if 0 > value or value > 1:
            raise ValueError(
                "Only risk factors between 0 and 1 are valid: %.2f" % value
            )
        self._risk = value

    def charge_fleet(self, timeslot):
        """ Perform a charging operation on the fleet for a given timeslot.
            Takes a a list of EVs as input and charges given its strategy.
        """

        # 1. Sort according to charging priority
        # TODO: Improve dispatch order
        available_evs = sorted(
            self.vpp.evs.values(), key=attrgetter("battery.level"), reverse=True
        )

        # 2. Charge balancing
        available_evs = self.charge_plan(timeslot, available_evs, self.balancing_plan)
        # 3. Charge intraday
        available_evs = self.charge_plan(timeslot, available_evs, self.intraday_plan)

        # 4. Charge remaining EVs regulary
        self.log(
            "Charging %d/%d EVs regulary." % (len(available_evs), len(self.vpp.evs))
        )
        self.dispatch(available_evs)

        # 5. Execute Bidding strategy
        self.strategy(self, timeslot, self._risk)

    def charge_plan(self, timeslot, available_evs, plan):
        """ Charge according to a predifined consumption plan"""

        planned_kw = plan.pop(timeslot)
        num_plan_evs = int(planned_kw // self.cfg.charging_power)
        self.log(
            "Consumption plan (%s): %.2fkWh, required EVs: %d."
            % (plan.name, planned_kw * (15 / 60), num_plan_evs)
        )

        # 1. Handle overcommitments
        if num_plan_evs > len(available_evs):
            imbalance_kw = (num_plan_evs - len(available_evs)) * self.cfg.charging_power
            self.vpp.imbalance += imbalance_kw * (15 / 60)
            self.warning(
                (
                    "Commited %d EVs, but only %d available,  "
                    "account for imbalance costs of %.2fkWh!"
                )
                % (num_plan_evs, len(available_evs), imbalance_kw * (15 / 60))
            )

            # Charge available EVs
            num_plan_evs = len(available_evs)

        # 2. Dispatch Charging from plan
        plan_evs = available_evs[:num_plan_evs]
        self.log(
            "Charging %d/%d EVs from %s plan."
            % (len(plan_evs), len(self.vpp.evs), plan.name)
        )
        self.dispatch(plan_evs)
        self.vpp.total_charged += (len(plan_evs) * self.cfg.charging_power) * (15 / 60)

        rest_evs = available_evs[num_plan_evs:]
        return rest_evs

    def dispatch(self, evs):
        """Dispatches EVs to charging"""
        for ev in evs:
            ev.action = ev.charge_timestep()

    def planned_kw(self, t):
        return self.balancing_plan.get(t) + self.intraday_plan.get(t)

    # TODO: Distort data for Prediction
    def predict_capacity(self, timeslot, accuracy=100):
        """ Predict the available capacity for a given 5min timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted fleet capacity in kW.
        """
        df = self.fleet_capacity
        try:
            return df.loc[df["timestamp"] == timeslot, "vpp_capacity_kw"].iat[0]
        except IndexError:
            raise ValueError(
                "Capacity prediction failed: %s is not in data."
                % datetime.fromtimestamp(timeslot)
            )

    def predict_min_capacity(self, timeslot, accuracy=100):
        """ Predict the minimum available capacity for a given 15min timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted fleet capacity in kW.
        """
        cap = float("inf")
        for t in [0, 5, 10]:
            try:
                cap = min(cap, self.predict_capacity(timeslot + (60 * t)))
            except ValueError:
                pass

        if cap == float("inf"):
            raise ValueError(
                "Capacity prediction failed: 15 min timeslot %s is not in data."
                % datetime.fromtimestamp(timeslot)
            )
        return cap

    # TODO: Distort data for Prediction?
    def predict_clearing_price(self, market, timeslot, accuracy=100):
        """ Predict the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted price in EUR/MWh.
        """

        return market.clearing_price(timeslot)


class ConsumptionPlan:
    def __init__(self, name):
        self.name = name
        self.plan = dict()

    def __repr__(self):
        return repr((self.plan))

    def add(self, timestamp, capacity):
        if timestamp in self.plan:
            raise ValueError(
                "%s was already in consumption plan" % datetime.fromtimestamp(timestamp)
            )

        self.plan[timestamp] = capacity

    def get(self, timestamp):
        return self.plan.get(timestamp, 0)

    def pop(self, timestamp):
        return self.plan.pop(timestamp, 0)
