import time

from django.core.management import BaseCommand
from django.utils import timezone

from core.models import cron_log_error

from trading.backedns.binance.client import ApiBinance
from trading.bots.strategy_average import BotAverage
from trading.models import MarketMyOrder, MarketBot
from trading.lib import print_debug

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

            # bot.check_market_stop_loss()

            # проверяем статусы открытых ордеров
            print('check statuses open orders')
            orders = MarketMyOrder.open_objects.filter(bot=bot)

            if orders:
                print('check orders', orders)
                for order in orders:
                    tb = BotAverage(bot, order.market)
                    bot_active_pairs += tb.check_order(order)

            markets = bot.get_markets(api)
            print('get_markets', markets)

            for market in markets:

                if bot_active_pairs > bot.max_rank_pairs:
                    continue

                tb = BotAverage(bot, market)

                print('----------------------', market.name)

                # получаем все открытые ордера
                orders = MarketMyOrder.open_objects.filter(market=market, bot=bot)
                print('*** check orders by market', market, orders)

                if orders:
                    for order in orders:
                        bot_active_pairs += tb.check_order(order)
                else:
                    # Проверяем тренд, если рынок в нужном состоянии, выставляем ордер на покупку
                    print('check_trend_buy')
                    trend_buy = tb.check_trend_buy()
                    if trend_buy:
                        # создаем ордер на покупку
                        if tb.create_buy():
                            bot_active_pairs += 1

                time.sleep(10)

            print('----- time.sleep(30) -----')
            time.sleep(30)
