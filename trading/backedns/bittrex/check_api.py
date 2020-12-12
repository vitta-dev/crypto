# from bittrex import Bittrex, API_V2_0, API_V1_1
# from trading.backedns.bittrex.client import ApiBittrex
#
# API_KEY = '5b8611d4a0094bbb8e971afb47900df1'
# API_SECRET = '059c048e8ce240c8ae607136857fc54d'

# my_bittrex = Bittrex(API_KEY, API_SECRET, api_version=API_V1_1)
# my_bittrex = ApiBittrex()

# res = my_bittrex.get_markets()
# print(res)
# print(res['result'])



# res = my_bittrex.get_currencies()API_V1_1
# print(res['result'])

# res = my_bittrex.get_market_summaries()
# print(res['result'])

# value = float('1.72e-05')
# string_value = "%f" % value

# >>> print 0.00001357
# 1.357e-05
# >>> print format(0.00001357, 'f')
# 0.000014
# >>> print format(0.00001357, '.8f')
# 0.00001357

# res = my_bittrex.get_marketsummary('BTC-LTC')
# print(res['result'])

# res = my_bittrex.get_orderbook('BTC-LTC')
# print(res['result'])


# res = my_bittrex.get_market_history('BTC-LTC')
# print(res['result'])

# res = my_bittrex.get_market_history('BTC-DOGE')
# print(res)

#
# res = my_bittrex.get_latest_candle('BTC-XVG', 'fiveMin')
# print(res['result'])
# print(res)


STOCK_FEE = 0.0025  # Какую комиссию берет биржа
markup = 1
spent = 100
amount = 1
order_spent, order_amount = spent, amount
new_rate = (order_spent + order_spent * markup / 100) / order_amount
print('new_rate', new_rate)

new_rate_fee = new_rate + (new_rate * STOCK_FEE * 2) / (1 - STOCK_FEE)
new_rate_fee = new_rate + (new_rate * STOCK_FEE * 2)
print('new_rate_fee', new_rate_fee)