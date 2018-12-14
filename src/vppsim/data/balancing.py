import logging
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_clearing_prices(df_results, df_activated_control_reserve):
    clearing_prices = list()

    for t in df_activated_control_reserve.itertuples():
        day = pd.to_datetime(t[1])
        # Find out product time
        product_time = "HT" if 8 <= day.hour < 20 else "NT"
        # We are only interested in negative control reserve clearing prices
        product_type = "NEG"

        cp = df_results.loc[
            (df_results["to"] >= pd.Timestamp(day.date()))
            & (df_results["from"] <= pd.Timestamp(day.date()))
            & (df_results["product_time"] == product_time)
            & (df_results["product_type"] == product_type)
            & (df_results["cumsum_allocated_mw"] >= t.neg_mw)
        ].iloc[0]["energy_price_mwh"]

        clearing_prices.append(cp)

    df = df_activated_control_reserve.drop(["pos_mw"], axis=1)
    df.columns = ["from", "to", "capacity_mw"]

    df["clearing_price"] = pd.Series(clearing_prices).values
    return df


def process_tender_results(df):
    df.drop(["TYPE_OF_RESERVES", "COUNTRY"], inplace=True, axis=1)
    df.columns = [
        "from",
        "to",
        "product",
        "capacity_price_mw",
        "energy_price_mwh",
        "payment_direction",
        "offered_mw",
        "allocated_mw",
    ]

    # Split product into product type and time for ease of use
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                df["product"].str.split("_", 1).tolist(),
                columns=["product_type", "product_time"],
            ),
        ],
        axis=1,
    )

    # Negative prices when grid pays provider for negative control reserve
    df.loc[
        (df["payment_direction"] == "GRID_TO_PROVIDER") & (df["product_type"] == "NEG"),
        ["energy_price_mwh"],
    ] = df["energy_price_mwh"] * (-1)
    df.drop(["product", "payment_direction"], axis=1, inplace=True)

    # Calculate cumulative sums of every timeslot for every product
    df = df.sort_values(["from", "product_type", "product_time", "energy_price_mwh"])

    days = df["from"].unique()
    types = df["product_type"].unique()
    times = df["product_time"].unique()
    cumsums = list()

    for d in days:
        for typ in types:
            for t in times:
                cs = df.loc[
                    (df["from"] == d)
                    & (df["product_type"] == typ)
                    & (df["product_time"] == t),
                    ["allocated_mw"],
                ].cumsum()
                cumsums.append(cs)

    df["cumsum_allocated_mw"] = pd.concat(cumsums)

    return df


def process_activated_reserve(df):
    df.drop(
        [
            "LETZTE AENDERUNG",
            "ERSATZWERT",
            "LETZTE AENDERUNG.1",
            "QUAL. NEG",
            "QUAL. POS",
        ],
        axis=1,
        inplace=True,
    )
    df.columns = ["date", "from", "to", "neg_mw", "pos_mw"]

    # Make "from" and "to" full datetime columns
    hours_minutes_from = df["from"].str.split(":", expand=True)
    df["from"] = pd.to_datetime(
        df["date"].astype(str)
        + " "
        + hours_minutes_from[0]
        + ":"
        + hours_minutes_from[1]
    )

    hours_minutes_to = df["to"].str.split(":", expand=True)
    df["to"] = pd.to_datetime(
        df["date"].astype(str) + " " + hours_minutes_to[0] + ":" + hours_minutes_to[1]
    )

    # Fix time where 0:00 belongs to previous day
    df.loc[
        (df["to"].dt.hour == 0) & (df["to"].dt.minute == 0), "to"
    ] = df.to + pd.DateOffset(days=1)

    df.drop("date", inplace=True, axis=1)
    return df
