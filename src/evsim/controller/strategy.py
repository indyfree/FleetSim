from datetime import datetime
from evsim.market import Bid


def regular(controller, timeslot, risk, accuracy=100):
    """ Charge all EVs at regular prices"""
    return 0


def balancing(controller, timeslot, risk, accuracy=100):
    """ Benchmark bidding strategy for balancing market only"""

    # NOTE: Bidding for 1 timeslot exactly 1 week ahead, not for whole week
    # 7 days lead time
    leadtime = 7 * (60 * 60 * 24)
    return market_strategy(
        controller,
        controller.balancing_market,
        controller.balancing_plan,
        timeslot,
        leadtime,
        risk,
        accuracy,
    )


def intraday(controller, timeslot, risk, accuracy=100):
    """ Benchmark bidding strategy for intraday market only"""

    # 30 minute lead time
    leadtime = 60 * 30
    return market_strategy(
        controller,
        controller.intraday_market,
        controller.intraday_plan,
        timeslot,
        leadtime,
        risk,
        accuracy,
    )


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


def market_strategy(controller, market, plan, timeslot, leadtime, risk, accuracy):
    market_period = timeslot + leadtime

    if int(market_period / 60) % 15 != 0:
        controller.log("Not a bidding period.")
        return 0

    controller.log(
        "Bidding for timeslot %s at balancing market."
        % datetime.fromtimestamp(market_period)
    )
    try:
        available_capacity = controller.predict_min_capacity(market_period, accuracy)
        controller.log(
            "Predicted %.2f available charging power at %s."
            % (available_capacity, datetime.fromtimestamp(market_period))
        )
        available_capacity = available_capacity - controller.planned_kw(market_period)
        quantity = available_capacity * (1 - risk)
        controller.log(
            "Bidding for %.2f charging power at %s. Evaluated risk %.2f"
            % (quantity, datetime.fromtimestamp(market_period), risk)
        )
        bid = _update_consumption_plan(
            controller, market, plan, market_period, quantity
        )

        profit = _bid_profit(bid, controller.cfg.industry_tariff) if bid else 0
        return profit
    except ValueError as e:
        controller.warning(e)
        return 0


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


def _bid_profit(bid, industry_tariff):
    # Quantity MWh * (cheaper tariff)
    profit = (bid.quantity * (15 / 60) / 1000) * (industry_tariff - bid.price)
    profit = round(profit, 2)
    return profit
