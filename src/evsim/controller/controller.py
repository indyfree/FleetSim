from operator import attrgetter
from datetime import datetime
import logging

from evsim.data import loader


class Controller:
    def __init__(self, strategy):
        self.logger = logging.getLogger(__name__)

        self.fleet_capacity = loader.load_car2go_capacity()
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

    def dispatch(self, fleet, criteria, n):
        """Return n EVs from fleet according to ascending EV criteria"""
        s = sorted(fleet, key=attrgetter(criteria))
        return s[:n]

    def bid(self, df, timeslot, price, quantity):
        """ Bid at intraday market given the price in EUR/MWh and quantity in kW
            at a given timeslot.
            Takes dataframe of the market as input.
        """

        # NOTE: Simplified auction process
        # TODO: Predict --> Real clearing price
        cp = self.predict_clearing_price(df, timeslot)
        if price >= cp:
            return (timeslot, price, quantity)

        return None

    def predict_clearing_price(self, df, timeslot):
        """ Predict the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the predicted price in EUR/MWh.
        """
        try:
            # TODO: Distort data --> Prediction
            return df.loc[df["delivery_date"] == timeslot, "unit_price_eur_mwh"].iat[0]
        except IndexError:
            raise ValueError(
                "%s is not in data. Specify in 15 minute intervals between %s and %s"
                % (timeslot, df["delivery_date"].min(), df["delivery_date"].max())
            )

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
            raise ValueError(
                "%s is not in data. Specify 5 minute intervals between %s and %s"
                % (
                    timeslot,
                    datetime.fromtimestamp(df["timestamp"].min()),
                    datetime.fromtimestamp(df["timestamp"].max()),
                )
            )
