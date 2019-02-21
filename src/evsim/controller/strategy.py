from datetime import datetime


def regular(env, controller, fleet, timestep):
    """ Charge all EVs at regular prices"""

    evs = controller.dispatch(fleet, criteria="battery.level", n=len(fleet) - 5)
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))


def intraday(env, controller, fleet, timestep):
    """ Charge available EVs with intraday electricity
        charge others with regulary"""

    # NOTE: Assumption: 30min ahead we can procure at price >= clearing price
    t = datetime.fromtimestamp(env.now + (60 * 30))

    # Only bid for 15-min timeslots
    if t.minute % 15 == 0:
        bid = _submit_bid(
            env, controller, controller.fleet_capacity, controller.intraday_prices, t
        )

        if not bid:
            controller.log(env, "Nothing bought.")
        elif bid[0] in controller.consumption_plan:
            raise ValueError("%s was already in consumption plan" % bid[0])
        else:
            controller.log(
                env,
                "Bought %.2f kW for %.2f EUR/MWh for 15-min timeslot %s"
                % (bid[1], bid[2], bid[0]),
            )
            # 3. Save in a day ahead consumption plan (t --> (quantity,price))
            controller.consumption_plan[bid[0].timestamp()] = bid[1]

    # Intraday charging
    if env.now in controller.consumption_plan:
        controller.log(
            env,
            "Charge %.2fkW from intraday market."
            % controller.consumption_plan[env.now],
        )

    # Regular charging
    evs = controller.dispatch(fleet, criteria="battery.level", n=len(fleet) - 5)
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))


def _submit_bid(env, controller, df_capacity, df_intraday, timeslot):
    try:
        clearing_price = controller.predict_clearing_price(
            controller.intraday_prices, timeslot
        )
    except ValueError as e:
        controller.warning(env, "Submitting bid failed %s: %s." % (timeslot, e))
        return None

    # We don't want to buy more expensive than Industry tariff
    # TODO: Parametrize and verify Industry Tariff
    if clearing_price > 250:
        controller.log(env, "The industry tariff is cheaper.")
        return None

    # Predict available capacity at t
    capacity = 0
    try:
        capacity = controller.predict_capacity(df_capacity, timeslot)
    except ValueError as e:
        controller.warning(env, "Submitting bid failed %s: %s." % (timeslot, e))
        return None

    if capacity == 0:
        controller.log(env, "No capacity predicted.")
        return None

    # Submit bid for predicted capacity at t
    return controller.bid(
        controller.intraday_prices, timeslot, clearing_price, capacity
    )
