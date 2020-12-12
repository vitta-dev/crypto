import time

from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.bittrex.client import ApiBittrex
from trading.bots.strategy_average import BotAverage
from trading.models import MarketMyOrder, MarketBot

api = ApiBittrex()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('bot_name', nargs='?')

    def handle(self, *args, **options):

        bot_name = options['bot_name']

        is_bot = True

        while is_bot:

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
            orders = MarketMyOrder.open_objects.filter(bot=bot)

            if orders:
                for order in orders:
                    order.refresh_from_db()
                    tb = BotAverage(bot, order.market)
                    bot_active_pairs += tb.check_order(order)

            markets = bot.get_markets(api)

            for market in markets:

                if bot_active_pairs > bot.max_rank_pairs:
                    continue

                tb = BotAverage(bot, market)

                print('----------------------')
                print(market.name)

                # получаем все открытые ордера
                orders = MarketMyOrder.open_objects.filter(market=market, bot=bot)
                print('open_orders', orders)

                if orders:
                    for order in orders:
                        order.refresh_from_db()
                        bot_active_pairs += tb.check_order(order)
                else:
                    # Проверяем тренд, если рынок в нужном состоянии, выставляем ордер на покупку
                    trend_buy = tb.check_trend_buy()
                    if trend_buy:
                        # создаем ордер на покупку
                        if tb.create_buy():
                            bot_active_pairs += 1

            print('----- time.sleep(3) -----')
            time.sleep(3)
