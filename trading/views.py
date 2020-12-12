# -*- coding:utf-8 -*-
import datetime
import math
from decimal import *

import numpy
import talib
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from trading.config import TICKINTERVAL_FIVEMIN
from trading.filters import MACDFilter
from trading.models import Market, MarketMyOrder, MarketBot, BotTestOrder
from trading.utils import get_chart_data, convert_ticker, get_heikin_ashi, TechnicalAnalysis


@staff_member_required
def charts(request, market_name=None, bot_name=None):
    """
        графики
        :param market_id:
        :param request:
    """
    base_tpl = 'admin/base.html'
    tpl = 'admin/director/dashboard.html'

    if market_name:
        market = Market.objects.get(name=market_name)
    else:
        market = Market.objects.filter(is_bot=True)[0]

    ta = TechnicalAnalysis(market)

    if bot_name:
        bot = get_object_or_404(MarketBot, name=bot_name)
    else:
        bot = MarketBot.objects.all()[0]
    api = bot.get_api()
    # charts_data = get_chart_data(market, TICKINTERVAL_THIRTYMIN)
    # group_to_periods = ["mm", "5mm", "30mm"]
    market_name = market.get_market_name(bot.exchange.code)
    tick_intervals = bot.get_tick_intervals()
    tick_interval = tick_intervals[0]
    charts_data = get_chart_data(market_name, api, tick_interval)

    group_to_periods = ["mm", "5mm"]
    # charts_data = get_chart_data(market, TICKINTERVAL_HOUR)
    # group_to_periods = ["mm", "5mm", "1hh"]
    # charts_data_macd = get_chart_data(market, 24)

    if settings.DEBUG and False:
        # for ch in charts_data:
        #     print(ch)
        #     print(charts_data[ch])

        # charts_data = convert_ticker(charts_data, round_to=15)
        charts_data = convert_ticker(charts_data, round_to_hours=4)
        group_to_periods = ["mm", "5mm", "4hh"]
        # charts_data = convert_ticker(charts_data, round_to=30, round_to_hours=None)
        # charts_data = convert_ticker(charts_data, round_to=60)

    macd_filter = MACDFilter(request.POST)

    macd, macdsignal, macdhist = talib.MACD(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                                            fastperiod=bot.macd_fastperiod,
                                            slowperiod=bot.macd_slowperiod,
                                            signalperiod=bot.macd_signalperiod)

    # WaveTrend Oscillator
    n1, n2, period = 10, 21, 60
    ob = 57  # "Over Bought Level"
    os = -57  # "Over Sold Level"

    ema1 = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                     timeperiod=bot.ema_fastperiod)
    ema2 = talib.MA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                    timeperiod=bot.ema_slowperiod)

    sma_fast = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                         timeperiod=bot.sma_fastperiod)
    sma_slow = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                         timeperiod=bot.sma_slowperiod)

    slowk, slowd = talib.STOCH(
        numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
        fastk_period=bot.stochastic_fastk_period,
        slowk_period=bot.stochastic_slowk_period, slowk_matype=0,
        slowd_period=bot.stochastic_slowd_period, slowd_matype=0)

    adx = talib.ADX(
        numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
        timeperiod=bot.adx_timeperiod)

    rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                    timeperiod=bot.rsi_timeperiod)

    print('charts_data', charts_data)
    if bot.is_ha:
        charts_data = get_heikin_ashi(charts_data, market)
        print('********************************* HA *****************************')
        print('charts_data', charts_data)

    # first_date = timezone.now()
    first_date = datetime.datetime.now()
    dates = []
    dojo_list = []
    sword_list = []
    hummer_list = []

    for i, d in enumerate(charts_data):
        dates.append(d)
        if d < first_date:
            first_date = d

        if bot.is_dodge:
            if ta.is_dodge(charts_data[d]):
                print('dojo ', d)
                dojo_list.append(d)
        # if bot.is_hummer:
        if ta.is_hummer(charts_data[d]):
            hummer_list.append(d)
        # if bot.is_sword:
        if ta.is_sword(charts_data[d]):
            sword_list.append(d)

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

        if not math.isnan(sma_fast[i]):
            charts_data[d]['sma_fast'] = sma_fast[i]
        else:
            charts_data[d]['sma_fast'] = charts_data[d]['close']

        if not math.isnan(sma_slow[i]):
            charts_data[d]['sma_slow'] = sma_slow[i]
        else:
            charts_data[d]['sma_slow'] = charts_data[d]['close']

        if not math.isnan(rsi[i]):
            charts_data[d]['rsi'] = rsi[i]
        else:
            charts_data[d]['rsi'] = 50

        if not math.isnan(adx[i]):
            charts_data[d]['adx'] = adx[i]
        else:
            charts_data[d]['adx'] = 30

        if not math.isnan(slowk[i]):
            charts_data[d]['slowk'] = slowk[i]
        else:
            charts_data[d]['slowk'] = 30

        if not math.isnan(slowd[i]):
            charts_data[d]['slowd'] = slowd[i]
        else:
            charts_data[d]['slowd'] = 30

    orders = MarketMyOrder.objects.filter(market=market, bot=bot).exclude(status=MarketMyOrder.Status.CANCELED)
    # get_marketsummary

    context = {'base_tpl': base_tpl,
               'market': market,
               'charts_data': charts_data,
               'first_date': first_date,
               'macd': macd,
               'macdsignal': macdsignal,
               'macdhist': macdhist,
               'orders': orders,
               'dates': dates,
               'macd_filter': macd_filter,
               "group_to_periods": group_to_periods,
               'dojo_list': dojo_list,
               'sword_list': sword_list,
               'hummer_list': hummer_list,
               'bot': bot,
               'tick_interval': tick_interval,
               }

    return render(request, 'check_charts.html', context)


@staff_member_required
def stats(request, bot_name='averaged_price'):
    """
        графики
        :param bot_name:
        :param request:
    """
    base_tpl = 'admin/base.html'

    if bot_name:
        bot = get_object_or_404(MarketBot, name=bot_name)
        data = {'bot': bot}
    else:
        bot = None
        data = {}

    orders = MarketMyOrder.objects.filter(**data)

    stats = {}
    for order in orders:
        if order.market.base_currency.name not in stats:
            stats[order.market.base_currency.name] = {
                'total_buy': 0,
                'total_sell': 0,
                'total_sum_buy': Decimal(0),
                'total_sum_sell': Decimal(0),
                'cancel_buy': 0,
                'cancel_sell': 0,
                'open_sum_sell': Decimal(0),
                'open_sell': 0,
                'open_sum_buy': Decimal(0),
                'open_buy': 0,
                'close_sum_buy': Decimal(0),
                'close_buy': 0,
                'filled_sum_buy': Decimal(0),
                'filled_buy': 0,
                'filled_sum_sell': Decimal(0),
                'filled_sell': 0,
                'part_filled_sum_buy': Decimal(0),
                'part_filled_buy': 0,
                'part_filled_sum_sell': Decimal(0),
                'part_filled_sell': 0,
                'profit': Decimal(0),
                'per_profit': Decimal(0),
                'pairs': {},
                'total_pair': 0,
                'start_sum': 0,
            }

    # stats = {
    #     'BTC': {
    #         'total_buy': 0,
    #         'total_sell': 0,
    #         'total_sum_buy': Decimal(0),
    #         'total_sum_sell': Decimal(0),
    #         'cancel_buy': 0,
    #         'cancel_sell': 0,
    #         'open_sum_sell': Decimal(0),
    #         'open_sell': 0,
    #         'open_sum_buy': Decimal(0),
    #         'open_buy': 0,
    #         'close_sum_buy': Decimal(0),
    #         'close_buy': 0,
    #         'filled_sum_buy': Decimal(0),
    #         'filled_buy': 0,
    #         'filled_sum_sell': Decimal(0),
    #         'filled_sell': 0,
    #         'part_filled_sum_buy': Decimal(0),
    #         'part_filled_buy': 0,
    #         'part_filled_sum_sell': Decimal(0),
    #         'part_filled_sell': 0,
    #         'profit': Decimal(0),
    #         'per_profit': Decimal(0),
    #         'pairs': {},
    #         'total_pair': 0,
    #         'start_sum': 0,
    #     },
    #     'USDT': {
    #         'total_buy': 0,
    #         'total_sell': 0,
    #         'total_sum_buy': Decimal(0),
    #         'total_sum_sell': Decimal(0),
    #         'cancel_buy': 0,
    #         'cancel_sell': 0,
    #         'open_sum_sell': Decimal(0),
    #         'open_sell': 0,
    #         'open_sum_buy': Decimal(0),
    #         'open_buy': 0,
    #         'filled_sum_buy': Decimal(0),
    #         'filled_buy': 0,
    #         'filled_sum_sell': Decimal(0),
    #         'filled_sell': 0,
    #         'part_filled_sum_buy': Decimal(0),
    #         'part_filled_buy': 0,
    #         'part_filled_sum_sell': Decimal(0),
    #         'part_filled_sell': 0,
    #         'close_sum_buy': Decimal(0),
    #         'close_buy': 0,
    #         'profit': Decimal(0),
    #         'per_profit': Decimal(0),
    #         'pairs': {},
    #         'total_pair': 0,
    #         'start_sum': Decimal(27.49431594),
    #     },
    # }
    for order in orders:
        if order.market.name not in stats[order.market.base_currency.name]['pairs']:
            stats[order.market.base_currency.name]['total_pair'] += 1
            # stats[order.market.base_currency.name]['start_sum'] += 2
            stats[order.market.base_currency.name]['pairs'][order.market.name] = {
                'id': order.market.id,
                'name': order.market.name,
                'total_buy': 0,
                'cancel_buy': 0,
                'cancel_sell': 0,
                'open_sum_sell': Decimal(0),
                'open_sell': 0,
                'open_buy': 0,
                'open_sum_buy': Decimal(0),
                'filled_sum_buy': Decimal(0),
                'filled_buy': 0,
                'filled_sum_sell': Decimal(0),
                'filled_sell': 0,
                'part_filled_sum_buy': Decimal(0),
                'part_filled_buy': 0,
                'part_filled_sum_sell': Decimal(0),
                'part_filled_sell': 0,
                'close_sum_buy': Decimal(0),
                'total_sum_sell': Decimal(0),
                'total_sum_buy': Decimal(0),
                'total_sell': 0,
                'profit': Decimal(0),
                'per_profit': Decimal(0),
            }
        if order.type == MarketMyOrder.Type.BUY:
            if order.status == MarketMyOrder.Status.CANCELED:
                stats[order.market.base_currency.name]['cancel_buy'] += 1
            else:
                if order.status == MarketMyOrder.Status.PART_FILLED:
                    stats[order.market.base_currency.name]['part_filled_buy'] += 1

                if order.status in [MarketMyOrder.Status.FILLED, MarketMyOrder.Status.CLOSED]:
                    stats[order.market.base_currency.name]['total_buy'] += 1
                    stats[order.market.base_currency.name]['total_sum_buy'] += order.price * order.amount

                    stats[order.market.base_currency.name]['pairs'][order.market.name]['total_buy'] += 1
                    stats[order.market.base_currency.name]['pairs'][order.market.name]['total_sum_buy'] += order.price * order.amount
                if order.status in [MarketMyOrder.Status.CLOSED]:
                    stats[order.market.base_currency.name]['pairs'][order.market.name]['close_sum_buy'] += order.price * order.amount
                    stats[order.market.base_currency.name]['close_sum_buy'] += order.price * order.amount
                    stats[order.market.base_currency.name]['close_buy'] += 1
                if order.status in [MarketMyOrder.Status.OPEN]:
                    stats[order.market.base_currency.name]['pairs'][order.market.name]['open_sum_buy'] += order.price * order.amount
                    stats[order.market.base_currency.name]['pairs'][order.market.name]['open_buy'] += 1
                    stats[order.market.base_currency.name]['open_sum_buy'] += order.price * order.amount
                    stats[order.market.base_currency.name]['open_buy'] += 1

        if order.type == MarketMyOrder.Type.SELL:
            if order.status == MarketMyOrder.Status.CANCELED:
                stats[order.market.base_currency.name]['cancel_sell'] += 1
            else:
                if order.status == MarketMyOrder.Status.PART_FILLED:
                    stats[order.market.base_currency.name]['part_filled_sell'] += 1
                if order.status in [MarketMyOrder.Status.FILLED, MarketMyOrder.Status.CLOSED]:
                    stats[order.market.base_currency.name]['total_sell'] += 1
                    stats[order.market.base_currency.name]['total_sum_sell'] += order.price * order.amount

                    stats[order.market.base_currency.name]['pairs'][order.market.name]['total_sell'] += 1
                    stats[order.market.base_currency.name]['pairs'][order.market.name]['total_sum_sell'] += order.price * order.amount

                if order.status in [MarketMyOrder.Status.OPEN]:
                    stats[order.market.base_currency.name]['open_sum_sell'] += order.price * order.amount
                    stats[order.market.base_currency.name]['open_sell'] += 1
                # if order.filled_at:
                #     stats[order.market.base_currency.name]['pairs'][order.market.name]['total_sum_sell'] += order.price * order.amount
                #     stats[order.market.base_currency.name]['pairs'][order.market.name]['total_sell'] += 1


        # stats[order.market.base_currency.name]['profit'] = stats[order.market.base_currency.name]['total_sum_sell'] - stats[order.market.base_currency.name]['total_sum_buy']

    for p, data in stats.items():
        for n, s in data['pairs'].items():
            s['profit'] = s['total_sum_sell'] - s['close_sum_buy']
            if s['close_sum_buy'] > 0:
                s['per_profit'] = (s['total_sum_sell']-s['close_sum_buy'])/s['close_sum_buy']*100
            data['profit'] += s['profit']
        # data['per_profit'] = (data['profit'] + data['start_sum']) / data['start_sum'] * 100
        if data['start_sum'] > 0:
            data['per_profit'] = data['profit']*100/data['start_sum']

    print('profit', data['profit'])
    print('per profit', data['per_profit'])
    print('start_sum', data['start_sum'])
    context = {'base_tpl': base_tpl,
               'stats': stats,
               'bot': bot,
               }

    return render(request, 'stats.html', context)


@staff_member_required
def check_bot_strategy(request, bot_name, market_name=None):
    """
        графики
        :param bot_name:
        :param market_name:
        :param request:
    """
    base_tpl = 'admin/base.html'

    if market_name:
        market = get_object_or_404(Market, name=market_name)
    else:
        market = Market.objects.filter(is_bot=True)[0]

    bot = get_object_or_404(MarketBot, name=bot_name)

    ta = TechnicalAnalysis(market)

    # charts_data = get_chart_data(market, TICKINTERVAL_FIVEMIN)
    api = bot.get_api()
    charts_data = get_chart_data(bot.market_name, api)

    group_to_periods = ["mm", "5mm", ]

    macd_filter = MACDFilter(request.POST)

    macd, macdsignal, macdhist = talib.MACD(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                                            fastperiod=bot.macd_fastperiod,
                                            slowperiod=bot.macd_slowperiod,
                                            signalperiod=bot.macd_signalperiod)

    ema1 = talib.EMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                     timeperiod=bot.ema_fastperiod)
    ema2 = talib.MA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                    timeperiod=bot.ema_slowperiod)

    sma_fast = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                         timeperiod=bot.sma_fastperiod)
    sma_slow = talib.SMA(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                        timeperiod=bot.sma_slowperiod)

    rsi = talib.RSI(numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
                    timeperiod=bot.rsi_timeperiod)

    adx = talib.ADX(
        numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
        timeperiod=bot.adx_timeperiod)

    slowk, slowd = talib.STOCH(
        numpy.asarray([charts_data[item]['high'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['low'] for item in sorted(charts_data)]),
        numpy.asarray([charts_data[item]['close'] for item in sorted(charts_data)]),
        fastk_period=bot.stochastic_fastk_period,
        slowk_period=bot.stochastic_slowk_period, slowk_matype=0,
        slowd_period=bot.stochastic_slowd_period, slowd_matype=0)

    if bot.is_ha:
        charts_data = get_heikin_ashi(charts_data, market)

    first_date = timezone.now()
    dates = []
    dojo_list = []
    sword_list = []
    hummer_list = []
    for i, d in enumerate(charts_data):
        dates.append(d)
        if d < first_date:
            first_date = d
        if bot.is_dodge:
            if ta.is_dodge(charts_data[d]):
                print('dojo ', d)
                dojo_list.append(d)
        # if bot.is_hummer:
        if ta.is_hummer(charts_data[d]):
            hummer_list.append(d)
        # if bot.is_sword:
        if ta.is_sword(charts_data[d]):
            sword_list.append(d)

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

        if not math.isnan(sma_fast[i]):
            charts_data[d]['sma_fast'] = sma_fast[i]
        else:
            charts_data[d]['sma_fast'] = charts_data[d]['close']

        if not math.isnan(sma_slow[i]):
            charts_data[d]['sma_slow'] = sma_slow[i]
        else:
            charts_data[d]['sma_slow'] = charts_data[d]['close']

        if not math.isnan(rsi[i]):
            charts_data[d]['rsi'] = rsi[i]
        else:
            charts_data[d]['rsi'] = 50

        if not math.isnan(adx[i]):
            charts_data[d]['adx'] = adx[i]
        else:
            charts_data[d]['adx'] = 30

        if not math.isnan(slowk[i]):
            charts_data[d]['slowk'] = slowk[i]
        else:
            charts_data[d]['slowk'] = 30

        if not math.isnan(slowd[i]):
            charts_data[d]['slowd'] = slowd[i]
        else:
            charts_data[d]['slowd'] = 30

    orders = BotTestOrder.objects.filter(bot=bot, market=market)

    context = {'base_tpl': base_tpl,
               'market': market,
               'charts_data': charts_data,
               'first_date': first_date,
               'macd': macd,
               'macdsignal': macdsignal,
               'macdhist': macdhist,
               'orders': orders,
               'dates': dates,
               'macd_filter': macd_filter,
               "group_to_periods": group_to_periods,
               'dojo_list': dojo_list,
               'sword_list': sword_list,
               'hummer_list': hummer_list,
               'bot': bot,
               }

    return render(request, 'check_charts.html', context)
