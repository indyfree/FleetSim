class Market:
    def __init__(self, data):
        self.data = data

    def bid(self, timeslot, price, quantity):
        """ Bid at intraday market given the price in EUR/MWh and quantity in kW
            at a given timeslot (string/datetime).
            Takes dataframe of the market as input.
        """

        # NOTE: Simplified bidding behavior
        cp = self.clearing_price(timeslot)
        if cp is None:
            return None
        elif price >= cp:
            return (timeslot, quantity, price)

    def clearing_price(self, timeslot):
        """ Get the clearing price for a 15-min contract at a given timeslot.
        Takes a dataframe and timeslot (string/datetime) as input.
        Returns the clearing price in EUR/MWh.
        """
        try:
            return self.data.loc[
                self.data["product_time"] == timeslot, "clearing_price_mwh"
            ].iat[0]
        except IndexError:
            raise ValueError(
                "Retrieving clearing price failed: %s is not in data." % timeslot
            )
