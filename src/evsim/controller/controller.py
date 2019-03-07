from operator import attrgetter
from datetime import datetime
import logging
import sys

from evsim.data import loader
from evsim.market import Market


class Controller:
    def __init__(self, strategy, charger_capacity=0, industry_tariff=0):
        self.logger = logging.getLogger(__name__)

        self.consumption_plan = dict()
        self.balancing = Market(loader.load_balancing_prices())
        self.intraday = Market(loader.load_intraday_prices())
        self.fleet_capacity = loader.load_car2go_capacity()
        self.strategy = strategy

        self.charger_capacity = charger_capacity
        self.industry_tariff = industry_tariff

        self.vpp = None

    def charge_fleet(self, env, fleet, industry_tariff, timestep):
        """ Perform a charging operation on the fleet for a given timestep.
            Takes a a list of EVs as input and charges given its strategy.
        """

        self.vpp.commited_capacity = self.consumption_plan.get(env.now, 0)
        self.strategy(env, self, fleet, timestep)

    def log(self, env, message, level=None):
        if level is None:
            level = self.logger.info

        level(
            "[%s] - %s(%s) %s"
            % (
                datetime.fromtimestamp(env.now),
                type(self).__name__,
                self.strategy.__name__,
                message,
            )
        )

    def error(self, env, message):
        self.log(env, message, self.logger.error)

    def warning(self, env, message):
        self.log(env, message, self.logger.warning)

    def dispatch(self, env, fleet, criteria, n, timestep, descending=False):
        """Dispatches n EVs from fleet according to EV attribute"""
        if n > len(fleet):
            raise ValueError(
                "Cannot dispatch %d EVs, only %d available" % (n, len(fleet))
            )
        elif n < 0:
            raise ValueError("Cannot dispatch negative number of EVs %d" % n)

        evs = sorted(fleet, key=attrgetter(criteria), reverse=descending)[:n]
        for ev in evs:
            ev.action = env.process(ev.charge_timestep(timestep))

    # TODO: Distort data for Prediction
    def predict_capacity(self, env, timeslot):
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

    def predict_min_capacity(self, env, timeslot):
        """ Predict the minimum available capacity for a given 15min timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted fleet capacity in kW.
        """
        cap = sys.maxsize
        for t in [0, 5, 10]:
            try:
                cap = min(cap, self.predict_capacity(env, timeslot + (60 * t)))
            except ValueError:
                pass

        if cap == sys.maxsize:
            raise ValueError(
                "Capacity prediction failed: 15 min timeslot %s is not in data."
                % datetime.fromtimestamp(timeslot)
            )
        return cap

    # TODO: Distort data for Prediction
    def predict_clearing_price(self, market, timeslot, accuracy=100):
        """ Predict the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the predicted price in EUR/MWh.
        """

        return market.clearing_price(timeslot)
