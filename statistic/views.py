# -*- coding:utf-8 -*-
import math
from decimal import *

import numpy
import talib
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from trading.config import TICKINTERVAL_FIVEMIN, TICKINTERVAL_FIFTEENMIN
from trading.filters import MACDFilter
from trading.models import Market, MarketMyOrder, MarketBot, BotTestOrder, BotStat
from trading.utils import get_chart_data, convert_ticker, get_heikin_ashi, TechnicalAnalysis
from trading.backedns.bittrex.client import ApiBittrex
from trading.backedns.binance.client import ApiBinance
from statistic.forms import OrderFilter, paginate


@staff_member_required
def index(request, exchange_name='binance'):
    """

    """
    base_tpl = 'admin/base.html'
    total = 0

    if exchange_name == 'bittrex':
        api = ApiBittrex()
        exchange = 'Bittrex'
        tpl = 'statistic/index.html'
        balances = api.get_balances()
    else:
        api = ApiBinance()
        exchange = 'Binance'
        tpl = 'statistic/index_binance.html'
        balances_all = api.get_balances()
        balances = [x for x in balances_all if x['free'] != '0.00000000' or x['locked'] != '0.00000000']

        for b in balances:
            b['free'] = Decimal(b['free'])
            b['locked'] = Decimal(b['locked'])
            b['total'] = b['free'] + b['locked']

            price_info = api.get_price(b['asset'], b['total'])
            b['price'] = price_info['price']
            b['USDT'] = price_info['USDT']

            total += b['USDT']

    orders = api.get_open_orders()

    context = {
        'base_tpl': base_tpl,
        'balances': balances,
        'orders': orders,
        'exchange': exchange,
        'total': total
    }

    return render(request, tpl, context)


@staff_member_required
def orders(request, exchange_name='binance', market_name='BTH-ETH'):
    """Список ордеров на бирже"""
    base_tpl = 'admin/base.html'
    market = get_object_or_404(Market, name=market_name)

    if exchange_name == 'bittrex':
        api = ApiBittrex()
        exchange = 'Bittrex'
        tpl = 'statistic/index.html'
        orders = []
    else:
        api = ApiBinance()
        exchange = 'Binance'
        tpl = 'statistic/orders_binance.html'
        res_orders = api.get_order_history(market.get_market_name(exchange_name))

        orders = sorted(res_orders, key=lambda k: k['time'], reverse=True)

    context = {
        'base_tpl': base_tpl,
        'orders': orders,
        'exchange': exchange,
        'market': market,
    }

    return render(request, tpl, context)


@staff_member_required
def stat_by_period(request):
    """

    """
    base_tpl = 'admin/base.html'
    tpl = 'statistic/stat_by_date.html'

    stats = BotStat.objects.filter()

    context = {
        'base_tpl': base_tpl,
        'stats': stats,
    }

    return render(request, tpl, context)


@staff_member_required
def list_orders(request):
    """
        список ордеров
        :param request:
    """
    base_tpl = 'admin/base.html'

    orders_filter = OrderFilter(request.user, request.GET)

    orders = orders_filter.apply_filter().order_by('-id')
    orders = paginate(orders, request.GET.get('page'), orders_filter.get_items_per_page())
    from trading.templatetags.utils_charts import progress_price
    buy_price = 0
    sell_price = 100
    current_price = 35
    d = progress_price(buy_price, sell_price, current_price)
    print('**d', d)
    context = {
        'base_tpl': base_tpl,
        'orders': orders,
        'orders_filter': orders_filter,
    }

    return render(request, 'statistic/order_list.html', context)
