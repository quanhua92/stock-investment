import os
if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

from vnstock3 import Vnstock
from datetime import datetime
import matplotlib.pyplot as plt 

import pandas as pd
pd.options.mode.chained_assignment = None

stock = Vnstock().stock(symbol="FRT", source="VCI")

list_origin_dates = ["2024-02-01", "2024-03-01", "2024-04-01", "2024-05-02"]

configs = {
    "NGAN_HANG": ["VNINDEX", "VCB", "BID", "CTG", "TCB", "VPB", "MBB", "ACB", "HDB", "VIB", "LPB", "STB"],
    "BAN_LE": ["VNINDEX", "MWG", "FRT", "DGW", "PET", "AST", "DHT"],
    "BAT_DONG_SAN": [
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
        "PNJ",
        "VGT",
        "TCM",
        "TLG",
        "MSH",
        "RAL",
    ],
    "THUC_PHAM": [
        "VNM",
        "MCH",
        "MSN",
        "SAB",
        "VSF",
        "KDC",
        "QNS",
        "VHC",
        "HAG",
        "BHN",
        "HNG",
        "ANV",
    ],
    "TAI_NGUYEN": [
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
        "BSR",
        "PLX",
        "PVS",
        "PVD",
        "OIL",
    ],
    "DICH_VU_CONG_NGHIEP": [
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
        "FPT",
        "CMG",
        "SAM",
    ],
    "BAO_HIEM": [
        "BVH",
        "PVI",
        "VNR",
        "BIC",
        "MIG",
        "BMI",
        "ABI",
    ],
    "HOA_CHAT": [
        "GVR",
        "DGC",
        "DCM",
        "DPM",
        "PHR",
        "AAA",
    ],
    "OTO_PHU_TUNG":[
        "DRC",
        "HHS",
        "CTF",
        "SVC",
        "CSM",
        "HAX",
    ],
    "DU_LICH": [
        "VJC",
        "SCS",
        "TSJ",
    ],
    "VIEN_THONG": [
        "VGI",
        "FOX",
        "VEF",
        "VNZ"
    ],
    "Y_TE":[
        "DHG",
    "IMP",
    "DVN",
    "DBD",
    ]
}

def get_data(symbol, origin_date, end_date):
    try:
        df = stock.quote.history(symbol=symbol, start="2023-01-01", end=end_date)
        origin_close = float(df[df["time"] == origin_date]["close"].iloc[0])
        scale = origin_close / 100
        
        data = df[["time", "close"]]
        data["close"] = data["close"].div(scale)
        return data[data["time"] >= origin_date]
    except:
        print("Error: {} {} {}".format(symbol, origin_date, end_date))
        return None


def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.get_cmap(name, n)

end_date = datetime.now().strftime("%Y-%m-%d")
for (group, tickers) in configs.items():
    cmap = get_cmap(len(tickers))
    for idx, origin_date in enumerate(list_origin_dates):
        file_name = "images/{}_{}.jpg".format(group, idx)
        if os.path.exists(file_name):
            print("Skip {}".format(file_name))
            continue
        fig, ax = plt.subplots()
        ax.set_title("{}_{} - {} to {}".format(group, idx, origin_date, end_date))
        for ticker_idx, ticker in enumerate(tickers):
            data_ticker = get_data(ticker, origin_date, end_date)
            if data_ticker is None:
                continue
            last_value = data_ticker["close"].iloc[-1]
            label = '{} {:.2f}'.format(ticker, last_value)
            data_ticker.plot(ax=ax, x='time', y='close', label=label, color=cmap(ticker_idx))
            ax.annotate('%0.2f' % last_value, xy=(1, last_value), xytext=(8, 0), 
                     xycoords=('axes fraction', 'data'), textcoords='offset points', color=cmap(ticker_idx))
        
        plt.savefig(file_name)
        print("Saved {}".format(file_name))
        plt.close()
        # plt.show()
