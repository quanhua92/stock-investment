import os
if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

from vnstock3 import Vnstock
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt 

import pandas as pd
pd.options.mode.chained_assignment = None

from vnstock3.explorer.msn.quote import *

stock = Vnstock().stock(symbol="FRT", source="VCI")

list_origin_dates = ["2024-03-01", "2024-04-01", "2024-05-02", "2024-06-03"]

MY_ID_MAPPING = {
    "BTC": "c2111",
    "ETH": "c2112",
    "USDT": "c2115",
    "USDC": "c211a", 
    "BNB": "c2113",
    "BUSD": "c211i",
    "XRP": "c2117",
    "ADA": "c2114",
    "SOL": "c2116",
    "DOGE": "c2119",
    "TON": "c23br",
    
    "SPX": "a33k6h",
    "DJI": "a6qja2",
    "GOLD": "b1hb7w",
    "NDX":"a3yy77",
    "VNINDEX": "aqk2nm",
    "JAPAN": "c1uvw7",
    "NYSE": "a74pqh",
    
    "USDEUR": "avyn9c",
    "USDVND": "avyufr",
    "JPYVND": "ave8sm",
    "AUDVND": "auxrkr",
    "EURVND": "av93ec",
    "GBPVND": "avyjtc",
}

def is_stock_group(name):
    return name not in ["INDEX", "CRYPTO", "FOREX"]

def is_crypto_group(name):
    return name in ["CRYPTO"]

configs = {
    "INDEX": ["VNINDEX", "GOLD", "SPX", "DJI", "NDX", "JAPAN", "NYSE"],
    "CRYPTO": ["VNINDEX", "BTC", "ETH", "USDT", "USDC", "BNB", "XRP", "ADA", "SOL", "DOGE", "TON"],
    "FOREX": ["VNINDEX", "USDEUR", "USDVND", "JPYVND", "AUDVND", "EURVND", "GBPVND"],
    "NGAN_HANG": ["VNINDEX", "VCB", "BID", "CTG", "TCB", "VPB", "MBB", "ACB", "HDB", "VIB", "LPB", "STB"],
    "BAN_LE": ["VNINDEX", "MWG", "FRT", "DGW", "PET", "AST", "DHT"],
    "BAT_DONG_SAN": [
        "VNINDEX",
        "VHM",
        "VIC",
        "BCM",
        "VRE",
        "NVL",
        "KDH",
        "SSH",
        "KBC",
        "NLG",
        "TCH",
        "NTL",
    ],
    "TAI_CHINH": [
        "VNINDEX",
        "SSI",
        "VND",
        "VCI",
        "HCM",
        "SHS",
        "MBS",
        "VIX",
        "FTS",
        "BSI",
        "EVF",
        "CTS",
        "DSC",
        "BVS",
    ],
    "HANG_CA_NHAN": [
        "VNINDEX",
        "PNJ",
        "VGT",
        "TCM",
        "TLG",
        "MSH",
        "RAL",
    ],
    "THUC_PHAM": [
        "VNINDEX",
        "VNM",
        "MCH",
        "MSN",
        "SAB",
        "KDC",
        "QNS",
        "VHC",
        "HAG",
        "BHN",
        "HNG",
        "ANV",
    ],
    "TAI_NGUYEN": [
        "VNINDEX",
        "HPG",
        "MSR",
        "HSG",
        "ACG",
        "NKG",
        "KSV",
        "VIF",
        "PTB",
        "TVN",
        "PRT",
    ],
    "XAY_DUNG": [
        "VNINDEX",
        "VGC",
        "HUT",
        "CTR",
        "VCG",
        "VCS",
        "BMP",
        "PC1",
        "CTD",
        "SCG",
        "HHV",
        "CII",
    ],
    "DIEN_NUOC_XANG": [
        "VNINDEX",
        "GAS",
        "PGV",
        "VSH",
        "POW",
        "BWE",
        "HND",
        "QTP",
        "NT2",
    ],
    "DAU_KHI": [
        "VNINDEX",
        "BSR",
        "PLX",
        "PVS",
        "PVD",
        "OIL",
    ],
    "DICH_VU_CONG_NGHIEP": [
        "VNINDEX",
        "ACV",
        "VEA",
        "GMD",
        "REE",
        "MVN",
        "GEX",
        "GEE",
        "PVT",
        "VTP",
    ],
    "CONG_NGHE": [
        "VNINDEX",
        "FPT",
        "CMG",
        "SAM",
    ],
    "BAO_HIEM": [
        "VNINDEX",
        "BVH",
        "PVI",
        "VNR",
        "BIC",
        "MIG",
        "BMI",
        "ABI",
    ],
    "HOA_CHAT": [
        "VNINDEX",
        "GVR",
        "DGC",
        "DCM",
        "DPM",
        "PHR",
        "AAA",
    ],
    "OTO_PHU_TUNG":[
        "VNINDEX",
        "DRC",
        "HHS",
        "CTF",
        "SVC",
        "CSM",
        "HAX",
    ],
    "DU_LICH": [
        "VNINDEX",
        "VJC",
        "SCS",
        # "TSJ",
    ],
    "VIEN_THONG": [
        "VNINDEX",
        "VGI",
        "FOX",
        "VEF",
        "VNZ"
    ],
    "Y_TE":[
        "VNINDEX",
        "DHG",
        "IMP",
        "DVN",
        "DBD",
    ],
    "PORT_GROUP_BIG_CAP": [
        "VNINDEX",
        "VCB", "MWG", "VHM", "SSI", "PNJ", "VNM", "HPG", "VGC",
        "GAS", "BSR", "ACV", "FPT", "BVH", "GVR", "DRC", "VJC",
        # "VGI"
        
    ],
    "PORT_GROUP_TOP_1": [
        "VNINDEX",
        "TCB", "DHT", "TCH", "BVS", "VGT", "MCH", "KSV", "VCS",
        "POW", "BSR", "ACV", "CMG", "MIG", "DCM", "HAX", "SCS",
        "FOX"
    ],
    "PORT_QH": [
        "VNINDEX",
        "BSR",
        "CTS",
        "DCM",
        "HAG",
        "LPB",
        "MBS",
        "MWG",
        "PLX",
        "PVT",
        "TCH",
        "TCM"
    ],
    "PORT_MT": [
        "VNINDEX",
        "VNM", "MWG", "SSI", "FRT", "ANV", "NKG", "AGG", "VCB",
        "QNS", "MBB", "HPG", "KBC", "TCB", "CII", "FUEVFVND",
        "DRC", "IDC", "PNJ", "ABB", "MSN", "CTG", "PVD"
    ],
}

def get_data(is_stock, is_crypto, symbol, origin_date, end_date, start_date="2023-01-01"):
    try:
        if is_stock:
            df = stock.quote.history(symbol=symbol, start=start_date, end=end_date)
        else:
            if symbol == "VNINDEX":
                df = stock.quote.history(symbol="VNINDEX", start=start_date, end=end_date)
            else:
                if is_crypto:
                    if origin_date == "2024-03-01":
                        origin_date = "2024-03-02"
                    if origin_date == "2024-05-02":
                        origin_date = "2024-05-01"
                symbol_id = MY_ID_MAPPING[symbol]
                quote = Quote(symbol_id=symbol_id)
                df = quote.history(start=start_date, end=end_date, interval='1D')
        origin_close = float(df[df["time"] == origin_date]["close"].iloc[0])
        scale = origin_close / 100
        data = df[["time", "close"]]
        data["close"] = data["close"].div(scale)
        return data[data["time"] >= origin_date]
    except Exception as e:
        print("Error {}: {} {} {} {}".format(e, is_stock, symbol, origin_date, end_date))
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
for (group, tickers) in configs.items():
    is_stock = is_stock_group(group)
    is_crypto = is_crypto_group(group)
    ticker_colors = get_colors(len(tickers))
    for idx, origin_date in enumerate(list_origin_dates):
        file_name = "images/{}_{}.jpg".format(group, idx)
        if os.path.exists(file_name):
            # print("Skip {}".format(file_name))
            continue
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.set_title("{}_{} - {} to {}".format(group, idx, origin_date, now.strftime("%Y-%m-%d %H:%M:%S")), fontsize=20, weight='bold')
        is_valid = False
        for ticker_idx, ticker in enumerate(tickers):
            data_ticker = get_data(is_stock, is_crypto, ticker, origin_date, end_date)
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
        
        if is_valid:
            plt.savefig(file_name)
            print("Saved {}".format(file_name))
        plt.close()
        # plt.show()
