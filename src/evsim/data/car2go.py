from datetime import datetime
import logging
import numpy as np
import pandas as pd

import evsim

logger = logging.getLogger(__name__)


def process(df):
    """Executes all preprocessing steps sequentially"""

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

    df_trips = add_charging_stations(df_trips, df_stations)
    df_trips = clean_trips(df_trips)
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
    rent = set()
    vpp = dict()
    charging = dict()
    total = set()
    df_charging = list()

    # Maximal SoC of an EV to be eligible for VPP.
    max_soc = (
        (evsim.MAX_EV_CAPACITY - evsim.TIME_UNIT_CHARGE) / evsim.MAX_EV_CAPACITY * 100
    )

    df["start_time"] = df["start_time"].apply(
        lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
    )
    df["end_time"] = df["end_time"].apply(
        lambda x: datetime.fromtimestamp(x).replace(second=0, microsecond=0)
    )

    timeslots = np.sort(pd.unique(df[["start_time", "end_time"]].values.ravel("K")))
    for t in timeslots:
        # 1. Each timestep (5min) plugged-in EVs charge linearly
        charging, vpp = _simulate_charge(charging, vpp, max_soc)

        # 2. Remove EVs from VPP when not enough available
        # battery capacity for next charge
        vpp = {k: v for k, v in vpp.items() if v <= max_soc}

        # 3. Starting EVs may be new to the fleet. Add to total EVs
        starting_evs = df.loc[df["start_time"] == t]
        total.update(set(starting_evs.EV))

        # 4. Trip-Ending EVs are available
        ending_evs = df.loc[df["end_time"] == t]
        rent, charging, vpp = _make_available(ending_evs, rent, charging, vpp, max_soc)

        # 4. Trip-Starting EVs are unavailable
        rent, charging, vpp = _make_unavailable(starting_evs, rent, charging, vpp)

        avg_soc = 0
        if len(charging) > 0:
            avg_soc = sum(charging.values()) / len(charging)

        df_charging.append((t, len(rent), len(charging), len(vpp), avg_soc, len(total)))

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
        * evsim.MAX_EV_CAPACITY
        * (100 - df_charging["ev_charging_soc_avg"])
        / 100
    )

    df_charging["available_charging_capacity_kw"] = (
        df_charging["ev_available_vpp"] * evsim.CHARGING_SPEED
    )

    df_charging = df_charging.set_index("timestamp").sort_index()
    return df_charging


def _make_unavailable(evs, rent, charging, vpp):
    rent.difference_update(set(evs.EV))

    # Starting EVs are not connected to charger anymore
    for ev in set(evs.EV):
        charging.pop(ev, None)
        vpp.pop(ev, None)

    return (rent, charging, vpp)


def _make_available(evs, rent, charging, vpp, max_soc):
    rent.update(set(evs.EV))

    charging_evs = evs.loc[evs["end_charging"] == 1]
    charging.update(dict(zip(charging_evs.EV, evs.end_soc)))
    # EVs are only eligible for VPP when they have enough available battery capacity
    vpp_evs = charging_evs.loc[charging_evs["end_soc"] <= max_soc]
    vpp.update(dict(zip(vpp_evs.EV, vpp_evs.end_soc)))

    return (rent, charging, vpp)


def _simulate_charge(charging, vpp, max_soc):
    # Increment is the amount of electricity that EVs charge during 5 Minutes
    increment = 100 * (evsim.TIME_UNIT_CHARGE / 3) / evsim.MAX_EV_CAPACITY

    for k in charging:
        if charging[k] <= max_soc:
            charging[k] += increment
        else:
            charging[k] = 100

    # No condition is needed here since EVs are not part of VPP when fully charged
    vpp.update((k, v + increment) for k, v in vpp.items())

    return (charging, vpp)


def calculate_trips(df_car):
    trips = list()
    prev = df_car.iloc[0]
    for row in df_car.itertuples():
        if (row.coordinates_lat != prev.coordinates_lat) | (
            row.coordinates_lon != prev.coordinates_lon
        ):
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

    return (trip_charge / 100) * evsim.MAX_EV_RANGE


def clean_trips(df):
    """
        Remove service trips (longer than 2 days) from trip data.
        When EV ended at a charging station, make
        previous trip end at charging station.

        Effects on Simulation:
          - Earlier charging of EV, if it has been parked at a charging
            station on the service trip.
          - Higher SoC in Sim than in the real data, since trips has been removed.
    """
    df = _end_charging_previous_trip(df)

    df_service = df.loc[df["trip_duration"] > 2 * 24 * 60]
    df.drop(df_service.index, inplace=True)

    logger.info("Removed %d trips that were longer than 2 days." % len(df_service))
    return df


def _end_charging_previous_trip(df):
    trips = list()

    num_trips = 0
    for ev in df["EV"].unique():
        df_car = df[df["EV"] == ev].reset_index().drop(["index"], axis=1)
        service_trips_idx = df_car[
            (df_car["trip_duration"] > 60 * 24 * 2)
            & ((df_car["end_charging"] == 1) | (df_car["trip_distance"].isna()))
        ].index

        for i in service_trips_idx:
            if i > 0:
                df_car.iat[i - 1, df_car.columns.get_loc("end_charging")] = 1

        trips.append(df_car)
        num_trips += len(service_trips_idx)

    df_trips = pd.concat(trips)
    df_trips = df_trips.sort_values("start_time").reset_index().drop(["index"], axis=1)
    logger.info("Changed %d trips to end at a charging station." % num_trips)
    return df_trips
