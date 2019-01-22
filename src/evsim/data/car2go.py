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
    # df_stations = determine_charging_stations(df)

    df.sort_values("timestamp", inplace=True)

    trips = list()
    cars = df["name"].unique()
    logger.info("Determining trips of %d cars..." % len(cars))
    for car in cars:
        ev_trips = calculate_trips(df[df["name"] == car])
        trips.append(ev_trips)

    df_trips = pd.concat(trips)
    df_trips = df_trips.sort_values("start_time").reset_index().drop("index", axis=1)
    logger.info(
        "Found %d trips, %d ended at a charging station."
        % (len(df_trips), len(df_trips[df_trips["end_charging"] == 1]))
    )

    # df_trips = add_charging_stations(df_trips, df_stations)
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
    if "end_charging" in df_trips.columns:
        df_trips.drop("end_charging", axis=1, inplace=True)

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
    charging = dict()
    fleet = dict()
    rent = dict()
    vpp = dict()

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

        # 3. Trip-Ending EVs are available
        ending_evs = df.loc[df["end_time"] == t]
        fleet, rent, charging, vpp = _end_trip(
            ending_evs, fleet, rent, charging, vpp, max_soc
        )

        # 4. Starting EVs may be new to the fleet. Add to fleet EVs.
        # Also make trip-starting EVs unavailable for rent and vpp.
        starting_evs = df.loc[df["start_time"] == t]
        fleet, rent, charging, vpp = _start_trip(
            starting_evs, fleet, rent, charging, vpp
        )

        df_charging.append(
            (
                t,
                len(fleet),
                _avg_soc(fleet),
                len(rent),
                _avg_soc(rent),
                len(charging),
                _avg_soc(charging),
                len(vpp),
                _avg_soc(vpp),
            )
        )

    df_charging = pd.DataFrame(
        df_charging,
        columns=[
            "timestamp",
            "fleet",
            "fleet_soc",
            "rent",
            "rent_soc",
            "charging",
            "charging_soc",
            "vpp",
            "vpp_soc",
        ],
    )

    df_charging["vpp_capacity_kw"] = df_charging["vpp"] * evsim.CHARGING_SPEED

    df_charging = df_charging.set_index("timestamp").sort_index()
    return df_charging


def _avg_soc(evs):
    avg_soc = 0
    if len(evs) > 0:
        avg_soc = sum(evs.values()) / len(evs)
    return avg_soc


def _start_trip(evs, fleet, rent, charging, vpp):
    # Update fleet SoC
    fleet.update(dict(zip(evs.EV, evs.start_soc)))

    # Starting EVs are note available for rent, charge, vpp
    for ev in set(evs.EV):
        rent.pop(ev, None)
        charging.pop(ev, None)
        vpp.pop(ev, None)

    return (fleet, rent, charging, vpp)


def _end_trip(evs, fleet, rent, charging, vpp, max_soc):
    # Update fleet SoC
    fleet.update(dict(zip(evs.EV, evs.end_soc)))

    # Make EVs available for rent
    rent.update(dict(zip(evs.EV, evs.end_soc)))

    # Add charging EVs
    charging_evs = evs.loc[evs["end_charging"] == 1]
    charging.update(dict(zip(charging_evs.EV, evs.end_soc)))

    # EVs are only eligible for VPP when they have enough available battery capacity
    vpp_evs = charging_evs.loc[charging_evs["end_soc"] <= max_soc]
    vpp.update(dict(zip(vpp_evs.EV, vpp_evs.end_soc)))

    return (fleet, rent, charging, vpp)


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
    charging = False
    prev_row = df_car.iloc[0]
    for row in df_car.itertuples():

        # New trip detected when location changes.
        if (row.coordinates_lat != prev_row.coordinates_lat) | (
            row.coordinates_lon != prev_row.coordinates_lon
        ):
            # Last location was at a charging station
            # Add charging info to previous trip.
            if charging and trips:
                previous_trip = trips.pop()
                previous_trip[-1] = 1
                trips.append(previous_trip)
                charging = False

            trip = [
                prev_row.name,
                prev_row.timestamp,
                prev_row.address,
                prev_row.coordinates_lat,
                prev_row.coordinates_lon,
                prev_row.fuel,
                row.timestamp,
                row.address,
                row.coordinates_lat,
                row.coordinates_lon,
                row.fuel,
                int((row.timestamp - prev_row.timestamp) / 60),
                trip_distance(prev_row.fuel - row.fuel),
                row.charging,
            ]
            trips.append(trip)

        # Charging at current location
        if row.charging == 1:
            charging = True

        prev_row = row

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
            "end_charging",
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
        Also remove EVs that had a faulty charging behaviour.

        Effects on Simulation:
          - Earlier charging of EV, if it has been parked at a charging
            station on the service trip.
          - Higher SoC in Sim than in the real data, since trips has been removed.
    """
    logger.info("Cleaning trips...")
    df = _remove_incorrect_charged_evs(df, 20)
    df = _end_charging_previous_trip(df)
    df_service = df.loc[df["trip_duration"] > 2 * 24 * 60]
    df.drop(df_service.index, inplace=True)
    logger.info("Removed %d trips that were longer than 2 days." % len(df_service))

    return df


def _remove_incorrect_charged_evs(df, soc_threshold):
    trips_error = df.sort_values(["EV", "start_time"])
    trips_error["n_EV"] = trips_error["EV"].shift(-1)
    trips_error["n_soc"] = trips_error["start_soc"].shift(-1)

    errors = trips_error[
        (trips_error["EV"] == trips_error["n_EV"])  # Same EV
        & (
            trips_error["n_soc"] - trips_error["end_soc"] > soc_threshold
        )  # Difference in SoC
        & (trips_error["end_charging"] == 0)  # Was not determined as charging last trip
    ]
    df.drop(df[df["EV"].isin(errors.EV.unique())].index, inplace=True)
    logger.info(
        "Removed %d EVs that had faulty charging behaviour." % len(errors.EV.unique())
    )
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
    logger.info(
        "Changed %d trips, previous to service trips, to end at a charging station."
        % num_trips
    )
    return df_trips
