import os
import time

if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

import json
import argparse
import matplotlib.pyplot as plt
from vnstock import Vnstock
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta, MO
from functools import cache

import pandas as pd
pd.options.mode.chained_assignment = None

from vnstock.explorer.msn.quote import *
OUTPUT_DATA_DIR = "data_week"

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", choices=["2022"])
args = parser.parse_args()

# load holiday
df = pd.read_csv("holiday_mapping.csv", header=None, names=['from', 'to'])
HOLIDAY_MAPPING = {k: v for k,v in zip(df["from"], df["to"])}
print("HOLIDAY_MAPPING", HOLIDAY_MAPPING)

today = date.today()

# load msn id mapping
df = pd.read_csv("msn_id_mapping.csv", header=None, names=['ticker', 'id'])
MSN_ID_MAPPING = {k: v for k,v in zip(df["ticker"], df["id"])}
print("MSN_ID_MAPPING keys = ", MSN_ID_MAPPING.keys())

configs = json.load(open("config_tickers.json"))
print("configs keys = ", configs.keys())

os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)
vnstock = Vnstock().stock(symbol="SSI", source="TCBS")

def get_stock_data(symbol, start_date, end_date, interval='1D'):
    try:
        df_raw = get_raw_stock_data(symbol, start_date, end_date, interval)
        if df_raw is not None:
            return df_raw.copy()
    except Exception as e:
        return None

@cache
def get_raw_stock_data(symbol, start_date, end_date, interval='1D'):
    global vnstock
    try:
        is_vnstock = symbol not in MSN_ID_MAPPING or symbol == "VNINDEX"
        if is_vnstock:
            if vnstock is None:
                vnstock = Vnstock().stock(source="TCBS")
            df = vnstock.quote.history(symbol=symbol, start=start_date, end=end_date, interval=interval)
            time.sleep(0.5)
        else:
            symbol_id = MSN_ID_MAPPING[symbol]
            quote = Quote(symbol_id=symbol_id)
            df = quote.history(start=start_date, end=end_date, interval=interval)
            time.sleep(2.0)
        return df
    except Exception as e:
        print("Error {}: is_vnstock = {} {} {} {}".format(e, is_vnstock, symbol, origin_date, end_date))
        print("Error {}: is_vnstock = {} {} {} {}".format(e, is_vnstock, symbol, start_date, end_date))
        return None

now = datetime.now(tz=timezone(timedelta(hours=7)))
# now_str = now.strftime("%Y-%m-%d %H:%M:%S") # Unused variable
end_date = now.strftime("%Y-%m-%d")

plt.style.use('dark_background')

# WEEKLY CHART
ticker = "VNINDEX"
WEEK_MONTH_DELTA = 5
WEEK_START_DATE = today - relativedelta(day=1, weekday=MO(1), months=WEEK_MONTH_DELTA)
WEEK_START_DATE = WEEK_START_DATE.strftime('%Y-%m-%d')
for group_idx, (group, tickers) in enumerate(configs.items()):
    if group not in ["INDEX", "CRYPTO", "FOREX", "US"]:
        week_ticker_list = []
        csv_file_name = "{}/{}_WEEK.csv".format(OUTPUT_DATA_DIR, group)
        for ticker_idx, ticker in enumerate(tickers):
            try:
                data_ticker_raw = get_stock_data(ticker, WEEK_START_DATE, end_date, interval='1W')
                # Weird because data_ticker_raw contains data from 2020 instead of WEEK_START_DATE ?
                data_ticker_raw = data_ticker_raw[data_ticker_raw["time"] >= WEEK_START_DATE]
                data_ticker_raw["ticker"] = ticker
                columns = ["ticker", "time", "open", "close", "high", "low"]
                if "volume" in data_ticker_raw:
                    columns.append("volume")
                week_ticker_list.append(data_ticker_raw[columns])
                print("Downloaded", group, ticker)
                time.sleep(1)
            except Exception as e:
                print(e)
        if len(week_ticker_list) > 0:
            df = pd.concat(week_ticker_list)
            df.to_csv(csv_file_name, index=False)
            print("Saved {}".format(csv_file_name))

