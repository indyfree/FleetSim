from datetime import datetime
from . import controller


def regular(env, controller, fleet, timestep):
    """ Charge all EVs at regular prices"""

    evs = controller.dispatch(fleet, criteria="battery.level", n=len(fleet) - 5)
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))


def intraday(env, controller, fleet, timestamp):
    """ Charge available EVs with intraday electricity
        charge others with regulary"""

    # 1. Predict available capacity +30min
    t = env.now
    dt = datetime.fromtimestamp(t + (60 * 30))
    capacity = controller.predict_capacity(controller.fleet_capacity, dt)

    # 2. Bid capacity at intraday market when predicted price cheaper than regular tariff
    clearing_price = controller.predict_clearing_price(controller.intraday_prices, dt)
    bid = controller.bid(controller.intraday_prices, dt, clearing_price + 0.5, capacity)

    if bid is not None:
        controller.log(
            env,
            "Bought %2.f kW for %2.f EUR/MWh for 15-min timeslot %s"
            % (bid[2], bid[1], bid[0]),
        )
    else:
        controller.log(env, "Nothing bought")

    # 3. Save in a day ahead consumption plan (t --> (quantity,price))

    return True
