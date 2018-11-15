#!/usr/bin/env python

import pandas as pd
from pathlib import Path


PROJECT_DIR = str(Path(__file__).resolve().parents[2])
CAR2GO_PATH = PROJECT_DIR + '/data/car2go/trips.2016.12.01-2017.02.22.csv'


def main():
    print(load())


def load():
    df = pd.read_csv(CAR2GO_PATH, sep=';')
    return df


if __name__ == '__main__':
    main()
