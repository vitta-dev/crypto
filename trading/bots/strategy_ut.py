from decimal import Decimal
from typing import Optional, Union, OrderedDict

from trading.bots.base import BotBase
from trading.config import TICKINTERVAL_FIFTEENMIN, TICKINTERVAL_FIVEMIN
from trading.models import MarketMyOrder, MarketOrderLog
from trading.lib import print_debug, convert_ticker

import json

import requests
import vectorbt as vbt
import pandas as pd
import numpy as np
import talib
import datetime as dt


class BotUT(BotBase):
    total_safety_orders = 0
    active_orders = 0
    open_status = [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]

    def check_order(self, order, count_active_orders=0):
        print_debug('BotUT check_order')
        # обновляем информацию из базы, для исключения коллизий со статусами
        order.refresh_from_db()

        print_debug("Check orders {} - {} {} [{}]".format(order.id, order.get_uuid(), order.type, order.status))
        if order.uuid:
            if order.status in [MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]:
                order = self.check_order_status(order)

            self.get_tickers()

            if order.type == MarketMyOrder.Type.SELL:

                # если выполнился ордер на продажу
                if order.status == MarketMyOrder.Status.FILLED:
                    # фиксируем историю баланса
                    hb = self.fix_current_balance()
                    hb.order = order.from_order
                    hb.save()
                    # закрываем сделку
                    order.close_trade()

            if order.type == MarketMyOrder.Type.BUY:
                print_debug('---------- CHECK BUY --------')
                if (order.status == MarketMyOrder.Status.FILLED
                        and not order.is_close
                        and order.kind == MarketMyOrder.Kind.MAIN):

                    # проверяем сигнал на продажу
                    trend_sell = self.check_trend_sell()
                    if trend_sell:
                        print('trend_sell', trend_sell)
                        # выставляем ордер на продажу
                        self.create_sell_by_current_price(order)

                if order.status in [MarketMyOrder.Status.OPEN]:
                    # Если buy не был исполнен, и прошло достаточно времени для отмены ордера, отменяем
                    if self.check_cancel_order(order):
                        # print_debug('Пора отменять ордер %s' % order)
                        print_debug('cancel order')
                        market_name = order.market.get_market_name(order.bot.exchange.code)
                        cancel_res = self.api.cancel(order.uuid, market_name=market_name, is_test=self.is_test)
                        print_debug(cancel_res)
                        if cancel_res:
                            order.cancel_order()

        return count_active_orders

    def cancel_sell_order(self, from_order):
        """Отменяем ордер на продажу"""
        sell_orders = MarketMyOrder.objects.filter(from_order=from_order,
                                                   type=MarketMyOrder.Type.SELL,
                                                   status=MarketMyOrder.Status.OPEN)

        for order in sell_orders:
            self.cancel_order(order, cancel_type=MarketMyOrder.CancelStatus.SAFETY)

    def create_sell_by_current_price(self, from_order: MarketMyOrder) -> Optional[MarketMyOrder]:
        """Создаем ордер на продажу по текущему курсу, без учета профита"""

        # отменяем ордер на продажу
        self.cancel_sell_order(from_order)

        # выставляем ордер на продажу по текущему курсу
        total_amount, average_price = from_order.get_amount_for_sell_new()
        rate = self.get_price_for_sell()
        order_spent = Decimal(total_amount * rate)

        sell_order = self.place_order(total_amount, rate, order_spent, from_order)

        return sell_order

    def check_trend_sell(self) -> bool:
        """Проверяем стратегию UT Bot"""
        print('check_trend_sell')
        trend_check = {}
        tick_intervals = self.bot.get_tick_intervals()

        for ticker_interval in tick_intervals:
            print('ticker_interval', ticker_interval)
            charts_data = self.download_kline_data(ticker_interval)
            trend_check[ticker_interval] = self.get_trends_sell_ut(charts_data)

        print('trend_check', trend_check)
        global_trend = True
        for i, trend in trend_check.items():
            if not trend:
                global_trend = False

        if global_trend:
            print('---------------- OK!!!! Can SELL!!! --------')

        return global_trend

    def get_chart_data(self, tick_interval):
        res = self.api.get_ticks(self.market_name, tick_interval)
        return res

    def download_kline_data(self, interval: str) -> pd.DataFrame:

        URL = 'https://api.binance.com/api/v3/klines'

        full_data = pd.DataFrame()

        par = {'symbol': self.market_name, 'interval': interval, 'limit': 1000}
        data = pd.DataFrame(json.loads(requests.get(URL, params=par).text))

        data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in data.iloc[:, 0]]
        data = data.astype(float)
        full_data = pd.concat([full_data, data])

        full_data.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Qav', 'Num_trades',
                             'Taker_base_vol', 'Taker_quote_vol', 'Ignore']

        return full_data

    def check_trend_buy(self) -> bool:
        """Проверяем стратегию UT Bot"""

        print('check_trend_buy')
        trend_check = {}
        tick_intervals = self.bot.get_tick_intervals()

        for ticker_interval in tick_intervals:
            print('ticker_interval', ticker_interval)
            charts_data = self.download_kline_data(ticker_interval)
            trend_check[ticker_interval] = self.get_trends_buy_ut(charts_data)

        print('trend_check', trend_check)
        global_trend = True
        for i, trend in trend_check.items():
            print(i, trend)
            if not trend:
                global_trend = False

        if global_trend:
            print('---------------- OK!!!! Can BUY!!! --------')

        return global_trend

    def get_trends_ut(self, pd_data: pd.DataFrame) -> pd.DataFrame:
        """Проверяем тренды на покупку"""

        # Compute ATR And nLoss variable
        pd_data["xATR"] = talib.ATR(pd_data["High"], pd_data["Low"], pd_data["Close"],
                                    timeperiod=self.bot.ut_atr_period)
        pd_data["nLoss"] = self.bot.ut_sensitivity * pd_data["xATR"]

        # Drop all rows that have nan, X first depending on the ATR preiod for the moving average
        pd_data = pd_data.dropna()
        pd_data = pd_data.reset_index()

        # Function to compute ATRTrailingStop
        def xATRTrailingStop_func(close, prev_close, prev_atr, nloss):
            if close > prev_atr and prev_close > prev_atr:
                return max(prev_atr, close - nloss)
            elif close < prev_atr and prev_close < prev_atr:
                return min(prev_atr, close + nloss)
            elif close > prev_atr:
                return close - nloss
            else:
                return close + nloss

        # Filling ATRTrailingStop Variable
        pd_data["ATRTrailingStop"] = [0.0] + [np.nan for i in range(len(pd_data) - 1)]

        len_pd_data = len(pd_data)
        for i in range(1, len_pd_data):
            pd_data.loc[i, "ATRTrailingStop"] = xATRTrailingStop_func(
                pd_data.loc[i, "Close"],
                pd_data.loc[i - 1, "Close"],
                pd_data.loc[i - 1, "ATRTrailingStop"],
                pd_data.loc[i, "nLoss"],
            )

        # Calculating signals
        ema = vbt.MA.run(pd_data["Close"], 1, short_name='EMA', ewm=True)

        pd_data["Above"] = ema.ma_crossed_above(pd_data["ATRTrailingStop"])
        pd_data["Below"] = ema.ma_crossed_below(pd_data["ATRTrailingStop"])

        pd_data["Buy"] = (pd_data["Close"] > pd_data["ATRTrailingStop"]) & (pd_data["Above"] == True)
        pd_data["Sell"] = (pd_data["Close"] < pd_data["ATRTrailingStop"]) & (pd_data["Below"] == True)

        return pd_data

    def get_trends_buy_ut(self, pd_data: pd.DataFrame) -> bool:
        """Проверяем тренд на покупку"""

        pd_data = self.get_trends_ut(pd_data)

        return pd_data['Buy'].values[-1]

    def get_trends_sell_ut(self, pd_data: pd.DataFrame) -> bool:
        """Проверяем тренд на продажу"""

        pd_data = self.get_trends_ut(pd_data)

        return pd_data['Sell'].values[-1]
