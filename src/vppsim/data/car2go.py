from datetime import datetime
import logging
import numpy as np
import pandas as pd

import vppsim

logger = logging.getLogger(__name__)


def process(df):

    # Preprocesing
    # GPS accuracy is only guaranteed at a granularity of 10m, round accordingly.
    # See also: https://wiki.openstreetmap.org/wiki/Precision_of_coordinates.
    df[["coordinates_lat", "coordinates_lon"]] = df[
        ["coordinates_lat", "coordinates_lon"]
    ].round(4)
    df_stations = determine_charging_stations(df)

    df.sort_values("timestamp", inplace=True)

    trips = list()
    cars = df["name"].unique()
    logger.info("Determining trips of %d cars..." % len(cars))
    for car in cars:
        ev_trips = calculate_trips(df[df["name"] == car])
        trips.append(ev_trips)

    df_trips = pd.concat(trips)
    df_trips = df_trips.sort_values("start_time").reset_index().drop("index", axis=1)

    df_trips = clean_trips(df_trips)
    df_trips = add_charging_stations(df_trips, df_stations)
    return df_trips


def add_charging_stations(df_trips, df_stations):
    df_trips = df_trips.merge(
        df_stations,
        left_on=["end_lat", "end_lon"],
        right_on=["coordinates_lat", "coordinates_lon"],
        how="left",
    )

    df_trips.drop(["coordinates_lat", "coordinates_lon"], axis=1, inplace=True)
    df_trips.rename(columns={"charging": "end_charging"}, inplace=True)
    return df_trips


def determine_charging_stations(df):
    """Find charging stations where EV has been charged once (charging==1)."""

    df_stations = df.groupby(["coordinates_lat", "coordinates_lon"])["charging"].max()
    df_stations = df_stations[df_stations == 1]
    df_stations = df_stations.reset_index()
    logger.info("Determined %d charging stations in the dataset" % len(df_stations))
    return df_stations


def calculate_capacity(df):
    available_rent = set()
    available_vpp = set()
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
        # Starting EVs may be new to the fleet. Add to total EVs
        total.update(evs_start)

        # Starting EVs are not available for rent or vpp
        available_rent.difference_update(evs_start)
        available_vpp.difference_update(evs_start)

        # Starting EVs are not charging anymore
        for ev in evs_start:
            charging.pop(ev, None)

        # EVs end trip so make them available for rent
        trips_end = df.loc[df["end_time"] == t]
        available_rent.update(set(trips_end.EV))

        # Track EVs which parked at a charging station
        trips_end_charging = trips_end.loc[trips_end["end_charging"] == 1]
        charging.update(dict(zip(trips_end_charging.EV, trips_end_charging.end_soc)))

        # Track EVs which have enough evailable battery capacity to be charged in a
        # timeslot and thus are available to use as VPP
        trips_available_vpp = trips_end_charging.loc[
            trips_end_charging["end_soc"]
            <= (
                (vppsim.MAX_EV_CAPACITY - vppsim.TIME_UNIT_CHARGE)
                / vppsim.MAX_EV_CAPACITY
            )
            * 100
        ]
        available_vpp.update(set(trips_available_vpp.EV))

        avg_soc = 0
        if len(charging) > 0:
            avg_soc = sum(charging.values()) / len(charging)

        # Save number of available_rent EVs
        df_charging.append(
            (
                t,
                len(available_rent),
                len(charging),
                len(available_vpp),
                avg_soc,
                len(total),
            )
        )

    df_charging = pd.DataFrame(
        df_charging,
        columns=[
            "timestamp",
            "ev_available_rent",
            "ev_charging",
            "ev_available_vpp",
            "ev_charging_soc_avg",
            "total_ev",
        ],
    )

    df_charging["available_battery_capacity_kwh"] = (
        df_charging["ev_charging"]
        * vppsim.MAX_EV_CAPACITY
        * (100 - df_charging["ev_charging_soc_avg"])
        / 100
    )

    df_charging["available_charging_capacity_kw"] = (
        df_charging["ev_available_vpp"] * vppsim.CHARGING_SPEED
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
            "trip_duration",
            "trip_distance",
        ],
    )


def trip_distance(trip_charge):
    # EV has been charged on the trip. Not possible to infer distance
    if trip_charge < 0:
        return np.nan

    return (trip_charge / 100) * vppsim.MAX_EV_RANGE


def clean_trips(df):
    # Trips longer than 2 days are service trips
    df_trips = df.loc[df["trip_duration"] < (2 * 24 * 60)]
    logger.info(
        "Removed %.2f%% trips that were longer than 2 days"
        % ((len(df) - len(df_trips)) / len(df))
    )

    trips = len(df_trips)
    # Trips where no distance could be determined have been charged on a trip
    df_trips = df_trips.loc[df["trip_distance"].notna()]
    logger.info(
        "Removed %.2f%% trips that were charged on a trip"
        % ((trips - len(df_trips)) / len(df))
    )

    return df_trips
