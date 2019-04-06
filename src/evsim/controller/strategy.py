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
    pb, pi = None, None
    try:
        pb = controller.predict_clearing_price(controller.balancing_market, timeslot)
    except ValueError as e:
        controller.warning(e)
    try:
        pi = controller.predict_clearing_price(controller.intraday_market, timeslot)
    except ValueError as e:
        controller.warning(e)

    profit = 0
    if pb and pi and (pi > pb):
        profit += balancing(controller, timeslot, risk=risk)
    elif pb:
        profit += balancing(controller, timeslot, risk=risk)

    profit += intraday(controller, timeslot, risk=0)
    return profit


def market_strategy(controller, market, plan, timeslot, leadtime, risk, accuracy):
    market_period = timeslot + leadtime
    mp_dt = datetime.fromtimestamp(market_period)

    if int(market_period / 60) % 15 != 0:
        controller.log("Not a bidding period.")
        return 0

    if plan.get(market_period) != 0:
        controller.log("Already bid for %s in %s"(market.__name__, mp_dt))
        return 0

    # Predict clearing price
    try:
        cp = market.clearing_price(market_period)
    except ValueError as e:
        controller.warning("Not bidding: %s" % e)
        return 0

    if cp > controller.cfg.industry_tariff:
        controller.log(
            "The industry tariff is cheaper (%.2f > %.2f)"
            % (cp, controller.cfg.industry_tariff)
        )
        return 0

    # Predict available charging power
    try:
        charging_power = controller.predict_min_capacity(market_period, accuracy)
    except ValueError as e:
        controller.warning("Not bidding: %s" % e)
        return 0
    controller.log(
        "Predicted %.2f available charging power at %s." % (charging_power, mp_dt)
    )

    # Reduce quantity if already something bought
    quantity = charging_power - controller.planned_kw(market_period)
    # Deduct risk factor from quantity
    quantity = quantity * (1 - risk)

    # Actual Bidding
    controller.log(
        "Bidding for %.2f charging power at %s. Evaluated risk %.2f"
        % (quantity, mp_dt, risk)
    )
    bid = Bid(market_period, cp, quantity)
    successful = market.place_bid(bid)
    if successful:
        controller.log(
            "Bought %.2f kWh for %.2f EUR/MWh for 15-min timeslot %s"
            % (bid.quantity * (15 / 60), bid.price, mp_dt)
        )
    else:
        controller.log("Bid unsuccessful")
        return 0

    # Update consumption plan for control periods
    for t in [0, 5, 10]:
        plan.add(bid.marketperiod + (60 * t), bid.quantity)

    profit = _bid_profit(bid, controller.cfg.industry_tariff)
    return profit


def _bid_profit(bid, industry_tariff):
    # Quantity MWh * (cheaper tariff)
    profit = (bid.quantity * (15 / 60) / 1000) * (industry_tariff - bid.price)
    profit = round(profit, 2)
    return profit
