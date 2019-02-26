from operator import attrgetter
from datetime import datetime
import logging

from evsim.data import loader
from evsim.market import Market


class Controller:
    def __init__(self, strategy):
        self.logger = logging.getLogger(__name__)

        self.consumption_plan = dict()
        self.balancing = Market(loader.load_balancing_prices())
        self.intraday = Market(loader.load_intraday_prices())
        self.fleet_capacity = loader.load_car2go_capacity()
        self.strategy = strategy

    def charge_fleet(self, env, fleet, timestep):
        """ Perform a charging operation on the fleet for a given timestep.
            Takes a a list of EVs as input and charges given its strategy.
        """

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

    def dispatch(self, fleet, criteria, n, descending=False):
        """Return n EVs from fleet according to ascending EV criteria"""
        s = sorted(fleet, key=attrgetter(criteria), reverse=descending)
        return s[:n]

    # TODO: Distort data for Prediction
    def predict_capacity(self, timeslot):
        """ Predict the available capacity for at a given 5min timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the predicted price capacity in kW.
        """
        df = self.fleet_capacity
        try:
            # NOTE: df["timestamp"] is in unix timestamp format, cast accordingly
            if type(timeslot) is datetime:
                ts = timeslot.timestamp()
            elif type(timeslot) is str:
                ts = datetime.fromisoformat(timeslot).timestamp()

            return df.loc[df["timestamp"] == ts, "vpp_capacity_kw"].iat[0]
        except IndexError:
            self.error(
                "Specify 5 minute intervals between %s and %s"
                % (
                    timeslot,
                    datetime.fromtimestamp(df["timestamp"].min()),
                    datetime.fromtimestamp(df["timestamp"].max()),
                )
            )
            raise ValueError(
                "Capacity prediction failed: %s is not in data." % timeslot
            )

    # TODO: Distort data for Prediction
    def predict_clearing_price(self, market, timeslot, accuracy=100):
        """ Predict the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the predicted price in EUR/MWh.
        """

        return market.clearing_price(timeslot)
