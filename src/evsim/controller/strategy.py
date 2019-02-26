from datetime import datetime, timedelta
import pandas as pd


def regular(env, controller, fleet, timestep):
    """ Charge all EVs at regular prices"""

    evs = controller.dispatch(
        fleet, criteria="battery.level", n=len(fleet) - 5, timestep=timestep
    )
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))


def balancing(env, controller, fleet, timestep):
    """ Charge predicted available EVs with balancing electricity
        charge others from regular electricity tariff"""

    # 1. Bid for every 15-minute slot of the next day at 16:00
    # NOTE: Look up exact balancing mechanism
    if datetime.fromtimestamp(env.now).hour == 16:
        tomorrow = datetime.now().date() + timedelta(days=1)
        intervals = pd.date_range(
            start=tomorrow, end=tomorrow + timedelta(days=1), freq="15min"
        )[:-1]

        for t in intervals:
            try:
                update_consumption_plan(env, controller, controller.balancing, t, 250)
            except ValueError as e:
                controller.error(env, "Could not update consumption plan: %s" % e)

    # 2. Charge from balancing if in consumption plan
    # TODO Pass EV capacity as param or use number EVs
    num_balancing_evs = int(controller.get_consumption(env.now) // 17.6)
    try:
        controller.dispatch(
            env, fleet, criteria="battery.level", n=num_balancing_evs, timestep=timestep
        )
        controller.log(
            env,
            "Charging %d/%d EVs from balancing market."
            % (num_balancing_evs, len(fleet)),
        )
    except ValueError as e:
        controller.error(env, str(e))

    # 3. Charge remaining EVs regulary
    num_regular_evs = len(fleet) - num_balancing_evs
    try:
        controller.dispatch(
            env,
            fleet,
            criteria="battery.level",
            n=num_regular_evs,
            descending=True,
            timestep=timestep,
        )
        controller.log(
            env, "Charging %d/%d EVs regulary." % (num_regular_evs, len(fleet))
        )
    except ValueError as e:
        controller.error(env, str(e))


def intraday(env, controller, fleet, timestep):
    """ Charge predicted available EVs with intraday electricity
        charge others from regular electricity tariff"""

    # NOTE: Assumption: 30min ahead we can procure at price >= clearing price
    t = datetime.fromtimestamp(env.now + (60 * 30))

    # 1. Bid for 15-min timeslots
    if t.minute % 15 == 0:
        try:
            update_consumption_plan(env, controller, controller.intraday, t, 250)
        except ValueError as e:
            controller.error(env, "Could not update consumption plan: %s" % e)

    # 2. Charge from intraday if in consumption plan
    # TODO Pass EV capacity as param or use number EVs
    num_intraday_evs = int(controller.get_consumption(env.now) // 17.6)
    try:
        controller.dispatch(
            env, fleet, criteria="battery.level", n=num_intraday_evs, timestep=timestep
        )
        controller.log(
            env,
            "Charging %d/%d EVs from intraday market." % (num_intraday_evs, len(fleet)),
        )
    except ValueError as e:
        controller.error(env, str(e))

    # 3. Charge remaining EVs regulary
    num_regular_evs = len(fleet) - num_intraday_evs
    try:
        controller.dispatch(
            env,
            fleet,
            criteria="battery.level",
            n=num_regular_evs,
            descending=True,
            timestep=timestep,
        )
        controller.log(
            env, "Charging %d/%d EVs regulary." % (num_regular_evs, len(fleet))
        )
    except ValueError as e:
        controller.error(env, str(e))


def update_consumption_plan(env, controller, market, timeslot, industry_tariff):
    predicted_clearing_price = controller.predict_clearing_price(market, timeslot)
    if predicted_clearing_price > industry_tariff:
        controller.log(env, "The industry tariff is cheaper.")
        return

    available_capacity = controller.predict_capacity(timeslot)
    if available_capacity == 0:
        controller.log(env, "No available capacity predicted.")
        return None

    # NOTE: Simple strategy to always bid at predicted clearing price
    bid = market.bid(timeslot, predicted_clearing_price, available_capacity)
    if bid is None:
        controller.log(env, "Bid unsuccessful")
        return
    elif bid[0] in controller.consumption_plan:
        raise ValueError("%s was already in consumption plan" % bid[0])
    else:
        controller.log(
            env,
            "Bought %.2f kW for %.2f EUR/MWh for 15-min timeslot %s"
            % (bid[1], bid[2], bid[0]),
        )

        # TODO: Better data structure to save 15 min consumption plan
        # TODO: Save prices
        # TODO: Check timestamp() utc??
        # Bought capacity will be for 3 * 5-min timeslots
        for t in [0, 5, 10]:
            time = bid[0] + timedelta(minutes=t)
            controller.consumption_plan[time.timestamp()] = bid[1]
