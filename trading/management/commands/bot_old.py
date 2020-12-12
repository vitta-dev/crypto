import datetime
import random
import time

from decimal import Decimal
from django.core.management import BaseCommand
from django.utils import timezone
from django.db.models import Q

from trading.backedns.bittrex.client import ApiBittrex
from trading.backedns.bittrex.config import USE_MACD, ORDER_LIFE_TIME
from trading.models import Market, MarketMyOrder
from trading.utils import get_chart_data, get_macd_advice, create_buy, create_sell
from trading.config import TICKINTERVAL_HOUR, TICKINTERVAL_FIVEMIN, TICKINTERVAL_THIRTYMIN

api = ApiBittrex()


def check_order(order):
    order_info = api.get_order(order)

    ticker_data = api.get_ticker(market=order.market.name)

    # sell - ASK
    # buy - BID
    random_action = 3
    # проверяем, если ордер на продажу SELL - если наш ордер <= BID отмечаем как исполненный
    if order.type == MarketMyOrder.Type.SELL and order.price <= ticker_data['Bid']:
        random_action = 1
    # проверяем, если ордер на покупку BUY -  если наш ордер >= ASK отмечаем как исполненный
    if order.type == MarketMyOrder.Type.BUY and order.price >= ticker_data['Ask']:
        random_action = 1

    # random_action = random.randint(1, 3)
    # random_action = 1
    if random_action == 1 or (order_info['Closed'] and not order_info['CancelInitiated']):
        # print('Ордер %s уже выполнен!' % order)
        order.filled_at = timezone.now()
        # order.price = order_info['Price']
        # order.amount = order_info['Quantity']
        order.spent = order.spent + Decimal(order_info["CommissionPaid"])
        order.fee = order_info["CommissionPaid"]
        order.save()
    elif random_action == 2 or (order_info['Closed'] and order_info['CancelInitiated']):
        # print(order.market, 'Ордер %s отменен!' % order)
        # order.price = order_info['Price']
        # order.order_amount = order_info['Quantity']
        order.fee = order_info["CommissionPaid"]
        order.cancelled_at = datetime.datetime.now()
        order.save()
        # print(order.market, "Ордер %s помечен отмененным в БД" % order)
    else:
        # print(order.market, "Ордер %s еще не выполнен" % order)
        if order_info['QuantityRemaining'] != order_info['Quantity']:
            # order.partially_filled = True
            order.save()

    return order


class Command(BaseCommand):

    def handle(self, *args, **options):

        is_bot = True
        ticker_interval = TICKINTERVAL_FIVEMIN

        while is_bot:

            print('----- time.sleep(3) -----')
            time.sleep(3)

            markets = Market.objects.filter(is_bot=True)

            for market in markets:
                print('----------------------')
                print(market.name)
                # log(market, "Получаем все неисполненные ордера по БД")
                orders = MarketMyOrder.objects.filter(Q(market=market),
                                                      Q(
                                                          Q(type=MarketMyOrder.Type.SELL, filled_at__isnull=True)
                                                          |
                                                          Q(type=MarketMyOrder.Type.BUY, filled_at__isnull=False,
                                                            is_close=False)
                                                          |
                                                          Q(type=MarketMyOrder.Type.BUY, filled_at__isnull=True)
                                                      )
                                                      )

                if orders:
                    for order in orders:
                        # print("Проверяем состояние ордера %s" % order.id)
                        if order.uuid:
                            if not order.filled_at and not order.created_at:
                                order = check_order(order)
                                # order_info = api.get_order(order)
                                #
                                # random_action = random.randint(1, 3)
                                # random_action = 1
                                # if random_action == 1 or (order_info['Closed'] and not order_info['CancelInitiated']):
                                #     print('Ордер %s уже выполнен!' % order)
                                #     order.filled_at = timezone.now()
                                #     # order.price = order_info['Price']
                                #     # order.amount = order_info['Quantity']
                                #     order.spent = order.spent + Decimal(order_info["CommissionPaid"])
                                #     order.fee = order_info["CommissionPaid"]
                                #     order.save()
                                # elif random_action == 2 or (order_info['Closed'] and order_info['CancelInitiated']):
                                #     print(market, 'Ордер %s отменен!' % order)
                                #     # order.price = order_info['Price']
                                #     # order.order_amount = order_info['Quantity']
                                #     order.fee = order_info["CommissionPaid"]
                                #     order.cancelled_at = datetime.datetime.now()
                                #     order.save()
                                #     print(market, "Ордер %s помечен отмененным в БД" % order)
                                # else:
                                #     print(market, "Ордер %s еще не выполнен" % order)
                                #     if order_info['QuantityRemaining'] != order_info['Quantity']:
                                #         # order.partially_filled = True
                                #         order.save()

                            if order.type == MarketMyOrder.Type.BUY:
                                print('---------- CHECK BUY --------')
                                if order.filled_at:  # если ордер на покупку был выполнен

                                    if USE_MACD:
                                        # проверяем, можно ли создать sell
                                        macd_advice = get_macd_advice(chart_data=get_chart_data(market, ticker_interval))
                                        if macd_advice['trand'] == 'BEAR' or (
                                                macd_advice['trand'] == 'BULL' and macd_advice['growing']):
                                            pass
                                            # print('Для ордера %s не создаем ордер на продажу, '
                                            #       'т.к. ситуация на рынке неподходящая' % order)
                                        else:
                                            # print("Для выполненного ордера на покупку выставляем ордер на продажу")
                                            print("Create order SELL")
                                            create_sell(from_order=order, market=market)
                                    else:  # создаем sell если тенденция рынка позволяет
                                        # print(market, "Для выполненного ордера на покупку выставляем ордер на продажу")
                                        print("Create order SELL")
                                        create_sell(from_order=order, market=market)
                                else:
                                    # Если buy не был исполнен, и прошло достаточно времени для отмены ордера,
                                    # отменяем
                                    # if not order.partially_filled and not order.cancelled_at:
                                    if not order.cancelled_at:
                                        # time_passed = time.time() - order.created_at
                                        # if time_passed > ORDER_LIFE_TIME * 60:
                                        # print(order.created_at)
                                        # print(timezone.now() - datetime.timedelta(seconds=ORDER_LIFE_TIME))
                                        if order.created_at <= timezone.now() - datetime.timedelta(seconds=ORDER_LIFE_TIME):
                                            # print('Пора отменять ордер %s' % order)
                                            print('cancel order')
                                            market_name = order.market.get_market_name(order.bot.exchange.code)
                                            cancel_res = api.api.cancel(order.uuid, market_name=market_name)
                                            # TODO: убрать эмуляцию
                                            if True or ('success' in cancel_res and cancel_res['success']):
                                                order.cancelled_at = timezone.now()
                                                order.save()
                                                # print(market, "Ордер %s помечен отмененным в БД" % order)
                            else:  # ордер на продажу
                                pass
                else:
                    # print(market, "Неисполненных ордеров в БД нет, пора ли создать новый?")
                    # Проверяем MACD, если рынок в нужном состоянии, выставляем ордер на покупку
                    if USE_MACD:
                        macd_advice = get_macd_advice(chart_data=get_chart_data(market, ticker_interval))
                        # print(macd_advice)
                        if macd_advice['trand'] == 'BEAR' and macd_advice['growing']:
                            # print(market, "Создаем ордер на покупку")
                            create_buy(market=market)
                        # else:
                        #     print(market, "Условия рынка не подходят для покупки", macd_advice)
                    else:
                        # print(market, "Создаем ордер на покупку")
                        create_buy(market=market)
