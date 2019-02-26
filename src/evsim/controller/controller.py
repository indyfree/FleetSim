from operator import attrgetter
from datetime import datetime
import logging

from evsim.data import loader


class Controller:
    def __init__(self, strategy):
        self.logger = logging.getLogger(__name__)

        self.consumption_plan = dict()
        self.fleet_capacity = loader.load_car2go_capacity()
        self.balancing_prices = loader.load_balancing_prices()
        self.intraday_prices = loader.load_intraday_prices()
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

    def bid(self, market, timeslot, price, quantity):
        """ Bid at intraday market given the price in EUR/MWh and quantity in kW
            at a given timeslot (string/datetime).
            Takes dataframe of the market as input.
        """
        if market == "intraday":
            cp = self._clearing_price(self.intraday_prices, timeslot)
        elif market == "balancing":
            cp = self._clearing_price(self.balancing_prices, timeslot)
        else:
            raise ValueError("Market does not exists: %s" % market)

        if price >= cp:
            return (timeslot, quantity, price)

        return None

    def predict_clearing_price(self, df, timeslot):
        """ Predict the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the predicted price in EUR/MWh.
        """

        # TODO: Distort data for Prediction
        return self._clearing_price(df, timeslot)

    def predict_capacity(self, df, timeslot):
        """ Predict the available capacity for at a given 5min timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the predicted price capacity in kW.
        """
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

    def _clearing_price(self, df, timeslot):
        """ Get the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the clearing price in EUR/MWh.
        """
        try:
            return df.loc[df["product_time"] == timeslot, "clearing_price_mwh"].iat[0]
        except IndexError:
            raise ValueError(
                "Retrieving clearing price failed: %s is not in data." % timeslot
            )
