#!/usr/bin/env python

import os
import pandas as pd
from pathlib import Path

from vppsim import data


PROJECT_DIR = str(Path(__file__).resolve().parents[3])
CAR2GO_PATH = PROJECT_DIR + '/data/raw/car2go/stuttgart.2016.12.01-2017.02.22.csv'
PROCESSED_DATA_PATH = PROJECT_DIR + '/data/processed'
PROCESSED_DATA_FILE = PROCESSED_DATA_PATH + '/trips.pkl'


def main():
    print(load_car2go(rebuild=True))


def load_car2go(rebuild=False):
    '''Loads processed data into a dataframe, process again if needed'''


    if not os.path.exists(PROCESSED_DATA_PATH):
        os.makedirs(PROCESSED_DATA_PATH)

    if rebuild is True or os.path.isfile(PROCESSED_DATA_FILE) is False:
        df = pd.read_csv(CAR2GO_PATH)
        data.process_car2go(df, PROCESSED_DATA_FILE)

    return pd.read_pickle(PROCESSED_DATA_FILE)


if __name__ == '__main__':
    main()
