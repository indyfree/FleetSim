import os
import pandas as pd


def process_car2go(df, path):
    logger = logging.getLogger('vppsim.data')
    logger.info('Processing Car2Go data..')

    df_trips = pd.DataFrame()
    for car in df['name'].unique():
        df_car = df[df['name'] == car]
        # TODO: Append with .loc
        df_trips = df_trips.append(calculate_trips(df_car))

    pd.to_pickle(df_trips, path)
    logger.info('Saved processed data to disk.')

def calculate_trips(df_car):
    trips = list()
    prev = df_car.iloc[0,:]
    for row in df_car.itertuples():
        if row.address != prev.address :
            trips.append([prev.name, prev.timestamp, prev.address, prev.coordinates_lat, prev.coordinates_lon, prev.fuel,
                           row.timestamp, row.address, row.coordinates_lat, row.coordinates_lon, row.fuel, row.charging,
                           int((row.timestamp - prev.timestamp)/60)])
        prev = row

    return pd.DataFrame(trips, columns=['EV', 'start_time', 'start_address', 'start_lat', 'start_lon', 'start_soc', 'end_time',
                                         'end_address', 'end_lat', 'end_lon', 'end_soc', 'end_charging', 'trip_duration'])
