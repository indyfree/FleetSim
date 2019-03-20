from datetime import datetime, timedelta, time
import pandas as pd

from evsim.market import Bid


def regular(controller, timeslot):
    """ Charge all EVs at regular prices"""
    pass


# TODO: Change for weekly bids!
def balancing(controller, timeslot, accuracy=100, risk=0):
    """ Benchmark bidding strategy for balancing market only"""

    # Bid for every 15-minute slot of the next day at 16:00
    dt = datetime.fromtimestamp(timeslot)
    if dt.time() != time(16, 0):
        controller.log("Not a bidding period at balancing market.")
        return

    tomorrow = dt.date() + timedelta(days=1)
    market_periods = pd.date_range(
        start=tomorrow, end=tomorrow + timedelta(days=1), freq="15min"
    )[:-1]

    for m in market_periods:
        try:
            ts = m.to_pydatetime().timestamp()
            available_capacity = controller.predict_min_capacity(ts, accuracy)
            quantity = available_capacity * (1 - risk)
            controller.log(
                "Bidding for timeslot %s at balancing market."
                % datetime.fromtimestamp(ts)
            )

            _update_consumption_plan(
                controller,
                controller.balancing,
                controller.balancing_plan,
                ts,
                quantity,
            )
        except ValueError as e:
            controller.warning("Could not update consumption plan: %s." % e)


def intraday(controller, timeslot, accuracy=100, risk=0):
    """ Benchmark bidding strategy for intraday market only"""

    # Bid for 15-min market period m 30 min ahead
    # NOTE: Assumption: 30min(!) ahead we can always procure
    # with a bidding price >= clearing price
    m = timeslot + (60 * 30)
    if int((m / 60)) % 15 == 0:
        controller.log(
            "Bidding for timeslot %s at intraday market." % datetime.fromtimestamp(m)
        )
        try:
            available_capacity = controller.predict_min_capacity(m, accuracy)
            charging_balancing = controller.balancing_plan.get(m)
            quantity = (available_capacity - charging_balancing) * (1 - risk)
            _update_consumption_plan(
                controller, controller.intraday, controller.intraday_plan, m, quantity
            )
        except ValueError as e:
            controller.warning(e)
    else:
        controller.log("Not a bidding period at intraday market.")


def integrated(controller, timestamp):
    """ Charge predicted available EVs according to an integrated strategy:

    1. Charge predicted amount from balancing one week ahead if cheaper than intraday
    2. Charge predicted rest from intraday 30-min ahead
    3. Charge rest regulary(?)

    """
    # TODO: Skip bidding balancing if intraday price better
    balancing(controller, timestamp, risk=0.7)
    intraday(controller, timestamp, risk=0)


def _update_consumption_plan(controller, market, consumption_plan, timeslot, quantity):
    """ Updates the consumption plan for a given timeslot (POSIX timestamp)
    """

    try:
        predicted_clearing_price = controller.predict_clearing_price(market, timeslot)
    except ValueError as e:
        controller.warning(e)
        return None

    if predicted_clearing_price > controller.cfg.industry_tariff:
        controller.log(
            "The industry tariff is cheaper (%.2f > %.2f)"
            % (predicted_clearing_price, controller.cfg.industry_tariff)
        )
        return None

    # NOTE: Simple strategy to always bid at predicted clearing price
    bid = Bid(timeslot, predicted_clearing_price, quantity)
    try:
        successful = market.place_bid(bid)
    except ValueError as e:
        controller.warning(e)
        return None

    if successful is False:
        controller.log("Bid unsuccessful")
        return
    elif consumption_plan.get(timeslot) != 0:
        raise ValueError(
            "%s was already in consumption plan"
            % datetime.fromtimestamp(bid.marketperiod)
        )
    else:
        controller.log(
            "Bought %.2f kWh for %.2f EUR/MWh for 15-min timeslot %s"
            % (
                bid.quantity * (15 / 60),
                bid.price,
                datetime.fromtimestamp(bid.marketperiod),
            )
        )

        _account_bid(controller, bid)

        # TODO: Better data structure to save 15 min consumption plan
        for t in [0, 5, 10]:
            time = bid.marketperiod + (60 * t)
            consumption_plan.add(time, bid.quantity)


def _account_bid(controller, bid):
    # Quantity MWh: (kw * h / 1000)
    quantity_mwh = bid.quantity * (15 / 60) / 1000
    costs = quantity_mwh * bid.price
    regular_costs = quantity_mwh * controller.cfg.industry_tariff
    revenue = regular_costs - costs

    costs = (bid.quantity * (15 / 60) / 1000) * (
        controller.cfg.industry_tariff - bid.price
    )
    controller.account.add(revenue)
    controller.log(
        "Charge for %.2f EUR less than regularly. Current balance: %.2f EUR."
        % (costs, controller.account.balance)
    )
