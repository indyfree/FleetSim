from datetime import datetime
import logging
import numpy as np
import pandas as pd

import vppsim

logger = logging.getLogger(__name__)


def process_car2go(df):
    df_trips = pd.DataFrame()
    for car in df["name"].unique():
        df_car = df[df["name"] == car]
        # TODO: Append with .loc
        df_trips = df_trips.append(calculate_trips(df_car))

    return df_trips.sort_values("start_time").reset_index().drop("index", axis=1)


def calculate_car2go_demand(df):
    available = set()
    charging = dict()
    total = set()
    df_charging = list()

    df["start_time"] = df["start_time"].apply(
        lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
    )
    df["end_time"] = df["end_time"].apply(
        lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
    )

    timeslots = np.sort(pd.unique(df[["start_time", "end_time"]].values.ravel("K")))
    for t in timeslots:
        evs_start = set(df[df["start_time"] == t].EV)
        total.update(evs_start)
        # Starting EVs are non-available
        available.difference_update(evs_start)
        for ev in evs_start:
            charging.pop(ev, None)

        # EVs end trip so make them available
        trips_end = df.loc[df["end_time"] == t]
        available.update(set(trips_end.EV))

        # Track EVs which parked at a charging station
        trips_end_charging = df.loc[(df["end_time"] == t) & (df["end_charging"] == 1)]
        charging.update(dict(zip(trips_end_charging.EV, trips_end_charging.end_soc)))

        avg_soc = 0
        if len(charging) > 0:
            avg_soc = sum(charging.values()) / len(charging)

        # Save number of available EVs
        df_charging.append((t, len(available), len(charging), avg_soc, len(total)))

    df_charging = pd.DataFrame(
        df_charging,
        columns=[
            "timestamp",
            "ev_available",
            "ev_charging",
            "ev_charging_soc_avg",
            "total_ev",
        ],
    )

    df_charging["capacity_available_kwh"] = (
        df_charging["ev_charging"]
        * vppsim.MAX_EV_CAPACITY
        * (100 - df_charging["ev_charging_soc_avg"])
        / 100
    )
    df_charging = df_charging.set_index("timestamp").sort_index()
    return df_charging


def calculate_trips(df_car):
    trips = list()
    prev = df_car.iloc[0]
    for row in df_car.itertuples():
        if row.address != prev.address:
            trips.append(
                [
                    prev.name,
                    prev.timestamp,
                    prev.address,
                    prev.coordinates_lat,
                    prev.coordinates_lon,
                    prev.fuel,
                    row.timestamp,
                    row.address,
                    row.coordinates_lat,
                    row.coordinates_lon,
                    row.fuel,
                    row.charging,
                    int((row.timestamp - prev.timestamp) / 60),
                    trip_distance(prev.fuel - row.fuel),
                ]
            )
        prev = row

    return pd.DataFrame(
        trips,
        columns=[
            "EV",
            "start_time",
            "start_address",
            "start_lat",
            "start_lon",
            "start_soc",
            "end_time",
            "end_address",
            "end_lat",
            "end_lon",
            "end_soc",
            "end_charging",
            "trip_duration",
            "trip_distance",
        ],
    )


def trip_distance(trip_charge):
    MAX_DISTANCE = 106  # km

    # EV has been charged on the trip. Not possible to infer distance
    if trip_charge < 0:
        return np.nan

    return (MAX_DISTANCE / 100) * trip_charge


# TODO: Clean trips
def clean_trips(df):
    # - Date
    # - Trips > 2d
    # - Trips where charged?
    return df
