from decimal import Decimal
from typing import Optional, Union

from trading.bots.base import BotBase
from trading.models import MarketMyOrder, MarketOrderLog
from trading.lib import print_debug


class BotAverage(BotBase):
    total_safety_orders = 0
    active_orders = 0
    open_status = [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]

    def check_order(self, order, count_active_orders=0):
        print_debug('BotAverage check_order')
        # обновляем информацию из базы, для исключения коллизий со статусами
        order.refresh_from_db()
        # TODO: сделать проверку ордеров
        print_debug("Check orders {} - {} {} [{}]".format(order.id, order.get_uuid(), order.type, order.status))
        if order.uuid:
            if order.status in [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]:
                order = self.check_order_status(order)

            self.get_tickers()

            if order.type == MarketMyOrder.Type.SELL:

                # если выполнился ордер на продажу отменяем все страховочные ордера
                if order.status == MarketMyOrder.Status.FILLED:
                    self.cancel_safety_orders(order.from_order)

                    # фиксируем историю баланса
                    hb = self.fix_current_balance()
                    hb.order = order.from_order
                    hb.save()
                # else:
                    # отключаем отмену ордера на продажу, продажа должна отменяться только
                    # в случае покупкпи страховочного ордера и выставить сразу новый ордер на продажу
                    # # если ордер на продажу проверяем stop loss
                    # if self.bot.is_trailing_cost:  # проверяем trailing cost
                    #     order = self.check_trailing_resell(order)
                    # else:
                    #     self.check_stop_loss_sell(order)
                    #
                    # # TODO: сделать проверку на отмену ордера на продажу при необходимости

            if order.type == MarketMyOrder.Type.BUY:
                print_debug('---------- CHECK BUY --------')
                if (order.status == MarketMyOrder.Status.FILLED
                        and not order.is_close
                        and order.kind == MarketMyOrder.Kind.MAIN):

                    # if not self.check_create_fix_order(order):
                    # проверяем страховочные ордера
                    self.check_safety_orders(order)

                    # если ордер на покупку был выполнен проверяем рынок и создаем ордер на продажу,
                    # для фиксации прибыли как только цена будет на нужном уровне
                    self.create_fix_sell(order)

                    # # проверяем stop loss
                    # # if self.check_stop_loss_buy(order):
                    # #     count_active_orders += 1
                    #
                    # закрываем скользящие продажи и делаем фиксацию продажи с прибылью
                    # if self.bot.is_trailing_cost:  # проверяем trailing cost
                    #     if self.check_trailing_sell(order):
                    #         self.create_sell_current(from_order=order, is_block_trade=True)
                    #
                    # # elif check_trend_sell(order.market, bot):   # проверяем тренды на продажу (красная свеча)
                    # #     create_sell_current(from_order=order, market=market, bot=bot)
                    #
                    # # elif self.create_sell(from_order=order, ):
                    # #     # если ордер на покупку был выполнен проверяем рынок и создаем ордер на продажу
                    # #     count_active_orders += 1

                # если выполнился страховочный ордер на покупку, отменяем продажу
                # и выставляем новый ордер на продажу с учетом изменившейся цены с профитом
                if order.kind == MarketMyOrder.Kind.SAFETY and order.status == MarketMyOrder.Status.FILLED:
                    self.cancel_sell_order(order.from_order)
                    self.create_fix_sell(order.from_order)

                if order.status in [MarketMyOrder.Status.OPEN]:
                    # Если buy не был исполнен, и прошло достаточно времени для отмены ордера,
                    # отменяем
                    if self.check_cancel_order(order):
                        # print_debug('Пора отменять ордер %s' % order)
                        print_debug('cancel order')
                        market_name = order.market.get_market_name(order.bot.exchange.code)
                        cancel_res = self.api.cancel(order.uuid, market_name=market_name, is_test=self.is_test)
                        print_debug(cancel_res)
                        if cancel_res:
                            order.cancel_order()

        return count_active_orders

    def check_safety_orders(self, order):
        """проверяем страховочные ордера"""
        print_debug('** check_safety_orders')
        self.total_safety_orders = MarketMyOrder.objects.filter(
            from_order=order, kind=MarketMyOrder.Kind.SAFETY
        ).exclude(status=MarketMyOrder.Status.CANCELED).count()
        print('66 self.active_orders', self.active_orders)
        safety_orders = MarketMyOrder.objects.filter(
            from_order=order, kind=MarketMyOrder.Kind.SAFETY, status__in=self.open_status
        )
        self.active_orders = safety_orders.count()
        print('69 self.total_safety_orders', self.total_safety_orders)

        # if self.total_safety_orders == 0:
        #     self.create_safety_orders(order)

        for safety_order in safety_orders:
            if safety_order.uuid:
                if safety_order.status in self.open_status:
                    safety_order = self.check_order_status(safety_order)

                    # проверяем если ордер страховочный ордер не исполнен и текущая цена ушла ниже, отменяем ордер
                    if (safety_order.status == MarketMyOrder.Status.OPEN
                            and safety_order.price > self.get_price_for_sell()):
                        self.cancel_order(safety_order)

        self.total_safety_orders = MarketMyOrder.objects.filter(
            from_order=order, kind=MarketMyOrder.Kind.SAFETY
        ).exclude(
            status=MarketMyOrder.Status.CANCELED
        ).count()

        self.active_orders = MarketMyOrder.objects.filter(from_order=order, kind=MarketMyOrder.Kind.SAFETY,
                                                          status__in=self.open_status).count()

        print('if ', self.active_orders, ' < ', self.bot.average_safety_orders_active_count,
              ' and ', self.total_safety_orders, ' < ', self.bot.average_safety_orders_max_count)
        print('if ', self.active_orders < self.bot.average_safety_orders_active_count
              and self.total_safety_orders < self.bot.average_safety_orders_max_count)
        if (self.active_orders < self.bot.average_safety_orders_active_count
                and self.total_safety_orders < self.bot.average_safety_orders_max_count):
            print_debug('create_safety_orders')
            self.create_safety_orders(order)

    @staticmethod
    def get_last_safety_order(from_order):
        print('def get_last_safety_order', from_order)
        try:
            last_order = MarketMyOrder.objects.filter(from_order=from_order, kind=MarketMyOrder.Kind.SAFETY).latest('id')
        except MarketMyOrder.DoesNotExist:
            print_debug('except MarketMyOrder.DoesNotExist:')
            last_order = None
        if not last_order:
            last_order = from_order
        print('last_order', last_order)
        return last_order

    def create_safety_orders(self, order):
        # создаем страховочные ордера
        print('def create_safety_orders')
        last_order = self.get_last_safety_order(order)

        is_safety = True
        print('is_safety', is_safety)
        while is_safety:
            print_debug('while is_safety:')
            if (self.active_orders < self.bot.average_safety_orders_active_count
                    and self.total_safety_orders < self.bot.average_safety_orders_max_count):
                price, amount = self.next_safety_price(last_order)
                print('price, amount', price, amount)
                # проверка доступного баланса
                market_currency = self.market.market_currency.name
                base_currency = self.market.base_currency.name
                print('market_currency', market_currency)
                print('base_currency', base_currency)
                available_balance_market = self.api.get_currency_balance(market_currency)
                available_balance_market1 = self.api.get_currency_balance(base_currency)
                print('amount < available_balance_market', amount, available_balance_market)
                print('available_balance_market1 ', available_balance_market1)
                print('amount * price', amount * price)
                print('amount / price', amount / price)
                # if amount < available_balance_market:
                if amount * price > available_balance_market1:
                    is_safety = False
                    print_debug('Not enough money for safety')
                    # TODO: сделать оповещение о нехватке баланса
                    # TODO: решить что делать в таких случаях
                else:
                    last_order = self.create_safety_order(order, price, amount)
                    print('create order', last_order)
                    self.active_orders += 1
                    self.total_safety_orders += 1
                    print('while', self.active_orders, self.total_safety_orders)
            else:
                is_safety = False
                print_debug('is_safety = False')

    def cancel_safety_orders(self, from_order):
        """Отменяем страховочные ордера"""
        safety_orders = MarketMyOrder.objects.filter(from_order=from_order,
                                                     kind=MarketMyOrder.Kind.SAFETY,
                                                     status=MarketMyOrder.Status.OPEN)

        for order in safety_orders:
            self.cancel_order(order)

    def cancel_sell_order(self, from_order):
        """Отменяем ордер на продажу"""
        sell_orders = MarketMyOrder.objects.filter(from_order=from_order,
                                                   type=MarketMyOrder.Type.SELL,
                                                   status=MarketMyOrder.Status.OPEN)

        for order in sell_orders:
            self.cancel_order(order, cancel_type=MarketMyOrder.CancelStatus.SAFETY)

    def next_safety_price(self, last_order):
        """ Высчитываем цену для страховочного ордера """

        print_debug('next_safety_price')
        print_debug(last_order.price)
        print_debug(last_order.amount)
        # price = last_order.price - last_order.price / 100 * self.bot.average_safety_ratio
        price = last_order.price - last_order.price / 100 * self.bot.average_safety_price_change
        # amount = last_order.amount + last_order.amount / 100 * self.bot.average_safety_step
        amount = last_order.amount + last_order.amount * self.bot.average_safety_step
        print(price, amount)
        # проверяем если цена уже ушла ниже выставляем по текущему курсу
        current_price = self.get_price_for_buy()
        if current_price < price:
            price = current_price
        return price, amount

    def create_safety_order(self, order, price, amount):
        # создает страховочный ордер
        return self.create_buy_price(price, amount, kind=MarketMyOrder.Kind.SAFETY, from_order=order)

    def get_profit_price(self, price):
        """Добавляем профит к цене с учетом комиссии"""
        return self.add_stock_fee(price + price * self.bot.markup / 100)

    def create_fix_sell(self, from_order: MarketMyOrder) -> Union[MarketMyOrder, bool]:
        """Создаем ордер на продажу"""

        new_sell_order = False

        # получаем сумму и среднюю цену с учетом прибыли
        total_amount, average_price = from_order.get_amount_for_sell_new()
        min_profit_price = self.get_profit_price(average_price)

        try:
            # если ордер на продажу есть, сверяем выставленную сумму и прайс
            sell_order = MarketMyOrder.objects.get(from_order=from_order,
                                                   type=MarketMyOrder.Type.SELL,
                                                   status=MarketMyOrder.Status.OPEN)

            # если сумма не совпадает отменяем ордер на продажу и выставляем новый
            if sell_order and (sell_order.amount != total_amount or sell_order.price != min_profit_price):
                self.cancel_order(sell_order, MarketMyOrder.CancelStatus.SAFETY)
                new_sell_order = self.create_fix_order(from_order)

        except MarketMyOrder.DoesNotExist:
            sell_orders = MarketMyOrder.objects.filter(
                from_order=from_order, type=MarketMyOrder.Type.SELL
            ).exclude(status=MarketMyOrder.Status.CANCELED)
            if sell_orders.count() == 0:
                # выставляем ордер на продажу
                new_sell_order = self.create_fix_order(from_order)

        return new_sell_order

    def create_sell_by_current_price(self, from_order: MarketMyOrder) -> Optional[MarketMyOrder]:
        """Создаем ордер на продажу по текущему курсу, без учета профита"""

        # отменяем страховочные ордера
        self.cancel_safety_orders(from_order)

        # отменяем ордер на продажу
        self.cancel_sell_order(from_order)

        # выставляем ордер на продажу по текущему курсу
        total_amount, average_price = from_order.get_amount_for_sell_new()
        rate = self.get_price_for_sell()
        order_spent = Decimal(total_amount * rate)

        sell_order = self.place_order(total_amount, rate, order_spent, from_order)

        return sell_order

    def create_fix_order(self,
                         order: MarketMyOrder,
                         total_amount: Optional[Decimal] = None,
                         average_price: Optional[Decimal] = None,
                         min_profit_price: Optional[Decimal] = None) -> Union[MarketMyOrder, bool]:
        """создаем фиксирующий ордер с учетом профита, вне зависимости от состояния рынка"""
        print_debug('create_fix_order')
        if not total_amount or not average_price or not min_profit_price:
            total_amount, average_price = order.get_amount_for_sell_new()
            min_profit_price = self.get_profit_price(average_price)

        order_spent = Decimal(total_amount * min_profit_price)
        sell_order = self.place_order(total_amount, min_profit_price, order_spent, order)
        # TODO: сделать отправку в бота
        if sell_order:
            print('sell_order', sell_order)
            return sell_order
        print_debug('False')
        return False

    def check_create_fix_order(self, order):
        """проверяем и создаем фиксирующий ордер"""
        print_debug('check_create_fix_order')
        average_price = order.get_average_price()
        min_profit_price = self.get_profit_price(average_price)
        current_rate = self.get_price_for_sell()

        if current_rate >= min_profit_price:
            sell_order = self.create_sell_current(order)
            print('sell_order', sell_order)
            return sell_order
        print_debug('False')
        return False
