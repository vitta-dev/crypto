import time

from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.binance.client import ApiBinance
from trading.bots.strategy_ut import BotUT
from trading.models import MarketMyOrder, MarketBot

api = ApiBinance()


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
                bot.save(update_fields=['bot_last_run'])
            except MarketBot.DoesNotExist:
                print('Bot "{}" Does Not Exist'.format(bot_name))
                return False

            # проверяем статусы открытых ордеров
            orders = MarketMyOrder.open_objects.filter(bot=bot)
            print('# проверяем статусы открытых ордеров', orders)
            if orders:
                for order in orders:
                    order.refresh_from_db()
                    tb = BotUT(bot, order.market)
                    bot_active_pairs += tb.check_order(order)

            markets = bot.get_markets(api)

            for market in markets:
                tb = BotUT(bot, market)

                if bot_active_pairs > bot.max_rank_pairs:
                    continue

                print('----------------------')
                print(market.name)

                # получаем все открытые ордера
                orders = MarketMyOrder.open_objects.filter(market=market, bot=bot)
                print('open_orders', orders)

                if orders:
                    # проверяем основные ордера
                    main_orders = orders.filter(kind=MarketMyOrder.Kind.MAIN)
                    for order in main_orders:
                        order.refresh_from_db()
                        bot_active_pairs += tb.check_order(order)

                    # # проверяем страховочные
                    # safety_orders = orders.filter(kind=MarketMyOrder.Kind.SAFETY)
                    # for order in safety_orders:
                    #     order.refresh_from_db()
                    #     bot_active_pairs += tb.check_order(order)
                elif not bot.is_block_panic_sell:
                    # Проверяем тренд, если рынок в нужном состоянии, выставляем ордер на покупку
                    trend_buy = tb.check_trend_buy()
                    if trend_buy:
                        # создаем ордер на покупку
                        if tb.create_buy():
                            bot_active_pairs += 1
                        # raise Exception

            print('----- time.sleep(3) -----')
            time.sleep(3)
            # is_bot = False
