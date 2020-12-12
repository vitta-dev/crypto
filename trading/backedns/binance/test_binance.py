from trading.backedns.binance.config import API_KEY, SECRET_KEY
from binance.client import Client

client = Client(API_KEY, SECRET_KEY)

# time_res = client.get_server_time()
# print(time_res)
#
#
# status = client.get_system_status()
# print(status)

# info = client.get_exchange_info()
# print(info)

data = {'symbol': 'EVXETH',
        'status': 'TRADING',
        'baseAsset': 'EVX',
        'baseAssetPrecision': 8,
        'quoteAsset': 'ETH',
        'quotePrecision': 8,
        'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
        'icebergAllowed': False,
        'filters': [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.00015180', 'maxPrice': '0.01517500', 'tickSize': '0.00000010'},
        {'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 'maxQty': '90000000.00000000', 'stepSize': '1.00000000'},
        {'filterType': 'MIN_NOTIONAL', 'minNotional': '0.01000000'},
        {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}
        ]}

# info = client.get_symbol_info('BNBBTC')
# print(info)

# products = client.get_products()
# print(products)

# depth = client.get_order_book(symbol='BNBBTC')
# print(depth)

# trades = client.get_recent_trades(symbol='BNBBTC')
# print(trades)

# trades = client.get_historical_trades(symbol='BNBBTC')
# print(trades)

# trades = client.get_aggregate_trades(symbol='BNBBTC')
# print(trades)

# Aggregate Trade Iterator

# agg_trades = client.aggregate_trade_iter(symbol='ETHBTC', start_str='30 minutes ago UTC')
#
# # iterate over the trade iterator
# for trade in agg_trades:
#     print(trade)
#     # do something with the trade data
#
# # convert the iterator to a list
# # note: generators can only be iterated over once so we need to call it again
# agg_trades = client.aggregate_trade_iter(symbol='ETHBTC', start_str='30 minutes ago UTC')
# agg_trade_list = list(agg_trades)
#
# # example using last_id value
# agg_trades = client.aggregate_trade_iter(symbol='ETHBTC', last_id=23380478)
# agg_trade_list = list(agg_trades)


# end Aggregate Trade Iterator

# candles = client.get_klines(symbol='BNBBTC', interval=Client.KLINE_INTERVAL_30MINUTE)
# print(candles)

# Get Historical Kline/Candlesticks
# fetch 1 minute klines for the last day up until now
# klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
# print(klines)
#
# # fetch 30 minute klines for the last month of 2017
# klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
# print(klines)
#
# # fetch weekly klines since it listed
# klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
# print(klines)
# end Get Historical Kline/Candlesticks

# tickers = client.get_ticker()
# print(tickers)

# prices = client.get_all_tickers()
# print(prices)

# tickers = client.get_orderbook_tickers()
# print(tickers)

# orders = client.get_all_orders(symbol='BNBBTC', limit=10)
# print(orders)

# info = client.get_account()
# print(info)

# balance = client.get_asset_balance(asset='BTC')
# print(balance)

# status = client.get_account_status()
# print(status)

# trades = client.get_my_trades(symbol='BNBBTC')
# print(trades)
