import logging
import pandas as pd

from evsim.data import balancing, car2go, files, intraday

logger = logging.getLogger(__name__)

# Default values
CHARGING_SPEED = 3.6
EV_CAPACITY = 17.6
EV_RANGE = 160

# Default values
CAR2GO_PRICE = 24  # 24 cent/km
DURATION_THRESHOLD = 60 * 24 * 2  # 2 Days in seconds


def rebuild(charging_speed=CHARGING_SPEED, ev_capacity=EV_CAPACITY, ev_range=EV_RANGE):
    car2go_trips(ev_range, rebuild=True)
    car2go_capacity(charging_speed, ev_capacity, ev_range, rebuild=True)
    balancing_prices(rebuild=True)
    intraday_prices(rebuild=True)


def simulation_baseline():
    if not files.simulation_baseline.is_file():
        raise FileNotFoundError(
            "%s not found. Run baseline simulation first." % files.simulation_baseline
        )
    return pd.read_csv(files.simulation_baseline)


def car2go_trips(
    ev_range=EV_RANGE,
    car2go_price=CAR2GO_PRICE,
    duration_threshold=DURATION_THRESHOLD,
    infer_chargers=False,
    rebuild=False,
):
    """Loads processed trip data into a dataframe, process again if needed"""

    if rebuild is True:
        files.processed_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Preprocessing and dropping columns.")
        for f in files.car2go:
            logger.info("Converting to pickle: %s..." % f)
            df = pd.read_csv(files.car2go_dir / f)
            df = car2go.preprocess(df)
            pd.to_pickle(df, _change_ext(files.car2go_dir / f, ".pkl"))

    # Return early if processed files is present
    if rebuild is True or files.trips.is_file():
        df = []
        for f in files.car2go:
            pkl_path = _change_ext(files.car2go_dir / f, ".pkl")
            logger.info("Reading %s..." % pkl_path.name)
            df.append(pd.read_pickle(pkl_path))
        df = pd.concat(df)

        df_trips = car2go.determine_trips(
            df, ev_range, car2go_price, duration_threshold, infer_chargers
        )
        df_trips = (
            df_trips.sort_values(["start_time"]).reset_index().drop(["index"], axis=1)
        )

        df_trips.to_csv(_change_ext(files.trips, ".csv"))
        pd.to_pickle(df_trips, files.trips)
        logger.info("Wrote all processed trips files to %s" % files.trips)

    return pd.read_pickle(files.trips)


def car2go_capacity(
    charging_speed=CHARGING_SPEED,
    ev_capacity=EV_CAPACITY,
    ev_range=EV_RANGE,
    simulate_charging=False,
    rebuild=False,
):
    """Loads processed capacity data into a dataframe, process again if needed"""
    df_trips = car2go_trips(ev_range)

    if rebuild is True or not files.capacity.is_file():
        logger.info("Processing %s..." % files.capacity)
        df = car2go.calculate_capacity(
            df_trips, charging_speed, ev_capacity, simulate_charging
        )
        df.to_csv(_change_ext(files.capacity, ".csv"))
        pd.to_pickle(df, files.capacity)
        logger.info("Wrote calculated car2go demand to %s" % files.capacity)

    return pd.read_pickle(files.capacity)


def intraday_prices(rebuild=False):
    """Loads intraday prices, calculate again if needed"""

    if rebuild is True or not files.intraday_prices.is_file():
        logger.info("Processing %s..." % files.procom_trades)
        df = pd.read_csv(
            files.procom_trades,
            sep=",",
            index_col=False,
            dayfirst=True,
            parse_dates=[1, 9],
            infer_datetime_format=True,
        )
        df[df["product"] == "H"].to_pickle(files.processed_data_dir / "procom_H.pkl")
        df[df["product"] == "Q"].to_pickle(files.processed_data_dir / "procom_Q.pkl")
        df[df["product"] == "B"].to_pickle(files.processed_data_dir / "procom_B.pkl")

        df_q = pd.read_pickle(files.processed_data_dir / "procom_Q.pkl")
        df_q = intraday.calculate_clearing_prices(df_q)
        df_q.to_csv(files.intraday_prices, index=False)
        logger.info(
            "Wrote calculated intraday clearing prices to %s" % files.intraday_prices
        )

    return pd.read_csv(
        files.intraday_prices, parse_dates=[0], infer_datetime_format=True
    )


def balancing_prices(rebuild=False):
    """Loads balancing prices, process again if needed"""

    if rebuild is True or not files.processed_tender_results.is_file():
        df_results = pd.read_csv(
            files.tender_results,
            sep=";",
            decimal=",",
            dayfirst=True,
            parse_dates=[0, 1],
            infer_datetime_format=True,
        )

        df_results = balancing.process_tender_results(df_results)
        df_results.to_csv(files.processed_tender_results, index=False)
        logger.info(
            "Wrote processed tender results to %s" % files.processed_tender_results
        )
    df_results = pd.read_csv(
        files.processed_tender_results, parse_dates=[0, 1], infer_datetime_format=True
    )

    if rebuild is True or not files.control_reserve.is_file():
        df_activated_srl = pd.read_csv(
            files.activated_balancing,
            sep=";",
            decimal=",",
            thousands=".",
            dayfirst=True,
            parse_dates=[0],
            infer_datetime_format=True,
        )

        df_activated_srl = balancing.process_activated_reserve(df_activated_srl)
        df_activated_srl.to_csv(files.control_reserve, index=False)
        logger.info(
            "Wrote processed activated control reserve to %s" % files.control_reserve
        )
    df_activated_srl = pd.read_csv(files.control_reserve)

    if rebuild is True or not files.balancing_prices.is_file():
        df = balancing.calculate_clearing_prices(df_results, df_activated_srl)
        df.to_csv(files.balancing_prices, index=False)
        logger.info(
            "Wrote processed balancing clearing prices to %s" % files.balancing_prices
        )

    return pd.read_csv(
        files.balancing_prices, parse_dates=[0], infer_datetime_format=True
    )


def _change_ext(path, ext):
    return path.parent / (path.stem + ext)
