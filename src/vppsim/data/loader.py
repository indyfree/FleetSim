#!/usr/bin/env python

import logging
import os
import pandas as pd
from pathlib import Path

from vppsim import data

logger = logging.getLogger(__name__)

PROJECT_DIR = str(Path(__file__).resolve().parents[3])
CAR2GO_PATH = PROJECT_DIR + '/data/raw/car2go/'
PROCESSED_DATA_PATH = PROJECT_DIR + '/data/processed/'
PROCESSED_TRIPS_FILE = PROCESSED_DATA_PATH + '/trips.pkl'
PROCESSED_DEMAND_FILE = PROCESSED_DATA_PATH + '/demand.pkl'
CAR2GO_FILES = ['stuttgart.2016.03.22-2016.11.30.csv', 'stuttgart.2016.12.01-2017.02.22.csv',
                'stuttgart.2017.02.23-2017-05-01.csv', 'stuttgart.2017.05.01-2017.10.31.csv',
                'stuttgart.2017.11.01-2018.01.31.csv']


def main():
    print(load_car2go_demand(rebuild=True))


def load_car2go_trips(rebuild=False):
    '''Loads processed trip data into a dataframe, process again if needed'''

    # Return early if processed files is present
    if rebuild is False and os.path.isfile(PROCESSED_TRIPS_FILE):
        return pd.read_pickle(PROCESSED_TRIPS_FILE)

    if not os.path.exists(PROCESSED_DATA_PATH):
        os.makedirs(PROCESSED_DATA_PATH)

    for f in CAR2GO_FILES:
        path = PROCESSED_DATA_PATH + 'trips.' + f.strip('stuttgart.').strip('.csv') + '.pkl'
        if rebuild is False and os.path.isfile(path):
            logger.info('Processed %s already found on disk' % f)
            continue

        logger.info('Processing %s...' % f)
        df = pd.read_csv(CAR2GO_PATH + f)
        df = data.process_car2go(df)
        df.to_csv(path + '.csv')
        pd.to_pickle(df, path)
        logger.info('Saved processed %s to disk.' % f)

    pkls = []
    logger.info('Concatening all files together...')
    for f in CAR2GO_FILES:
        path = PROCESSED_DATA_PATH + 'trips.' + f.strip('stuttgart.').strip('.csv') + '.pkl'
        pkls.append(pd.read_pickle(path))

    df = pd.concat(pkls).sort_values(['start_time']).reset_index()
    df.to_csv(PROCESSED_TRIPS_FILE.strip('.pkl') + '.csv')
    pd.to_pickle(df, PROCESSED_TRIPS_FILE)
    logger.info('Wrote all processed trips files to %s' % PROCESSED_TRIPS_FILE)

    return pd.read_pickle(PROCESSED_TRIPS_FILE)

def load_car2go_demand(rebuild=False):
    '''Loads processed demand data into a dataframe, process again if needed'''
    df_trips = load_car2go_trips()

    if rebuild is False and os.path.isfile(PROCESSED_DEMAND_FILE):
        return pd.read_pickle(PROCESSED_DEMAND_FILE)

    logger.info('Processing %s...' % PROCESSED_DEMAND_FILE)
    df = data.calculate_car2go_demand(df_trips)
    df.to_csv(PROCESSED_DEMAND_FILE.strip('.pkl') + '.csv')
    pd.to_pickle(df, PROCESSED_DEMAND_FILE)
    logger.info('Wrote calculated car2go demand to %s' % PROCESSED_DEMAND_FILE)
    return pd.read_pickle(PROCESSED_DEMAND_FILE)

if __name__ == '__main__':
    main()
