from datetime import datetime, timedelta, time
from operator import attrgetter
import pandas as pd


def regular(env, controller, timestep):
    """ Charge all EVs at regular prices"""
    pass


def balancing(env, controller, timestep):
    """ Charge predicted available EVs with balancing electricity
        charge others from regular electricity tariff"""

    # 1. Charge from balancing if in consumption plan, regulary else
    _charge_consumption_plan(env, controller, timestep)

    # 2. Bid for every 15-minute slot of the next day at 16:00
    dt = datetime.fromtimestamp(env.now)
    if dt.time() != time(16, 0):
        return

    tomorrow = dt.date() + timedelta(days=1)
    intervals = pd.date_range(
        start=tomorrow, end=tomorrow + timedelta(days=1), freq="15min"
    )[:-1]

    for i in intervals:
        try:
            ts = i.to_pydatetime().timestamp()
            _update_consumption_plan(env, controller, controller.balancing, ts)
        except ValueError as e:
            controller.error(env, "Could not update consumption plan: %s" % e)


def intraday(env, controller, timestep):
    """ Charge predicted available EVs with intraday electricity
        charge others from regular electricity tariff"""

    # 1. Charge from intraday if in consumption plan, regulary else
    _charge_consumption_plan(env, controller, timestep)

    # 2. Bid for 15-min market periods 30 min ahead
    # NOTE: Assumption: 30min(!) ahead we can procure at price >= clearing price
    m_30 = env.now + (60 * 30)
    if int((m_30 / 60)) % 15 == 0:
        try:
            _update_consumption_plan(env, controller, controller.intraday, m_30)
        except ValueError as e:
            controller.error(env, "Could not update consumption plan: %s" % e)


def integrated(env, controller, timestep):
    """ Charge predicted available EVs according to an integrated strategy:

    1. Charge predicted amount from balancing one week ahead if cheaper than intraday
    2. Charge predicted rest from intraday 30-min ahead
    3. Charge rest regulary(?)

    """
    #
    if dt.time() == time(16, 0):
        tomorrow = dt.date() + timedelta(days=1)
        intervals = pd.date_range(
            start=tomorrow, end=tomorrow + timedelta(days=1), freq="15min"
        )[:-1]

        for i in intervals:
            ts = i.to_pydatetime().timestamp()
            p_b = controller.predict_clearing_price(controller.balancing, ts)
            p_i = controller.predict_clearing_price(controller.intraday, ts)
            if p_b > p_i:
                try:
                    ts = i.to_pydatetime().timestamp()
                    _update_consumption_plan(env, controller, controller.balancing, ts)
                except ValueError as e:
                    controller.error(env, "Could not update consumption plan: %s" % e)
    pass


def _update_consumption_plan(env, controller, market, timeslot):
    """ Updates the consumption plan for a given timeslot (POSIX timestamp)
    """

    try:
        predicted_clearing_price = controller.predict_clearing_price(market, timeslot)
    except ValueError as e:
        controller.warning(env, e)
        return None

    if predicted_clearing_price > controller.industry_tariff:
        controller.log(env, "The industry tariff is cheaper.")
        return None

    try:
        available_capacity = controller.predict_min_capacity(env, timeslot)
    except ValueError as e:
        controller.warning(env, e)
        return None
    if available_capacity == 0:
        controller.log(env, "No available capacity predicted.")
        return None

    # NOTE: Simple strategy to always bid at predicted clearing price
    try:
        bid = market.bid(timeslot, predicted_clearing_price, available_capacity)
    except ValueError as e:
        controller.warning(env, e)
        return None

    if bid is None:
        controller.log(env, "Bid unsuccessful")
        return
    elif bid[0] in controller.consumption_plan:
        raise ValueError(
            "%s was already in consumption plan" % datetime.fromtimestamp(bid[0])
        )
    else:
        controller.log(
            env,
            "Bought %.2f kWh for %.2f EUR/MWh for 15-min timeslot %s"
            % (bid[1] * (15 / 60), bid[1], bid[2], datetime.fromtimestamp(bid[0])),
        )

        _account_bid(env, controller, bid)

        # TODO: Better data structure to save 15 min consumption plan
        # TODO: Save prices
        # TODO: Check timestamp() utc??
        # Bought capacity will be for 3 * 5-min timeslots
        for t in [0, 5, 10]:
            time = bid[0] + (60 * t)
            controller.consumption_plan[time] = bid[1]


def _account_bid(env, controller, bid):
    # Quantity MWh: (kw * h / 1000)
    quantity_mwh = bid[1] * (15 / 60) / 1000
    costs = quantity_mwh * bid[2]
    regular_costs = quantity_mwh * controller.industry_tariff
    revenue = regular_costs - costs

    costs = (bid[1] * (15 / 60) / 1000) * (controller.industry_tariff - bid[2])
    controller.account.add(revenue)
    controller.log(
        env,
        "Charge for %.2f EUR less than regularly. Current balance: %.2f EUR."
        % (costs, controller.account.balance),
    )
