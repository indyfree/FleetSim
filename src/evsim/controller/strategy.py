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

    # NOTE: Assumption: 30min ahead we can procure at price >= clearing price
    t = datetime.fromtimestamp(env.now + (60 * 30))

    # Only bid for 15-min timeslots
    if t.minute % 15 == 0:
        bid = _submit_bid(
            controller, controller.fleet_capacity, controller.intraday_prices, t
        )

        if bid:
            controller.log(
                env,
                "Bought %.2f kW for %.2f EUR/MWh for 15-min timeslot %s"
                % (bid[2], bid[1], bid[0]),
            )
        else:
            controller.log(env, "Nothing bought")

    # 3. Save in a day ahead consumption plan (t --> (quantity,price))

    return True


def _submit_bid(controller, df_capacity, df_intraday, timeslot):
    clearing_price = controller.predict_clearing_price(
        controller.intraday_prices, timeslot
    )

    # We don't want to buy more expensive than Industry tariff
    # TODO: Parametrize and verify Industry Tariff
    if clearing_price > 250:
        return None

    # Predict available capacity at t
    capacity = controller.predict_capacity(df_capacity, timeslot)
    print(capacity)
    # Submit bid for predicted capacity at t
    return controller.bid(
        controller.intraday_prices, timeslot, clearing_price, capacity
    )
