import requests
import json
from bittrex import Bittrex, TICKINTERVAL_FIVEMIN, TICKINTERVAL_THIRTYMIN
from .config import BITTREX_API_KEY, BITTREX_SECRET_KEY, BITTREX_APY_VER, API_V1_1, API_V2_0, PROTECTION_PUB
from trading.models import Currency, Market, MarketSettings, Exchange


class ApiBittrex(object):

    code = 'bittrex'
    exchange = None

    convert_ticker = {
        "Bid": 'Bid',
        "Ask": 'Ask',
        "Last": 'Last',
    }

    convert_tickers = {
        'MarketName': 'MarketName',
        'High': 'High',
        'Low': 'Low',
        'Volume': 'Volume',
        'Last': 'Last',
        'BaseVolume': 'BaseVolume',
        'TimeStamp': 'TimeStamp',
        'Bid': 'Bid',
        'Ask': 'Ask',
        'OpenBuyOrders': 'OpenBuyOrders',
        'OpenSellOrders': 'OpenSellOrders',
        'PrevDay': 'PrevDay',
        'Created': 'Created'
    }

    convert_market_history = {'Id': 'Id',
                              'TimeStamp': 'TimeStamp',
                              'Quantity': 'Quantity',
                              'Price': 'Price',
                              'Total': 'Total',
                              'FillType': 'FillType',
                              'OrderType': 'SELL'}

    class Error(Exception):
        def __init__(self, message):
            self.message = message

    def __init__(self):
        self.api = Bittrex(BITTREX_API_KEY, BITTREX_SECRET_KEY, api_version=BITTREX_APY_VER)
        self.exchange = Exchange.objects.get(code=self.code)

    @staticmethod
    def convert_market(market):
        return market

    @staticmethod
    def get_market(market_name):
        currencies = market_name.split('-')
        base_currency, created = Currency.objects.get_or_create(name=currencies[0])
        market_currency, created = Currency.objects.get_or_create(name=currencies[1])
        data = {
            'market_currency': market_currency,
            'base_currency': base_currency,
        }
        market, created = Market.objects.get_or_create(**data)
        return market

    def get_currencies(self):
        """
        Получить валюты
        """

        result = self.api.get_currencies()
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_markets(self):
        """
        Получить валютные пары
        """

        result = self.api.get_markets()
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_market_summaries(self):
        """
        Получить
        """
        result = self.api.get_market_summaries()

        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_balances(self):
        """
        Получить
        """
        result = self.api.get_balances()
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_marketsummary(self, market):
        """
        Получить
        """
        result = self.api.get_marketsummary(market=market)
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_order_history(self, market=None):
        """
        Используется для получения истории заказов.
        """
        result = self.api.get_order_history(market=market)
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_open_orders(self, market=None):
        """
        Получите все заказы, которые вы сейчас открыли. Можно запросить конкретный рынок.
        """
        result = self.api.get_open_orders(market=market)
        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def get_market_history(self, market):
        """
        Используется для получения последних сделок, которые произошли для определенного рынка.
        """
        result = self.api.get_market_history(market)
        if 'success' in result and result['success']:
            return result['result']
        else:
            print('get_market_history', result)
            return False

    def get_ticker(self, market):
        """
        Используется для получения текущих значений тика для рынка.
        """
        result = self.api.get_ticker(market)
        if 'success' in result and result['success']:
            return result['result']
        else:
            print('get_ticker', market, result)
            return False

    def get_order(self, order, is_test=False):
        """
        Используется для получения одного заказа с помощью uuid.
        """
        if is_test:
            result = {
                "success": True,
                "message": "",
                "result": {
                    "AccountId": None,
                    "OrderUuid": str(order.uuid),
                    "Exchange": "BTC-SHLD",
                    "Type": "LIMIT_BUY",
                    "Quantity": 1000.00000000,
                    "QuantityRemaining": 1000.00000000,
                    "Limit": 0.00000001,
                    "Reserved": 0.00001000,
                    "ReserveRemaining": 0.00001000,
                    "CommissionReserved": 0.00000002,
                    "CommissionReserveRemaining": 0.00000002,
                    "CommissionPaid": 0.00000000,
                    "Price": 0.00000000,
                    "PricePerUnit": None,
                    "Opened": "2014-07-13T07:45:46.27",
                    "Closed": None,
                    "IsOpen": True,
                    "Sentinel": "6c454604-22e2-4fb4-892e-179eede20972",
                    "CancelInitiated": False,
                    "ImmediateOrCancel": False,
                    "IsConditional": False,
                    "Condition": "NONE",
                    "ConditionTarget": None
                }
            }

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
        else:
            result = self.api.get_order(order.uuid)
            print('get_order', result)

        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def buy_limit(self, market, quantity, rate, is_test=False):
        """
        Используется для размещения заказа на покупку на определенном рынке. Используйте buylimitдля размещения
        лимитных ордеров. Убедитесь, что у вас есть соответствующие разрешения, установленные на ваших ключах API,
        чтобы этот вызов работал.
        :param market:
        :param quantity:
        :param rate:
        :param is_test:
        :return:
        """
        if is_test:
            import uuid
            result = {
                "success": True,
                "message": "",
                "result": {
                    "uuid": str(uuid.uuid4())
                }
            }
        else:
            result = self.api.buy_limit(market, float(quantity), float(rate))
            print('buy_limit', result)

        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    @staticmethod
    def get_uuid_order(order_info):
        return order_info.get('uuid')

    def get_ext_id_order(self, order_info):
        raise self.Error('method not ready get_ext_id_order')

    def sell_limit(self, market, quantity, rate, is_test=False):

        if is_test:
            import uuid
            result = {
                "success": True,
                "message": "",
                "result": {
                    "uuid": str(uuid.uuid4())
                }
            }
        else:
            result = self.api.sell_limit(market, float(quantity), float(rate))
            print('sell_limit', result)

        if 'success' in result and result['success']:
            return result['result']
        else:
            return False

    def cancel(self, uuid, market_name=None, is_test=False):

        if is_test:
            import uuid
            result = {
                "success": True,
                "message": "",
                "result": {
                    "uuid": str(uuid.uuid4())
                }
            }
        else:
            result = self.api.cancel(uuid)
            print('cancel', result)

        if 'success' in result and result['success']:
            return result['result']
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
        try:

            res = requests.get(
                "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={}&tickInterval={}".format(market_name,
                                                                                                        tick_interval))

            if res.status_code == 200:
                # print(res.json()['result'])
                return res.json()['result']
            else:
                print('get_ticks', res)
                return {
                    'success': False,
                    'message': 'NO_API_RESPONSE',
                    'result': None
                }
        except:
            return {
                'success': False,
                'message': 'ConnectionError',
                'result': None
            }
        # return self.api._api_query(path_dict={
        #     API_V2_0: '/pub/Market/GetTicks'
        # }, options={'market': market, 'tickInterval': tick_interval}, protection=PROTECTION_PUB)

    def check_price(self, market_name, price, amount):

        # market_settings = self.get_market_info(market_name)
        #
        # # цену приводим к требованиям биржи о кратности
        # price = self.adjust_to_step(price, market_settings['filters'][0]['tickSize'])
        #
        # # Рассчитываем кол-во, которое можно купить, и тоже приводим его к кратному значен)ию
        # amount = self.adjust_to_step(amount, market_settings['filters'][2]['stepSize']
        #
        # return price, amount

        raise self.Error('method not ready check_price')
