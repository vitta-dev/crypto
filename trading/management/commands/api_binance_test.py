from decimal import Decimal
from decimal import Decimal

from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.binance.client import ApiBinance
from trading.models import MarketBot, ExchangeCurrencyStatistic, Currency

api = ApiBinance()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('bot_name', nargs='?')

    # @cron_log_error('bot_binance', 360, 360)
    def handle(self, *args, **options):

        bot_name = options['bot_name']

        is_bot = True

        while is_bot:
            is_bot = False

            bot_active_pairs = 0

            try:
                bot = MarketBot.objects.get(name=bot_name)
                bot.bot_last_run = timezone.now()
                bot.save()
            except MarketBot.DoesNotExist:
                print('Bot "{}" Does Not Exist'.format(bot_name))
                return False

            api = bot.get_api()
            # # проверяем доступный баланс
            # balances = api.get_balances()
            # for b in balances:
            #     b_free = Decimal(b['free'])
            #     if b_free > 0:
            #         print(b)
            #     b_locked = Decimal(b['locked'])
            #     if b_locked > 0:
            #         print(b)
            #
            # # orders = api.get_open_orders()
            # # print(orders)
            #
            # orders = api.get_order_history('BNBBTC')
            # for o in orders:
            #     print('\n', o)
            #
            # orders = api.get_my_trades('BNBBTC')
            # for o in orders:
            #     print('\n', o)
            #
            # r2 = {'symbol': 'BNBBTC', 'orderId': 383300471, 'orderListId': -1,
            #       'clientOrderId': 'x2dra19HqzMLBgokOvIkld', 'price': '0.00175020', 'origQty': '5.56000000',
            #       'executedQty': '5.56000000', 'cummulativeQuoteQty': '0.00973111', 'status': 'FILLED',
            #       'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'SELL', 'stopPrice': '0.00000000',
            #       'icebergQty': '0.00000000', 'time': 1589092916786, 'updateTime': 1589092932980, 'isWorking': True,
            #       'origQuoteOrderQty': '0.00000000'}
            #
            # r1 = {'symbol': 'BNBBTC', 'id': 77610744, 'orderId': 383300471, 'orderListId': -1, 'price': '0.00175020',
            #       'qty': '5.56000000', 'quoteQty': '0.00973111', 'commission': '0.00416976', 'commissionAsset': 'BNB',
            #       'time': 1589092932980, 'isBuyer': False, 'isMaker': True, 'isBestMatch': True}

            symbol = 'BNBUSDT'
            symbol = 'BTCUSDT'
            r = api.get_avg_price(symbol)
            print(r)

            info = api.get_account()
            print(info)

            # balances_all = api.get_balances()
            # currencies = ['BNB', 'BTC', 'USDT', 'ETH']
            # for balance in balances_all:
            #     if balance['asset'] in currencies:
            #         currency = Currency.objects.get(name=balance['asset'])
            #         stat = ExchangeCurrencyStatistic.objects.create(
            #             currency=currency,
            #             free=Decimal(balance['free']),
            #             locked=Decimal(balance['locked']),
            #             operation='',
            #         )
            #         stat.set_total(api)


# bot.check_market_stop_loss()

            # проверяем статусы открытых ордеров
            # orders = MarketMyOrder.open_objects.filter(bot=bot)
            #
            # if orders:
            #     print('check orders', orders)
            #     for order in orders:
            #         tb = BotAverage(bot, order.market)
            #         bot_active_pairs += tb.check_order(order)
            #
            # markets = bot.get_markets(api)
            # print('get_markets', markets)
            #
            # for market in markets:
            #
            #     if bot_active_pairs > bot.max_rank_pairs:
            #         continue
            #
            #     tb = BotAverage(bot, market)
            #
            #     print('----------------------')
            #     print(market.name)
            #
            #     # получаем все открытые ордера
            #     orders = MarketMyOrder.open_objects.filter(market=market, bot=bot)
            #     print('check orders by market', market, orders)
            #
            #     if orders:
            #         for order in orders:
            #             bot_active_pairs += tb.check_order(order)
            #     else:
            #         # Проверяем тренд, если рынок в нужном состоянии, выставляем ордер на покупку
            #         trend_buy = tb.check_trend_buy()
            #         if trend_buy:
            #             # создаем ордер на покупку
            #             if tb.create_buy():
            #                 bot_active_pairs += 1
            #
            #     time.sleep(10)
            #
            # print('----- time.sleep(3) -----')
            # time.sleep(30)
