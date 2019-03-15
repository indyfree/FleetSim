from datetime import datetime, timedelta, time
import pandas as pd


def regular(controller, timestamp):
    """ Charge all EVs at regular prices"""
    pass


# TODO: Change for weekly bids!
def balancing(controller, timestamp, ratio=1):
    """ Benchmark bidding strategy for balancing market only"""

    # Bid for every 15-minute slot of the next day at 16:00
    dt = datetime.fromtimestamp(timestamp)
    if dt.time() != time(16, 0):
        return

    tomorrow = dt.date() + timedelta(days=1)
    intervals = pd.date_range(
        start=tomorrow, end=tomorrow + timedelta(days=1), freq="15min"
    )[:-1]

    for i in intervals:
        try:
            ts = i.to_pydatetime().timestamp()
            quantity = controller.predict_min_capacity(ts) * ratio

            _update_consumption_plan(
                controller,
                controller.balancing,
                controller.balancing_plan,
                ts,
                quantity,
            )
        except ValueError as e:
            controller.warning("Could not update consumption plan: %s" % e)


def intraday(controller, timestamp, ratio=1):
    """ Benchmark bidding strategy for intraday market only"""

    # Bid for 15-min market periods 30 min ahead
    # NOTE: Assumption: 30min(!) ahead we can always procure
    # with a bidding price >= clearing price
    m_30 = timestamp + (60 * 30)
    if int((m_30 / 60)) % 15 == 0:
        try:
            quantity = controller.predict_min_capacity(m_30) * ratio
            _update_consumption_plan(
                controller,
                controller.intraday,
                controller.intraday_plan,
                m_30,
                quantity,
            )
        except ValueError as e:
            controller.warning("Could not update consumption plan: %s" % e)


def integrated(controller, timestamp):
    """ Charge predicted available EVs according to an integrated strategy:

    1. Charge predicted amount from balancing one week ahead if cheaper than intraday
    2. Charge predicted rest from intraday 30-min ahead
    3. Charge rest regulary(?)

    """
    # NOTE: Nice to have: If cannot bid at one market, bid at other
    # TODO: If intraday better price than balancing
    # balancing(controller, timestamp, 0.5)
    intraday(controller, timestamp, 1.1)


def _update_consumption_plan(controller, market, consumption_plan, timeslot, quantity):
    """ Updates the consumption plan for a given timeslot (POSIX timestamp)
    """

    try:
        predicted_clearing_price = controller.predict_clearing_price(market, timeslot)
    except ValueError as e:
        controller.warning(e)
        return None

    if predicted_clearing_price > controller.industry_tariff:
        controller.log("The industry tariff is cheaper.")
        return None

    # NOTE: Simple strategy to always bid at predicted clearing price
    try:
        bid = market.bid(timeslot, predicted_clearing_price, quantity)
    except ValueError as e:
        controller.warning(e)
        return None

    if bid is None:
        controller.log("Bid unsuccessful")
        return
    elif consumption_plan.get(timeslot) != 0:
        raise ValueError(
            "%s was already in consumption plan" % datetime.fromtimestamp(bid[0])
        )
    else:
        controller.log(
            "Bought %.2f kWh for %.2f EUR/MWh for 15-min timeslot %s"
            % (bid[1] * (15 / 60), bid[2], datetime.fromtimestamp(bid[0]))
        )

        _account_bid(controller, bid)

        # TODO: Better data structure to save 15 min consumption plan
        for t in [0, 5, 10]:
            time = bid[0] + (60 * t)
            consumption_plan.add(time, bid[1])


def _account_bid(controller, bid):
    # Quantity MWh: (kw * h / 1000)
    quantity_mwh = bid[1] * (15 / 60) / 1000
    costs = quantity_mwh * bid[2]
    regular_costs = quantity_mwh * controller.industry_tariff
    revenue = regular_costs - costs

    costs = (bid[1] * (15 / 60) / 1000) * (controller.industry_tariff - bid[2])
    controller.account.add(revenue)
    controller.log(
        "Charge for %.2f EUR less than regularly. Current balance: %.2f EUR."
        % (costs, controller.account.balance)
    )
