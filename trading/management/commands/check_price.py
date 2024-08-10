from decimal import Decimal

from django.core.management import BaseCommand

from trading.backedns.binance.client import ApiBinance
from trading.backedns.bittrex.client import ApiBittrex
from trading.bots.strategy_ut import BotUT
from trading.models import Currency, Market, MarketBot


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('market', nargs='?')

    def handle(self, *args, **options):

        market_symbol = options['market']
        market_name = 'USDT-BTC'
        bot_name = 'usdt_btc'

        api = ApiBinance()

        bot = MarketBot.objects.get(name=bot_name)
        market = Market.objects.get(name=market_name)

        results = api.get_market_info(market_symbol)
        print(results)

        tb = BotUT(bot, market)
        tb.get_tickers()

        rate = tb.get_price_for_sell()
        rate = tb.get_price_for_buy()
        print('rate', rate)

        avr_price = api.get_avg_price(market_symbol)
        print('avr_price', avr_price)

        # rate = avr_price['price']
        # print('rate_avr', rate)

        quantity = '0.00009000'
        market_name = 'BTCUSDT'
        # order = tb.api.sell_limit(market_name, quantity=quantity, rate=rate, is_test=True)
        # print(order)

        bc = tb.api.api
        # result = bc.create_test_order(
        #     symbol=market_name,
        #     side=bc.SIDE_SELL,
        #     type=bc.ORDER_TYPE_LIMIT,
        #     timeInForce=bc.TIME_IN_FORCE_GTC,
        #     quantity=quantity,
        #     price=rate,
        # )
        # print('test real result', result)

        def get_price_filter(symbol):
            data_from_api = bc.get_exchange_info()
            symbol_info = next(filter(lambda x: x['symbol'] == symbol, data_from_api['symbols']))
            return next(filter(lambda x: x['filterType'] == 'PRICE_FILTER', symbol_info['filters']))

        price_filter = get_price_filter(market_name)
        print('price_filter', price_filter)

        order_data = {
            'symbol': market_name,
            # 'side': bc.SIDE_SELL,
            'side': bc.SIDE_SELL,
            'type': bc.ORDER_TYPE_LIMIT,
            'timeInForce': bc.TIME_IN_FORCE_GTC,
            'quantity': quantity,
            'price': rate,
        }
        print('order_data', order_data)

        result = bc.create_test_order(**order_data)
        print('test real result', result)
