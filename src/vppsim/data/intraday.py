import logging
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_clearing_prices(df):
    time = df["product_time"].str.split("Q", expand=True)
    df["delivery_date"] = pd.to_datetime(
        df["delivery_date"].astype(str)
        + " "
        + time[0]
        + ":"
        + ((time[1].astype(int) - 1) * 15).astype(str)
    )

    # Clearing price is the lowest conducted trade. Bidding above the clearing price
    # will always be sucessful
    df = df.groupby("delivery_date").min()

    # Transform to EUR/MWh
    df.loc[:, "unit_price"] = df["unit_price"] / 100

    df = df.loc[:, ["unit_price"]]
    df.columns = ["unit_price_eur_mwh"]
    return df
