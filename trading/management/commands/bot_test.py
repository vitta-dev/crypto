import math
import time

import numpy
import talib
from django.core.management import BaseCommand
from django.shortcuts import get_object_or_404
from django.utils import timezone

from trading.backedns.bittrex.client import ApiBittrex
from trading.config import TICKINTERVAL_FIVEMIN, TICKINTERVAL_FIFTEENMIN
from trading.models import Market, MarketBot, BotTestOrder
from trading.utils import check_trend_buy, get_chart_data, convert_ticker, check_trend_sell

api = ApiBittrex()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('bot_name', nargs='?')
        parser.add_argument('market_name', nargs='?')

        parser.add_argument('--clear', default='bot', choices=['bot', 'all', ], dest='clear', )

    def handle(self, *args, **options):

        bot_name = options['bot_name']
        market_name = options['market_name']
        clear = options['clear']
        is_open_order = False

        if market_name:
            market = get_object_or_404(Market, name=market_name)
        else:
            market = Market.objects.filter(is_bot=True)[0]

        bot = get_object_or_404(MarketBot, name=bot_name)

        data_clear = {}
        if clear == 'bot':
            data_clear['bot'] = bot
        BotTestOrder.objects.filter(**data_clear).delete()
        print('Delete old data test')

        charts_data = get_chart_data(market, TICKINTERVAL_FIVEMIN)

        macd, macdsignal, macdhist = talib.MACD(
            numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
            fastperiod=bot.macd_fastperiod,
            slowperiod=bot.macd_slowperiod,
            signalperiod=bot.macd_signalperiod)

        ema1 = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                         timeperiod=bot.ema_fastperiod)
        ema2 = talib.MA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                        timeperiod=bot.ema_slowperiod)

        rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                        timeperiod=bot.rsi_timeperiod)

        first_date = timezone.now()
        dates = []

        # if bot.is_ha:
        #     charts_data = get_heikin_ashi(charts_data)

        for i, d in enumerate(charts_data):
            dates.append(d)
            if d < first_date:
                first_date = d
            if not math.isnan(macd[i]):
                charts_data[d]['macd'] = macd[i]
                charts_data[d]['macdsignal'] = macdsignal[i]
                charts_data[d]['macdhist'] = macdhist[i]
            else:
                charts_data[d]['macd'] = 0
                charts_data[d]['macdsignal'] = 0
                charts_data[d]['macdhist'] = 0

            if not math.isnan(ema1[i]):
                charts_data[d]['ema1'] = ema1[i]
            else:
                charts_data[d]['ema1'] = charts_data[d]['close']

            if not math.isnan(ema2[i]):
                charts_data[d]['ema2'] = ema2[i]
            else:
                charts_data[d]['ema2'] = charts_data[d]['close']

            if not math.isnan(rsi[i]):
                charts_data[d]['rsi'] = rsi[i]
            else:
                charts_data[d]['rsi'] = 50

        # tick_intervals = [t.value for t in bot.tick_intervals.all()]
        tick_intervals = bot.get_tick_intervals()

        tick_intervals_charts_data = {}
        for ticker_interval in tick_intervals:
            if ticker_interval == TICKINTERVAL_FIFTEENMIN:
                charts_data = get_chart_data(market, TICKINTERVAL_FIVEMIN)
                charts_data = convert_ticker(charts_data, round_to=15)
            else:
                charts_data = get_chart_data(market, ticker_interval)
            tick_intervals_charts_data[ticker_interval] = charts_data

        for i, d in enumerate(dates):
            print('')
            print('check_trend_buy', d)
            if is_open_order:
                trend_sell = check_trend_sell(market, bot, tick_intervals_charts_data, d)
                if trend_sell:
                    print('============================== TREND SELL =============================')
                    print(charts_data[d])
                    BotTestOrder.objects.create(price=charts_data[d]['open'],
                                                created_at=d,
                                                type=BotTestOrder.Type.SELL,
                                                bot=bot,
                                                market=market,
                                                ticker_data=charts_data[d],
                                                )
                    is_open_order = False
            else:
                trend_buy = check_trend_buy(market, bot, tick_intervals_charts_data, d)
                if trend_buy:
                    print('============================== TREND BUY =============================')
                    print(charts_data[d])
                    BotTestOrder.objects.create(price=charts_data[d]['open'],
                                                created_at=d,
                                                type=BotTestOrder.Type.BUY,
                                                bot=bot,
                                                market=market,
                                                ticker_data=charts_data[d],
                                                )
                    is_open_order = True



