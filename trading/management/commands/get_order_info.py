import datetime
import time
from decimal import *

import numpy
import talib
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.bittrex.config import BEAR_PERC, BULL_PERC, CAN_SPEND, MARKUP, STOCK_FEE
from trading.backedns.bittrex.client import ApiBittrex
from trading.backedns.bittrex.config import ORDER_LIFE_TIME
from trading.config import TICKINTERVAL_HOUR, TICKINTERVAL_FIVEMIN, TICKINTERVAL_ONEMIN, \
    TICKINTERVAL_FIFTEENMIN
from trading.models import Market, MarketMyOrder, MarketBot, MarketBotRank
from trading.utils import get_chart_data, create_buy, create_sell, check_order, convert_ticker, check_trend_buy, \
    get_heikin_ashi, check_trend_sell, create_sell_current

api = ApiBittrex()
getcontext().prec = 8

satoshi_1 = 0.00000001
satoshi_100 = 0.000001


class Command(BaseCommand):

    def handle(self, *args, **options):
        # получаем все открытые ордера
        orders = MarketMyOrder.objects.exclude(status=MarketMyOrder.Status.CANCELED)
        # orders = MarketMyOrder.objects.all()
        if orders:
            for order in orders:
                print(order)
                order_info = api.get_order(order, is_test=order.bot.is_test)
                order.update_info(order_info)
