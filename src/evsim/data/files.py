from pathlib import Path

# Search data dir
search_dirs = [
    Path("./data"),
    Path("../data"),
    Path(__file__).resolve().parents[3] / "data",
]
data_dir = None
for p in search_dirs:
    if p.is_dir():
        data_dir = p
        break

# base dirs
raw_data_dir = data_dir / "raw"
processed_data_dir = data_dir / "processed"
car2go_dir = raw_data_dir / "car2go"
balancing_dir = raw_data_dir / "balancing"
intraday_dir = raw_data_dir / "intraday"

# raw file paths
activated_balancing = balancing_dir / "activated_balancing_2016_2017.csv"
tender_results = balancing_dir / "tender_results_2016_2017.csv"
procom_trades = intraday_dir / "procom_data.csv"

# processed files paths
trips = processed_data_dir / "trips.pkl"
capacity = processed_data_dir / "capacity.pkl"
control_reserve = processed_data_dir / "activated_control_reserve.csv"
processed_tender_results = processed_data_dir / "tender_results.csv"
balancing_prices = processed_data_dir / "balancing_prices.csv"
intraday_prices = processed_data_dir / "intraday_prices.csv"
# simulation result file paths
simulation_baseline = processed_data_dir / "sim-baseline.csv"

# car2go Files
car2go = [
    # "stuttgart.2016.03.22-2016.11.30.csv",
    # "stuttgart.2016.12.01-2017.02.22.csv",
    "stuttgart.2017.02.23-2017-05-01.csv",
    # "stuttgart.2017.05.01-2017.10.31.csv",
    # "stuttgart.2017.11.01-2018.01.31.csv",
]
