import os
if "ACCEPT_TC" not in os.environ:
    os.environ["ACCEPT_TC"] = "tôi đồng ý"

from vnstock3 import Vnstock

stock = Vnstock().stock(symbol="FRT", source="VCI")
print(stock.listing.all_symbols())
print(stock.quote.history(start='2020-01-01', end='2024-12-31'))

