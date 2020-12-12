import datetime
import time
from decimal import *

import numpy
import talib
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from trading.backedns.bittrex.config import BEAR_PERC, BULL_PERC, CAN_SPEND, MARKUP, STOCK_FEE
from trading.backedns.bittrex.client import ApiBittrex
from trading.backedns.bittrex.config import ORDER_LIFE_TIME
from trading.config import TICKINTERVAL_HOUR, TICKINTERVAL_FIVEMIN, TICKINTERVAL_ONEMIN, \
    TICKINTERVAL_FIFTEENMIN
from trading.models import Market, MarketMyOrder, MarketBot, MarketBotRank, BotStat, Market
from trading.utils import get_chart_data, create_buy, create_sell, check_order, convert_ticker, check_trend_buy, \
    get_heikin_ashi, check_trend_sell, create_sell_current


class Command(BaseCommand):

    def handle(self, *args, **options):

        # получаем последнюю дату статистики
        try:
            obj = BotStat.objects.latest('date')
            last_stat_date = obj.date

        except BotStat.DoesNotExist:
            # если нет данных берем первую дату из закрытых ордеров
            obj = MarketMyOrder.close_objects.earliest('created_at')
            last_stat_date = obj.created_at.date()

        end_date_stat = datetime.date.today()
        while last_stat_date:
            # получаем все ордера за указаную дату с шагом +1 день
            date_stat = {}
            stat_buy = MarketMyOrder.objects.values('bot', 'market').filter(
                filled_at__year=last_stat_date.year,
                filled_at__month=last_stat_date.month,
                filled_at__day=last_stat_date.day,
                type=MarketMyOrder.Type.BUY
            ).annotate(data_sum=Sum('spent'), data_count=Count('id'))

            for d in stat_buy:
                if d:
                    if d['bot'] not in date_stat:
                        date_stat[d['bot']] = {}

                    if d['market'] not in date_stat[d['bot']]:
                        date_stat[d['bot']][d['market']] = {'buy': 0, 'buy_sum': 0, 'sell': 0, 'sell_sum': 0, }

                    date_stat[d['bot']][d['market']]['buy'] = d['data_count']
                    date_stat[d['bot']][d['market']]['buy_sum'] = d['data_sum']

            stat_sell = MarketMyOrder.objects.values('bot', 'market').filter(
                filled_at__year=last_stat_date.year,
                filled_at__month=last_stat_date.month,
                filled_at__day=last_stat_date.day,
                type=MarketMyOrder.Type.SELL
            ).annotate(data_sum=Sum('spent'), data_count=Count('id'))

            for d in stat_sell:

                if d['bot'] not in date_stat:
                    date_stat[d['bot']] = {}

                if d['market'] not in date_stat[d['bot']]:
                    date_stat[d['bot']][d['market']] = {'buy': 0, 'buy_sum': 0, 'sell': 0, 'sell_sum': 0}

                date_stat[d['bot']][d['market']]['sell'] = d['data_count']
                date_stat[d['bot']][d['market']]['sell_sum'] = d['data_sum']

            # сохраняем статистику
            for bot_id, data_bot in date_stat.items():
                bot = MarketBot.objects.get(id=bot_id)
                for market_id, data_market in data_bot.items():
                    market = Market.objects.get(id=market_id)
                    try:
                        stat = BotStat.objects.get(
                            market=market, bot=bot, date=last_stat_date,
                        )
                    except BotStat.DoesNotExist:
                        stat = BotStat.objects.create(
                            market=market, bot=bot, date=last_stat_date,
                        )
                        stat.buy = data_market['buy']
                        stat.buy_sum = data_market['buy_sum']
                        stat.sell = data_market['sell']
                        stat.sell_sum = data_market['sell_sum']
                        stat.save()

            last_stat_date = last_stat_date + datetime.timedelta(days=1)
            if last_stat_date > end_date_stat:
                last_stat_date = False
