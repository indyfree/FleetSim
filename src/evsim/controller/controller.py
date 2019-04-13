from datetime import datetime
import logging
from operator import attrgetter
import random

from evsim.data import load
from evsim.market import Market


class Controller:
    def __init__(
        self, cfg, strategy, accuracy=(100, 100), risk=(0, 0), imbalance_costs=1000
    ):
        self.logger = logging.getLogger(__name__)

        self.cfg = cfg
        self.account = Account()
        self.strategy = strategy
        self.accuracy = accuracy

        self.balancing_plan = ConsumptionPlan("Balancing")
        self.intraday_plan = ConsumptionPlan("Intraday")

        # NOTE: When regular strategy no need for capacity and price data
        if strategy.__name__ != "regular":
            self.fleet_capacity = load.simulation_baseline()
            self.balancing_market = Market(load.balancing_prices())
            self.intraday_market = Market(load.intraday_prices())

        # Risk parameter set from outside, i.e. RL Agent
        self._risk = risk
        # Imbalance Costs for learning
        self.imbalance_costs = imbalance_costs

        # Reference simulation objects
        self.env = None
        self.vpp = None

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
        return self._risk

    @risk.setter
    def risk(self, value):
        b, i = value
        if 0 > b or b > 1:
            raise ValueError("Only risk factors between 0 and 1 are valid: %s" % b)
        if 0 > i or i > 1:
            raise ValueError("Only risk factors between 0 and 1 are valid: %s" % i)
        self._risk = value

    def planned_kw(self, t):
        return self.balancing_plan.get(t) + self.intraday_plan.get(t)

    def charge_fleet(self, timeslot):
        """ Perform a charging operation on the fleet for a given timeslot.
            Takes a a list of EVs as input and charges given its strategy.
        """

        # 1. Sort according to charging priority
        available_evs = sorted(
            self.vpp.evs.values(), key=attrgetter("battery.level"), reverse=True
        )

        # 2. Charge balancing
        vpp_charged_kwh, imbalance_kwh = 0, 0
        available_evs, charged, imbalance = self.charge_plan(
            timeslot, available_evs, self.balancing_plan
        )
        vpp_charged_kwh += charged
        imbalance_kwh += imbalance

        # 3. Charge intraday
        available_evs, charged, imbalance = self.charge_plan(
            timeslot, available_evs, self.intraday_plan
        )
        vpp_charged_kwh += charged
        imbalance_kwh += imbalance

        # 4. Charge remaining EVs regulary
        self.log(
            "Charging %d/%d EVs regulary." % (len(available_evs), len(self.vpp.evs))
        )
        self.dispatch(available_evs)
        regular_charged_kwh = self._evs_to_kwh(len(available_evs))

        # 5. Execute Bidding strategy
        profit = self.strategy(self, timeslot, self.risk, self.accuracy)

        # 6. Account for cost and profits
        imbalance_eur = imbalance_kwh * self.imbalance_costs
        self.account.subtract(imbalance_eur)
        self.account.add(profit)

        self.log(
            "Charge for %.2f EUR less than regularly. Current balance: %.2f EUR."
            % (profit, self.account.balance)
        )

        return profit, vpp_charged_kwh, regular_charged_kwh, imbalance_kwh

    def charge_plan(self, timeslot, available_evs, plan):
        """ Charge according to a predifined consumption plan"""

        planned_kw = plan.pop(timeslot)
        num_plan_evs = int(planned_kw // self.cfg.charging_power)
        self.log(
            "Consumption plan (%s): %.2fkWh, required EVs: %d."
            % (plan.name, planned_kw * (15 / 60), num_plan_evs)
        )

        # 1. Handle overcommitments
        imbalance_kwh = 0
        if num_plan_evs > len(available_evs):
            imbalance_kwh = self._evs_to_kwh(num_plan_evs - len(available_evs))
            self.warning(
                (
                    "Commited %d EVs, but only %d available,  "
                    "account for imbalance costs of %.2fkWh!"
                )
                % (num_plan_evs, len(available_evs), imbalance_kwh)
            )

            # Charge remaining available EVs
            num_plan_evs = len(available_evs)

        # 2. Dispatch Charging from plan
        plan_evs = available_evs[:num_plan_evs]
        self.log(
            "Charging %d/%d EVs from %s plan."
            % (len(plan_evs), len(self.vpp.evs), plan.name)
        )
        self.dispatch(plan_evs)
        charged_kwh = self._evs_to_kwh(len(plan_evs))

        rest_evs = available_evs[num_plan_evs:]
        return rest_evs, charged_kwh, imbalance_kwh

    def dispatch(self, evs):
        """Dispatches EVs to charging"""
        for ev in evs:
            ev.action = ev.charge_timestep()

    # TODO: Better distort data for prediction
    def predict_capacity(self, timeslot, accuracy=100):
        """ Predict the available capacity for a given 5min timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted fleet capacity in kW.
        """
        df = self.fleet_capacity
        try:

            # NOTE: Simple uniform distortion.
            # Improve by gaussian with mean = accuracy
            range = 1 - (accuracy / 100)
            distortion = random.uniform(1 - range, 1 + range)  # e.g. [0.9, 1.1]
            cap = df.loc[df["timestamp"] == timeslot, "vpp_charging_power_kw"].iat[0]
            return cap * distortion
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
                cap = min(cap, self.predict_capacity(timeslot + (60 * t), accuracy))
            except ValueError:
                pass

        if cap == float("inf"):
            raise ValueError(
                "Capacity prediction failed: 15 min timeslot %s is not in data."
                % datetime.fromtimestamp(timeslot)
            )

        self.log(
            "Predicted %.2fkw available charging power at %s with %d%% accuracy."
            % (cap, datetime.fromtimestamp(timeslot), accuracy)
        )
        return cap

    def _evs_to_kwh(self, nb_evs):
        return (nb_evs * self.cfg.charging_power) * (15 / 60)


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


class Account:
    def __init__(self, balance=0):
        self.balance = balance
        self.rental_profits = 0
        self.lost_rental_eur = 0
        self.lost_rental_nb = 0

    def add(self, amount):
        self.balance += amount

    def subtract(self, amount):
        self.balance -= amount

    def rental(self, price):
        self.rental_profits += price

    def lost_rental(self, price):
        self.lost_rental_eur += price
        self.lost_rental_nb += 1

    def lost_rental_reset(self):
        self.lost_rental_eur = 0
        self.lost_rental_nb = 0
