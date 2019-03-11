from datetime import datetime, timedelta, time
from operator import attrgetter
import pandas as pd


def regular(env, controller, timestep):
    """ Charge all EVs at regular prices"""

    try:
        controller.dispatch(env, controller.vpp.evs.values(), timestep=timestep)
    except ValueError as e:
        controller.error(env, "Could not charge: %s" % str(e))


def balancing(env, controller, timestep):
    """ Charge predicted available EVs with balancing electricity
        charge others from regular electricity tariff"""

    # 1. Bid for every 15-minute slot of the next day at 16:00
    # NOTE: Look up exact balancing mechanism
    dt = datetime.fromtimestamp(env.now)
    if dt.time() == time(16, 0):
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

    # 2. Charge from balancing if in consumption plan, regulary else
    _charge_consumption_plan(env, controller, timestep)


def intraday(env, controller, timestep):
    """ Charge predicted available EVs with intraday electricity
        charge others from regular electricity tariff"""

    # NOTE: Assumption: 30min ahead we can procure at price >= clearing price
    dt = datetime.fromtimestamp(env.now + (60 * 30))

    # 1. Bid for 15-min timeslots
    if dt.minute % 15 == 0:
        try:
            _update_consumption_plan(
                env, controller, controller.intraday, dt.timestamp()
            )
        except ValueError as e:
            controller.error(env, "Could not update consumption plan: %s" % e)

    # 2. Charge from balancing if in consumption plan, regulary else
    _charge_consumption_plan(env, controller, timestep)


def _charge_consumption_plan(env, controller, timestep):
    cap = controller.charger_capacity
    n_plan = int(controller.consumption_plan.get(env.now, 0) // cap)

    controller.log(
        env,
        "Consumption plan for %s: %.2fkW, required EVs: %d."
        % (
            datetime.fromtimestamp(env.now),
            controller.consumption_plan.get(env.now, 0),
            n_plan,
        ),
    )

    if n_plan > len(controller.vpp.evs):
        controller.warning(
            env,
            "Commited %.2fkW capacity, but only %.2fkw available,  account for imbalance costs!"
            % (n_plan * cap, len(controller.vpp.evs) * cap),
        )
        controller.vpp.imbalance += (n_plan - len(controller.vpp.evs)) * cap

        # Charge all possible EVs from consumption plan
        n_plan = len(controller.vpp.evs)

    # TODO: When always charging ALL EVs, sorting and splitting makes no sense
    # Sort fleet according to ascending battery level
    fleet = sorted(
        controller.vpp.evs.values(), key=attrgetter("battery.level"), reverse=True
    )
    plan_evs = fleet[: n_plan + 1]
    regular_evs = fleet[n_plan + 1 :]

    # 2. Charge from consumption plan
    controller.dispatch(env, plan_evs, timestep=timestep)
    controller.log(
        env, "Charging %d/%d EVs from consumption plan." % (len(plan_evs), len(fleet))
    )

    # 3. Charge remaining EVs regulary
    controller.dispatch(env, regular_evs, timestep=timestep)
    controller.log(env, "Charging %d/%d EVs regulary." % (len(regular_evs), len(fleet)))


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
            "Bought %.2f kW for %.2f EUR/MWh for 15-min timeslot %s"
            % (bid[1], bid[2], datetime.fromtimestamp(bid[0])),
        )

        # TODO: Better data structure to save 15 min consumption plan
        # TODO: Save prices
        # TODO: Check timestamp() utc??
        # Bought capacity will be for 3 * 5-min timeslots
        for t in [0, 5, 10]:
            time = bid[0] + (60 * t)
            controller.consumption_plan[time] = bid[1]
