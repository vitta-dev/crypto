import time
from decimal import *

from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.bittrex.client import ApiBittrex
from trading.models import MarketMyOrder, MarketBot
from trading.utils import create_buy, check_trend_buy, \
    check_orders

api = ApiBittrex()
getcontext().prec = 8

satoshi_1 = 0.00000001
satoshi_100 = 0.000001


class Command(BaseCommand):

    def handle(self, *args, **options):

        res = api.get_ticks('BTC-LTC', 'fiveMin')
        print(res)

        # orders = MarketMyOrder.objects.filter(status__in=[MarketMyOrder.Status.FILLED, MarketMyOrder.Status.CLOSED],
        #                                       type=MarketMyOrder.Type.BUY,
        #                                       kind=MarketMyOrder.Kind.MAIN,
        #                                       market_id=275)

        # orders = MarketMyOrder.objects.filter(id__in=[2997, 2998, 2995])
        # print(orders)
        # for order in orders:
        #     print('-----', order)
        #     print(order.get_spent())
        #     print(order.get_profit())
        #     print(order.get_profit_percent())
            # order_info = api.get_order(order)
            # if order_info and 'result' not in order_info:
            #     print(order)
            #     print(order_info)
            #     # order.test_spent = order.price * order.amount + order.fee
            #     order.test_spent = order_info['Price'] + order_info['CommissionPaid']
            #     order.save()
