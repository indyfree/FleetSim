from datetime import datetime, timedelta, time
import pandas as pd

from evsim.market import Bid


def regular(controller, timeslot, risk, accuracy=100):
    """ Charge all EVs at regular prices"""
    return 0


# TODO: Change for weekly bids!
def balancing_real(controller, timeslot, risk, accuracy=100):
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

            bid = _update_consumption_plan(
                controller,
                controller.balancing,
                controller.balancing_plan,
                ts,
                quantity,
            )
            profit = _account_bid(controller, bid)
            return profit
        except ValueError as e:
            controller.warning("Could not update consumption plan: %s." % e)


def balancing(controller, timeslot, risk, accuracy=100):
    """ Benchmark bidding strategy for balancing market only"""

    # Bid for 15-min market period 'm' one week ahead
    # Assumption: Always get accepted with a bidding price >= clearing price
    # NOTE: Bidding for 1 timeslot exactly 1 week ahead, not for whole week
    m = timeslot + (7 * (60 * 60 * 24))
    if int((m / 60)) % 15 != 0:
        return 0

    controller.log(
        "Bidding for timeslot %s at balancing market." % datetime.fromtimestamp(m)
    )
    try:
        available_capacity = controller.predict_min_capacity(m, accuracy)
        controller.log(
            "Predicted %.2f available charging power at %s."
            % (available_capacity, datetime.fromtimestamp(m))
        )
        quantity = available_capacity * (1 - risk)
        controller.log(
            "Bidding for %.2f charging power at %s. Evaluated risk %.2f"
            % (quantity, datetime.fromtimestamp(m), risk)
        )
        bid = _update_consumption_plan(
            controller, controller.balancing, controller.balancing_plan, m, quantity
        )
        profit = _account_bid(controller, bid)
        return profit
    except ValueError as e:
        controller.warning(e)
        return 0


def intraday(controller, timeslot, risk, accuracy=100):
    """ Benchmark bidding strategy for intraday market only"""

    # Bid for 15-min market period m 30 min ahead
    # NOTE: Assumption: 30min(!) ahead we can always procure
    # with a bidding price >= clearing price
    m = timeslot + (60 * 30)
    if int((m / 60)) % 15 != 0:
        controller.log("Not a bidding period at intraday market.")
        return 0

    controller.log(
        "Bidding for timeslot %s at intraday market." % datetime.fromtimestamp(m)
    )
    try:
        available_capacity = controller.predict_min_capacity(m, accuracy)
        controller.log(
            "Predicted %.2f available charging power at %s."
            % (available_capacity, datetime.fromtimestamp(m))
        )
        charging_balancing = controller.balancing_plan.get(m)
        quantity = (available_capacity - charging_balancing) * (1 - risk)
        controller.log(
            "Bidding for %.2f charging power at %s. Evaluated risk %.2f"
            % (quantity, datetime.fromtimestamp(m), risk)
        )
        bid = _update_consumption_plan(
            controller, controller.intraday, controller.intraday_plan, m, quantity
        )
        profit = _account_bid(controller, bid) if bid else 0
        return profit

    except ValueError as e:
        controller.warning(e)
        return 0


def integrated(controller, timeslot, risk, accuracy=100):
    """ Charge predicted available EVs according to an integrated strategy:

    1. Charge predicted amount from balancing one week ahead if cheaper than intraday
    2. Charge predicted rest from intraday 30-min ahead
    3. Charge rest regulary(?)

    """
    # TODO: Skip bidding balancing if intraday price better
    profit = 0
    profit += balancing(controller, timeslot, risk=risk)
    profit += intraday(controller, timeslot, risk=0)
    return profit


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

    bid = Bid(timeslot, predicted_clearing_price, quantity)
    try:
        successful = market.place_bid(bid)
    except ValueError as e:
        controller.warning(e)
        return None

    if successful is False:
        controller.log("Bid unsuccessful")
        return None
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

        # TODO: Better data structure to save 15 min consumption plan
        for t in [0, 5, 10]:
            time = bid.marketperiod + (60 * t)
            consumption_plan.add(time, bid.quantity)

        return bid


def _account_bid(controller, bid):
    # Quantity MWh: (kw * h / 1000)
    quantity_mwh = bid.quantity * (15 / 60) / 1000
    costs = quantity_mwh * bid.price
    regular_costs = quantity_mwh * controller.cfg.industry_tariff
    profit = regular_costs - costs

    costs = (bid.quantity * (15 / 60) / 1000) * (
        controller.cfg.industry_tariff - bid.price
    )
    controller.log(
        "Charge for %.2f EUR less than regularly. Current balance: %.2f EUR."
        % (costs, controller.account.balance)
    )
    return profit
