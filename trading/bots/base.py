from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal, InvalidOperation, getcontext
from typing import Optional, Any, Union

import numpy
import talib

from django.conf import settings
from django.utils import timezone

from trading.config import TICKINTERVAL_FIVEMIN, TICKINTERVAL_FIFTEENMIN
from trading.lib import (
    convert_ticker_to_decimal, convert_date, add_stock_fee, convert_ticker
)
from trading.lib import print_debug
from trading.models import ExchangeCurrencyStatistic, MarketMyOrder, MarketOrderLog, HistoryBalance
from trading.ta import TechnicalAnalysis

# Если нет нужных пакетов - читаем тут: https://bablofil.ru/python-indicators/

getcontext().prec = 8


class BotBase:

    satoshi_1 = Decimal(0.00000001)
    # stock_fee = Decimal(0.0025)         # Какую комиссию берет биржа
    stock_fee = Decimal(0.0075)         # Какую комиссию берет биржа - Binance в BNB 0,0075%

    bot = None
    is_test = True
    market = None
    market_rank = None
    market_name = None

    res_ticker_data = None
    ticker_data = None

    exchange = 'bittrex'

    def __init__(self, bot, market):
        self.bot = bot
        self.is_test = self.bot.is_test
        self.market = market
        self.market_rank = self.bot.get_market_rank(self.market)
        self.exchange = bot.exchange.code
        self.market_name = market.get_market_name(self.exchange)
        self.api = self.bot.get_api()
        self.ta = TechnicalAnalysis(self.market)

    def fix_current_balance(self) -> HistoryBalance:
        """Фиксируем текущий баланс валют на бирже"""

        available_balance_btc = self.api.get_currency_balance('BTC')
        available_balance_bnb = self.api.get_currency_balance('BNB')
        available_balance_usdt = self.api.get_currency_balance('USDT')
        hb = HistoryBalance.objects.create(
            btc=available_balance_btc,
            bnb=available_balance_bnb,
            usdt=available_balance_usdt,
        )
        return hb

    def get_heikin_ashi(self, chart_data):

        ha_data = OrderedDict()
        candle_previous = None
        ha = None
        for dt_obj, candle in chart_data.items():
            ha = self.ta.heikin_ashi(candle, candle_previous, ha)
            ha_data[dt_obj] = ha
            candle_previous = candle

        return ha_data

    def get_tickers(self):
        print('BotBase get_tickers')
        # if not self.res_ticker_data:
        self.res_ticker_data = self.api.get_ticker(market=self.market_name)
        self.bot.update_current_price(self.res_ticker_data, self.market)
        self.ticker_data = convert_ticker_to_decimal(self.res_ticker_data)

    def get_chart_data(self, tick_interval=TICKINTERVAL_FIVEMIN, hours=None, ):
        # Получаем с биржи данные, необходимые для построения индикаторов
        print('get_chart_data')
        chart_data = OrderedDict()

        # Получаем готовые данные свечей
        res = self.api.get_ticks(self.market_name, tick_interval)
        # print('# Получаем готовые данные свечей')
        if res:
            for item in res:
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

        # Добираем недостающее
        # print('# Добираем недостающее')
        # TODO: надо смотреть оставлять этот функционал или нет
        # res = self.api.get_market_history(self.market_name)
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

    def create_buy_price(self, price, amount, kind=MarketMyOrder.Kind.MAIN, from_order=None):
        """создаем ордер на покупку"""

        order_res = self.api.buy_limit(
            self.market_name, quantity=amount, rate=price, is_test=self.is_test
        )

        order_uuid = self.api.get_uuid_order(order_res)
        ext_id = self.api.get_ext_id_order(order_res)

        if order_uuid:
            order = MarketMyOrder.objects.create(uuid=order_uuid,
                                                 ext_id=ext_id,
                                                 market=self.market,
                                                 price=price,
                                                 amount=amount,
                                                 spent=self.bot.max_spend,
                                                 bot=self.bot,
                                                 ticker_data=self.res_ticker_data,
                                                 is_test=self.is_test,
                                                 from_order=from_order,
                                                 kind=kind,
                                                 )

            order.create_log(MarketOrderLog.Type.CREATE_ORDER, ticker_data=self.res_ticker_data)

            print(self.market, 'Create order BUY')
            self.market_rank.clear_max_price()
            return order

        return False

    def create_buy(self):
        """Создаем оредер на покупку"""

        # print(self.market, 'Получаем текущие курсы')
        # Получаем публичные данные тикера

        self.get_tickers()

        if self.res_ticker_data:
            # Берем цену, по которой кто-то продает - стоимость комиссии заложим в цену продажи
            # current_rate = Decimal(ticker_data['Ask'])
            if self.ticker_data['Bid']:
                current_rate = self.get_price_for_buy()
                # can_buy = self.bot.max_spend / current_rate
                can_buy = self.bot.average_safety_start_order_amount / current_rate
                # TODO: проверять минимально возможную покупку и сигнализировать, если пытаемся купить меньше

                pair = self.market_name
                # print(self.market, """
                #     Текущая цена - %0.8f
                #     На сумму %0.8f %s можно купить %0.8f %s
                #     Создаю ордер на покупку
                #     """ % (current_rate, CAN_SPEND, pair[0], can_buy, pair[1])
                #     )

                try:
                    current_rate = current_rate.quantize(Decimal('.00000000'))
                except InvalidOperation:
                    pass

                try:
                    can_buy = can_buy.quantize(Decimal('.00000000'))
                except InvalidOperation:
                    pass

                if settings.BOT_PRINT_DEBUG:
                    print('*quantity: ', can_buy, ', rate: ', current_rate)
                    print('sum: ', can_buy * current_rate)

                current_rate, can_buy = self.api.check_price(self.market_name, current_rate, can_buy)

                # проверяем доступный баланс
                print('################## проверяем доступный баланс')
                base_currency = self.market.base_currency.name
                market_currency = self.market.market_currency.name
                available_balance = self.api.get_currency_balance(base_currency)
                available_balance_market = self.api.get_currency_balance(market_currency)

                if settings.BOT_PRINT_DEBUG:
                    print('-quantity: ', can_buy, ', rate: ', current_rate)
                    print('sum: ', Decimal(can_buy) * Decimal(current_rate))

                # если денег не достаточно ордер не создаем
                # if available_balance < Decimal(current_rate):
                if available_balance < Decimal(can_buy) * Decimal(current_rate):
                    print('Не достаточно средств для открытия ордера')
                    raise Exception('Не достаточно средств для открытия ордера')
                    # return False

                # фиксируем историю баланса
                hb = self.fix_current_balance()

                order_res = self.api.buy_limit(
                    self.market_name,
                    quantity=can_buy,
                    rate=current_rate,
                    is_test=self.is_test
                )
                if settings.BOT_PRINT_DEBUG:
                    print(self.market_name, order_res)
                order_uuid = self.api.get_uuid_order(order_res)
                # ext_id = self.api.get_ext_id_order(order_res)
                ext_id = self.api.get_uuid_order(order_res)
                if order_res and (order_uuid or ext_id):
                    print('if order_res and (order_uuid or ext_id):')
                    order = MarketMyOrder.objects.create(uuid=order_uuid,
                                                         ext_id=ext_id,
                                                         market=self.market,
                                                         price=current_rate,
                                                         amount=can_buy,
                                                         spent=self.bot.max_spend,
                                                         bot=self.bot,
                                                         ticker_data=self.res_ticker_data,
                                                         is_test=self.is_test
                                                         )

                    order.create_log(MarketOrderLog.Type.CREATE_ORDER, ticker_data=self.res_ticker_data)
                    # фиксируем в истории баланса ордер перед покупкой которого была фиксация
                    hb.order = order
                    hb.save()
                    # if is_test:
                    #     order.status = MarketMyOrder.Status.FILLED
                    #     order.save()
                    print(self.market, 'Create order BUY', order)
                    self.market_rank.clear_max_price()
                    # TODO: необходимо проверять есть ли ордер на продажу,
                    #  и если выставлять сразу на продажу с учетом страховочных ордеров

                    return order

        return False

    # @staticmethod
    # def get_average_price(total_spend, orders_buy_count):
    #     """Получаем среднюю цену для продажи с учетом страховочных ордеров"""
    #     return Decimal(total_spend / orders_buy_count).quantize(Decimal('.00000000'))

    def create_sell(self, from_order) -> Optional[MarketMyOrder]:
        """создание ордера на продажу + процент к покупке"""

        pair = self.market_name
        # buy_order_q = MarketMyOrder.objects.get(id=from_order.id)
        buy_order_q = from_order

        order_amount, orders_buy_count, sum_prices = buy_order_q.get_amount_for_sell()

        order_spent = buy_order_q.spent
        # получаем цену для продажу с учетом страховочных ордеров
        new_rate = (order_spent + order_spent * self.bot.markup / 100) / order_amount

        # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
        new_rate_fee = self.add_stock_fee(new_rate, orders_buy_count)

        self.get_tickers()

        if self.res_ticker_data:
            # Берем цену, по которой кто-то покупает
            # current_rate = ticker_data['Bid']
            current_rate = self.get_price_for_sell()

            # делаем сверку с текущей ценой
            choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee

            # print(market, """
            #     Итого на этот ордер было потрачено %0.8f %s, получено %0.8f %s
            #     Что бы выйти в плюс, необходимо продать купленную валюту по курсу %0.8f
            #     Тогда, после вычета комиссии %0.4f останется сумма %0.8f %s
            #     Итоговая прибыль составит %0.8f %s
            #     Текущий курс продажи %0.8f
            #     Создаю ордер на продажу по курсу %0.8f
            # """
            #     % (
            #         order_spent, pair[0], order_amount, pair[1],
            #         new_rate_fee,
            #         STOCK_FEE, (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE), pair[0],
            #         (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE) - order_spent, pair[0],
            #         current_rate,
            #         choosen_rate,
            #     )
            #     )

            try:
                order_amount = order_amount.quantize(Decimal('.00000000'))
            except InvalidOperation:
                pass

            try:
                choosen_rate = choosen_rate.quantize(Decimal('.00000000'))
            except (InvalidOperation, AttributeError):
                pass

            if settings.BOT_PRINT_DEBUG:
                print('-2 quantity: ', order_amount, ', rate: ', choosen_rate)
                print('sum: ', order_amount * choosen_rate)

            base_currency = self.market.base_currency.name
            market_currency = self.market.market_currency.name
            available_balance = self.api.get_currency_balance(base_currency)

            order_res = self.api.sell_limit(self.market_name, quantity=order_amount, rate=choosen_rate, is_test=self.is_test)
            order_uuid = self.api.get_uuid_order(order_res)
            if order_uuid:
                order = MarketMyOrder.objects.create(
                    uuid=order_uuid,
                    market=self.market,
                    price=choosen_rate,
                    amount=order_amount,
                    spent=order_spent,
                    from_order=from_order,
                    type=MarketMyOrder.Type.SELL,
                    bot=self.bot,
                    ticker_data=self.res_ticker_data
                )
                order.create_log(MarketOrderLog.Type.CREATE_ORDER,
                                 ticker_data=self.res_ticker_data)
                from_order.close_order()
                # print(market, "Создан ордер на продажу %s" % order.uuid)
                print(self.market, 'Create order SELL')
                return order
        return False

    # Ф-ция для создания ордера на продажу + процент к покупке
    def create_sell_current(self, from_order, is_block_trade=False):

        pair = self.market_name
        buy_order_q = MarketMyOrder.objects.get(id=from_order.id)

        order_spent = buy_order_q.spent
        order_amount, order_buy_count, sum_prices = buy_order_q.get_amount_for_sell()
        # new_rate = (order_spent + order_spent * self.bot.markup / 100) / order_amount
        #
        # # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
        # new_rate_fee = add_stock_fee(new_rate)

        self.get_tickers()

        if self.res_ticker_data:
            # Берем цену, по которой кто-то покупает
            current_rate = self.get_price_for_sell()

            # choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee
            choosen_rate = current_rate

            try:
                order_amount = order_amount.quantize(Decimal('.00000000'))
            except InvalidOperation:
                pass

            try:
                choosen_rate = choosen_rate.quantize(Decimal('.00000000'))
            except (InvalidOperation, AttributeError):
                pass

            if settings.BOT_PRINT_DEBUG:
                print('-3 quantity: ', order_amount, ', rate: ', choosen_rate)
                print('sum: ', order_amount * choosen_rate)

            new_spent = order_amount * choosen_rate
            order = self.place_order(order_amount, choosen_rate, new_spent, from_order)
            if order:
                # if is_test:
                #     order.status = MarketMyOrder.Status.FILLED
                #     order.save()
                #     from_order.spent = order.spent + order.spent / 100 * Decimal(0.4)
                #     from_order.fee = order.spent / 100 * Decimal(0.4)
                from_order.close_order()
                # print(market, "Создан ордер на продажу %s" % order.uuid)
                print(self.market, 'Create order SELL')
                if is_block_trade and self.market_rank:
                    self.market_rank.block_trade()
                return order
        return False

    def place_order(self, order_amount, rate, spent, from_order):
        """Размещаем ордер на бирже"""
        order_res = self.api.sell_limit(
            self.market_name,
            quantity=order_amount,
            rate=rate,
            is_test=self.is_test
        )
        order_uuid = self.api.get_uuid_order(order_res)
        if order_uuid:
            order = MarketMyOrder.objects.create(
                uuid=order_uuid,
                market=self.market,
                price=rate,
                amount=order_amount,
                spent=spent,
                from_order=from_order,
                type=MarketMyOrder.Type.SELL,
                bot=self.bot,
                ticker_data=self.res_ticker_data,
            )
            if self.is_test:
                # во время теста считаем, что ордер сразу исполняется
                order.status = MarketMyOrder.Status.FILLED
                order.save()
            order.create_log(MarketOrderLog.Type.CREATE_ORDER,
                             ticker_data=self.res_ticker_data)

            return order
        return None

    def check_trailing_resell(self, order: MarketMyOrder):
        print('===== check_trailing_sell =====')

        if self.market_rank:

            self.get_tickers()

            if self.res_ticker_data:

                check_price = self.get_price_for_sell()

                trailing_stop_loss = self.market_rank.trailing_price - self.market_rank.trailing_price / 100 * self.bot.trailing_stop_lost
                if check_price <= trailing_stop_loss and self.check_cancel_order(order):
                    print('====== trailing stop lost ======')
                    order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
                                     ticker_data=self.res_ticker_data,
                                     max_price=self.market_rank.max_price,
                                     )
                    # отменяем текущий ордер на продажу и выставляем новый ордер
                    self.cancel_order(order, cancel_type=order.CancelStatus.TRAILING_STOP_LOSS)

                    choosen_rate = self.ticker_data['Bid'] - Decimal(self.satoshi_1)
                    order_amount, orders_buy_count, sum_prices = order.get_amount_for_sell()
                    # order_spent = order.from_order.spent
                    order_spent = order_amount * choosen_rate
                    order_res = self.api.sell_limit(market_name=order.market.get_market_name(self.exchange),
                                                    quantity=order_amount,
                                                    rate=choosen_rate,
                                                    is_test=self.is_test)

                    order_uuid = self.api.get_uuid_order(order_res)
                    if order_uuid:
                        from_order = order.from_order
                        new_order = MarketMyOrder.objects.create(
                            uuid=order_uuid,
                            market=order.market,
                            price=choosen_rate,
                            amount=order_amount,
                            spent=order_spent,
                            from_order=from_order,
                            type=MarketMyOrder.Type.SELL,
                            bot=self.bot,
                            ticker_data=self.res_ticker_data,
                            is_stop_loss=True,
                        )
                        from_order.close_order()

                        print(order.market, 'Create order STOP TRAILING SELL')

                        order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
                                         ticker_data=self.res_ticker_data,
                                         max_price=self.market_rank.max_price)
                        if self.market_rank:
                            self.market_rank.block_trade()

        return order

    def add_stock_fee(self, rate):
        """Добавляем комиссию"""
        new_rate = rate + (rate * self.stock_fee * 2)
        new_rate = new_rate.quantize(Decimal('.00000000'))
        return new_rate

    def add_stock_fee_new_test(self, rate, orders_buy_count=1):
        # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
        new_rate = rate + (rate * self.stock_fee * (orders_buy_count + 1))
        return new_rate

    def check_cancel_order(self, order):
        """проверяем надо ли отменять ордер по времени"""
        if order.kind in [order.Kind.MAIN] \
                and order.created_at <= timezone.now() - timedelta(seconds=self.bot.order_life_time):
            return True
        # попробуем увеличить время жизни страховочных оредров
        # if order.kind in [order.Kind.SAFETY] \
        #         and order.created_at <= timezone.now() - timedelta(seconds=self.bot.order_life_time*3):
        #     return True
        return False

    def check_trailing_sell(self, order):
        print('===== check_trailing_sell =====')

        if self.market_rank:

            self.get_tickers()

            if self.res_ticker_data:

                check_price = self.get_price_for_sell()
                # check_price = add_stock_fee(check_price)
                print('market_rank.max_price', self.market_rank.max_price)
                print('check_price', check_price)

                # если не установлена максимальная цена и достигнут минимальный профит, устанавливаем максимальную цену
                if not self.market_rank.max_price:
                    min_trailing_cost_up = order.get_min_trailing_cost_up()
                    min_trailing_cost_up = add_stock_fee(min_trailing_cost_up)
                    print('min_trailing_cost_up')
                    if min_trailing_cost_up <= check_price:
                        self.market_rank.max_price = check_price
                        self.market_rank.save()
                        print('set new max price')
                        order.create_log(MarketOrderLog.Type.MAX_PRICE_FIXED,
                                         ticker_data=self.res_ticker_data,
                                         max_price=check_price)

                # если цена установлена и новая ставка больше, обновляем максимальную цену
                elif self.market_rank.max_price:
                    if self.market_rank.max_price < check_price:
                        self.market_rank.max_price = check_price
                        self.market_rank.save()
                        print('update max price')
                        order.create_log(MarketOrderLog.Type.MAX_PRICE_UPDATED,
                                         ticker_data=self.res_ticker_data,
                                         max_price=check_price)

                    else:
                        trailing_cost_fall = self.market_rank.max_price - self.market_rank.max_price / 100 * self.bot.trailing_cost_fall
                        if check_price <= trailing_cost_fall:
                            print('====== trailing cost ======')
                            order.create_log(MarketOrderLog.Type.TRAILING_FALL,
                                             ticker_data=self.res_ticker_data,
                                             max_price=self.market_rank.max_price,
                                             )
                            return True

                if not self.market_rank.trailing_price:
                    self.market_rank.trailing_price = check_price
                    self.market_rank.save()
                    order.create_log(MarketOrderLog.Type.TRAILING_MAX_PRICE_FIXED,
                                     ticker_data=self.res_ticker_data,
                                     max_price=check_price)
                elif self.market_rank.trailing_price:
                    trailing_stop_loss = self.market_rank.trailing_price - self.market_rank.trailing_price / 100 * self.bot.trailing_stop_lost
                    if check_price <= trailing_stop_loss:
                        print('====== trailing stop lost ======')
                        order.create_log(MarketOrderLog.Type.TRAILING_STOP_LOSS,
                                         ticker_data=self.res_ticker_data,
                                         max_price=self.market_rank.max_price,
                                         )
                        return True

                    if self.market_rank.trailing_price < check_price:
                        self.market_rank.trailing_price = check_price
                        self.market_rank.save()
                        print('update trailing price')
                        order.create_log(MarketOrderLog.Type.TRAILING_MAX_PRICE_UPDATED,
                                         ticker_data=self.res_ticker_data,
                                         max_price=check_price)

        return False

    def cancel_order(self, order, cancel_type=None):
        """Отменяем выставленный ордер"""
        print('cancel order')
        market_name = order.market.get_market_name(order.bot.exchange.code)
        cancel_res = self.api.cancel(order.uuid, market_name=market_name, is_test=self.is_test)
        print(cancel_res)
        if cancel_res:
            order.cancel_order(cancel_type=cancel_type)

    def check_stop_loss_sell(self, order):
        order_info = self.api.get_order(order, is_test=self.is_test)

        order.update_info(order_info)

        self.bot.update_current_price(self.res_ticker_data, order.market)

        ticker_data = {}

        stop_loss = order.from_order.price - order.from_order.price / 100 * self.bot.stop_loss

        if ticker_data and order_info:
            # проверяем, если ордер на продажу SELL и сработал STOP LOSS
            if order.status == MarketMyOrder.Status.OPEN and order.type == MarketMyOrder.Type.SELL:
                if 'Bid' in ticker_data and ticker_data['Bid'] and stop_loss >= ticker_data['Bid']:
                    if self.check_cancel_order(order):
                        print('---------------- STOP LOSS SELL!!!! ------------')
                        # отменяем текущий ордер на продажу и выставляем новый ордер
                        self.cancel_order(order, cancel_type=order.CancelStatus.STOP_LOSS)

                        choosen_rate = ticker_data['Bid'] - Decimal(self.satoshi_1)
                        order_amount, orders_buy_count, sum_prices = order.get_amount_for_sell()
                        # order_spent = order.from_order.spent
                        order_spent = order_amount * choosen_rate
                        order_res = self.api.sell_limit(market_name=order.market.get_market_name(self.exchange),
                                                        quantity=order_amount,
                                                        rate=choosen_rate,
                                                        is_test=self.is_test)
                        order_uuid = self.api.get_uuid_order(order_res)
                        if order_uuid:
                            from_order = order.from_order
                            new_order = MarketMyOrder.objects.create(
                                uuid=order_uuid,
                                market=order.market,
                                price=choosen_rate,
                                amount=order_amount,
                                spent=order_spent,
                                from_order=from_order,
                                type=MarketMyOrder.Type.SELL,
                                bot=self.bot,
                                ticker_data=self.res_ticker_data,
                                is_stop_loss=True,
                            )
                            from_order.close_order()

                            print(order.market, 'Create order STOP SELL')

                            order.create_log(MarketOrderLog.Type.STOP_LOSS,
                                             ticker_data=self.res_ticker_data,
                                             max_price=self.market_rank.max_price)
                            if self.market_rank:
                                self.market_rank.block_trade()

                            return new_order

        return order

    def check_stop_loss_buy(self, order):
        print('check_stop_loss_buy')

        order_info = self.api.get_order(order, is_test=self.is_test)

        order.update_info(order_info)

        self.bot.update_current_price(self.res_ticker_data, order.market)

        p = order.price
        s = self.bot.stop_loss
        stop_loss = order.price - order.price / 100 * self.bot.stop_loss

        if self.ticker_data and order_info:
            # проверяем, если ордер на продажу BUY и сработал STOP LOSS
            if order.status == MarketMyOrder.Status.FILLED and order.type == MarketMyOrder.Type.BUY and not order.is_close:
                if 'Bid' in self.ticker_data and self.ticker_data['Bid'] and stop_loss >= self.ticker_data['Bid']:
                    print('---------------- STOP LOSS BUY!!!! ------------')

                    choosen_rate = self.ticker_data['Bid'] - Decimal(self.satoshi_1)
                    order_amount, orders_buy_count, sum_prices = order.get_amount_for_sell()
                    order_spent = order_amount * choosen_rate
                    order_res = self.api.sell_limit(market_name=order.market.get_market_name(self.exchange),
                                                    quantity=order_amount,
                                                    rate=choosen_rate,
                                                    is_test=self.is_test)
                    order_uuid = self.api.get_uuid_order(order_res)
                    if order_uuid:
                        new_order = MarketMyOrder.objects.create(
                            uuid=order_uuid,
                            market=order.market,
                            price=choosen_rate,
                            amount=order_amount,
                            spent=order_spent,
                            from_order=order,
                            type=MarketMyOrder.Type.SELL,
                            bot=self.bot,
                            ticker_data=self.res_ticker_data,
                            is_stop_loss=True,
                        )

                        print(order.market, 'Create order STOP SELL BUY')
                        order.close_order()

                        order.create_log(MarketOrderLog.Type.STOP_LOSS,
                                         ticker_data=self.res_ticker_data,
                                         max_price=self.market_rank.max_price)
                        if self.market_rank:
                            self.market_rank.block_trade()

                        return True

        return False

    def check_order(self, order, count_active_orders=0):
        # print("Проверяем состояние ордера %s" % order.id)
        if order.uuid:
            if order.status in [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]:
                order = self.check_order_status(order)

            self.get_tickers()

            # если ордер на продажу проверяем stop loss
            if order.type == MarketMyOrder.Type.SELL:

                if self.bot.is_trailing_cost:  # проверяем trailing cost
                    order = self.check_trailing_resell(order)

                self.check_stop_loss_sell(order)

            if order.type == MarketMyOrder.Type.BUY:
                print('---------- CHECK BUY --------')
                if order.status == MarketMyOrder.Status.FILLED and not order.is_close:
                    # проверяем stop loss
                    if self.check_stop_loss_buy(order):
                        count_active_orders += 1

                    elif self.bot.is_trailing_cost:  # проверяем trailing cost
                        if self.check_trailing_sell(order):
                            self.create_sell_current(from_order=order, is_block_trade=True)

                    # elif check_trend_sell(order.market, bot):   # проверяем тренды на продажу (красная свеча)
                    #     create_sell_current(from_order=order, market=market, bot=bot)

                    # elif self.create_sell(from_order=order, ):
                    #     # если ордер на покупку был выполнен проверяем рынок и создаем ордер на продажу
                    #     count_active_orders += 1

                if order.status in [MarketMyOrder.Status.OPEN]:
                    # Если buy не был исполнен, и прошло достаточно времени для отмены ордера,
                    # отменяем
                    if self.check_cancel_order(order):
                        # print('Пора отменять ордер %s' % order)
                        self.cancel_order(order)

        return count_active_orders

    def emulation_trades(self, order):
        print('emulation_trades')
        test_action = False
        # проверяем, если ордер на продажу SELL - если наш ордер <= BID отмечаем как исполненный
        if order.type == MarketMyOrder.Type.SELL:
            if 'Ask' in self.ticker_data and self.ticker_data['Ask'] and order.price <= self.ticker_data['Ask']:
                test_action = True

        # эмуляция торгов
        # проверяем, если ордер на покупку BUY -  если наш ордер >= ASK отмечаем как исполненный
        if order.type == MarketMyOrder.Type.BUY \
                and 'Bid' in self.ticker_data and self.ticker_data['Bid'] and order.price >= self.ticker_data['Bid']:
            test_action = True

        print(self.ticker_data['Ask'], order.price)

        if test_action:
            order.filled_at = timezone.now()
            order.status = MarketMyOrder.Status.FILLED
            order.save()
            if order.type == MarketMyOrder.Type.SELL and order.from_order:
                from_order = order.from_order
                from_order.status = MarketMyOrder.Status.CLOSED
                from_order.save()

        return order

    def check_order_status(self, order):
        """Проверяет статус открытого или частично исполненного ордера"""
        print_debug('BotBase check_order_status')
        self.get_tickers()
        order_info = self.api.get_order(order, is_test=self.is_test)

        self.bot.update_current_price(self.res_ticker_data, order.market)

        order.update_info(order_info, self.res_ticker_data)

        if self.ticker_data and order_info:
            # sell - ASK
            # buy - BID

            if self.is_test:
                # эмуляция торгов
                order = self.emulation_trades(order)

            else:
                # if order_info['Closed'] and not order_info['CancelInitiated']:
                # statuses = ['NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED']
                # TODO: исправить, сделать универсальное решение проверки статуса на исполнение
                # ордера на уровне client.py
                if order_info.get('status') == 'FILLED':
                    # print('Ордер %s уже выполнен!' % order)
                    order.filled_at = timezone.now()
                    # order.price = order_info['Price']
                    # order.amount = order_info['Quantity']

                    # TODO: сделать подсчет комиссии в bnb - вынести на уровень client.py
                    # order.spent = order.spent + Decimal(order_info["CommissionPaid"])
                    # order.fee = order_info["CommissionPaid"]

                    order.status = MarketMyOrder.Status.FILLED
                    order.save()
                    # TODO: вынести закрытие основного ордера в отдельный метод в модель MarketMyOrder
                    if order.type == MarketMyOrder.Type.SELL and order.from_order:
                        from_order = order.from_order
                        from_order.status = MarketMyOrder.Status.CLOSED
                        from_order.save()

                    # сохраняем в лог изменение валюты ExchangeCurrencyStatistic
                    try:
                        balances_all = self.api.get_balances()
                        for balance in balances_all:
                            if order.market.market_currency.name == balance['asset']:
                                stat = ExchangeCurrencyStatistic.objects.create(
                                    currency=order.market.market_currency,
                                    order=order,
                                    free=balance['free'],
                                    locked=balance['locked'],
                                    operation=order.type,
                                )
                                stat.set_total(self.api)
                            if order.market.base_currency.name == balance['asset']:
                                stat = ExchangeCurrencyStatistic.objects.create(
                                    currency=order.market.base_currency,
                                    order=order,
                                    free=balance['free'],
                                    locked=balance['locked'],
                                    operation=order.type,
                                )
                                stat.set_total(self.api)
                    except:
                        # TODO: сделать сохранение ошибок в отдельную таблицу логов ошибок
                        pass

                # elif order_info['Closed'] and order_info['CancelInitiated']:
                elif order_info.get('status') == 'CANCELED':
                    # print(order.market, 'Ордер %s отменен!' % order)
                    # order.price = order_info['Price']
                    # order.order_amount = order_info['Quantity']

                    # order.fee = order_info["CommissionPaid"]  # TODO: исправить комиссию
                    order.cancelled_at = timezone.now()
                    order.status = MarketMyOrder.Status.CANCELED
                    order.save()
                    # print(order.market, "Ордер %s помечен отмененным в БД" % order)
                else:
                    # print(order.market, "Ордер %s еще не выполнен" % order)
                    # if order_info['QuantityRemaining'] != order_info['Quantity']:
                    if order_info.get('status') == 'PARTIALLY_FILLED':
                        # order.partially_filled = True
                        order.status = MarketMyOrder.Status.PART_FILLED
                        order.save()

        return order

    def get_trends(self, charts_data, check_date=None):
        # print('get_trends')
        print('get_trends')
        is_ema = self.bot.is_ema
        is_stochastic = self.bot.is_stochastic
        is_stochastic_cross = self.bot.is_stochastic_cross
        is_stochastic_fast_up = self.bot.is_stochastic_fast_up

        is_green = self.bot.is_green
        is_dodge = self.bot.is_dodge
        is_hummer = self.bot.is_hummer
        is_sword = self.bot.is_sword
        is_simple = self.bot.is_simple
        is_fat = self.bot.is_fat

        is_min_value = self.bot.is_min_value
        is_compare_value = self.bot.is_compare_value
        is_ratio_open_close = self.bot.is_ratio_open_close
        is_sma = self.bot.is_sma

        is_rsi = self.bot.is_rsi
        is_macd = self.bot.is_macd
        is_macd_cross_bottom_to_top = self.bot.is_macd_cross_bottom_to_top

        is_sma_cross_bottom_to_top = self.bot.is_sma_cross_bottom_to_top

        is_adx = self.bot.is_adx

        trend_check = {}

        if is_ema:
            trend_check['ema_cross'] = False

        if is_stochastic:
            trend_check['stochastic'] = False

        if is_stochastic_cross:
            trend_check['stochastic_cross'] = False
        if is_stochastic_fast_up:
            trend_check['is_stochastic_fast_up'] = False

        if is_green:
            trend_check['is_green'] = False
        if is_dodge:
            trend_check['is_dodge'] = False
        if is_hummer:
            trend_check['is_hummer'] = False
        if is_sword:
            trend_check['is_sword'] = False
        if is_simple:
            trend_check['is_simple'] = False
        if is_fat:
            trend_check['is_fat'] = False

        if is_min_value:
            trend_check['is_min_value'] = False
        if is_compare_value:
            trend_check['is_compare_value'] = False

        if is_sma:
            trend_check['sma'] = False
        if is_sma_cross_bottom_to_top:
            trend_check['sma_cross'] = False

        if is_ratio_open_close:
            trend_check['is_ratio_open_close'] = False

        if is_rsi:
            trend_check['rsi'] = False

        if is_adx:
            trend_check['adx'] = False

        if is_macd:
            trend_check['macd'] = False
        if is_macd_cross_bottom_to_top:
            trend_check['macd_cross'] = False

        if not charts_data:
            return trend_check

        sorted_dates = sorted(charts_data)

        macd, macdsignal, macdhist = talib.MACD(
            numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
            fastperiod=self.bot.macd_fastperiod,
            slowperiod=self.bot.macd_slowperiod,
            signalperiod=self.bot.macd_signalperiod)
        # fastperiod=8, slowperiod=17, signalperiod=9)
        # fastperiod=12, slowperiod=26, signalperiod=9)

        if is_ema:
            ema_fast = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                                 timeperiod=self.bot.ema_fastperiod)
            ema_slow = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                                 timeperiod=self.bot.ema_slowperiod)
        if is_stochastic or is_stochastic_cross or is_stochastic_fast_up:
            slowk, slowd = talib.STOCH(
                numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
                numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
                numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                fastk_period=self.bot.stochastic_fastk_period,
                slowk_period=self.bot.stochastic_slowk_period, slowk_matype=0,
                slowd_period=self.bot.stochastic_slowd_period, slowd_matype=0)

        rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
                        timeperiod=self.bot.rsi_timeperiod)

        if is_sma:
            sma = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
                            timeperiod=self.bot.sma_timeperiod)

        if is_adx:
            adx = talib.ADX(numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
                            numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
                            numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                            timeperiod=self.bot.adx_timeperiod)

        if is_sma_cross_bottom_to_top:
            sma_fast = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
                                 timeperiod=self.bot.sma_fastperiod)
            sma_slow = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
                                 timeperiod=self.bot.sma_slowperiod)

        if self.bot.is_ha:
            charts_data = self.get_heikin_ashi(charts_data)

        for i, d in enumerate(charts_data):
            charts_data[d]['macd'] = macd[i]
            charts_data[d]['macdsignal'] = macdsignal[i]
            charts_data[d]['macdhist'] = macdhist[i]

            if is_sma:
                charts_data[d]['sma'] = sma[i]

            if is_sma_cross_bottom_to_top:
                charts_data[d]['sma_fast'] = sma_fast[i]
                charts_data[d]['sma_slow'] = sma_slow[i]

            if is_ema:
                charts_data[d]['ema_fast'] = ema_fast[i]
                charts_data[d]['ema_slow'] = ema_slow[i]

            if is_stochastic or is_stochastic_cross or is_stochastic_fast_up:
                charts_data[d]['stochastic_fast'] = slowk[i]
                charts_data[d]['stochastic_slow'] = slowd[i]

            charts_data[d]['rsi'] = rsi[i]

            if is_adx:
                charts_data[d]['adx'] = adx[i]

        if check_date:
            print('if check_date', check_date)
            try:
                i = sorted_dates.index(check_date)
                print('i', i - 2, i)
                dates = sorted_dates[i - 1: i + 1]
                prev_date = sorted_dates[-(i - 1)]
                pprev_date = sorted_dates[-(i - 2)]
                print('dates', dates)
            except ValueError:
                dates = []
                check_date = None
                prev_date = None
                pprev_date = None
        else:
            dates = sorted_dates[len(charts_data) - 2:]
            print('else dates', dates)
            check_date = sorted_dates[-1]
            print('check_date', check_date)
            try:
                prev_date = sorted_dates[-2]
                pprev_date = sorted_dates[-3]
            except IndexError:
                prev_date = None
                pprev_date = None

        if settings.BOT_PRINT_DEBUG:
            print('dates', dates)

        trends = {}

        if is_rsi:
            trends['rsi'] = {'value': None, 'trend': None, 'dir': None}

        if is_adx:
            trends['adx'] = {'value': None, 'trend': None, 'dir': None}
            trends['adx_direction'] = {'value': None, 'trend': None}

        if is_macd:
            trends['macd'] = {'value': None, 'trend': None}
        if is_macd_cross_bottom_to_top:
            trends['macd_cross'] = {'value': None, 'trend': None, 'macd': None, 'macdsignal': None, 'dir': None}

        if is_ema:
            trends['ema_cross'] = {'value': None, 'trend': None, 'ema_fast': None, 'ema_slow': None, 'dir': None}
            # trends['ema'] = {'value': None, 'trend': None}
            # trends['ema_fast'] = {'value': None, 'trend': None}
            # trends['ema_slow'] = {'value': None, 'trend': None}

        if is_stochastic:
            trends['stochastic'] = {'value': None, 'trend': None, 'dir': None}

        if is_stochastic_cross:
            trends['stochastic_cross'] = {'value': None, 'trend': None, 'stochastic_fast': None,
                                          'stochastic_slow': None,
                                          'dir': None}

        if is_stochastic_fast_up:
            trends['is_stochastic_fast_up'] = {'value': None, 'trend': None, 'stochastic_fast': None,
                                               'stochastic_slow': None,
                                               'dir': None}

        if is_green:
            trends['is_green'] = {'trend': None}
        if is_dodge:
            trends['is_dodge'] = {'trend': None}
        if is_hummer:
            trends['is_hummer'] = {'trend': None}
        if is_sword:
            trends['is_sword'] = {'trend': None}
        if is_simple:
            trends['is_simple'] = {'trend': None}
        if is_fat:
            trends['is_fat'] = {'trend': None}

        if is_min_value:
            trends['is_min_value'] = {'trend': None}

        if is_compare_value:
            trends['is_compare_value'] = {'trend': None}

        if is_sma:
            trends['is_sma'] = {'trend': None}

        if is_sma_cross_bottom_to_top:
            trends['sma_cross'] = {'value': None, 'trend': None, 'sma_fast': None, 'sma_slow': None, 'dir': None}

        if is_ratio_open_close:
            trends['is_ratio_open_close'] = {'trend': None}

        # prev_date = None
        # pprev_date = None

        # for d in dates:
        if check_date:
            d = check_date
            if is_green:
                trends['is_green']['trend'] = self.ta.is_green(charts_data[d])
            if is_dodge:
                print('if is_dodge:', d, prev_date)
                if prev_date:
                    trends['is_dodge']['trend'] = self.ta.is_dodge(charts_data[prev_date])
                # trends['is_dodge']['trend'] = self.ta.is_dodge(charts_data[d])
                print("trends['is_dodge']['trend'] ", trends['is_dodge']['trend'])
                # prev_dodge_trend = False
                # pprev_dodge_trend = False
                # if prev_date:
                #     prev_dodge_trend = self.ta.is_dodge(charts_data[prev_date])
                # if prev_date:
                #     pprev_dodge_trend = self.ta.is_dodge(charts_data[prev_date])
                # if prev_dodge_trend or pprev_dodge_trend:
                #     trends['is_dodge']['trend'] = True
            if is_hummer:
                trends['is_hummer']['trend'] = self.ta.is_hummer(charts_data[d])
            if is_sword:
                trends['is_sword']['trend'] = self.ta.is_sword(charts_data[d])
            if is_simple:
                trends['is_simple']['trend'] = self.ta.is_simple(charts_data[d])
            if is_fat:
                trends['is_fat']['trend'] = self.ta.is_fat(charts_data[d])

            if is_min_value:
                trends['is_min_value']['trend'] = self.ta.is_min_value(charts_data[d], self.bot.min_value)

            if prev_date and is_compare_value:
                trends['is_compare_value']['trend'] = self.ta.is_compare_value(charts_data[d], charts_data[prev_date])

            if prev_date and is_ratio_open_close:
                trends['is_ratio_open_close']['trend'] = self.ta.is_ratio_open_close(charts_data[d],
                                                                                     charts_data[prev_date],
                                                                                     self.bot.ratio_open_close)

            if is_sma:
                trends['is_sma']['trend'] = self.ta.is_sma(charts_data[d])

            if is_stochastic:
                if self.bot.stochastic_less and self.bot.stochastic_more:
                    if self.bot.stochastic_more < charts_data[d]['stochastic_fast'] < self.bot.stochastic_less:
                        print('******* if date' + str(d) + ' ' + str(self.bot.stochastic_more) + ' < ' + str(
                            charts_data[d]['stochastic_fast']) + ' < ' + str(self.bot.stochastic_less))
                        trends['stochastic']['trend'] = 'CALL'
                elif self.bot.stochastic_more and not self.bot.stochastic_less:
                    if self.bot.stochastic_more < charts_data[d]['stochastic_fast']:
                        trends['stochastic']['trend'] = 'CALL'
                elif not self.bot.stochastic_more and self.bot.stochastic_less:
                    if charts_data[d]['stochastic_fast'] < self.bot.stochastic_less:
                        trends['stochastic']['trend'] = 'CALL'

                if prev_date and charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
                    trends['stochastic']['dir'] = 'UP'

                trends['stochastic']['value'] = charts_data[d]['stochastic_fast']

            if is_stochastic_cross:
                if prev_date:
                    if self.ta.is_cross(charts_data[prev_date]['stochastic_fast'], charts_data[prev_date]['stochastic_slow'],
                                        charts_data[d]['stochastic_fast'], charts_data[d]['stochastic_slow']):
                        # print('+++++++++++++++++++++++++++ stochastic_cross ++++++++++++++++++++++++')
                        trends['stochastic_cross']['trend'] = 'CALL'

                    if charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
                        trends['stochastic_cross']['dir'] = 'UP'

                trends['stochastic_cross']['stochastic_fast'] = charts_data[d]['stochastic_fast']
                trends['stochastic_cross']['stochastic_slow'] = charts_data[d]['stochastic_slow']

            if is_stochastic_fast_up:
                if prev_date and charts_data[prev_date]['stochastic_fast'] < charts_data[d]['stochastic_fast']:
                    trends['is_stochastic_fast_up']['dir'] = 'UP'

                trends['is_stochastic_fast_up']['stochastic_fast'] = charts_data[d]['stochastic_fast']
                trends['is_stochastic_fast_up']['stochastic_slow'] = charts_data[d]['stochastic_slow']

            if is_sma_cross_bottom_to_top:
                if prev_date:
                    if self.ta.is_cross(charts_data[prev_date]['sma_fast'], charts_data[prev_date]['sma_slow'],
                                        charts_data[d]['sma_fast'], charts_data[d]['sma_slow']):
                        # print('++++++++++++++++++++++++++++++ sma_cross ++++++++++++++++++++++++++')
                        trends['sma_cross']['trend'] = 'CALL'

                    if charts_data[prev_date]['sma_fast'] < charts_data[d]['sma_fast']:
                        trends['sma_cross']['dir'] = 'UP'

                trends['sma_cross']['sma_fast'] = charts_data[d]['sma_fast']
                trends['sma_cross']['sma_slow'] = charts_data[d]['sma_slow']

            if is_rsi:
                if self.bot.rsi_less and self.bot.rsi_more:
                    if self.bot.rsi_more < charts_data[d]['rsi'] < self.bot.rsi_less:
                        trends['rsi']['trend'] = 'CALL'
                elif self.bot.rsi_more and not self.bot.rsi_less:
                    if self.bot.rsi_more < charts_data[d]['rsi']:
                        trends['rsi']['trend'] = 'CALL'
                elif not self.bot.rsi_more and self.bot.rsi_less:
                    if charts_data[d]['rsi'] < self.bot.rsi_less:
                        trends['rsi']['trend'] = 'CALL'

                if prev_date and charts_data[prev_date]['rsi'] < charts_data[d]['rsi']:
                    # print('if ', prev_date, ' and ', charts_data[prev_date]['rsi'], ' < ', charts_data[d]['rsi'])
                    # print(trends)
                    trends['rsi']['dir'] = 'UP'
                    # time.sleep(10)

                trends['rsi']['value'] = charts_data[d]['rsi']

            if is_macd:
                if prev_date:
                    if charts_data[prev_date]['macd'] < charts_data[d]['macd']:
                        trends['macd']['trend'] = 'UP'
                    else:
                        charts_data[prev_date]['trend'] = 'DOWN'
                trends['macd']['value'] = charts_data[d]['macd']

            if is_macd_cross_bottom_to_top:
                try:
                    if prev_date:
                        if self.ta.is_cross(charts_data[prev_date]['macd'], charts_data[prev_date]['macdsignal'],
                                            charts_data[d]['macd'], charts_data[d]['macdsignal']):
                            print('++++++++++++++++++++++++++++++ macd_cross ++++++++++++++++++++++++++')
                            trends['macd_cross']['trend'] = 'CALL'

                        if charts_data[prev_date]['macd'] < charts_data[d]['macd']:
                            trends['macd_cross']['dir'] = 'UP'

                    trends['macd_cross']['macd'] = charts_data[d]['macd']
                    trends['macd_cross']['macdsignal'] = charts_data[d]['macdsignal']

                except TypeError:
                    pass

            if is_ema:

                if prev_date:
                    if self.ta.is_cross(charts_data[prev_date]['ema_fast'], charts_data[prev_date]['ema_slow'],
                                        charts_data[d]['ema_fast'], charts_data[d]['ema_slow']):
                        print('++++++++++++++++++++++++++++++ EMA_cross ++++++++++++++++++++++++++')
                        trends['ema_cross']['trend'] = 'CALL'

                    if charts_data[prev_date]['ema_fast'] < charts_data[d]['ema_fast']:
                        trends['ema_cross']['dir'] = 'UP'

                trends['ema_cross']['ema_fast'] = charts_data[d]['ema_fast']
                trends['ema_cross']['ema_slow'] = charts_data[d]['ema_slow']

            if is_adx:
                # print('bot.adx_less', self.bot.adx_less)
                # print('bot.adx_more', self.bot.adx_more)
                # print('adx', charts_data[d]['adx'])
                trends['adx']['value'] = charts_data[d]['adx']
                if self.bot.adx_less and self.bot.adx_more:
                    if self.bot.adx_more < charts_data[d]['adx'] < self.bot.adx_less:
                        trends['adx']['trend'] = 'CALL'
                        # print('if', bot.adx_more, ' < ', charts_data[d]['adx'], ' < ', bot.adx_less)
                        # time.sleep(3)
                elif self.bot.adx_more and not self.bot.adx_less:
                    if self.bot.adx_more < charts_data[d]['adx']:
                        trends['adx']['trend'] = 'CALL'
                elif not self.bot.adx_more and self.bot.adx_less:
                    if charts_data[d]['adx'] < self.bot.adx_less:
                        trends['adx']['trend'] = 'CALL'

                # if not trends['adx_direction']['value']:
                #     trends['adx_direction']['value'] = charts_data[d]['adx']
                # else:
                if prev_date and charts_data[prev_date]['adx'] < charts_data[d]['adx']:
                    trends['adx_direction']['trend'] = 'UP'
                else:
                    trends['adx_direction']['trend'] = 'DOWN'
                trends['adx_direction']['value'] = charts_data[d]['adx']

            # print(d)
            # print('rsi', charts_data[d]['rsi'])
            # print('macd', charts_data[d]['macd'])
            # print('ema_fast', charts_data[d]['ema_fast'])
            # print('ema_slow', charts_data[d]['ema_slow'])
            d = check_date

            pprev_date = prev_date
            prev_date = d

        print('trends (1206) ', trends)

        if is_rsi and trends['rsi']['trend'] == 'CALL' and trends['rsi']['dir'] == 'UP':
            trend_check['rsi'] = True

        # if trends['rsi']['trend'] == 'UP' and trends['rsi']['value'] >= 50:
        #     trend_check['rsi'] = True

        # if is_ema and trends['ema']['value'] and trends['ema_fast']['trend'] == 'UP':
        #     trend_check['ema'] = True
        #     print('---- EMA TRUE ----')

        if is_stochastic_cross and trends['stochastic_cross']['trend'] == 'CALL' \
                and trends['stochastic_cross']['dir'] == 'UP':
            print(
                '+++++++++++++++++++++++++++++++++++++++ UP stochastic CROSS +++++++++++++++++++++++++++++++++++++++++')
            trend_check['stochastic_cross'] = True

        if is_stochastic_fast_up and trends['is_stochastic_fast_up']['dir'] == 'UP':
            print(
                '+++++++++++++++++++++++++++++++++++++++ UP stochastic Fast ++++++++++++++++++++++++++++++++++++++++++')
            trend_check['is_stochastic_fast_up'] = True

        if is_stochastic and trends['stochastic']['trend'] == 'CALL' and trends['stochastic']['dir'] == 'UP':
            print('+++++++++++++++++++++++++++++++++++++++ stochastic value ++++++++++++++++++++++++++++++++++++++++++')
            trend_check['stochastic'] = True

        if is_ema and trends['ema_cross']['trend'] == 'CALL' and trends['ema_cross']['dir'] == 'UP':
            print('+++++++++++++++++++++++++++++++++++++++ UP EMA CROSS +++++++++++++++++++++++++++++++++++++++++++++')
            trend_check['ema_cross'] = True

        if is_macd_cross_bottom_to_top and trends['macd_cross']['trend'] == 'CALL' and trends['macd_cross'][
            'dir'] == 'UP':
            # if is_macd_cross_bottom_to_top and trends['macd_cross']['trend'] == 'CALL':
            print('+++++++++++++++++++++++++++++++++++++++ UP MACD CROSS +++++++++++++++++++++++++++++++++++++++++++++')
            trend_check['macd_cross'] = True

        if is_macd and trends['macd']['trend'] == 'UP':
            trend_check['macd'] = True

        if is_sma_cross_bottom_to_top and trends['sma_cross']['trend'] == 'CALL' and trends['sma_cross']['dir'] == 'UP':
            print('+++++++++++++++++++++++++++++++++++++++ UP SMA CROSS +++++++++++++++++++++++++++++++++++++++++++++')
            trend_check['sma_cross'] = True

        if is_green and trends['is_green']['trend']:
            trend_check['is_green'] = True
        if is_dodge and trends['is_dodge']['trend']:
            trend_check['is_dodge'] = True
        if is_hummer and trends['is_hummer']['trend']:
            trend_check['is_hummer'] = True
        if is_sword and trends['is_sword']['trend']:
            trend_check['is_sword'] = True
        if is_simple and trends['is_simple']['trend']:
            trend_check['is_simple'] = True
        if is_fat and trends['is_fat']['trend']:
            trend_check['is_fat'] = True

        if is_min_value and trends['is_min_value']['trend']:
            trend_check['is_min_value'] = True
        if is_compare_value and trends['is_compare_value']['trend']:
            trend_check['is_compare_value'] = True
        if is_sma and trends['is_sma']['trend']:
            trend_check['sma'] = True
        if is_ratio_open_close and trends['is_ratio_open_close']['trend']:
            trend_check['is_ratio_open_close'] = True

        if is_adx and trends['adx_direction']['trend'] == 'UP' and trends['adx']['trend'] == 'CALL':
            trend_check['adx'] = True
        # print('trend_check (1221) ', trend_check)
        return trend_check

    def check_trend_buy(self, tick_intervals_charts_data: Any = None, check_date: Any = None) -> bool:
        """
        Индикаторная стратегия на основе EMA, MACD и RSI.

        Компоненты:
            EMA: 7 и 26
            MACD: параметры по умолчанию (12, 26, 9)
            RSI: 14

        Call - Покупка:
            EMA 7 пересекает EMA 26 снизу вверх
            MACD направлен вверх
            RSI больше 50

        Put - Продажа:
            EMA 7 пересекает EMA 26 сверху вниз
            MACD направлен вниз
            RSI меньше 50
        """
        print('check_trend_buy')
        trend_check = {}
        tick_intervals = self.bot.get_tick_intervals()

        if tick_intervals_charts_data:
            for ticker_interval, charts_data in tick_intervals_charts_data.items():
                trend_check[ticker_interval] = self.get_trends(charts_data, check_date)
        else:
            for ticker_interval in tick_intervals:
                if ticker_interval == TICKINTERVAL_FIFTEENMIN:
                    charts_data = self.get_chart_data(TICKINTERVAL_FIVEMIN)
                    charts_data = convert_ticker(charts_data, round_to=15)
                else:
                    charts_data = self.get_chart_data(ticker_interval)
                trend_check[ticker_interval] = self.get_trends(charts_data)

        global_trend = True
        for i, data in trend_check.items():
            for k, v in data.items():
                if not v:
                    global_trend = False

        if global_trend:
            print('---------------- OK!!!! Can BUY!!! --------')

        print('trend_check ', trend_check)
        return global_trend

    def check_trend_sell(self, tick_intervals_charts_data=None, check_date=None):

        global_trend = True

        trend_check = {}
        # tick_intervals = [t.value for t in self.bot.tick_intervals.all()]
        tick_intervals = self.bot.get_tick_intervals()

        if tick_intervals_charts_data:
            for ticker_interval, charts_data in tick_intervals_charts_data.items():
                trend_check[ticker_interval] = self.get_trends_sell(charts_data, check_date)
        else:
            for ticker_interval in tick_intervals:
                if ticker_interval == TICKINTERVAL_FIFTEENMIN:
                    charts_data = self.get_chart_data(TICKINTERVAL_FIVEMIN)
                    charts_data = convert_ticker(charts_data, round_to=15)
                else:
                    charts_data = self.get_chart_data(ticker_interval)
                trend_check[ticker_interval] = self.get_trends_sell(charts_data)
        print('trend_check sell', trend_check)
        for i, data in trend_check.items():
            for k, v in data.items():
                if not v:
                    global_trend = False

        return global_trend

    def get_trends_sell(self, charts_data, check_date=None):
        print('get_trends_sell')

        is_red = True

        trend_check = {}

        if is_red:
            trend_check['is_red'] = False

        if not charts_data:
            return trend_check

        sorted_dates = sorted(charts_data)

        macd, macdsignal, macdhist = talib.MACD(
            numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
            fastperiod=self.bot.macd_fastperiod, slowperiod=self.bot.macd_slowperiod, signalperiod=self.bot.macd_signalperiod)
        # fastperiod=8, slowperiod=17, signalperiod=9)
        # fastperiod=12, slowperiod=26, signalperiod=9)

        rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted_dates]),
                        timeperiod=self.bot.rsi_timeperiod)

        if self.bot.is_ha:
            charts_data = self.get_heikin_ashi(charts_data)

        for i, d in enumerate(charts_data):
            charts_data[d]['macd'] = macd[i]
            charts_data[d]['macdsignal'] = macdsignal[i]
            charts_data[d]['macdhist'] = macdhist[i]

            charts_data[d]['rsi'] = rsi[i]

        if check_date:
            print('if check_date', check_date)
            try:
                i = sorted_dates.index(check_date)
                print('i', i - 2, i)
                dates = sorted_dates[i - 1: i + 1]
                prev_date = sorted_dates[-(i - 1)]
                print('dates', dates)
            except ValueError:
                dates = []
                check_date = None
                prev_date = None
        else:
            dates = sorted_dates[len(charts_data) - 2:]
            print('else dates', dates)
            check_date = sorted_dates[-1]
            print('check_date', check_date)
            try:
                prev_date = sorted_dates[-2]
            except IndexError:
                prev_date = None

        if settings.BOT_PRINT_DEBUG:
            print('dates', dates)

        trends = {}

        if is_red:
            trends['is_red'] = {'trend': None}

        if check_date:
            d = check_date
            # if is_red and self.ta.is_red(charts_data[d]) and self.ta.is_red(charts_data[prev_date]):
            if is_red and self.ta.is_red(charts_data[d]):
                print('+++++++++++++++++++++++++++++++++++++++ IS RED ++++++++++++++++++++++++++++++++++++++++++')
                trends['is_red']['trend'] = True

        if is_red and trends['is_red']['trend']:
            trend_check['is_red'] = True

        print('trend_check (1221) ', trend_check)
        return trend_check

    def get_price_for_buy(self):
        """
        Определяем цену покупки
        :return:
        """
        # return ticker_data['Bid'] - satoshi_1
        rate = Decimal(self.ticker_data.get('Bid', 0))
        try:
            rate = rate.quantize(Decimal('.00000000'))
        except (InvalidOperation, AttributeError):
            pass
        return rate

    def get_price_for_sell(self):
        """
        Определяем цену продажи
        :return:
        """
        # return ticker_data['Ask'] - satoshi_1
        rate = Decimal(self.ticker_data.get('Ask', 0))
        try:
            rate = rate.quantize(Decimal('.00000000'))
        except (InvalidOperation, AttributeError):
            pass
        return rate
