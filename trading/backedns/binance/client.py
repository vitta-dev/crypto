import time
import random
import math
import datetime
from decimal import Decimal

import requests
import json
from bittrex import Bittrex, TICKINTERVAL_FIVEMIN, TICKINTERVAL_THIRTYMIN
from django.utils import timezone
from trading.backedns.binance.config import API_KEY, SECRET_KEY, COMMISSION
from binance.client import Client
from trading.lib import print_debug
from trading.models import Currency, Market, MarketSettings, Exchange


client = Client(API_KEY, SECRET_KEY)


class ApiBinance(object):
    """
    Клиент, для работы с биржой Binance
    https://python-binance.readthedocs.io/en/latest/overview.html
    """

    code = 'binance'
    exchange = None

    commission = Decimal(COMMISSION)

    convert_ticker = {
        "Bid": 'bidPrice',
        "Ask": 'askPrice',
        "Last": '--',
    }

    convert_tickers = {
        'MarketName': 'symbol',
        'High': 'highPrice',
        'Low': 'lowPrice',
        'Volume': 'volume',
        'Last': 'lastPrice',
        'BaseVolume': '--',
        'TimeStamp': '--',
        'Bid': 'bidPrice',
        'Ask': 'askPrice',
        'OpenBuyOrders': '--',
        'OpenSellOrders': '--',
        'PrevDay': 'prevClosePrice',
        'Created': '--'
    }

    class Error(Exception):
        def __init__(self, message):
            self.message = message

    def __init__(self):
        self.api = Client(API_KEY, SECRET_KEY)
        self.exchange = Exchange.objects.get(code=self.code)

    def get_currencies(self):
        print_debug('binance get_currencies')
        """
        Получить валюты
        Return rate limits and list of symbols        
        
        """

        # result = self.api.get_currencies()
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     return False
        raise self.Error('method not ready get_currencies')

    def get_markets(self):
        """
        Получить валютные пары
        {
            "timezone": "UTC",
            "serverTime": 1508631584636,
            "rateLimits": [
                {
                    "rateLimitType": "REQUESTS",
                    "interval": "MINUTE",
                    "limit": 1200
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "SECOND",
                    "limit": 10
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "DAY",
                    "limit": 100000
                }
            ],
            "exchangeFilters": [],
            "symbols": [
                {
                    "symbol": "ETHBTC",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "BTC",
                    "quotePrecision": 8,
                    "orderTypes": ["LIMIT", "MARKET"],
                    "icebergAllowed": false,
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.00000100",
                            "maxPrice": "100000.00000000",
                            "tickSize": "0.00000100"
                        }, {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00100000",
                            "maxQty": "100000.00000000",
                            "stepSize": "0.00100000"
                        }, {
                            "filterType": "MIN_NOTIONAL",
                            "minNotional": "0.00100000"
                        }
                    ]
                }
            ]
        }
        """

        result = self.api.get_exchange_info()
        if 'symbols' in result and result['symbols']:
            return result['symbols']
        else:
            return False

    def get_market_summaries(self):
        print_debug('binance get_market_summaries')
        """
        Получить
        """
        # result = self.api.get_market_summaries()
        result = self.api.get_ticker()
        print(result)
        return result

    @staticmethod
    def convert_market(market):
        return market.replace('-', '')

    def market_settings(self, market):
        market_settings, created = MarketSettings.objects.get_or_create(market=market, exchange=self.exchange)
        if created or market_settings.updated_at <= timezone.now() - datetime.timedelta(minutes=15):
            market_info = self.get_market_info(market.code)
            market_settings.settings = market_info
            if market_info['status'] == 'TRADING':
                market_settings.is_active = True
            else:
                market_settings.is_active = False
            market_settings.save()
        return market_settings

    def get_market(self, market_name):

        try:
            market = Market.objects.get(code=market_name)
            market_settings = self.market_settings(market)
            return market
        except Market.DoesNotExist:
            market_info = self.get_market_info(market_name)
            base_currency, created = Currency.objects.get_or_create(name=market_info['quoteAsset'])
            market_currency, created = Currency.objects.get_or_create(name=market_info['baseAsset'])
            data = {
                'market_currency': market_currency,
                'base_currency': base_currency,
            }
            market, created = Market.objects.get_or_create(**data)
            market.code = market_name
            market.save()
            market_settings = self.market_settings(market)
            if not market.name:
                market.name = '{}-{}'.format(market_info['quoteAsset'], market_info['baseAsset'])
                market.save()

            return market

    def get_market_info(self, symbol):
        result = self.api.get_symbol_info(symbol)
        print(result)
        return result

    def get_currency_balance(self, currency):
        """Возвращает баланс по выбраной валюте"""
        balances = self.get_balances()
        for b in balances:
            if b['asset'] == currency:
                return Decimal(b['free'])

        return 0

    def get_balances(self):
        print_debug('binance get_balances')
        """
        Получить баланс текущих активов.
        
        {
          "makerCommission": 15,
          "takerCommission": 15,
          "buyerCommission": 0,
          "sellerCommission": 0,
          "canTrade": true,
          "canWithdraw": true,
          "canDeposit": true,
          "updateTime": 123456789,
          "balances": [
            {
              "asset": "BTC",
              "free": "4723846.89208129",
              "locked": "0.00000000"
            },
            {
              "asset": "LTC",
              "free": "4763368.68006011",
              "locked": "0.00000000"
            }
          ]
        }
        """
        result = self.api.get_account()
        return result['balances']
        # raise self.Error('method not ready get_balances')

    def get_marketsummary(self, market):
        print_debug('binance get_marketsummary')
        """
        Получить
        """
        # result = self.api.get_marketsummary(market=market)
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     return False
        raise self.Error('method not ready get_marketsummary')

    def get_order_history(self, market):
        print_debug('binance get_order_history')
        """
        Используется для получения истории заказов.
        """
        result = self.api.get_all_orders(symbol=market)
        return result
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     return False
        # raise self.Error('method not ready get_order_history')

    def get_open_orders(self, market=None):
        print_debug('binance get_open_orders')
        """
        Получите все заказы, которые вы сейчас открыли. Можно запросить конкретный рынок.
        """
        # result = self.api.get_open_orders(market=market)
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     return False
        # raise self.Error('method not ready get_open_orders')
        orders = self.api.get_open_orders()
        return orders

    def get_market_history(self, market):
        print_debug('binance get_market_history')
        """
        Используется для получения последних сделок, которые произошли для определенного рынка.
        """
        bittrex = {'MarketName': 'USDT-ZEC',
                   'High': 219.0,
                   'Low': 188.8212564,
                   'Volume': 2162.81528553, 'Last': 212.06715761, 'BaseVolume': 443607.17464441,
                   'TimeStamp': '2018-07-24T16:20:10.903', 'Bid': 212.06715761, 'Ask': 212.4, 'OpenBuyOrders': 375,
                   'OpenSellOrders': 564, 'PrevDay': 202.92909, 'Created': '2017-07-14T17:10:10.673'}
        # result = self.api.get_market_history(market)
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     print('get_market_history', result)
        #     return False
        raise self.Error('method not ready get_market_history')

    def get_ticker(self, market):
        print_debug('binance get_ticker')
        """
        Используется для получения текущих значений тика для рынка.
        """
        # result = self.api.get_ticker(market)
        # result = self.api.get_klines(symbol='BNBBTC', interval=Client.KLINE_INTERVAL_30MINUTE)
        print('market', self.convert_market(market))
        result = self.api.get_orderbook_ticker(symbol=self.convert_market(market))
        print(result)
        convert_data = {
            'bidPrice': "Bid",
            'askPrice': "Ask",
        }
        if result:
            return_result = {}
            for key in result:
                if key in convert_data:
                    return_result[convert_data[key]] = result[key]
            print('convert', return_result)
            return return_result
        else:
            print('get_ticker', market, result)
            return False

        # raise self.Error('method not ready get_ticker')

    def get_order(self, order, is_test=False):
        print_debug('binance get_order')
        """
        Используется для получения одного заказа с помощью uuid.
        Получить ордер
        
        * status *
        'NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED'
        """

        if is_test:
            statuses = ['NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED']

            result = {
                "success": True,
                "message": "",
                "result": {
                    'IsOpen': None,
                    'CommissionReserved': None,
                    'CommissionReserveRemaining': None,
                    'PricePerUnit': 0.00000998,
                    'ConditionTarget': None,
                    'AccountId': None,
                    'ImmediateOrCancel': None,
                    'IsConditional': None,
                    'Reserved': 101.21457,
                    'Exchange': 'BTC-TRX',
                    'ReserveRemaining': 101.21457,
                    'Closed': '2018-05-26T21:24:24.97',
                    'Price': 0.00101113,
                    'CommissionPaid': 0.00000252,
                    'Quantity': 101.21457,
                    'Type': 'LIMIT_SELL',
                    'Sentinel': '46a1ba51-7dca-46f8-a84e-a96402bdddc8',
                    'Limit': 0.00000999,
                    'CancelInitiated': None,
                    'Condition': None,
                    'OrderUuid': 'f0179fd9-7283-4036-9fa1-0ef636652de7',
                    'Opened': '2018-05-26T21:23:40.28',
                    'QuantityRemaining': None
                }
            }

            result = {
                "symbol": "LTCBTC",
                "orderId": 1,
                "clientOrderId": "myOrder1",
                "price": str(order.price),
                "origQty": str(order.amount),
                "executedQty": str(order.amount),
                "status": random.choice(statuses),
                "timeInForce": "GTC",
                "type": "LIMIT",
                "side": "BUY",
                "stopPrice": "0.0",
                "icebergQty": "0.0",
                "time": 1499827319559
            }
        else:
            # result = self.api.get_order(symbol=order.market.code, orderId=order.ext_id)
            result = self.api.get_order(symbol=order.market.code, origClientOrderId=order.uuid)
            print('get_order', result)

        return result

    def buy_limit(self, market_name, quantity, rate, is_test=False):
        """
        Используйте вспомогательные функции, чтобы легко разместить заказ на покупку или продажу лимита

        order = client.order_limit_buy(
            symbol='BNBBTC',
            quantity=100,
            price='0.00001')

        order = client.order_limit_sell(
            symbol='BNBBTC',
            quantity=100,
            price='0.00001')
        :param market_name:
        :param quantity:
        :param rate:
        :param is_test:
        :return:
        """
        print_debug('binance buy_limit')
        market = Market.objects.get(code=market_name)
        market_settings = self.market_settings(market)
        print_debug(market_settings.settings)

        quantity = self.check_notional(quantity, rate, market_settings.settings)
        quantity = self.check_quantity(quantity, market_settings.settings)

        rate, quantity = self.check_price(market_name, rate, quantity)

        print('quantity', quantity)
        # if not self.check_notional(quantity, rate, market_settings.settings):
        #     print_debug('MIN_NOTIONAL - итоговая сумма ордера (объем*цена) должна быть выше minNotional')
        #     return False
        # TODO: сделать проверку максимально допустимой траты ордера
        rrr = str(rate)
        if is_test:
            result = self.api.create_test_order(
                symbol=market_name,
                side=self.api.SIDE_BUY,
                type=self.api.ORDER_TYPE_LIMIT,
                timeInForce=self.api.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=rate,
            )
            print('test real result', result)
            # time.sleep(30)

            result = {
                "symbol": market_name,
                "orderId": 28,
                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                "transactTime": 1507725176595,
                "price": str(rate),
                "origQty": str(quantity),
                "executedQty": str(quantity),
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": "MARKET",
                "side": "BUY"
            }
            print('test order result', result)

            # time.sleep(30)
            # import uuid
            # result = {
            #     "success": True,
            #     "message": "",
            #     "result": {
            #         "uuid": str(uuid.uuid4())
            #     }
            # }
        else:
            result = self.api.order_limit_buy(
                symbol=market_name,
                quantity=float(quantity),
                price=float(rate)
            )
            print('buy_limit', result)
            # time.sleep(30)
        result['price'] = Decimal(result['price'])
        result['origQty'] = Decimal(result['origQty'])
        result['executedQty'] = Decimal(result['executedQty'])
        return result
        # raise self.Error('method not ready buy_limit')

    @staticmethod
    def get_uuid_order(order_info):
        return order_info.get('clientOrderId')

    @staticmethod
    def get_ext_id_order(order_info):
        return order_info.get('orderId')

    def check_notional(self, quantity, price, settings):
        """
        проверка лимитов???
        :param quantity:
        :param price:
        :param settings:
        :return:
        """
        print_debug('check_notional')
        f = self.get_filter(settings, 'MIN_NOTIONAL')
        min_notional = Decimal(f.get('minNotional', 0))
        quantity = Decimal(quantity)
        price = Decimal(price)
        print('min_notional', min_notional)
        print('quantity * price', quantity * price)
        print('price', price)
        print('quantity', quantity)
        if quantity * price < min_notional:
            quantity = min_notional / price
            print('new_quantity', quantity)
        return quantity

    def check_quantity(self, quantity, settings):

        minQty, step_size = self.get_min_qty(settings)
        if Decimal(quantity) < Decimal(minQty):
            print('change quantity')
            quantity = Decimal(minQty)
        quantity = self.format_quantity(quantity, step_size)
        return quantity

    @staticmethod
    def step_size_to_precision(ss):
        return ss.find('1') - 1

    def format_quantity(self, val, step_size_str):
        val = Decimal(val)
        precision = self.step_size_to_precision(step_size_str)
        if precision > 0:
            return "{:0.0{}f}".format(val, precision)
        return math.floor(int(val))

    def get_min_qty(self, settings):
        f = self.get_filter(settings, 'LOT_SIZE')
        if f:
            return Decimal(f.get('minQty', 0)), f.get('stepSize', '0')

        return 0, '0'

    @staticmethod
    def get_filter(settings, filter_type):

        filters = settings.get('filters')
        if filters:
            for f in filters:
                if f.get('filterType') == filter_type:
                    return f

    def sell_limit(self, market_name, quantity, rate, is_test=False):
        print_debug('binance sell_limit')
        # if is_test:
        #     import uuid
        #     result = {
        #         "success": True,
        #         "message": "",
        #         "result": {
        #             "uuid": str(uuid.uuid4())
        #         }
        #     }
        # else:
        #     result = self.api.sell_limit(market, float(quantity), float(rate))
        #     print('sell_limit', result)
        #
        # if 'success' in result and result['success']:
        #     return result['result']
        # else:
        #     return False
        market = Market.objects.get(code=market_name)
        market_settings = self.market_settings(market)
        print_debug(market_settings.settings)
        quantity = self.check_quantity(quantity, market_settings.settings)

        rate, quantity = self.check_price(market_name, rate, quantity)

        print('quantity', quantity)
        # if not self.check_notional(quantity, rate, market_settings.settings):
        #     print_debug('MIN_NOTIONAL - итоговая сумма ордера (объем*цена) должна быть выше minNotional')
        #     return False
        # TODO: сделать проверку максимально допустимой траты ордера
        rrr = str(rate)
        if is_test:
            result = self.api.create_test_order(
                symbol=market_name,
                side=self.api.SIDE_SELL,
                type=self.api.ORDER_TYPE_LIMIT,
                timeInForce=self.api.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=rate,
            )
            print('test real result', result)
            time.sleep(30)

            result = {
                "symbol": market_name,
                "orderId": 28,
                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                "transactTime": 1507725176595,
                "price": str(rate),
                "origQty": str(quantity),
                "executedQty": str(quantity),
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": "MARKET",
                "side": "BUY"
            }
            print('test order result', result)

            # time.sleep(30)
            # import uuid
            # result = {
            #     "success": True,
            #     "message": "",
            #     "result": {
            #         "uuid": str(uuid.uuid4())
            #     }
            # }
        else:
            result = self.api.order_limit_sell(
                symbol=market_name,
                quantity=quantity,
                price=rate
            )
            print('sell_limit', result)
            time.sleep(30)

        return result
        # raise self.Error('method not ready sell_limit')

    def cancel(self, uuid, market_name, is_test=False):
        """
        Отменить активный заказ. Должен быть отправлен либо orderId, либо origClientOrderId.
        {
            "symbol": "LTCBTC",
            "origClientOrderId": "myOrder1",
            "orderId": 1,
            "clientOrderId": "cancelMyOrder1"
        }
        :param uuid:
        :param is_test:
        :return:
        """
        print_debug('binance cancel')
        if is_test:
            result = {
                "symbol": market_name,
                "origClientOrderId": uuid,
                "orderId": uuid,
                "clientOrderId": "cancelMyOrder1",
                "status": "CANCELED",
            }
        else:
            result = self.api.cancel_order(symbol=market_name, origClientOrderId=uuid)
            print_debug(result)

        if result.get('status') == 'CANCELED':
            return True
        else:
            return False

    def get_ticks(self, market_name, tick_interval=TICKINTERVAL_FIVEMIN):
        """
        Used to get the current tick values for a market.

        Endpoints:
        1.1 /public/getticker
        2.0 NO EQUIVALENT -- but get_candlesticks gives comparable data

        :param market_name: String literal for the market (ex: BTC-LTC)
        :type market_name: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        print_debug('binance get_ticks')
        # print('************************************************************ tick_interval', tick_interval)


        # result = self.api.get_klines(symbol=market_name, interval=Client.KLINE_INTERVAL_5MINUTE)
        result = self.api.get_klines(symbol=market_name, interval=tick_interval, limit=1000)
        # print(result)

        d = [
            1499040000000,  # Open time 0
            "0.01634790",  # Open 1
            "0.80000000",  # High 2
            "0.01575800",  # Low 3
            "0.01577100",  # Close 4
            "148976.11427815",  # Volume 5
            1499644799999,  # Close time 6
            "2434.19055334",  # Quote asset volume 7
            308,  # Number of trades 8
            "1756.87402397",  # Taker buy base asset volume 9
            "28.46694368",  # Taker buy quote asset volume 10
            "17928899.62484339"  # Can be ignored 11
        ]

        return_result = []
        if result:
            for r in result:
                return_result.append({
                    'O': r[1],  # Open
                    'H': r[2],  # High
                    'L': r[3],  # Low
                    'C': r[4],  # Close
                    'V': r[5],  # Volume
                    'T': r[0],  # Open time
                    'BV': '--',
                })
        # print(return_result)
        return return_result

        # try:
        #
        #     res = requests.get(
        #         "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={}&tickInterval={}".format(market_name,
        #                                                                                                 tick_interval))
        #
        #     if res.status_code == 200:
        #         return res.json()
        #     else:
        #         print('get_ticks', res)
        #         return {
        #             'success': False,
        #             'message': 'NO_API_RESPONSE',
        #             'result': None
        #         }
        # except:
        #     return {
        #         'success': False,
        #         'message': 'ConnectionError',
        #         'result': None
        #     }

        # raise self.Error('method not ready get_ticks')

    @staticmethod
    def adjust_to_step(value, step, increase=False):
        """
        Ф-ция, которая приводит любое число к числу, кратному шагу, указанному биржей
        Если передать параметр increase=True то округление произойдет к следующему шагу
        :param step:
        :param increase:
        :return:
        """
        value = float(value)
        return ((int(value * 100000000) - int(value * 100000000) % int(
            float(step) * 100000000)) / 100000000) + (float(step) if increase else 0)

        # return ((int(value * 100000000) - int(value * 100000000) % int(
        #     Decimal(step) * 100000000)) / 100000000) + (Decimal(step) if increase else 0)

    def check_price(self, market_name, price, amount):
        print_debug('check_price')
        print_debug(price)
        print_debug(amount)

        market_settings = self.get_market_info(market_name)

        thick_size = 0
        step_size = 0

        for d in market_settings['filters']:
            if d['filterType'] == 'PRICE_FILTER':
                thick_size = d.get('tickSize')

            if d['filterType'] == 'LOT_SIZE':
                step_size = d.get('stepSize')

        # цену приводим к требованиям биржи о кратности
        price = self.adjust_to_step(price, thick_size)
        price = "{price:0.{precision}f}".format(
                                price=price, precision=market_settings['baseAssetPrecision'])

        # Рассчитываем кол-во, которое можно купить, и тоже приводим его к кратному значению
        amount = self.adjust_to_step(amount, step_size)
        amount = "{quantity:0.{precision}f}".format(
            quantity=amount, precision=market_settings['baseAssetPrecision']
        )
        print_debug(price)
        print_debug(amount)
        return price, amount

    def get_my_trades(self, symbol):
        """Получить последние сделки по выбраной паре"""
        print_debug('binance get_my_trades')

        result = self.api.get_my_trades(symbol=symbol)
        return result

    def get_avg_price(self, symbol):
        """Получить текущую цену"""

        result = self.api.get_avg_price(symbol=symbol)

        return result

    def get_price(self, currency: str, total: Decimal = 0) -> dict:

        price_info = {
            'USDT': 0,
            'price': 0,
        }

        if currency == 'USDT':
            price_info['USDT'] = total
        else:
            symbol = '{}USDT'.format(currency)
            try:
                r = self.get_avg_price(symbol)
                price = Decimal(r.get('price', 0))
                price_info['price'] = price
                price_info['USDT'] = price * total
            except:
                pass

        return price_info
