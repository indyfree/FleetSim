from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Bid:
    marketperiod: int
    price: float
    quantity: float


class Market:
    def __init__(self, data):
        self.data = data

    def place_bid(self, bid):
        """ Bid at intraday market given the price in EUR/MWh and quantity in kW
            at a given timeslot (POSIX timestamp).
            Takes dataframe of the market as input.
        """

        # NOTE: Simplified bidding behavior
        cp = self.clearing_price(bid.marketperiod)
        if cp is None:
            return False
        elif bid.price >= cp:
            return True

    def clearing_price(self, timeslot):
        """ Get the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (POSIX timestamp) as input.
        Returns the clearing price in EUR/MWh.
        """
        # Market data has datetime format timeslots
        dt = datetime.fromtimestamp(timeslot)
        try:
            return self.data.loc[
                self.data["product_time"] == dt, "clearing_price_mwh"
            ].iat[0]
        except IndexError:
            raise ValueError(
                "Retrieving clearing price failed: %s is not in data." % dt
            )
