import os

if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

import json
import argparse
import matplotlib.pyplot as plt 
import mplfinance as mpf
import traceback
from vnstock3 import Vnstock
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta, MO
from functools import cache

import pandas as pd
pd.options.mode.chained_assignment = None

from vnstock3.explorer.msn.quote import *

TOP_TICKERS_FOR_AVERAGE_GROUP = 5
AVG_GROUP_NAMES = [
    "NGAN_HANG", 
    "CHUNG_KHOAN", 
    "BAT_DONG_SAN", 
    "BAT_DONG_SAN_KCN", 
    "BAN_LE", 
    "XAY_DUNG", 
    "DAU_TU_CONG", 
    "THEP", 
    "VLXD", 
    "THUC_PHAM", 
    "NANG_LUONG", 
    "DAU_KHI", 
    "NONG_NGHIEP", 
    "THUY_SAN", 
    "NHUA", 
    "HOA_CHAT", 
    "VAN_TAI", 
    "HANG_KHONG", 
    "BAO_HIEM", 
    "SUC_KHOE", 
    "CONG_NGHE", 
    "KHAI_KHOANG", 
    "CAO_SU", 
    "DET_MAY", 
    "THUC_PHAM", 
    "XAY_LAP_DIEN", 
    "OTHERS", 
    "PENNY"
]
AVG_TOP_GROUP = [
    "NGAN_HANG", 
    "BAT_DONG_SAN", 
    "TAI_CHINH", 
    "BAN_LE",
    "DAU_KHI", 
    "THUC_PHAM", 
    "HOA_CHAT",
    "PENNY"
]

# vnstock = Vnstock().stock(source="VCI")
OUTPUT_DIR = "images"
START_DATE = "2024-01-01"

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", choices=["2022"])
args = parser.parse_args()

# load holiday
df = pd.read_csv("holiday_mapping.csv", header=None, names=['from', 'to'])
HOLIDAY_MAPPING = {k: v for k,v in zip(df["from"], df["to"])}
print("HOLIDAY_MAPPING", HOLIDAY_MAPPING)

# prepare origin dates
NUM_MONTHS_FOR_ORIGIN_DATES = 2
today = date.today()
list_origin_dates = []
for month_delta in reversed(range(NUM_MONTHS_FOR_ORIGIN_DATES)):
    origin_date = today - relativedelta(day=1, weekday=MO(1), months=month_delta)
    origin_date = origin_date.strftime('%Y-%m-%d')
    origin_date = HOLIDAY_MAPPING.get(origin_date, origin_date)
    list_origin_dates.append(origin_date)
print("list_origin_dates", list_origin_dates)

RS_BASE_TICKER = "VNINDEX"
RS_START_DATE = START_DATE
RS_MONTH_DELTA = 4
RS_PERIOD = 20
RS_ORIGIN_DATE = today - relativedelta(day=1, weekday=MO(1), months=RS_MONTH_DELTA)
RS_ORIGIN_DATE = RS_ORIGIN_DATE.strftime('%Y-%m-%d')

if args.mode == '2022':
    OUTPUT_DIR = "images_2022"
    START_DATE = "2022-01-01"
    list_origin_dates = ["2022-04-01", "2022-11-16", "2023-08-09", "2024-03-28"]
    RS_START_DATE = START_DATE
    RS_ORIGIN_DATE = list_origin_dates[0]

# load msn id mapping
df = pd.read_csv("msn_id_mapping.csv", header=None, names=['ticker', 'id'])
MSN_ID_MAPPING = {k: v for k,v in zip(df["ticker"], df["id"])}
print("MSN_ID_MAPPING keys = ", MSN_ID_MAPPING.keys())

configs = json.load(open("config_tickers.json"))
print("configs keys = ", configs.keys())

os.makedirs(OUTPUT_DIR, exist_ok=True)
vnstock = Vnstock().stock(symbol="SSI", source="VCI")

@cache
def get_stock_data(symbol, start_date, end_date):
    global vnstock
    try:
        is_vnstock = symbol not in MSN_ID_MAPPING or symbol == "VNINDEX"
        if is_vnstock:
            if vnstock is None:
                vnstock = Vnstock().stock(source="VCI")
            df = vnstock.quote.history(symbol=symbol, start=start_date, end=end_date, interval='1D')
        else:
            symbol_id = MSN_ID_MAPPING[symbol]
            quote = Quote(symbol_id=symbol_id)
            df = quote.history(start=start_date, end=end_date, interval='1D')
        return df
    except Exception as e:
        print("Error {}: is_vnstock = {} {} {} {}".format(e, is_vnstock, symbol, origin_date, end_date))
        return None

def get_data(symbol, origin_date, end_date, start_date=START_DATE, rs_period=RS_PERIOD):
    df = get_stock_data(symbol, start_date, end_date)
    if df is None:
        return df
    # convert time to format yyyy-mm-dd
    df["time_str"] = df["time"].dt.strftime('%Y-%m-%d')
    df["rs_diff"] = df["close"] / df["close"].shift(rs_period, fill_value=1)

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
            columns = ["time", "open", "close", "high", "low", "rs_diff"]
            if "volume" in df:
                columns.append("volume")
            data = df[columns]
            data["open_scaled"] = data["open"].div(scale)
            data["high_scaled"] = data["high"].div(scale)
            data["low_scaled"] = data["low"].div(scale)
            data["close_scaled"] = data["close"].div(scale)
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

now = datetime.now(tz=timezone(timedelta(hours=7)))
end_date = now.strftime("%Y-%m-%d")

# CALCULATE STOCK CHARTS
if True:
    start_date = RS_START_DATE
    base_ticker = get_stock_data(RS_BASE_TICKER, start_date, end_date)
    base_ticker_raw = base_ticker.copy()
    base_ticker_start_time = base_ticker.iloc[0]["time"]
    scale = base_ticker.iloc[0]["close"] / 100
    base_ticker["open"] = base_ticker["open"].div(scale)
    base_ticker["high"] = base_ticker["high"].div(scale)
    base_ticker["low"] = base_ticker["low"].div(scale)
    base_ticker["close"] = base_ticker["close"].div(scale)

    for group_idx, (group, tickers) in enumerate(configs.items()):
        ticker_colors = get_colors(len(tickers) + 1)
        file_name = "{}/{}_CHART.jpg".format(OUTPUT_DIR, group)
        if os.path.exists(file_name):
            # print("Skip {}".format(file_name))
            continue

        avg_ticker_list = []
        for ticker_idx, ticker in enumerate(tickers):
            data_ticker = get_stock_data(ticker, start_date, end_date)
            if ticker == "VNINDEX" or len(avg_ticker_list) >= TOP_TICKERS_FOR_AVERAGE_GROUP:
                continue

            try:
                scale = data_ticker[data_ticker["time"] == base_ticker_start_time].iloc[0]["close"] / 100
                
                data_ticker["open"] = data_ticker["open"].div(scale)
                data_ticker["high"] = data_ticker["high"].div(scale)
                data_ticker["low"] = data_ticker["low"].div(scale)
                data_ticker["close"] = data_ticker["close"].div(scale)
                data_ticker["rs"] = data_ticker["close"] / base_ticker["close"]
                if ticker != "VNINDEX" and len(avg_ticker_list) < TOP_TICKERS_FOR_AVERAGE_GROUP:
                    avg_ticker_list.append(data_ticker)
            except IndexError:
                continue
    
        plt.style.use('dark_background')
        if len(avg_ticker_list) > 0:
            try:
                avg_df = pd.concat(avg_ticker_list)
                avg_df = avg_df.set_index("time")
                avg_df = avg_df.groupby(avg_df.index).mean()

                has_volume = "volume" in avg_df and not avg_df["volume"].isnull().any().any()
                style = "yahoo"
                title = "{}_CHART: {} - {}".format(group, start_date, end_date)
                apds = [
                    mpf.make_addplot(avg_df['rs'], panel=2, type='line', label="RS(VNINDEX) MA(49)", mav=49)
                ]
                fig, axs = mpf.plot(avg_df, mav=(10, 20, 50, 100), mavcolors=['r', 'g', 'b', 'gray'], 
                         figsize=(30, 10), panel_ratios=(3, 1),figratio=(1,1), figscale=1.5, fontscale=2, tight_layout=False,
                         addplot=apds,
                         xrotation=0,
                         type="candle", style=style, 
                         scale_width_adjustment=dict(candle=2, lines=2),
                         update_width_config=dict(candle_linewidth=1.5),
                         volume=has_volume,
                         returnfig=True
                     )

                axs[0].set_title(title);
                fig.savefig(file_name,bbox_inches='tight')
                print("Saved {}".format(file_name))
            except Exception as e:
                print("Skip {} - {}".format(file_name, e))
                print(traceback.format_exc())

# CALCULATE RS CHARTS
plt.style.use('dark_background')

if False:
    origin_date = RS_ORIGIN_DATE
    base_ticker = get_data(symbol=RS_BASE_TICKER, origin_date=RS_ORIGIN_DATE, end_date=end_date, start_date=RS_START_DATE, rs_period=RS_PERIOD)
    base_rs_diff = base_ticker["rs_diff"]
    base_ticker["rs"] = base_ticker["rs_diff"] / base_rs_diff
    last_value = base_ticker["rs"].dropna().iloc[-1]

    # AVG_GROUP
    avg_colors = get_colors(len(configs) + 1)
    
    avg_file_name = "{}/AVG_GROUP_RS.jpg".format(OUTPUT_DIR)
    avg_fig, avg_axs = plt.subplots(2, figsize=(15, 15))
    avg_fig.suptitle("AVG_GROUP_RS PERIOD={} - {} to {}".format(RS_PERIOD, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')
    avg_axs[0].set_ylim([0.9, 1.2])
    avg_axs[1].set_ylim([0.9, 1.2])

    label = RS_BASE_TICKER
    color = "#f5ec42"
    base_ticker.plot(ax=avg_axs[0], x='time', y='rs', label=label, color=color)
    avg_axs[0].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')
    base_ticker.plot(ax=avg_axs[1], x='time', y='rs', label=label, color=color)
    avg_axs[1].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')

    # AVG_TOP_GROUP
    avg_top_colors = get_colors(len(configs) + 1)

    avg_top_file_name = "{}/AVG_TOP_GROUP_RS.jpg".format(OUTPUT_DIR)
    avg_top_fig, avg_top_axs = plt.subplots(2, figsize=(15, 15))
    avg_top_fig.suptitle("AVG_TOP_GROUP_RS PERIOD={} - {} to {}".format(RS_PERIOD, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')
    avg_top_axs[0].set_ylim([0.9, 1.2])
    avg_top_axs[1].set_ylim([0.9, 1.2])

    base_ticker.plot(ax=avg_top_axs[0], x='time', y='rs', label=label, color=color)
    avg_top_axs[0].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')
    base_ticker.plot(ax=avg_top_axs[1], x='time', y='rs', label=label, color=color)
    avg_top_axs[1].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')

    for group_idx, (group, tickers) in enumerate(configs.items()):
        ticker_colors = get_colors(len(tickers) + 1)
        file_name = "{}/{}_RS.jpg".format(OUTPUT_DIR, group)
        if os.path.exists(file_name):
            print("Skip {}".format(file_name))
            continue
        fig, axs = plt.subplots(2, figsize=(15, 15))
        fig.suptitle("{}_RS PERIOD={} - {} to {}".format(group, RS_PERIOD,  origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')

        is_valid = False
        avg_ticker_list = []
        for ticker_idx, ticker in enumerate(tickers):
            try:
                data_ticker = get_data(ticker, origin_date, end_date, start_date=RS_START_DATE, rs_period=RS_PERIOD)
                print("data_ticker", data_ticker, ticker)
                if data_ticker is None:
                    continue
                data_ticker["rs"] = data_ticker["rs_diff"] / base_rs_diff

                color = ticker_colors[ticker_idx]
                is_valid = True
                last_value = data_ticker["rs"].dropna().iloc[-1]

                if last_value > 0.99:
                    ax = axs[0]
                else:
                    ax = axs[1]
                label = '{} {:.2f}'.format(ticker, last_value)
                data_ticker.plot(ax=ax, x='time', y='rs', label=label, color=color)
                ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                         xycoords=('axes fraction', 'data'), textcoords='offset points', 
                         color=color, fontsize=12, weight='bold')
                if ticker == "VNINDEX":
                    data_ticker.plot(ax=axs[1], x='time', y='rs', label=label, color=color)
                    axs[1].annotate(label, xy=(1, last_value), xytext=(8, 0), 
                         xycoords=('axes fraction', 'data'), textcoords='offset points', 
                         color=color, fontsize=12, weight='bold')
                if ticker != "VNINDEX" and len(avg_ticker_list) < TOP_TICKERS_FOR_AVERAGE_GROUP:
                    avg_ticker_list.append(data_ticker)
                    avg_ticker_raw_list.append(data_ticker_raw)
            except:
                continue

        if len(avg_ticker_list) > 0:
            avg_df = pd.concat(avg_ticker_list)
            avg_df = avg_df.groupby(avg_df.index).mean()
            
            # AVG_GROUP
            last_value = avg_df["rs"].dropna().iloc[-1]
            avg_label = '{} {:.2f}'.format(group, last_value)
            avg_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
            if group in AVG_GROUP_NAMES:
                if last_value > 0.99:
                    avg_ax = avg_axs[0]
                else:
                    avg_ax = avg_axs[1]
                avg_df.plot(ax=avg_ax, x='time', y='rs', label=avg_label, color=avg_color)
                avg_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                             xycoords=('axes fraction', 'data'), textcoords='offset points', 
                             color=avg_color, fontsize=12, weight='bold')
            # AVG_TOP_GROUP
            avg_top_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
            if group in AVG_TOP_GROUP:
                if last_value > 0.99:
                    avg_top_ax = avg_top_axs[0]
                else:
                    avg_top_ax = avg_top_axs[1]
                avg_df.plot(ax=avg_top_ax, x='time', y='rs', label=avg_label, color=avg_top_color)
                avg_top_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                             xycoords=('axes fraction', 'data'), textcoords='offset points', 
                             color=avg_top_color, fontsize=12, weight='bold')
    
        plt.style.use('dark_background')
        if is_valid:
            axs[0].legend(loc='upper left')
            axs[1].legend(loc='upper left')
            fig.savefig(file_name)
            print("Saved {}".format(file_name))
            plt.close(fig)
        print("is_valid", is_valid)
        raise 11
    plt.style.use('dark_background')
    avg_axs[0].legend(loc='upper left')
    avg_axs[1].legend(loc='upper left')
    avg_fig.savefig(avg_file_name)
    print("Saved AVG_GROUP: {}".format(avg_file_name))
    avg_top_axs[0].legend(loc='upper left')
    avg_top_axs[1].legend(loc='upper left')
    avg_top_fig.savefig(avg_top_file_name)
    print("Saved AVG_TOP_GROUP: {}".format(avg_top_file_name))
    plt.close()

# END RS CHARTS


# CALCULATE SCALE CHARTS
if True:
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
                data_ticker  = get_data(ticker, origin_date, end_date)
                color = ticker_colors[ticker_idx]
                if data_ticker is None:
                    continue
                is_valid = True
                last_value = data_ticker["close_scaled"].iloc[-1]
                label = '{} {:.2f}'.format(ticker, last_value)
                data_ticker.plot(ax=ax, x='time', y='close_scaled', label=label, color=color)
                ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                        xycoords=('axes fraction', 'data'), textcoords='offset points', 
                        color=color, fontsize=12, weight='bold')
                if ticker == "VNINDEX" and is_vnindex_in_avg == False:
                    is_vnindex_in_avg = True
                    # AVG_GROUP
                    avg_color = avg_colors[0]
                    data_ticker.plot(ax=avg_ax, x='time', y='close_scaled', label=label, color=avg_color)
                    avg_ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                            xycoords=('axes fraction', 'data'), textcoords='offset points', 
                            color=avg_color, fontsize=12, weight='bold')
                    # AVG_TOP_GROUP
                    avg_top_color = avg_top_colors[0]
                    data_ticker.plot(ax=avg_top_ax, x='time', y='close_scaled', label=label, color=avg_top_color)
                    avg_top_ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                            xycoords=('axes fraction', 'data'), textcoords='offset points', 
                            color=avg_top_color, fontsize=12, weight='bold')
                if ticker != "VNINDEX" and len(avg_ticker_list) < TOP_TICKERS_FOR_AVERAGE_GROUP:
                    avg_ticker_list.append(data_ticker)
            if len(avg_ticker_list) > 0:
                avg_df = pd.concat(avg_ticker_list)
                avg_df = avg_df.groupby(avg_df.index).mean()
                last_value = avg_df["close_scaled"].iloc[-1]
                avg_label = '{} {:.2f}'.format(group, last_value)
                # AVG_GROUP
                avg_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
                if group in AVG_GROUP_NAMES:
                    avg_df.plot(ax=avg_ax, x='time', y='close_scaled', label=avg_label, color=avg_color)
                    avg_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                                xycoords=('axes fraction', 'data'), textcoords='offset points', 
                                color=avg_color, fontsize=12, weight='bold')
                # AVG_TOP_GROUP
                avg_top_color = avg_colors[group_idx + 1] # 0 is for VNINDEX
                if group in AVG_TOP_GROUP:
                    avg_df.plot(ax=avg_top_ax, x='time', y='close_scaled', label=avg_label, color=avg_top_color)
                    avg_top_ax.annotate(avg_label, xy=(1, last_value), xytext=(8, 0), 
                                xycoords=('axes fraction', 'data'), textcoords='offset points', 
                                color=avg_top_color, fontsize=12, weight='bold')
            
            if is_valid:
                ax.legend(loc='upper left')
                fig.savefig(file_name)
                print("Saved {}".format(file_name))

        avg_ax.legend(loc='upper left')
        avg_fig.savefig(avg_file_name)
        print("Saved AVG_GROUP: {}".format(avg_file_name))
        avg_top_ax.legend(loc='upper left')
        avg_top_fig.savefig(avg_top_file_name)
        print("Saved AVG_TOP_GROUP: {}".format(avg_top_file_name))
        plt.close()
