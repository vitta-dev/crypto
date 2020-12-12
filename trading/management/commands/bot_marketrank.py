import datetime
import time
from decimal import *

import numpy
import talib
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

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

    def add_arguments(self, parser):
        parser.add_argument('bot_name', nargs='?')

    def handle(self, *args, **options):

        bot_name = options['bot_name']

        is_bot = True

        while is_bot:

            try:
                bot = MarketBot.objects.get(name=bot_name)
                bot.bot_last_run = timezone.now()
                bot.save()
            except MarketBot.DoesNotExist:
                print('Bot "{}" Does Not Exist'.format(bot_name))
                return False

            markets = bot.get_markets(api)

            markets = []
            is_bot = False
            for market in markets:
                print('----------------------')
                print(market.name)

                # получаем все открытые ордера
                orders = MarketMyOrder.open_objects.filter(market=market, bot=bot)
                print(orders)

                if orders:
                    for order in orders:
                        # print("Проверяем состояние ордера %s" % order.id)
                        if order.uuid:
                            if order.status in [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]:
                                order = check_order(order, bot=bot)

                            if order.type == MarketMyOrder.Type.BUY:
                                print('---------- CHECK BUY --------')
                                if order.status == MarketMyOrder.Status.FILLED and not order.is_close:
                                    # если ордер на покупку был выполнен создаем ордер на продажу

                                    if check_trend_sell(market, bot):
                                        create_sell_current(from_order=order, market=market, bot=bot)

                                if order.status in [MarketMyOrder.Status.OPEN]:
                                    # Если buy не был исполнен, и прошло достаточно времени для отмены ордера,
                                    # отменяем
                                    if order.created_at <= timezone.now() - datetime.timedelta(seconds=ORDER_LIFE_TIME):
                                        # print('Пора отменять ордер %s' % order)
                                        print('cancel order')
                                        market_name = order.market.get_market_name(order.bot.exchange.code)
                                        cancel_res = api.cancel(order.uuid, market_name=market_name, is_test=bot.is_test)
                                        # TODO: убрать эмуляцию ?? Проверить работу
                                        if 'success' in cancel_res and cancel_res['success']:
                                            order.cancelled_at = timezone.now()
                                            order.status = MarketMyOrder.Status.CANCELED
                                            order.save()
                                            # print(market, "Ордер %s помечен отмененным в БД" % order)

                else:
                    # print(market, "Неисполненных ордеров в БД нет, пора ли создать новый?")
                    # Проверяем тренд, если рынок в нужном состоянии, выставляем ордер на покупку
                    # print(check_trend_sell(market, bot))
                    trend_buy = check_trend_buy(market, bot)
                    if trend_buy:
                        create_buy(market=market, bot=bot)

            print('----- time.sleep(3) -----')
            time.sleep(3)