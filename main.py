import os
if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

import json
from vnstock3 import Vnstock
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta, MO
import matplotlib.pyplot as plt 

import pandas as pd
pd.options.mode.chained_assignment = None

from vnstock3.explorer.msn.quote import *

TOP_TICKERS_FOR_AVERAGE_GROUP = 5
AVG_GROUP_NAMES = ["NGAN_HANG", "BAN_LE", "BAT_DONG_SAN", "TAI_CHINH", "HANG_CA_NHAN", "TAI_NGUYEN", "XAY_DUNG", "DIEN_NUOC_XANG", "DAU_KHI", "DICH_VU_CONG_NGHIEP", "CONG_NGHE", "BAO_HIEM", "HOA_CHAT", "OTO_PHU_TUNG"]
AVG_TOP_GROUP = ["NGAN_HANG", "BAT_DONG_SAN", "TAI_CHINH"]

vnstock = Vnstock().stock(symbol="FRT", source="VCI")
OUTPUT_DIR = "images"
START_DATE = "2024-01-01"

# load holiday
df = pd.read_csv("holiday_mapping.csv", header=None, names=['from', 'to'])
HOLIDAY_MAPPING = {k: v for k,v in zip(df["from"], df["to"])}
print("HOLIDAY_MAPPING", HOLIDAY_MAPPING)

# prepare origin dates
today = date.today()
list_origin_dates = []
for month_delta in reversed(range(4)):
    origin_date = today - relativedelta(day=1, weekday=MO(1), months=month_delta)
    origin_date = origin_date.strftime('%Y-%m-%d')
    origin_date = HOLIDAY_MAPPING.get(origin_date, origin_date)
    list_origin_dates.append(origin_date)
print("list_origin_dates", list_origin_dates)

# if False:
#     OUTPUT_DIR = "images_2022"
#     START_DATE = "2022-01-01"
#     list_origin_dates = ["2022-04-01", "2022-11-16", "2023-08-09", "2024-03-28"]

# load msn id mapping
df = pd.read_csv("msn_id_mapping.csv", header=None, names=['ticker', 'id'])
MSN_ID_MAPPING = {k: v for k,v in zip(df["ticker"], df["id"])}
print("MSN_ID_MAPPING keys = ", MSN_ID_MAPPING.keys())

configs = json.load(open("config_tickers.json"))
print("configs keys = ", configs.keys())

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_data(symbol, origin_date, end_date, start_date=START_DATE, group=None):
    try:
        is_vnstock = symbol not in MSN_ID_MAPPING or symbol == "VNINDEX"
        if is_vnstock:
            df = vnstock.quote.history(symbol=symbol, start=start_date, end=end_date, interval='1D')
        else:
            symbol_id = MSN_ID_MAPPING[symbol]
            quote = Quote(symbol_id=symbol_id)
            df = quote.history(start=start_date, end=end_date, interval='1D')
    except Exception as e:
        print("Error {}: is_vnstock = {} {} {} {}".format(e, is_vnstock, symbol, origin_date, end_date))
        return None
    # convert time to format yyyy-mm-dd
    df["time_str"] = df["time"].dt.strftime('%Y-%m-%d')

    origin_date_str = origin_date
    err = None
    for offset in range(7):
        if offset > 0:
            cur_date = datetime.strptime(origin_date, '%Y-%m-%d')
            cur_date = cur_date - relativedelta(days=offset)
            origin_date_str = cur_date.strftime('%Y-%m-%d')
        try:
            origin_close = float(df[df["time_str"] == origin_date_str]["close"].iloc[0])
            scale = origin_close / 100
            data = df[["time", "close"]]
            data["close"] = data["close"].div(scale)
            if offset > 0:
                print("Fixed symbol {} with offset = {} new_date = {}".format(symbol, offset, origin_date_str))
            dt_origin_date_str = datetime.strptime(origin_date_str, '%Y-%m-%d')
            return data[data["time"] >= dt_origin_date_str]
        except Exception as e:
            err = e
    print("Error with df:\n{}".format(df))
    print("Error {}: is_vnstock {} {} {} {}".format(err, is_vnstock, symbol, origin_date, end_date))
    return None

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.get_cmap(name, n)

def get_colors(n):
    colors = ["#ffe50b", "#12bfff", "#e48128", "#8e4eff", "#59f05f", "#2cecd2", "#ff3939", "#ff79a6", "#82b1ff", "#3983ff", "#ff00ae", "#1eff00", "#ff6600", "#1d9502", "#1d789f"]
    if n <= len(colors):
        return colors[0:n]
    
    outputs = list(colors)
    m = n - len(outputs)
    cmap = get_cmap(m)
    for i in range(m):
        outputs.append(cmap(i))
    return outputs

plt.style.use('dark_background')

now = datetime.now(tz=timezone(timedelta(hours=7)))
end_date = now.strftime("%Y-%m-%d")
for idx, origin_date in enumerate(list_origin_dates):
    is_vnindex_in_avg = False

    # AVG_GROUP
    avg_file_name = "{}/AVG_GROUP_{}.jpg".format(OUTPUT_DIR, idx)
    avg_fig, avg_ax = plt.subplots(figsize=(15, 10))
    avg_colors = get_colors(len(configs) + 1)
    avg_ax.set_title("AVG_GROUP_{} - {} to {}".format(idx, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')

    # AVG_TOP_GROUP
    avg_top_file_name = "{}/AVG_TOP_GROUP_{}.jpg".format(OUTPUT_DIR, idx)
    avg_top_fig, avg_top_ax = plt.subplots(figsize=(15, 10))
    avg_top_colors = get_colors(len(configs) + 1)
    avg_top_ax.set_title("AVG_TOP_GROUP_{} - {} to {}".format(idx, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')

    for group_idx, (group, tickers) in enumerate(configs.items()):
        ticker_colors = get_colors(len(tickers) + 1)
        file_name = "{}/{}_{}.jpg".format(OUTPUT_DIR, group, idx)
        if os.path.exists(file_name):
            # print("Skip {}".format(file_name))
            continue
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.set_title("{}_{} - {} to {}".format(group, idx, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')
        is_valid = False
        avg_ticker_list = []
        for ticker_idx, ticker in enumerate(tickers):
            data_ticker = get_data(ticker, origin_date, end_date, group=group)
            color = ticker_colors[ticker_idx]
            if data_ticker is None:
                continue
            is_valid = True
            last_value = data_ticker["close"].iloc[-1]
            label = '{} {:.2f}'.format(ticker, last_value)
            data_ticker.plot(ax=ax, x='time', y='close', label=label, color=color)
            ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                     xycoords=('axes fraction', 'data'), textcoords='offset points', 
                     color=color, fontsize=12, weight='bold')
            if ticker == "VNINDEX" and is_vnindex_in_avg == False:
                is_vnindex_in_avg = True
                # AVG_GROUP
                avg_color = avg_colors[0]
                data_ticker.plot(ax=avg_ax, x='time', y='close', label=label, color=avg_color)
                avg_ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                         xycoords=('axes fraction', 'data'), textcoords='offset points', 
                         color=avg_color, fontsize=12, weight='bold')
                # AVG_TOP_GROUP
                avg_top_color = avg_top_colors[0]
                data_ticker.plot(ax=avg_top_ax, x='time', y='close', label=label, color=avg_top_color)
                avg_top_ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                         xycoords=('axes fraction', 'data'), textcoords='offset points', 
                         color=avg_top_color, fontsize=12, weight='bold')
            if ticker != "VNINDEX" and len(avg_ticker_list) < TOP_TICKERS_FOR_AVERAGE_GROUP:
                avg_ticker_list.append(data_ticker)
        if len(avg_ticker_list) > 0:
            avg_df = pd.concat(avg_ticker_list)
            avg_df = avg_df.groupby(avg_df.index).mean()
            last_value = avg_df["close"].iloc[-1]
            avg_label = '{} {:.2f}'.format(group, last_value)
            # AVG_GROUP
            avg_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
            if group in AVG_GROUP_NAMES:
                avg_df.plot(ax=avg_ax, x='time', y='close', label=avg_label, color=avg_color)
                avg_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                             xycoords=('axes fraction', 'data'), textcoords='offset points', 
                             color=avg_color, fontsize=12, weight='bold')
            # AVG_TOP_GROUP
            avg_top_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
            if group in AVG_TOP_GROUP:
                avg_df.plot(ax=avg_top_ax, x='time', y='close', label=avg_label, color=avg_top_color)
                avg_top_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                             xycoords=('axes fraction', 'data'), textcoords='offset points', 
                             color=avg_top_color, fontsize=12, weight='bold')
        
        if is_valid:
            fig.savefig(file_name)
            print("Saved {}".format(file_name))

    avg_fig.savefig(avg_file_name)
    print("Saved AVG_GROUP: {}".format(avg_file_name))
    avg_top_fig.savefig(avg_top_file_name)
    print("Saved avg_top_GROUP: {}".format(avg_top_file_name))
