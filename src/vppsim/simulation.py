#!/usr/bin/env python

from datetime import datetime
import logging
import simpy
import os

from vppsim.entities import EV, VPP
from vppsim.data import loader

# PHYSICAL CONSTANTS
CHARGING_SPEED = 4.6  # 4.6 kWh per hour
MAX_EV_CAPACITY = 17.6  # kWh
MAX_EV_RANGE = 160  # km
TIME_UNIT = 15  # Minutes
TIME_UNIT_CHARGE = CHARGING_SPEED / (60 / TIME_UNIT)  # kwh

CHARGING_STEP_KWH = CHARGING_SPEED / (60 / 5)  # kwh in 5 minutes charging
CHARGING_STEP_SOC = (
    100 * CHARGING_STEP_KWH / MAX_EV_CAPACITY
)  # SoC in 5 minutes charging


def main():
    logger = setup_logger()
    df = loader.load_car2go_trips()

    env = simpy.Environment(initial_time=df.start_time.min())
    vpp = VPP(env, "VPP-1", num_evs=len(df.EV.unique()))
    env.process(lifecycle(logger, env, vpp, df))

    logger.info(
        "[%s] - ---- STARTING SIMULATION -----" % datetime.fromtimestamp(env.now)
    )
    env.run(until=df.end_time.max())


def lifecycle(logger, env, vpp, df):
    evs = {}
    previous = df.iloc[0, :]

    for rental in df.itertuples():

        # Wait until next rental
        yield env.timeout(rental.start_time - previous.start_time)  # sec

        if rental.EV not in evs:
            logger.info(
                "[%s] - ---------- NEW EV %d ----------"
                % (datetime.fromtimestamp(env.now), rental.Index)
            )
            evs[rental.EV] = EV(env, vpp, rental.EV, rental.start_soc)

        ev = evs[rental.EV]
        env.process(
            ev.drive(
                rental.Index,
                rental.trip_duration,
                rental.start_soc - rental.end_soc,
                rental.end_charging,
            )
        )
        previous = rental


def setup_logger():
    os.makedirs("./logs", exist_ok=True)

    # Log to file
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)-10s: %(levelname)-7s %(message)s",
        filename="./logs/sim-%s.log" % datetime.now().strftime("%Y%m%d-%H%M%S"),
        filemode="w",
    )
    logger = logging.getLogger("vppsim")

    # Also log to stdout
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    logging.getLogger("").addHandler(console)

    return logger


if __name__ == "__main__":
    main()
