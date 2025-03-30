import os
import time

if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

import json
import argparse
import matplotlib.pyplot as plt 
import mplfinance as mpf
import traceback
from vnstock import Vnstock
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta, MO
from functools import cache

import pandas as pd
pd.options.mode.chained_assignment = None

from vnstock.explorer.msn.quote import *

DEBUG = False

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
    "CHUNG_KHOAN", 
    "BAN_LE",
    "NONG_NGHIEP",
    "THEP",
    "THUC_PHAM", 
    "DAU_KHI"
]
SPECIAL_TICKERS = [
    "VNINDEX", "VN30", 
    "VHM",
    "VCB", "TPB", "MSB", "EIB",
    "HCM", "MBS", "ORS", "BVS", "SSI",
    "FPT",
    "MWG", "DGW",
    "VNM", "MSN",
    "VGS", "HPG",
]


# vnstock = Vnstock().stock(source="TCBS")
OUTPUT_DIR = "images"
OUTPUT_DATA_DIR = "data"
START_DATE = "2024-11-11"

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
    print("origin_date", origin_date, " days = ", (origin_date - today).days)
    if abs((origin_date - today).days) < 7:
        origin_date = today - timedelta(days=7)
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
    list_origin_dates = ["2023-03-23", "2023-12-04"]
    RS_START_DATE = START_DATE
    RS_ORIGIN_DATE = list_origin_dates[0]

# load msn id mapping
df = pd.read_csv("msn_id_mapping.csv", header=None, names=['ticker', 'id'])
MSN_ID_MAPPING = {k: v for k,v in zip(df["ticker"], df["id"])}
print("MSN_ID_MAPPING keys = ", MSN_ID_MAPPING.keys())

configs = json.load(open("config_tickers.json"))
print("configs keys = ", configs.keys())

os.makedirs(OUTPUT_DIR, exist_ok=True)
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
        return df
    except Exception as e:
        print("Error {}: is_vnstock = {} {} {} {}".format(e, is_vnstock, symbol, origin_date, end_date))
        return None

def get_data(symbol, origin_date, end_date, start_date=START_DATE, rs_period=RS_PERIOD, should_scale=True):
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
            columns = ["time", "open", "close", "high", "low", "rs_diff"]
            if "volume" in df:
                columns.append("volume")
            data = df[columns]
            if should_scale:
                scale = origin_close / 100
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
    print("Error {}: {} {} {}".format(err, symbol, origin_date, end_date))
    return None

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.get_cmap(name, n)

def get_colors(n):
    colors = ["#eef745", "#f22c2c", "#f2672c", "#f2882c", "#f2ad2c", "#adf22c", "#5df22c", "#2cf278", "#2cf2d1", "#2c9cf2", "#2c5af2", "#7f2cf2", "#bd2cf2", "#f22ce2", "#f22c75", "#a61212", "#ab6203", "#a3ab03", "#65ab03", "#03ab1c", "#03ab95", "#0357ab", "#462cdb", "#9a03ab", "#ab0365"]
    if n <= len(colors):
        return colors[0:n]
    
    outputs = list(colors)
    m = n - len(outputs)
    cmap = get_cmap(m)
    for i in range(m):
        outputs.append(cmap(i))
    return outputs

now = datetime.now(tz=timezone(timedelta(hours=7)))
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
end_date = now.strftime("%Y-%m-%d")

plt.style.use('dark_background')

# INDEX CHARTS
if not DEBUG:
    start_date = RS_START_DATE

    ticker = "VNINDEX"
    data_ticker_raw = get_stock_data(ticker, start_date, end_date)
    if data_ticker_raw is not None:
        data_ticker = data_ticker_raw.copy()
        file_name = "{}/{}_CHART.jpg".format(OUTPUT_DIR, ticker)
        style = "yahoo"
        title = "{}_CHART: {} - {} - {}".format(ticker, start_date, now_str, ticker)
        fig, axs = mpf.plot(data_ticker.set_index("time"), mav=(10, 20, 50, 100), mavcolors=['r', 'g', 'b', 'gray'], 
                 figsize=(30, 10), panel_ratios=(3, 1),figratio=(1,1), figscale=1.5, fontscale=2, tight_layout=False,
                 xrotation=0,
                 type="candle", style=style, 
                 scale_width_adjustment=dict(candle=2, lines=2),
                 update_width_config=dict(candle_linewidth=1.5),
                 volume=True,
                 returnfig=True
             )

        axs[0].set_title(title);
        fig.savefig(file_name, bbox_inches='tight')
        print("Saved {}".format(file_name))

        base_data_ticker = data_ticker.copy()

        SPECIAL_TICKERS += [x for x in configs["PORT_LONG_TERM"] if x not in SPECIAL_TICKERS]

        fp = open("README_TICKERS.md", "w")

        for ticker in SPECIAL_TICKERS:
            data_ticker_raw = get_stock_data(ticker, start_date, end_date)
            if data_ticker_raw is None:
                continue
            data_ticker = data_ticker_raw.copy()
            data_ticker["rs"] = data_ticker["close"] / base_data_ticker["close"]

            file_name = "{}/{}_CHART.jpg".format(OUTPUT_DIR, ticker)
            style = "yahoo"
            title = "{}_CHART: {} - {} - {}".format(ticker, start_date, now_str, ticker)
            apds = [
                mpf.make_addplot(data_ticker['rs'], panel=2, type='line', label="RS(VNINDEX) MA(49)", mav=49)
            ]
            fig, axs = mpf.plot(data_ticker.set_index("time"), mav=(10, 20, 50, 100), mavcolors=['r', 'g', 'b', 'gray'], 
                     figsize=(30, 10), panel_ratios=(3, 1),figratio=(1,1), figscale=1.5, fontscale=2, tight_layout=False,
                     addplot=apds,
                     xrotation=0,
                     type="candle", style=style, 
                     scale_width_adjustment=dict(candle=2, lines=2),
                     update_width_config=dict(candle_linewidth=1.5),
                     volume=True,
                     returnfig=True
                 )

            axs[0].set_title(title);
            fig.savefig(file_name, bbox_inches='tight')
            print("Saved {}".format(file_name))
            line = "!['{}_CHART']({})\n".format(ticker, file_name)
            fp.write(line)
        fp.close()

        plt.style.use('dark_background')
    
# CALCULATE STOCK CHARTS
if not DEBUG:
    plt.style.use('dark_background')
    start_date = RS_START_DATE

    # PREPARE FIGURES
    # AVG_GROUP
    avg_colors = get_colors(len(configs) + 1)
    
    avg_file_name = "{}/AVG_GROUP_RS.jpg".format(OUTPUT_DIR)
    avg_fig, avg_axs = plt.subplots(2, figsize=(15, 30))
    avg_fig.suptitle("AVG_GROUP_RS - {} to {}".format(start_date, now_str), fontsize=20, weight='bold')
    # avg_axs[0].set_ylim([0.9, 1.2])
    # avg_axs[1].set_ylim([0.9, 1.2])

    # AVG_TOP_GROUP
    avg_top_colors = get_colors(len(configs) + 1)

    avg_top_file_name = "{}/AVG_TOP_GROUP_RS.jpg".format(OUTPUT_DIR)
    avg_top_fig, avg_top_axs = plt.subplots(2, figsize=(15, 30))
    avg_top_fig.suptitle("AVG_TOP_GROUP_RS - {} to {}".format(start_date, now_str), fontsize=20, weight='bold')
    # avg_top_axs[0].set_ylim([0.9, 1.2])
    # avg_top_axs[1].set_ylim([0.9, 1.2])
    
    # CALCULATE BASE_TICKER
    base_ticker = get_stock_data(RS_BASE_TICKER, start_date, end_date)
    base_ticker_raw = base_ticker.copy()
    base_ticker_start_time = base_ticker.iloc[0]["time"]
    scale = base_ticker.iloc[0]["close"] / 100
    base_ticker["open"] = base_ticker["open"].div(scale)
    base_ticker["high"] = base_ticker["high"].div(scale)
    base_ticker["low"] = base_ticker["low"].div(scale)
    base_ticker["close"] = base_ticker["close"].div(scale)
    base_ticker["rs"] = 1.0

    # plot base_ticker
    label = RS_BASE_TICKER
    last_value = 1.0
    color = "#f5ec42"
    base_ticker.plot(ax=avg_axs[0], x='time', y='rs', label=label, color=color)
    avg_axs[0].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')
    base_ticker.plot(ax=avg_axs[1], x='time', y='rs', label=label, color=color)
    avg_axs[1].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')
    base_ticker.plot(ax=avg_top_axs[0], x='time', y='rs', label=label, color=color)
    avg_top_axs[0].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')
    base_ticker.plot(ax=avg_top_axs[1], x='time', y='rs', label=label, color=color)
    avg_top_axs[1].annotate(label, xy=(1, last_value), xytext=(8, 0), 
             xycoords=('axes fraction', 'data'), textcoords='offset points', 
             color=color, fontsize=12, weight='bold')

    # plot groups
    fp = open("README_CHART.md", "w")
    line = "!['{}_CHART']({})\n".format("VNINDEX", "{}/VNINDEX_CHART.jpg".format(OUTPUT_DIR))
    fp.write(line)
    line = "!['{}_CHART']({})\n".format("VN30", "{}/VN30_CHART.jpg".format(OUTPUT_DIR))
    fp.write(line)
    line = "!['{}']({})\n".format("AVG_GROUP_RS", avg_file_name)
    fp.write(line)
    line = "!['{}']({})\n".format("AVG_TOP_GROUP_RS", avg_top_file_name)
    fp.write(line)

    for group_idx, (group, tickers) in enumerate(configs.items()):
        ticker_colors = get_colors(len(tickers) + 1)
        file_name = "{}/{}_CHART.jpg".format(OUTPUT_DIR, group)
        if not "PORT" in group and group not in ["INDEX", "CRYPTO", "FOREX", "US"]:
            line = "{}\n".format(group)
            fp.write(line)
            line = "!['{}_CHART']({})\n".format(group, file_name)
            fp.write(line)
        if os.path.exists(file_name):
            # print("Skip {}".format(file_name))
            continue

        # RS for group tickers
        plt.style.use('dark_background')
        file_name_rs = "{}/{}_RS.jpg".format(OUTPUT_DIR, group)
        fig_rs, axs_rs = plt.subplots(2, figsize=(15, 15))
        fig_rs.suptitle("{}_RS - {} to {} - {}".format(group, start_date, now_str, group), fontsize=20, weight='bold')
        ticker_colors = get_colors(len(tickers) + 1)
        is_valid = False

        avg_ticker_list = []
        for ticker_idx, ticker in enumerate(tickers):
            data_ticker_raw = get_stock_data(ticker, start_date, end_date)
            if data_ticker_raw is None:
                continue
            data_ticker = data_ticker_raw.copy()

            try:
                scale = data_ticker[data_ticker["time"] == base_ticker_start_time].iloc[0]["close"] / 100
                
                data_ticker["open"] = data_ticker["open"].div(scale)
                data_ticker["high"] = data_ticker["high"].div(scale)
                data_ticker["low"] = data_ticker["low"].div(scale)
                data_ticker["close"] = data_ticker["close"].div(scale)
                data_ticker["rs"] = data_ticker["close"] / base_ticker["close"]
                if ticker != "VNINDEX" and len(avg_ticker_list) < TOP_TICKERS_FOR_AVERAGE_GROUP:
                    avg_ticker_list.append(data_ticker)

                # plot group ticker
                if True:
                    last_value = data_ticker["rs"].dropna().iloc[-1]
                    label = '{} {:.2f}'.format(ticker, last_value)
                    color = ticker_colors[ticker_idx]

                    is_valid = True
                    if last_value > 0.99:
                        ax = axs_rs[0]
                    else:
                        ax = axs_rs[1]
                    plt.style.use('dark_background')
                    data_ticker.plot(ax=ax, x='time', y='rs', label=label, color=color)
                    ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                             xycoords=('axes fraction', 'data'), textcoords='offset points', 
                             color=color, fontsize=12, weight='bold')
                    if ticker == "VNINDEX":
                        ax = axs_rs[1]
                        data_ticker.plot(ax=ax, x='time', y='rs', label=label, color=color)
                        ax.annotate(label, xy=(1, last_value), xytext=(8, 0), 
                                 xycoords=('axes fraction', 'data'), textcoords='offset points', 
                                 color=color, fontsize=12, weight='bold')
                        
            except:
                continue

        if is_valid:
            plt.style.use('dark_background')
            axs_rs[0].grid(False)
            axs_rs[1].grid(False)
            axs_rs[0].legend(fontsize=10, loc='upper left')
            axs_rs[1].legend(fontsize=10, loc='upper left')
            fig_rs.savefig(file_name_rs, bbox_inches='tight')
            print("Saved {}".format(file_name_rs))
    
        if len(avg_ticker_list) > 0:
            try:
                avg_df = pd.concat(avg_ticker_list)
                avg_df = avg_df.groupby(avg_df.index).mean()

                has_volume = "volume" in avg_df and not avg_df["volume"].isnull().any().any()
                style = "yahoo"
                title = "{}_CHART: {} - {} - {}".format(group, start_date, now_str, group)
                apds = [
                    mpf.make_addplot(avg_df['rs'], panel=2, type='line', label="RS(VNINDEX) MA(49)", mav=49)
                ]
                fig, axs = mpf.plot(avg_df.set_index("time"), mav=(10, 20, 50, 100), mavcolors=['r', 'g', 'b', 'gray'], 
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
                fig.savefig(file_name, bbox_inches='tight')
                print("Saved {}".format(file_name))

                plt.style.use('dark_background')
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
            except Exception as e:
                print("Skip {} - {}".format(file_name, e))
                print(traceback.format_exc())

    # save figs
    plt.style.use('dark_background')
    avg_axs[0].grid(False)
    avg_axs[1].grid(False)
    avg_top_axs[0].grid(False)
    avg_top_axs[1].grid(False)
    avg_axs[0].legend(fontsize=10, loc='upper left')
    avg_axs[1].legend(fontsize=10, loc='upper left')
    avg_fig.savefig(avg_file_name, bbox_inches='tight')
    print("Saved AVG_GROUP: {}".format(avg_file_name))
    avg_top_axs[0].legend(fontsize=10, loc='upper left')
    avg_top_axs[1].legend(fontsize=10, loc='upper left')
    avg_top_fig.savefig(avg_top_file_name, bbox_inches='tight')
    print("Saved AVG_TOP_GROUP: {}".format(avg_top_file_name))
    plt.close()

# CALCULATE SCALE CHARTS
if True:
    plt.style.use('dark_background')
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
            csv_file_name = "{}/{}_{}.csv".format(OUTPUT_DATA_DIR, group, idx)
            if os.path.exists(file_name):
                # print("Skip {}".format(file_name))
                continue
            fig, ax = plt.subplots(figsize=(15, 10))
            
            ax.set_title("{}_{} - {} to {} - {}".format(group, idx, origin_date, now.strftime("%Y-%m-%d %H:%M:%S"), group), fontsize=20, weight='bold')
            is_valid = False
            avg_ticker_list = []
            raw_ticker_list = []
            for ticker_idx, ticker in enumerate(tickers):
                raw_data_ticker = None
                try:
                    raw = get_data(ticker, origin_date, end_date, should_scale=False)
                    raw["ticker"] = ticker
                    columns = ["ticker", "time", "open", "close", "high", "low"]
                    if "volume" in raw:
                        columns.append("volume")
                    raw_data_ticker = raw[columns]
                except:
                    pass
                if ticker == "SSI":
                    print("raw_data_ticker: before ", raw_data_ticker)
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
                if raw_data_ticker is not None:
                    raw_ticker_list.append(raw_data_ticker)
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
                plt.style.use('dark_background')
                ax.legend(fontsize=10, loc='upper left')
                ax.grid(False)
                fig.savefig(file_name, bbox_inches='tight')
                print("Saved {}".format(file_name))

                raw_df = pd.concat(raw_ticker_list)
                raw_df.to_csv(csv_file_name, index=False)
                print("Saved {}".format(csv_file_name))               

        plt.style.use('dark_background')
        avg_ax.legend(fontsize=10, loc='upper left')
        avg_ax.grid(False)
        avg_fig.savefig(avg_file_name, bbox_inches='tight')
        print("Saved AVG_GROUP: {}".format(avg_file_name))
        avg_top_ax.legend(fontsize=10, loc='upper left')
        avg_top_ax.grid(False)
        avg_top_fig.savefig(avg_top_file_name, bbox_inches='tight')
        print("Saved AVG_TOP_GROUP: {}".format(avg_top_file_name))
        plt.close()
