from django.conf import settings
from bittrex import API_V2_0, API_V1_1

from decimal import Decimal

BITTREX_API_KEY = settings.BITTREX_API_KEY
BITTREX_SECRET_KEY = settings.BITTREX_SECRET_KEY
BITTREX_APY_VER = getattr(settings, 'BITTREX_APY_VER', API_V1_1)

PROTECTION_PUB = 'pub'  # public methods
PROTECTION_PRV = 'prv'  # authenticated methods

CAN_SPEND = 2  # Сколько USDT готовы вложить в бай
# CAN_SPEND = 0.00013256  # Сколько USDT готовы вложить в бай
MARKUP = Decimal(0.01)  # 0.001 = 0.1% - Какой навар со сделки хотим получать

STOCK_FEE = Decimal(0.0025)  # Какую комиссию берет биржа

# ORDER_LIFE_TIME = 0.5  # Через сколько минут отменять неисполненный ордер на покупку 0.5 = 30 сек.
ORDER_LIFE_TIME = 60    # Через сколько секунд отменять неисполненный ордер на покупку

USE_MACD = True  # True - оценивать тренд по MACD, False - покупать и продавать невзирая ни на что

BEAR_PERC = 70  # % что считаем поворотом при медведе (подробности - https://bablofil.ru/macd-python-stock-bot/
BULL_PERC = 99.5  # % что считаем поворотом при быке

