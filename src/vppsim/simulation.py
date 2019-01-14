#!/usr/bin/env python

from datetime import datetime
import logging
import pandas as pd
import simpy
import os

from evsim.entities import EV, VPP
from evsim.data import loader

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

    stats = []
    stat_filename = "./logs/stats-%s.csv" % datetime.now().strftime("%Y%m%d-%H%M%S")

    env = simpy.Environment(initial_time=df.start_time.min())
    vpp = VPP(env, "BALANCING", num_evs=len(df.EV.unique()))
    env.process(lifecycle(logger, env, vpp, df, stats))

    logger.info(
        "[%s] - ---- STARTING SIMULATION -----" % datetime.fromtimestamp(env.now)
    )
    env.run(until=df.end_time.max())

    save_stats(stats, stat_filename, datetime.fromtimestamp(env.now), vpp)


def lifecycle(logger, env, vpp, df, stats):
    evs = {}
    previous = df.iloc[0, :]

    for rental in df.itertuples():

        # Wait until next rental
        yield env.timeout(rental.start_time - previous.start_time)  # sec
        if rental.start_time - previous.start_time > 0:
            logger.info(
                "[%s] - ---------- TIMESLOT %s ----------"
                % (datetime.fromtimestamp(env.now), datetime.fromtimestamp(env.now))
            )

        if rental.EV not in evs:
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

        stats.append(
            [
                datetime.fromtimestamp(env.now),
                len(vpp.evs),
                vpp.avg_soc(),
                vpp.capacity(),
            ]
        )


def save_stats(stats, filename, timestamp, vpp):
    df_stats = pd.DataFrame(
        data=stats, columns=["timestamp", "ev_vpp", "vpp_soc", "vpp_capacity_kw"]
    )
    df_stats = df_stats.groupby("timestamp").last()
    df_stats = df_stats.reset_index()
    df_stats.to_csv(filename, index=False)
    df_stats.to_csv("./logs/stats.csv", index=False)


def setup_logger():
    os.makedirs("./logs", exist_ok=True)

    # Log to file
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)-10s: %(levelname)-7s %(message)s",
        filename="./logs/sim-%s.log" % datetime.now().strftime("%Y%m%d-%H%M%S"),
        filemode="w",
    )
    logger = logging.getLogger("evsim")

    # Also log to stdout
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    console.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    logging.getLogger("").addHandler(console)

    return logger


if __name__ == "__main__":
    main()
