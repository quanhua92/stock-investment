import os

if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

import json
import random
import argparse
import traceback
from vnstock3 import Vnstock
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta, MO
from functools import cache

MARKET_CAP_MAP = dict()

@cache
def get_market_cap_vnstock(symbol):
    try:
        stock = Vnstock().stock(symbol, source="VCI")
        data = stock.finance.ratio(period='year', lang='vi')
        mc = data[('Chỉ tiêu định giá', 'Vốn hóa (Tỷ đồng)')].iloc[0]
        mc = int(mc)
        MARKET_CAP_MAP[symbol] = mc
        print(symbol, mc)
        return mc
    except Exception as e:
        print("Error", e)
        return -1

CONFIG_FILE_NAME = "config_tickers.json"

configs = json.load(open(CONFIG_FILE_NAME))
print("configs keys = ", configs.keys())

SKIP_GROUPS = ["US", "CRYPTO", "FOREX", "INDEX"]

for group, tickers in configs.items():
    if group in SKIP_GROUPS:
        continue
    sorted_tickers = []
    need_market_cap = []
    for ticker in tickers:
        if ticker == "VNINDEX":
            sorted_tickers.append(ticker)
        else:
            need_market_cap.append(ticker)
    need_market_cap.sort(key=lambda name: get_market_cap_vnstock(name), reverse=True)
    sorted_tickers.extend(need_market_cap)
    # overwrite configs
    configs[group] = sorted_tickers
            
        
print("configs", configs["PORT_LONG_TERM"])

with open(CONFIG_FILE_NAME, 'w') as f:
    json.dump(configs, f, indent=4, sort_keys=True)
    print("SAVED: ", CONFIG_FILE_NAME)

with open('stock_market_cap.csv', 'w') as f:
    for symbol, mc in MARKET_CAP_MAP.items():
        f.write(','.join([symbol, str(mc)]))
        f.write('\n')
    print("SAVED stock_market_cap.csv")

