#!/usr/bin/env python

import pandas as pd
from pathlib import Path


PROJECT_DIR = str(Path(__file__).resolve().parents[2])
CAR2GO_PATH = PROJECT_DIR + '/data/car2go/S-GO2268.csv'

def main():
    print(load())


def load():
    return pd.read_csv(CAR2GO_PATH, sep=';')


if __name__ == '__main__':
    main()
