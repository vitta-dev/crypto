import time

from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import *

# Если нет нужных пакетов - читаем тут: https://bablofil.ru/python-indicators/
import numpy
import pytz
import talib
from django.conf import settings
from django.utils import timezone

from trading.lib import convert_number, convert_ticker_to_decimal, convert_date, round_time, \
    get_price_for_sell, get_price_for_buy, add_stock_fee, convert_ticker
from trading.backedns.bittrex.client import ApiBittrex
from trading.backedns.bittrex.config import BEAR_PERC, BULL_PERC, CAN_SPEND, MARKUP, STOCK_FEE
from trading.config import TICKINTERVAL_THIRTYMIN, TICKINTERVAL_FIVEMIN, TICKINTERVAL_ONEMIN, TICKINTERVAL_HOUR, \
    TICKINTERVAL_FIFTEENMIN
from trading.models import MarketMyOrder, MarketOrderLog
from trading.ta import TechnicalAnalysis

# api = ApiBittrex()
getcontext().prec = 8
satoshi_1 = Decimal(0.00000001)


def get_heikin_ashi(chart_data, market):

    ta = TechnicalAnalysis(market)
    ha_data = OrderedDict()
    candle_previous = None
    ha = None
    for dt_obj, candle in chart_data.items():
        ha = ta.heikin_ashi(candle, candle_previous, ha)
        ha_data[dt_obj] = ha
        candle_previous = candle

    return ha_data


def get_chart_data(market_name, api, tick_interval=TICKINTERVAL_FIVEMIN, hours=None, ):
    # Получаем с биржи данные, необходимые для построения индикаторов
    chart_data = OrderedDict()

    # Получаем готовые данные свечей
    res = api.get_ticks(market_name, tick_interval)
    # print('# Получаем готовые данные свечей')
    try:
        charts = res.get('result')
    except AttributeError:
        charts = res

    if charts:
        for item in charts:
            dt_obj = convert_date(item['T'], '%Y-%m-%dT%H:%M:%S')
            if hours and dt_obj >= timezone.now() - timedelta(hours=hours):
                if dt_obj not in chart_data:
                    chart_data[dt_obj] = {'open': float(item['O']),
                                          'close': float(item['C']),
                                          'high': float(item['H']),
                                          'low': float(item['L']),
                                          'value': float(item['V']),
                                          }
            else:
                chart_data[dt_obj] = {'open': float(item['O']),
                                      'close': float(item['C']),
                                      'high': float(item['H']),
                                      'low': float(item['L']),
                                      'value': float(item['V']),
                                      }

    # TODO: Добираем недостающее
    # print('# Добираем недостающее')
    # res = api.get_market_history(market_name)
    # if res:
    #     for trade in reversed(res):
    #         try:
    #             dt_obj = convert_date(trade['TimeStamp'], '%Y-%m-%dT%H:%M:%S.%f')
    #         except ValueError:
    #             dt_obj = convert_date(trade['TimeStamp'], '%Y-%m-%dT%H:%M:%S')
    #
    #         # ts = int((time.mktime(dt_obj.timetuple()) / 1800)) * 1800  # округляем до 5 минут
    #         # ts = (time.mktime(dt_obj.timetuple()) / 1800) * 1800  # округляем до 5 минут
    #
    #         if tick_interval == TICKINTERVAL_FIVEMIN:
    #             tick_round = 5
    #         elif tick_interval == TICKINTERVAL_THIRTYMIN:
    #             tick_round = 30
    #         elif tick_interval == TICKINTERVAL_FIFTEENMIN:
    #             tick_round = 15
    #         elif tick_interval == TICKINTERVAL_ONEMIN:
    #             tick_round = 1
    #         elif tick_interval == TICKINTERVAL_HOUR:
    #             tick_round = 60
    #         # else:
    #         #     tick_round = 60
    #
    #         # print('----- ', tick_round, ' - ', dt_obj)
    #         # округляем до tick_round минут
    #         # dt_obj += timedelta(minutes=tick_round)
    #         # print(dt_obj.minute % tick_round)
    #         # dt_obj -= timedelta(minutes=dt_obj.minute % tick_round, seconds=dt_obj.second, milliseconds=dt_obj.microsecond)
    #
    #         dt_obj = round_time(dt_obj, round_to=tick_round)
    #         ts = dt_obj
    #         # print('округлили ', ts)
    #         if ts not in chart_data:
    #             chart_data[ts] = {'open': 0, 'close': 0, 'high': 0, 'low': 0, 'value': 0}
    #
    #         if ts in chart_data:
    #             chart_data[ts]['close'] = float(trade['Price'])
    #
    #             if not chart_data[ts]['open']:
    #                 chart_data[ts]['open'] = float(trade['Price'])
    #
    #             if not chart_data[ts]['high'] or chart_data[ts]['high'] < float(trade['Price']):
    #                 chart_data[ts]['high'] = float(trade['Price'])
    #
    #             if not chart_data[ts]['low'] or chart_data[ts]['low'] > float(trade['Price']):
    #                 chart_data[ts]['low'] = float(trade['Price'])

    return chart_data


# def check_orders(orders, bot):
#     count_active_orders = 0
#     for order in orders:
#         # print("Проверяем состояние ордера %s" % order.id)
#         if order.uuid:
#             if order.status in [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]:
#                 order = check_order(order, bot=bot)
#
#             # если ордер на продажу проверяем stop loss
#             if order.type == MarketMyOrder.Type.SELL:
#
#                 if bot.is_trailing_cost:  # проверяем trailing cost
#                     order = check_trailing_resell(order, bot)
#
#                 check_stop_loss_sell(order, bot)
#
#             if order.type == MarketMyOrder.Type.BUY:
#                 print('---------- CHECK BUY --------')
#                 if order.status == MarketMyOrder.Status.FILLED and not order.is_close:
#                     # проверяем stop loss
#                     if check_stop_loss_buy(order, bot):
#                         count_active_orders += 1
#
#                     elif bot.is_trailing_cost:    # проверяем trailing cost
#                         if check_trailing_sell(order, bot):
#                             create_sell_current(from_order=order, market=order.market, bot=bot, is_block_trade=True)
#
#                     # elif check_trend_sell(order.market, bot):   # проверяем тренды на продажу (красная свеча)
#                     #     create_sell_current(from_order=order, market=market, bot=bot)
#
#                     elif create_sell(from_order=order, market=order.market, bot=bot):
#                         # если ордер на покупку был выполнен проверяем рынок и создаем ордер на продажу
#                         count_active_orders += 1
#
#                 if order.status in [MarketMyOrder.Status.OPEN]:
#                     # Если buy не был исполнен, и прошло достаточно времени для отмены ордера,
#                     # отменяем
#                     if order.created_at <= timezone.now() - timedelta(seconds=bot.order_life_time):
#                         # print('Пора отменять ордер %s' % order)
#                         print('cancel order')
#                         cancel_res = api.cancel(order.uuid, is_test=bot.is_test)
#                         print(cancel_res)
#                         # TODO: убрать эмуляцию ?? Проверить работу
#                         # if 'success' in cancel_res and cancel_res['success']:
#                         if cancel_res:
#                             order.cancel_order()
#
#     return count_active_orders


# # Ф-ция для создания ордера на покупку
# def create_buy(market, bot=None):
#     global USE_LOG
#     USE_LOG = True
#
#     if bot:
#         is_test = bot.is_test
#     else:
#         is_test = False
#
#     # print(market, 'Получаем текущие курсы')
#     # Получаем публичные данные тикера
#     res_ticker_data = api.get_ticker(market.name)
#     if res_ticker_data:
#         ticker_data = convert_ticker_to_decimal(res_ticker_data)
#         # Берем цену, по которой кто-то продает - стоимость комиссии заложим в цену продажи
#         # current_rate = Decimal(ticker_data['Ask'])
#         if ticker_data['Bid']:
#             current_rate = get_price_for_buy(ticker_data)
#             can_buy = bot.max_spend / current_rate
#             # TODO: проверять минимально возможную покупку и сигнализировать, если пытаемся купить меньше
#
#             pair = market.name
#             # print(market, """
#             #     Текущая цена - %0.8f
#             #     На сумму %0.8f %s можно купить %0.8f %s
#             #     Создаю ордер на покупку
#             #     """ % (current_rate, CAN_SPEND, pair[0], can_buy, pair[1])
#             #     )
#
#             try:
#                 current_rate = current_rate.quantize(Decimal('.00000000'))
#             except InvalidOperation:
#                 pass
#
#             try:
#                 can_buy = can_buy.quantize(Decimal('.00000000'))
#             except InvalidOperation:
#                 pass
#
#             if settings.BOT_PRINT_DEBUG:
#                 print('quantity: ', can_buy, ', rate: ', current_rate)
#                 print('sum: ', can_buy * current_rate)
#
#             order_res = api.buy_limit(market.name, quantity=can_buy, rate=current_rate, is_test=is_test)
#             if settings.BOT_PRINT_DEBUG:
#                 print(market.nameorder_res)
#             if order_res and order_res['uuid']:
#
#                 order = MarketMyOrder.objects.create(uuid=order_res['uuid'],
#                                                      market=market,
#                                                      price=current_rate,
#                                                      amount=can_buy,
#                                                      spent=bot.max_spend,
#                                                      bot=bot,
#                                                      ticker_data=res_ticker_data,
#                                                      is_test=bot.is_test
#                                                      )
#
#                 order.create_log(MarketOrderLog.Type.CREATE_ORDER,
#                                  ticker_data=res_ticker_data)
#                 # if is_test:
#                 #     order.status = MarketMyOrder.Status.FILLED
#                 #     order.save()
#                 print(market, 'Create order BUY')
#                 market_rank = bot.get_market_rank(market)
#                 market_rank.clear_max_price()
#                 return order
#
#     return False

#
# # Ф-ция для создания ордера на продажу + процент к покупке
# def create_sell(from_order, market, bot=None):
#     global USE_LOG
#     USE_LOG = True
#
#     if bot:
#         is_test = bot.is_test
#     else:
#         is_test = False
#
#     pair = market.name
#     buy_order_q = MarketMyOrder.objects.get(id=from_order.id)
#
#     order_spent, order_amount = buy_order_q.spent, buy_order_q.get_amount_for_sell()
#     new_rate = (order_spent + order_spent * bot.markup / 100) / order_amount
#
#     # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
#     new_rate_fee = add_stock_fee(new_rate)
#
#     res_ticker_data = api.get_ticker(market=market.name)
#     if res_ticker_data:
#         ticker_data = convert_ticker_to_decimal(res_ticker_data)
#         # Берем цену, по которой кто-то покупает
#         # current_rate = ticker_data['Bid']
#         current_rate = get_price_for_sell(ticker_data)
#
#         choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee
#
#         # print(market, """
#         #     Итого на этот ордер было потрачено %0.8f %s, получено %0.8f %s
#         #     Что бы выйти в плюс, необходимо продать купленную валюту по курсу %0.8f
#         #     Тогда, после вычета комиссии %0.4f останется сумма %0.8f %s
#         #     Итоговая прибыль составит %0.8f %s
#         #     Текущий курс продажи %0.8f
#         #     Создаю ордер на продажу по курсу %0.8f
#         # """
#         #     % (
#         #         order_spent, pair[0], order_amount, pair[1],
#         #         new_rate_fee,
#         #         STOCK_FEE, (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE), pair[0],
#         #         (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE) - order_spent, pair[0],
#         #         current_rate,
#         #         choosen_rate,
#         #     )
#         #     )
#
#         try:
#             order_amount = order_amount.quantize(Decimal('.00000000'))
#         except InvalidOperation:
#             pass
#
#         try:
#             choosen_rate = choosen_rate.quantize(Decimal('.00000000'))
#         except (InvalidOperation, AttributeError):
#             pass
#
#         if settings.BOT_PRINT_DEBUG:
#             print('quantity: ', order_amount, ', rate: ', choosen_rate)
#             print('sum: ', order_amount*choosen_rate)
#
#         order_res = api.sell_limit(market=market.name, quantity=order_amount, rate=choosen_rate, is_test=is_test)
#         if order_res['uuid']:
#             order = MarketMyOrder.objects.create(
#                 uuid=order_res['uuid'],
#                 market=market,
#                 price=choosen_rate,
#                 amount=order_amount,
#                 spent=order_spent,
#                 from_order=from_order,
#                 type=MarketMyOrder.Type.SELL,
#                 bot=bot,
#                 ticker_data=res_ticker_data
#             )
#             order.create_log(MarketOrderLog.Type.CREATE_ORDER,
#                              ticker_data=res_ticker_data)
#             from_order.close_order()
#             # print(market, "Создан ордер на продажу %s" % order.uuid)
#             print(market, 'Create order SELL')
#             return order
#     return False

#
# # Ф-ция для создания ордера на продажу + процент к покупке
# def create_sell_current(from_order, market, bot=None, is_block_trade=False):
#     global USE_LOG
#     USE_LOG = True
#
#     if bot:
#         is_test = bot.is_test
#     else:
#         is_test = False
#
#     pair = market.name
#     buy_order_q = MarketMyOrder.objects.get(id=from_order.id)
#
#     order_spent, order_amount = buy_order_q.spent, buy_order_q.get_amount_for_sell()
#     # new_rate = (order_spent + order_spent * bot.markup / 100) / order_amount
#     #
#     # # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
#     # new_rate_fee = add_stock_fee(new_rate)
#
#     res_ticker_data = api.get_ticker(market=market.name)
#     if res_ticker_data:
#         ticker_data = convert_ticker_to_decimal(res_ticker_data)
#         # Берем цену, по которой кто-то покупает
#         current_rate = get_price_for_sell(ticker_data)
#
#         # choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee
#         choosen_rate = current_rate
#
#         # print(market, """
#         #     Итого на этот ордер было потрачено %0.8f %s, получено %0.8f %s
#         #     Что бы выйти в плюс, необходимо продать купленную валюту по курсу %0.8f
#         #     Тогда, после вычета комиссии %0.4f останется сумма %0.8f %s
#         #     Итоговая прибыль составит %0.8f %s
#         #     Текущий курс продажи %0.8f
#         #     Создаю ордер на продажу по курсу %0.8f
#         # """
#         #     % (
#         #         order_spent, pair[0], order_amount, pair[1],
#         #         new_rate_fee,
#         #         STOCK_FEE, (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE), pair[0],
#         #         (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE) - order_spent, pair[0],
#         #         current_rate,
#         #         choosen_rate,
#         #     )
#         #     )
#
#         try:
#             order_amount = order_amount.quantize(Decimal('.00000000'))
#         except InvalidOperation:
#             pass
#
#         try:
#             choosen_rate = choosen_rate.quantize(Decimal('.00000000'))
#         except (InvalidOperation, AttributeError):
#             pass
#
#         if settings.BOT_PRINT_DEBUG:
#             print('quantity: ', order_amount, ', rate: ', choosen_rate)
#             print('sum: ', order_amount*choosen_rate)
#
#         new_spent = order_amount * choosen_rate
#         order_res = api.sell_limit(market=market.name, quantity=order_amount, rate=choosen_rate, is_test=is_test)
#         if order_res and order_res['uuid']:
#             order = MarketMyOrder.objects.create(
#                 uuid=order_res['uuid'],
#                 market=market,
#                 price=choosen_rate,
#                 amount=order_amount,
#                 spent=new_spent,
#                 from_order=from_order,
#                 type=MarketMyOrder.Type.SELL,
#                 bot=bot,
#                 ticker_data=res_ticker_data,
#             )
#             order.create_log(MarketOrderLog.Type.CREATE_ORDER,
#                              ticker_data=res_ticker_data)
#             # if is_test:
#             #     order.status = MarketMyOrder.Status.FILLED
#             #     order.save()
#             #     from_order.spent = order.spent + order.spent / 100 * Decimal(0.4)
#             #     from_order.fee = order.spent / 100 * Decimal(0.4)
#             from_order.close_order()
#             # print(market, "Создан ордер на продажу %s" % order.uuid)
#             print(market, 'Create order SELL')
#             if is_block_trade:
#                 market_rank = bot.get_market_rank(market)
#                 if market_rank:
#                     market_rank.block_trade()
#             return order
#     return False


# def check_trailing_resell(order, bot):
#     print('===== check_trailing_sell =====')
#     res_ticker_data = api.get_ticker(market=order.market.name)
#     market_rank = bot.get_market_rank(order.market)
#     print('market_rank', market_rank)
#     if market_rank:
#
#         if res_ticker_data:
#             ticker_data = convert_ticker_to_decimal(res_ticker_data)
#
#             check_price = get_price_for_sell(ticker_data)
#
#             trailing_stop_loss = market_rank.trailing_price - market_rank.trailing_price / 100 * bot.trailing_stop_lost
#             if check_price <= trailing_stop_loss and order.created_at <= timezone.now() - timedelta(seconds=bot.order_life_time):
#                 print('====== trailing stop lost ======')
#                 order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
#                                  ticker_data=res_ticker_data,
#                                  max_price=market_rank.max_price,
#                                  )
#                 # отменяем текущий ордер на продажу и выставляем новый ордер
#                 print('cancel order')
#                 cancel_res = api.cancel(order.uuid, is_test=bot.is_test)
#                 print(cancel_res)
#                 if cancel_res:
#                     order.cancel_order(cancel_type=order.CancelStatus.TRAILING_STOP_LOSS)
#
#                 choosen_rate = ticker_data['Bid'] - Decimal(satoshi_1)
#                 order_amount = order.from_order.get_amount_for_sell()
#                 # order_spent = order.from_order.spent
#                 order_spent = order_amount * choosen_rate
#                 order_res = api.sell_limit(market=order.market.name,
#                                            quantity=order_amount,
#                                            rate=choosen_rate,
#                                            is_test=bot.is_test)
#                 if order_res and order_res['uuid']:
#                     from_order = order.from_order
#                     new_order = MarketMyOrder.objects.create(
#                         uuid=order_res['uuid'],
#                         market=order.market,
#                         price=choosen_rate,
#                         amount=order_amount,
#                         spent=order_spent,
#                         from_order=from_order,
#                         type=MarketMyOrder.Type.SELL,
#                         bot=bot,
#                         ticker_data=res_ticker_data,
#                         is_stop_loss=True,
#                     )
#                     from_order.close_order()
#
#                     print(order.market, 'Create order STOP TRAILING SELL')
#
#                     market_rank = bot.get_market_rank(order.market)
#                     order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
#                                      ticker_data=res_ticker_data,
#                                      max_price=market_rank.max_price)
#                     if market_rank:
#                         market_rank.block_trade()
#
#     return order


# def check_trailing_sell(order, bot):
#     print('===== check_trailing_sell =====')
#     res_ticker_data = api.get_ticker(market=order.market.name)
#     market_rank = bot.get_market_rank(order.market)
#     print('market_rank', market_rank)
#     if market_rank:
#
#         if res_ticker_data:
#             ticker_data = convert_ticker_to_decimal(res_ticker_data)
#
#             check_price = get_price_for_sell(ticker_data)
#             # check_price = add_stock_fee(check_price)
#             print('market_rank.max_price', market_rank.max_price)
#             print('check_price', check_price)
#
#             # если не установлена максимальная цена и достигнут минимальный профит, устанавливаем максимальную цену
#             if not market_rank.max_price:
#                 min_trailing_cost_up = order.get_min_trailing_cost_up()
#                 min_trailing_cost_up = add_stock_fee(min_trailing_cost_up)
#                 print('min_trailing_cost_up')
#                 if min_trailing_cost_up <= check_price:
#                     market_rank.max_price = check_price
#                     market_rank.save()
#                     print('set new max price')
#                     order.create_log(MarketOrderLog.Type.MAX_PRICE_FIXED,
#                                      ticker_data=res_ticker_data,
#                                      max_price=check_price)
#
#             # если цена установлена и новая ставка больше, обновляем максимальную цену
#             elif market_rank.max_price:
#                 if market_rank.max_price < check_price:
#                     market_rank.max_price = check_price
#                     market_rank.save()
#                     print('update max price')
#                     order.create_log(MarketOrderLog.Type.MAX_PRICE_UPDATED,
#                                      ticker_data=res_ticker_data,
#                                      max_price=check_price)
#
#                 else:
#                     trailing_cost_fall = market_rank.max_price - market_rank.max_price / 100 * bot.trailing_cost_fall
#                     if check_price <= trailing_cost_fall:
#                         print('====== trailing cost ======')
#                         order.create_log(MarketOrderLog.Type.TRAILING_FALL,
#                                          ticker_data=res_ticker_data,
#                                          max_price=market_rank.max_price,
#                                          )
#                         return True
#
#             if not market_rank.trailing_price:
#                 market_rank.trailing_price = check_price
#                 market_rank.save()
#                 order.create_log(MarketOrderLog.Type.TRAILING_MAX_PRICE_FIXED,
#                                  ticker_data=res_ticker_data,
#                                  max_price=check_price)
#             elif market_rank.trailing_price:
#                 trailing_stop_loss = market_rank.trailing_price - market_rank.trailing_price / 100 * bot.trailing_stop_lost
#                 if check_price <= trailing_stop_loss:
#                     print('====== trailing stop lost ======')
#                     order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
#                                      ticker_data=res_ticker_data,
#                                      max_price=market_rank.max_price,
#                                      )
#                     return True
#
#                 if market_rank.trailing_price < check_price:
#                     market_rank.trailing_price = check_price
#                     market_rank.save()
#                     print('update trailing price')
#                     order.create_log(MarketOrderLog.Type.TRAILING_MAX_PRICE_UPDATED,
#                                      ticker_data=res_ticker_data,
#                                      max_price=check_price)
#
#     return False


# def check_stop_loss_sell(order, bot):
#     order_info = api.get_order(order, is_test=bot.is_test)
#
#     order.update_info(order_info)
#
#     res_ticker_data = api.get_ticker(market=order.market.name)
#     bot.update_current_price(res_ticker_data, order.market)
#
#     ticker_data = {}
#     if res_ticker_data:
#         ticker_data = convert_ticker_to_decimal(res_ticker_data)
#
#     stop_loss = order.from_order.price - order.from_order.price / 100 * bot.stop_loss
#
#     if ticker_data and order_info:
#         # проверяем, если ордер на продажу SELL и сработал STOP LOSS
#         if order.status == MarketMyOrder.Status.OPEN and order.type == MarketMyOrder.Type.SELL:
#             if 'Bid' in ticker_data and ticker_data['Bid'] and stop_loss >= ticker_data['Bid']:
#                 if order.created_at <= timezone.now() - timedelta(seconds=bot.order_life_time):
#                     print('---------------- STOP LOSS SELL!!!! ------------')
#                     # отменяем текущий ордер на продажу и выставляем новый ордер
#                     print('cancel order')
#                     cancel_res = api.cancel(order.uuid, is_test=bot.is_test)
#                     print(cancel_res)
#                     if cancel_res:
#                         order.cancel_order(cancel_type=order.CancelStatus.STOP_LOSS)
#
#                     choosen_rate = ticker_data['Bid'] - Decimal(satoshi_1)
#                     order_amount = order.from_order.get_amount_for_sell()
#                     # order_spent = order.from_order.spent
#                     order_spent = order_amount * choosen_rate
#                     order_res = api.sell_limit(market=order.market.name,
#                                                quantity=order_amount,
#                                                rate=choosen_rate,
#                                                is_test=bot.is_test)
#                     if order_res['uuid']:
#                         from_order = order.from_order
#                         new_order = MarketMyOrder.objects.create(
#                             uuid=order_res['uuid'],
#                             market=order.market,
#                             price=choosen_rate,
#                             amount=order_amount,
#                             spent=order_spent,
#                             from_order=from_order,
#                             type=MarketMyOrder.Type.SELL,
#                             bot=bot,
#                             ticker_data=res_ticker_data,
#                             is_stop_loss=True,
#                         )
#                         from_order.close_order()
#
#                         print(order.market, 'Create order STOP SELL')
#
#                         market_rank = bot.get_market_rank(order.market)
#                         order.create_log(MarketOrderLog.Type.STOP_LOSS,
#                                          ticker_data=res_ticker_data,
#                                          max_price=market_rank.max_price)
#                         if market_rank:
#                             market_rank.block_trade()
#
#                         return new_order
#
#     return order


# def check_stop_loss_buy(order, bot):
#     print('check_stop_loss_buy')
#
#     order_info = api.get_order(order, is_test=bot.is_test)
#
#     order.update_info(order_info)
#
#     res_ticker_data = api.get_ticker(market=order.market.name)
#     bot.update_current_price(res_ticker_data, order.market)
#
#     ticker_data = {}
#     if res_ticker_data:
#         ticker_data = convert_ticker_to_decimal(res_ticker_data)
#
#     p = order.price
#     s = bot.stop_loss
#     stop_loss = order.price - order.price / 100 * bot.stop_loss
#
#     if ticker_data and order_info:
#         # проверяем, если ордер на продажу BUY и сработал STOP LOSS
#         if order.status == MarketMyOrder.Status.FILLED and order.type == MarketMyOrder.Type.BUY and not order.is_close:
#             if 'Bid' in ticker_data and ticker_data['Bid'] and stop_loss >= ticker_data['Bid']:
#                 print('---------------- STOP LOSS BUY!!!! ------------')
#
#                 choosen_rate = ticker_data['Bid'] - Decimal(satoshi_1)
#                 order_amount = order.get_amount_for_sell()
#                 order_spent = order_amount * choosen_rate
#                 order_res = api.sell_limit(market=order.market.name,
#                                            quantity=order_amount,
#                                            rate=choosen_rate,
#                                            is_test=bot.is_test)
#                 if order_res and order_res['uuid']:
#                     new_order = MarketMyOrder.objects.create(
#                         uuid=order_res['uuid'],
#                         market=order.market,
#                         price=choosen_rate,
#                         amount=order_amount,
#                         spent=order_spent,
#                         from_order=order,
#                         type=MarketMyOrder.Type.SELL,
#                         bot=bot,
#                         ticker_data=res_ticker_data,
#                         is_stop_loss=True,
#                     )
#
#                     print(order.market, 'Create order STOP SELL BUY')
#                     order.close_order()
#
#                     market_rank = bot.get_market_rank(order.market)
#                     order.create_log(MarketOrderLog.Type.STOP_LOSS,
#                                      ticker_data=res_ticker_data,
#                                      max_price=market_rank.max_price)
#                     if market_rank:
#                         market_rank.block_trade()
#
#                     return True
#
#     return False


# def check_order(order, bot):
#     order_info = api.get_order(order, is_test=bot.is_test)
#
#     res_ticker_data = api.get_ticker(market=order.market.name)
#     bot.update_current_price(res_ticker_data, order.market)
#
#     ticker_data = convert_ticker_to_decimal(res_ticker_data)
#     order.update_info(order_info, res_ticker_data)
#
#     if ticker_data and order_info:
#         # sell - ASK
#         # buy - BID
#         random_action = 3
#         # эмуляция торгов
#         # проверяем, если ордер на продажу SELL - если наш ордер <= BID отмечаем как исполненный
#         if order.type == MarketMyOrder.Type.SELL:
#             if 'Bid' in ticker_data and ticker_data['Bid'] and order.price <= ticker_data['Bid']:
#                 random_action = 1
#                 print('---------------- SEL!!!! ------------')
#             else:
#                 print('----------------cant`t SEL ((( ------------')
#                 print('Bid', ticker_data['Bid'])
#                 print('Ask', ticker_data['Ask'])
#                 print('Last', ticker_data['Last'])
#                 print('price', order.price)
#
#         # эмуляция торгов
#         # проверяем, если ордер на покупку BUY -  если наш ордер >= ASK отмечаем как исполненный
#         if order.type == MarketMyOrder.Type.BUY \
#                 and 'Ask' in ticker_data and ticker_data['Ask'] and order.price >= ticker_data['Ask']:
#             random_action = 1
#
#         # random_action = random.randint(1, 3)
#         # random_action = 1
#         if random_action == 1 or (order_info['Closed'] and not order_info['CancelInitiated']):
#             # print('Ордер %s уже выполнен!' % order)
#             order.filled_at = timezone.now()
#             # order.price = order_info['Price']
#             # order.amount = order_info['Quantity']
#             order.spent = order.spent + Decimal(order_info["CommissionPaid"])
#             order.fee = order_info["CommissionPaid"]
#             order.status = MarketMyOrder.Status.FILLED
#             order.save()
#             if order.type == MarketMyOrder.Type.SELL and order.from_order:
#                 from_order = order.from_order
#                 from_order.status = MarketMyOrder.Status.CLOSED
#                 from_order.save()
#
#         elif random_action == 2 or (order_info['Closed'] and order_info['CancelInitiated']):
#             # print(order.market, 'Ордер %s отменен!' % order)
#             # order.price = order_info['Price']
#             # order.order_amount = order_info['Quantity']
#             order.fee = order_info["CommissionPaid"]
#             order.cancelled_at = timezone.now()
#             order.status = MarketMyOrder.Status.CANCELED
#             order.save()
#             # print(order.market, "Ордер %s помечен отмененным в БД" % order)
#         else:
#             # print(order.market, "Ордер %s еще не выполнен" % order)
#             if order_info['QuantityRemaining'] != order_info['Quantity']:
#                 # order.partially_filled = True
#                 order.status = MarketMyOrder.Status.PART_FILLED
#                 order.save()
#
#     return order


# def get_trends(charts_data, bot, check_date=None, market=None):
#     # print('get_trends')
#
#     ta = TechnicalAnalysis(market)
#
#     is_ema = bot.is_ema
#     is_stochastic = bot.is_stochastic
#     is_stochastic_cross = bot.is_stochastic_cross
#     is_stochastic_fast_up = bot.is_stochastic_fast_up
#
#     is_green = bot.is_green
#     is_dodge = bot.is_dodge
#     is_hummer = bot.is_hummer
#     is_sword = bot.is_sword
#     is_simple = bot.is_simple
#     is_fat = bot.is_fat
#
#     is_min_value = bot.is_min_value
#     is_compare_value = bot.is_compare_value
#     is_ratio_open_close = bot.is_ratio_open_close
#     is_sma = bot.is_sma
#
#     is_rsi = bot.is_rsi
#     is_macd = bot.is_macd
#     is_macd_cross_bottom_to_top = bot.is_macd_cross_bottom_to_top
#
#     is_sma_cross_bottom_to_top = bot.is_sma_cross_bottom_to_top
#
#     is_adx = bot.is_adx
#
#     trend_check = {}
#
#     if is_ema:
#         trend_check['ema_cross'] = False
#
#     if is_stochastic:
#         trend_check['stochastic'] = False
#
#     if is_stochastic_cross:
#         trend_check['stochastic_cross'] = False
#     if is_stochastic_fast_up:
#         trend_check['is_stochastic_fast_up'] = False
#
#     if is_green:
#         trend_check['is_green'] = False
#     if is_dodge:
#         trend_check['is_dodge'] = False
#     if is_hummer:
#         trend_check['is_hummer'] = False
#     if is_sword:
#         trend_check['is_sword'] = False
#     if is_simple:
#         trend_check['is_simple'] = False
#     if is_fat:
#         trend_check['is_fat'] = False
#
#     if is_min_value:
#         trend_check['is_min_value'] = False
#     if is_compare_value:
#         trend_check['is_compare_value'] = False
#
#     if is_sma:
#         trend_check['sma'] = False
#     if is_sma_cross_bottom_to_top:
#         trend_check['sma_cross'] = False
#
#     if is_ratio_open_close:
#         trend_check['is_ratio_open_close'] = False
#
#     if is_rsi:
#         trend_check['rsi'] = False
#
#     if is_adx:
#         trend_check['adx'] = False
#
#     if is_macd:
#         trend_check['macd'] = False
#     if is_macd_cross_bottom_to_top:
#         trend_check['macd_cross'] = False
#
#     if not charts_data:
#         return trend_check
#
#     sorted_dates = sorted(charts_data)
#
#     macd, macdsignal, macdhist = talib.MACD(
#         numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
#         fastperiod=bot.macd_fastperiod, slowperiod=bot.macd_slowperiod, signalperiod=bot.macd_signalperiod)
#     # fastperiod=8, slowperiod=17, signalperiod=9)
#     # fastperiod=12, slowperiod=26, signalperiod=9)
#
#     if is_ema:
#         ema_fast = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
#                              timeperiod=bot.ema_fastperiod)
#         ema_slow = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
#                              timeperiod=bot.ema_slowperiod)
#     if is_stochastic or is_stochastic_cross or is_stochastic_fast_up:
#         slowk, slowd = talib.STOCH(
#             numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
#             numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
#             numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
#             fastk_period=bot.stochastic_fastk_period,
#             slowk_period=bot.stochastic_slowk_period, slowk_matype=0,
#             slowd_period=bot.stochastic_slowd_period, slowd_matype=0)
#
#     rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]), timeperiod=bot.rsi_timeperiod)
#
#     if is_sma:
#         sma = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
#                         timeperiod=bot.sma_timeperiod)
#
#     if is_adx:
#         adx = talib.ADX(numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
#                         numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
#                         numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
#                         timeperiod=bot.adx_timeperiod)
#
#     if is_sma_cross_bottom_to_top:
#         sma_fast = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
#                              timeperiod=bot.sma_fastperiod)
#         sma_slow = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
#                              timeperiod=bot.sma_slowperiod)
#
#     if bot.is_ha:
#         charts_data = get_heikin_ashi(charts_data, market)
#
#     for i, d in enumerate(charts_data):
#         charts_data[d]['macd'] = macd[i]
#         charts_data[d]['macdsignal'] = macdsignal[i]
#         charts_data[d]['macdhist'] = macdhist[i]
#
#         if is_sma:
#             charts_data[d]['sma'] = sma[i]
#
#         if is_sma_cross_bottom_to_top:
#             charts_data[d]['sma_fast'] = sma_fast[i]
#             charts_data[d]['sma_slow'] = sma_slow[i]
#
#         if is_ema:
#             charts_data[d]['ema_fast'] = ema_fast[i]
#             charts_data[d]['ema_slow'] = ema_slow[i]
#
#         if is_stochastic or is_stochastic_cross or is_stochastic_fast_up:
#             charts_data[d]['stochastic_fast'] = slowk[i]
#             charts_data[d]['stochastic_slow'] = slowd[i]
#
#         charts_data[d]['rsi'] = rsi[i]
#
#         if is_adx:
#             charts_data[d]['adx'] = adx[i]
#
#     if check_date:
#         print('if check_date', check_date)
#         try:
#             i = sorted_dates.index(check_date)
#             print('i', i-2, i)
#             dates = sorted_dates[i-1: i+1]
#             prev_date = sorted_dates[-(i-1)]
#             pprev_date = sorted_dates[-(i-2)]
#             print('dates', dates)
#         except ValueError:
#             dates = []
#             check_date = None
#             prev_date = None
#             pprev_date = None
#     else:
#         dates = sorted_dates[len(charts_data) - 2:]
#         print('else dates', dates)
#         check_date = sorted_dates[-1]
#         print('check_date', check_date)
#         try:
#             prev_date = sorted_dates[-2]
#             pprev_date = sorted_dates[-3]
#         except IndexError:
#             prev_date = None
#             pprev_date = None
#
#     if settings.BOT_PRINT_DEBUG:
#         print('dates', dates)
#
#     trends = {}
#
#     if is_rsi:
#         trends['rsi'] = {'value': None, 'trend': None, 'dir': None}
#
#     if is_adx:
#         trends['adx'] = {'value': None, 'trend': None, 'dir': None}
#         trends['adx_direction'] = {'value': None, 'trend': None}
#
#     if is_macd:
#         trends['macd'] = {'value': None, 'trend': None}
#     if is_macd_cross_bottom_to_top:
#         trends['macd_cross'] = {'value': None, 'trend': None, 'macd': None, 'macdsignal': None, 'dir': None}
#
#     if is_ema:
#         trends['ema_cross'] = {'value': None, 'trend': None, 'ema_fast': None, 'ema_slow': None, 'dir': None}
#         # trends['ema'] = {'value': None, 'trend': None}
#         # trends['ema_fast'] = {'value': None, 'trend': None}
#         # trends['ema_slow'] = {'value': None, 'trend': None}
#
#     if is_stochastic:
#         trends['stochastic'] = {'value': None, 'trend': None, 'dir': None}
#
#     if is_stochastic_cross:
#         trends['stochastic_cross'] = {'value': None, 'trend': None, 'stochastic_fast': None, 'stochastic_slow': None,
#                                       'dir': None}
#
#     if is_stochastic_fast_up:
#         trends['is_stochastic_fast_up'] = {'value': None, 'trend': None, 'stochastic_fast': None, 'stochastic_slow': None,
#                                       'dir': None}
#
#     if is_green:
#         trends['is_green'] = {'trend': None}
#     if is_dodge:
#         trends['is_dodge'] = {'trend': None}
#     if is_hummer:
#         trends['is_hummer'] = {'trend': None}
#     if is_sword:
#         trends['is_sword'] = {'trend': None}
#     if is_simple:
#         trends['is_simple'] = {'trend': None}
#     if is_fat:
#         trends['is_fat'] = {'trend': None}
#
#     if is_min_value:
#         trends['is_min_value'] = {'trend': None}
#
#     if is_compare_value:
#         trends['is_compare_value'] = {'trend': None}
#
#     if is_sma:
#         trends['is_sma'] = {'trend': None}
#
#     if is_sma_cross_bottom_to_top:
#         trends['sma_cross'] = {'value': None, 'trend': None, 'sma_fast': None, 'sma_slow': None, 'dir': None}
#
#     if is_ratio_open_close:
#         trends['is_ratio_open_close'] = {'trend': None}
#
#     # prev_date = None
#     # pprev_date = None
#
#     # for d in dates:
#     if check_date:
#         d = check_date
#         if is_green:
#             trends['is_green']['trend'] = ta.is_green(charts_data[d])
#         if is_dodge:
#             print('if is_dodge:')
#             if prev_date:
#                 trends['is_dodge']['trend'] = ta.is_dodge(charts_data[prev_date])
#             # trends['is_dodge']['trend'] = ta.is_dodge(charts_data[d])
#             print("trends['is_dodge']['trend'] ", trends['is_dodge']['trend'])
#             # prev_dodge_trend = False
#             # pprev_dodge_trend = False
#             # if prev_date:
#             #     prev_dodge_trend = ta.is_dodge(charts_data[prev_date])
#             # if prev_date:
#             #     pprev_dodge_trend = ta.is_dodge(charts_data[prev_date])
#             # if prev_dodge_trend or pprev_dodge_trend:
#             #     trends['is_dodge']['trend'] = True
#         if is_hummer:
#             trends['is_hummer']['trend'] = ta.is_hummer(charts_data[d])
#         if is_sword:
#             trends['is_sword']['trend'] = ta.is_sword(charts_data[d])
#         if is_simple:
#             trends['is_simple']['trend'] = ta.is_simple(charts_data[d])
#         if is_fat:
#             trends['is_fat']['trend'] = ta.is_fat(charts_data[d])
#
#         if is_min_value:
#             trends['is_min_value']['trend'] = ta.is_min_value(charts_data[d], bot.min_value)
#
#         if prev_date and is_compare_value:
#             trends['is_compare_value']['trend'] = ta.is_compare_value(charts_data[d], charts_data[prev_date])
#
#         if prev_date and is_ratio_open_close:
#             trends['is_ratio_open_close']['trend'] = ta.is_ratio_open_close(charts_data[d],
#                                                                             charts_data[prev_date],
#                                                                             bot.ratio_open_close)
#
#         if is_sma:
#             trends['is_sma']['trend'] = ta.is_sma(charts_data[d])
#
#         if is_stochastic:
#             if bot.stochastic_less and bot.stochastic_more:
#                 if bot.stochastic_more < charts_data[d]['stochastic_fast'] < bot.stochastic_less:
#                     print('******* if date' + str(d) + ' ' + str(bot.stochastic_more) + ' < ' + str(
#                         charts_data[d]['stochastic_fast']) + ' < ' + str(bot.stochastic_less))
#                     trends['stochastic']['trend'] = 'CALL'
#             elif bot.stochastic_more and not bot.stochastic_less:
#                 if bot.stochastic_more < charts_data[d]['stochastic_fast']:
#                     trends['stochastic']['trend'] = 'CALL'
#             elif not bot.stochastic_more and bot.stochastic_less:
#                 if charts_data[d]['stochastic_fast'] < bot.stochastic_less:
#                     trends['stochastic']['trend'] = 'CALL'
#
#             if prev_date and charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
#                 trends['stochastic']['dir'] = 'UP'
#
#             trends['stochastic']['value'] = charts_data[d]['stochastic_fast']
#
#         if is_stochastic_cross:
#             if prev_date:
#                 if ta.is_cross(charts_data[prev_date]['stochastic_fast'], charts_data[prev_date]['stochastic_slow'],
#                                charts_data[d]['stochastic_fast'], charts_data[d]['stochastic_slow']):
#                     # print('+++++++++++++++++++++++++++ stochastic_cross ++++++++++++++++++++++++')
#                     trends['stochastic_cross']['trend'] = 'CALL'
#
#                 if charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
#                     trends['stochastic_cross']['dir'] = 'UP'
#
#             trends['stochastic_cross']['stochastic_fast'] = charts_data[d]['stochastic_fast']
#             trends['stochastic_cross']['stochastic_slow'] = charts_data[d]['stochastic_slow']
#
#         if is_stochastic_fast_up:
#             if prev_date and charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
#                 trends['is_stochastic_fast_up']['dir'] = 'UP'
#
#             trends['is_stochastic_fast_up']['stochastic_fast'] = charts_data[d]['stochastic_fast']
#             trends['is_stochastic_fast_up']['stochastic_slow'] = charts_data[d]['stochastic_slow']
#
#         if is_sma_cross_bottom_to_top:
#             if prev_date:
#                 if ta.is_cross(charts_data[prev_date]['sma_fast'], charts_data[prev_date]['sma_slow'],
#                                charts_data[d]['sma_fast'], charts_data[d]['sma_slow']):
#                     # print('++++++++++++++++++++++++++++++ sma_cross ++++++++++++++++++++++++++')
#                     trends['sma_cross']['trend'] = 'CALL'
#
#                 if charts_data[prev_date]['sma_fast'] < charts_data[d]['sma_fast']:
#                     trends['sma_cross']['dir'] = 'UP'
#
#             trends['sma_cross']['sma_fast'] = charts_data[d]['sma_fast']
#             trends['sma_cross']['sma_slow'] = charts_data[d]['sma_slow']
#
#         if is_rsi:
#             if bot.rsi_less and bot.rsi_more:
#                 if bot.rsi_more < charts_data[d]['rsi'] < bot.rsi_less:
#                     trends['rsi']['trend'] = 'CALL'
#             elif bot.rsi_more and not bot.rsi_less:
#                 if bot.rsi_more < charts_data[d]['rsi']:
#                     trends['rsi']['trend'] = 'CALL'
#             elif not bot.rsi_more and bot.rsi_less:
#                 if charts_data[d]['rsi'] < bot.rsi_less:
#                     trends['rsi']['trend'] = 'CALL'
#
#             if prev_date and charts_data[prev_date]['rsi'] < charts_data[d]['rsi']:
#                 # print('if ', prev_date, ' and ', charts_data[prev_date]['rsi'], ' < ', charts_data[d]['rsi'])
#                 # print(trends)
#                 trends['rsi']['dir'] = 'UP'
#                 # time.sleep(10)
#
#             trends['rsi']['value'] = charts_data[d]['rsi']
#
#         if is_macd:
#             if prev_date:
#                 if charts_data[prev_date]['macd'] < charts_data[d]['macd']:
#                     trends['macd']['trend'] = 'UP'
#                 else:
#                     charts_data[prev_date]['trend'] = 'DOWN'
#             trends['macd']['value'] = charts_data[d]['macd']
#
#         if is_macd_cross_bottom_to_top:
#             try:
#                 if prev_date:
#                     if ta.is_cross(charts_data[prev_date]['macd'], charts_data[prev_date]['macdsignal'],
#                                    charts_data[d]['macd'], charts_data[d]['macdsignal']):
#                         print('++++++++++++++++++++++++++++++ macd_cross ++++++++++++++++++++++++++')
#                         trends['macd_cross']['trend'] = 'CALL'
#
#                     if charts_data[prev_date]['macd'] < charts_data[d]['macd']:
#                         trends['macd_cross']['dir'] = 'UP'
#
#                 trends['macd_cross']['macd'] = charts_data[d]['macd']
#                 trends['macd_cross']['macdsignal'] = charts_data[d]['macdsignal']
#
#             except TypeError:
#                 pass
#
#         if is_ema:
#
#             if prev_date:
#                 if ta.is_cross(charts_data[prev_date]['ema_fast'], charts_data[prev_date]['ema_slow'],
#                                charts_data[d]['ema_fast'], charts_data[d]['ema_slow']):
#                     print('++++++++++++++++++++++++++++++ EMA_cross ++++++++++++++++++++++++++')
#                     trends['ema_cross']['trend'] = 'CALL'
#
#                 if charts_data[prev_date]['ema_fast'] < charts_data[d]['ema_fast']:
#                     trends['ema_cross']['dir'] = 'UP'
#
#             trends['ema_cross']['ema_fast'] = charts_data[d]['ema_fast']
#             trends['ema_cross']['ema_slow'] = charts_data[d]['ema_slow']
#
#         if is_adx:
#             # print('bot.adx_less', bot.adx_less)
#             # print('bot.adx_more', bot.adx_more)
#             # print('adx', charts_data[d]['adx'])
#             trends['adx']['value'] = charts_data[d]['adx']
#             if bot.adx_less and bot.adx_more:
#                 if bot.adx_more < charts_data[d]['adx'] < bot.adx_less:
#                     trends['adx']['trend'] = 'CALL'
#                     # print('if', bot.adx_more, ' < ', charts_data[d]['adx'], ' < ', bot.adx_less)
#                     # time.sleep(3)
#             elif bot.adx_more and not bot.adx_less:
#                 if bot.adx_more < charts_data[d]['adx']:
#                     trends['adx']['trend'] = 'CALL'
#             elif not bot.adx_more and bot.adx_less:
#                 if charts_data[d]['adx'] < bot.adx_less:
#                     trends['adx']['trend'] = 'CALL'
#
#             # if not trends['adx_direction']['value']:
#             #     trends['adx_direction']['value'] = charts_data[d]['adx']
#             # else:
#             if prev_date and charts_data[prev_date]['adx'] < charts_data[d]['adx']:
#                 trends['adx_direction']['trend'] = 'UP'
#             else:
#                 trends['adx_direction']['trend'] = 'DOWN'
#             trends['adx_direction']['value'] = charts_data[d]['adx']
#
#         # print(d)
#         # print('rsi', charts_data[d]['rsi'])
#         # print('macd', charts_data[d]['macd'])
#         # print('ema_fast', charts_data[d]['ema_fast'])
#         # print('ema_slow', charts_data[d]['ema_slow'])
#         d = check_date
#
#         pprev_date = prev_date
#         prev_date = d
#
#     print('trends (1155) ', trends)
#
#     if is_rsi and trends['rsi']['trend'] == 'CALL' and trends['rsi']['dir'] == 'UP':
#         trend_check['rsi'] = True
#
#     # if trends['rsi']['trend'] == 'UP' and trends['rsi']['value'] >= 50:
#     #     trend_check['rsi'] = True
#
#     # if is_ema and trends['ema']['value'] and trends['ema_fast']['trend'] == 'UP':
#     #     trend_check['ema'] = True
#     #     print('---- EMA TRUE ----')
#
#     if is_stochastic_cross and trends['stochastic_cross']['trend'] == 'CALL' and trends['stochastic_cross']['dir'] == 'UP':
#         print('+++++++++++++++++++++++++++++++++++++++ UP stochastic CROSS ++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['stochastic_cross'] = True
#
#     if is_stochastic_fast_up and trends['is_stochastic_fast_up']['dir'] == 'UP':
#         print('+++++++++++++++++++++++++++++++++++++++ UP stochastic Fast ++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['is_stochastic_fast_up'] = True
#
#     if is_stochastic and trends['stochastic']['trend'] == 'CALL' and trends['stochastic']['dir'] == 'UP':
#         print('+++++++++++++++++++++++++++++++++++++++ stochastic value ++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['stochastic'] = True
#
#     if is_ema and trends['ema_cross']['trend'] == 'CALL' and trends['ema_cross']['dir'] == 'UP':
#         print('+++++++++++++++++++++++++++++++++++++++ UP EMA CROSS +++++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['ema_cross'] = True
#
#     if is_macd_cross_bottom_to_top and trends['macd_cross']['trend'] == 'CALL' and trends['macd_cross']['dir'] == 'UP':
#     # if is_macd_cross_bottom_to_top and trends['macd_cross']['trend'] == 'CALL':
#         print('+++++++++++++++++++++++++++++++++++++++ UP MACD CROSS +++++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['macd_cross'] = True
#
#     if is_macd and trends['macd']['trend'] == 'UP':
#         trend_check['macd'] = True
#
#     if is_sma_cross_bottom_to_top and trends['sma_cross']['trend'] == 'CALL' and trends['sma_cross']['dir'] == 'UP':
#         print('+++++++++++++++++++++++++++++++++++++++ UP SMA CROSS +++++++++++++++++++++++++++++++++++++++++++++')
#         trend_check['sma_cross'] = True
#
#     if is_green and trends['is_green']['trend']:
#         trend_check['is_green'] = True
#     if is_dodge and trends['is_dodge']['trend']:
#         trend_check['is_dodge'] = True
#     if is_hummer and trends['is_hummer']['trend']:
#         trend_check['is_hummer'] = True
#     if is_sword and trends['is_sword']['trend']:
#         trend_check['is_sword'] = True
#     if is_simple and trends['is_simple']['trend']:
#         trend_check['is_simple'] = True
#     if is_fat and trends['is_fat']['trend']:
#         trend_check['is_fat'] = True
#
#     if is_min_value and trends['is_min_value']['trend']:
#         trend_check['is_min_value'] = True
#     if is_compare_value and trends['is_compare_value']['trend']:
#         trend_check['is_compare_value'] = True
#     if is_sma and trends['is_sma']['trend']:
#         trend_check['sma'] = True
#     if is_ratio_open_close and trends['is_ratio_open_close']['trend']:
#         trend_check['is_ratio_open_close'] = True
#
#     if is_adx and trends['adx_direction']['trend'] == 'UP' and trends['adx']['trend'] == 'CALL':
#         trend_check['adx'] = True
#     # print('trend_check (1221) ', trend_check)
#     return trend_check


# def check_trend_buy(market, bot, tick_intervals_charts_data=None, check_date=None):
#     """
#     Индикаторная стратегия на основе EMA, MACD и RSI.
#
#     Компоненты:
#         EMA: 7 и 26
#         MACD: параметры по умолчанию (12, 26, 9)
#         RSI: 14
#
#     Call - Покупка:
#         EMA 7 пересекает EMA 26 снизу вверх
#         MACD направлен вверх
#         RSI больше 50
#
#     Put - Продажа:
#         EMA 7 пересекает EMA 26 сверху вниз
#         MACD направлен вниз
#         RSI меньше 50
#     """
#
#     trend_check = {}
#     tick_intervals = [t.value for t in bot.tick_intervals.all()]
#
#     if tick_intervals_charts_data:
#         for ticker_interval, charts_data in tick_intervals_charts_data.items():
#             trend_check[ticker_interval] = get_trends(charts_data, bot, check_date, market)
#     else:
#         for ticker_interval in tick_intervals:
#             if ticker_interval == TICKINTERVAL_FIFTEENMIN:
#                 charts_data = get_chart_data(market, TICKINTERVAL_FIVEMIN)
#                 charts_data = convert_ticker(charts_data, round_to=15)
#             else:
#                 charts_data = get_chart_data(market, ticker_interval)
#             trend_check[ticker_interval] = get_trends(charts_data, bot, market=market)
#
#     global_trend = True
#     for i, data in trend_check.items():
#         for k, v in data.items():
#             if not v:
#                 global_trend = False
#
#     if global_trend:
#         print('---------------- OK!!!! Can BUY!!! --------')
#
#     print('trend_check ', trend_check)
#     return global_trend


# def check_trend_sell(market, bot, tick_intervals_charts_data=None, check_date=None):
#
#     global_trend = True
#
#     trend_check = {}
#     tick_intervals = [t.value for t in bot.tick_intervals.all()]
#
#     if tick_intervals_charts_data:
#         for ticker_interval, charts_data in tick_intervals_charts_data.items():
#             trend_check[ticker_interval] = get_trends_sell(charts_data, bot, check_date, market)
#     else:
#         for ticker_interval in tick_intervals:
#             if ticker_interval == TICKINTERVAL_FIFTEENMIN:
#                 charts_data = get_chart_data(market, TICKINTERVAL_FIVEMIN)
#                 charts_data = convert_ticker(charts_data, round_to=15)
#             else:
#                 charts_data = get_chart_data(market, ticker_interval)
#             trend_check[ticker_interval] = get_trends_sell(charts_data, bot, market=market)
#     print('trend_check sell', trend_check)
#     for i, data in trend_check.items():
#         for k, v in data.items():
#             if not v:
#                 global_trend = False
#
#     return global_trend


# def get_trends_sell(charts_data, bot, check_date=None, market=None):
#     print('get_trends_sell')
#
#     ta = TechnicalAnalysis(market)
#
#     is_red = True
#
#     trend_check = {}
#
#     if is_red:
#         trend_check['is_red'] = False
#
#     if not charts_data:
#         return trend_check
#
#     sorted_dates = sorted(charts_data)
#
#     macd, macdsignal, macdhist = talib.MACD(
#         numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
#         fastperiod=bot.macd_fastperiod, slowperiod=bot.macd_slowperiod, signalperiod=bot.macd_signalperiod)
#     # fastperiod=8, slowperiod=17, signalperiod=9)
#     # fastperiod=12, slowperiod=26, signalperiod=9)
#
#     rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]), timeperiod=bot.rsi_timeperiod)
#
#     if bot.is_ha:
#         charts_data = get_heikin_ashi(charts_data, market)
#
#     for i, d in enumerate(charts_data):
#         charts_data[d]['macd'] = macd[i]
#         charts_data[d]['macdsignal'] = macdsignal[i]
#         charts_data[d]['macdhist'] = macdhist[i]
#
#         charts_data[d]['rsi'] = rsi[i]
#
#     if check_date:
#         print('if check_date', check_date)
#         try:
#             i = sorted_dates.index(check_date)
#             print('i', i - 2, i)
#             dates = sorted_dates[i - 1: i + 1]
#             prev_date = sorted_dates[-(i - 1)]
#             print('dates', dates)
#         except ValueError:
#             dates = []
#             check_date = None
#             prev_date = None
#     else:
#         dates = sorted_dates[len(charts_data) - 2:]
#         print('else dates', dates)
#         check_date = sorted_dates[-1]
#         print('check_date', check_date)
#         try:
#             prev_date = sorted_dates[-2]
#         except IndexError:
#             prev_date = None
#
#     if settings.BOT_PRINT_DEBUG:
#         print('dates', dates)
#
#     trends = {}
#
#     if is_red:
#         trends['is_red'] = {'trend': None}
#
#     if check_date:
#         d = check_date
#         # if is_red and ta.is_red(charts_data[d]) and ta.is_red(charts_data[prev_date]):
#         if is_red and ta.is_red(charts_data[d]):
#             print('+++++++++++++++++++++++++++++++++++++++ IS RED ++++++++++++++++++++++++++++++++++++++++++')
#             trends['is_red']['trend'] = True
#
#     if is_red and trends['is_red']['trend']:
#         trend_check['is_red'] = True
#
#     print('trend_check (1221) ', trend_check)
#     return trend_check
