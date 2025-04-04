# -*- coding: utf-8 -*-
from decimal import *

from django.contrib import admin
from django.urls import reverse
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from trading.models import (
    BotStat, BotTestOrder, CheckMarketFilter, Currency, ExchangeCurrencyStatistic, Market, MarketBot, MarketBotRank,
    MarketMyOrder, MarketOrderLog, MarketSettings, MarketSummary, MarketTickInterval, HistoryBalance
)
from trading.utils import add_stock_fee


@admin.register(CheckMarketFilter)
class CheckMarketFilterAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'created_at', 'maxPrice', 'minPrice', 'tickSize', 'p_avgPriceMins', 'multiplierUp',
                    'multiplierDown', 'maxQty', 'minQty', 'stepSize', 'minNotional', 'n_avgPriceMins', 'applyToMarket',
                    'limit', 'maxNumAlgoOrders')


@admin.register(ExchangeCurrencyStatistic)
class ExchangeCurrencyStatisticAdmin(admin.ModelAdmin):
    list_display = ('currency', 'created_at', 'order', 'free', 'locked', 'total', 'operation', 'price', 'usdt')
    list_filter = ['operation', ]
    search_fields = ['currency__name', ]

    @admin.display(
        description='Total'
    )
    def total(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """
        total = obj.free + obj.locked
        # str_format = Decimal(total).quantize(Decimal('.00000000'))

        return total



@admin.register(MarketTickInterval)
class MarketTickIntervalAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'value_binance')


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_long', 'coin_type', 'tx_fee', 'min_confirmation', 'is_active', 'is_base')

    fieldsets = (
        (None, {
            'fields': ('coin_type', 'name', 'name_long', 'is_active')
        }),

        ('Коэффициенты', {
            'fields': ('coef_level', 'coef_all_candle_min', 'coef_all_candle_mid', 'coef_all_candle_max',
                       'coef_high_low_min', 'coef_high_low_max', 'sword_multilier', 'hummer_multiplier'),
        }),

    )

    list_filter = ['coin_type', 'is_active', 'is_base']
    # list_editable = ['is_base']
    search_fields = ['name', ]


class MarketSettingsInline(admin.TabularInline):
    fields = ['exchange', 'settings', 'is_active', ]
    readonly_fields = ['exchange', 'is_active', 'settings']
    model = MarketSettings
    extra = 0

    @admin.display(
        description='settings'
    )
    def settings_info(self, obj):
        """
        Settings
        :param obj:
        :return:
        """
        # return '<div style="width: 500px;"><div class="col-md-12"><pre>{}</pre></div></div>'.format(obj.settings)
        return format_html('<pre> {} <br></pre>'.format(obj.settings))
        # return '<code>{}</code>'.format(obj.settings)
        # return '{}'.format(obj.settings)



@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'min_trade_size', 'is_active', 'is_active_binance', 'is_bot', 'created_at',)
    fields = ['name', 'base_currency', 'market_currency', 'min_trade_size', 'is_active',  'is_active_binance', 'created_at', 'updated_at']
    list_filter = ['is_active', 'is_bot', 'base_currency']
    # list_editable = ['is_bot', ]
    search_fields = ['name', ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MarketSettingsInline]


@admin.register(BotStat)
class BotStatAdmin(admin.ModelAdmin):
    list_display = ('date', 'bot', 'market', 'buy', 'buy_sum', 'sell', 'sell_sum')
    fields = ['date', 'bot', 'market', 'buy', 'buy_sum', 'sell', 'sell_sum']
    list_filter = ['bot', 'market']
    search_fields = ['market__name', ]


@admin.register(MarketSummary)
class MarketSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'market', 'rank', 'updated_at', 'high', 'low', 'volume', 'last', 'base_volume', 'bid', 'ask', 'open_by_orders',
                    'open_sell_orders', 'prev_day')
    # fields = ['name', 'base_currency', 'market_currency', 'min_trade_size', 'is_active']
    # list_filter = ['is_active']
    search_fields = ['market__name', ]
    date_hierarchy = 'created_at'


class MarketOrderLogFormSet(BaseInlineFormSet):
    def get_queryset(self):
        qs = super(MarketOrderLogFormSet, self).get_queryset()
        return qs[:50]


class MarketOrderLogInline(admin.TabularInline):
    fields = ['created_at', 'type', 'tickers', 'max_price', 'bot_data_display']
    readonly_fields = ['created_at', 'type', 'tickers', 'bot_data_display', 'max_price']
    model = MarketOrderLog
    extra = 0
    formset = MarketOrderLogFormSet

    @admin.display(
        description='Ticker data'
    )
    def tickers(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """

        str_format = ''
        if obj.ticker_data:
            for key, val in obj.ticker_data.items():
                try:
                    str_format += format_html('{}: {}<br>', key, Decimal(val).quantize(Decimal('.00000000')))
                except InvalidOperation:
                    str_format += format_html('{}: {}<br>', key, val)

        return format_html(str_format)


    @admin.display(
        description='Bot data'
    )
    def bot_data_display(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """

        str_format = ''
        if obj.bot_data:
            for key, val in obj.bot_data.items():
                try:
                    str_format += format_html('{}: {}<br>', key, Decimal(val).quantize(Decimal('.00000000')))
                except InvalidOperation:
                    str_format += format_html('{}: {}<br>', key, val)

        return format_html(str_format)



@admin.register(MarketMyOrder)
class MarketMyOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'kind', 'status', 'created_at', 'filled_at', 'cancelled_at', 'charts',
                    'format_price', 'format_amount', 'format_spent', 'format_commission', 'profit', 'wait_price',
                    'from_order',
                    'is_close', 'bot', 'tickers', 'is_stop_loss', 'max_price')
    readonly_fields = ['id', 'type', 'created_at', 'filled_at', 'cancelled_at', 'charts',
                       'format_price', 'price', 'format_amount', 'amount', 'format_spent', 'format_commission', 'spent',
                       'test_spent', 'fee', 'profit', 'wait_price',  'from_order',
                       'bot', 'tickers', 'is_stop_loss', 'max_price', 'ticker_data', 'uuid', 'is_test',
                       'market', 'commission',
                       'get_order_result', 'order_info'
                       ]
    fieldsets = (
        (None, {
            'fields': (('uuid', 'ext_id', 'type', 'status', 'is_close', 'is_stop_loss', 'bot', 'charts'), )
        }),
        (None, {
            'fields': (('created_at', 'filled_at', 'cancelled_at'), )
        }),
        (None, {
            'fields': (('price', 'amount', 'spent', 'commission', ),
                       ('tickers', 'order_info', ), )
        }),

        (None, {
            'fields': (('wait_price', 'profit', ),)
        }),
    )
    list_filter = ['kind', 'type', 'is_close', 'status', 'bot', 'is_stop_loss']
    search_fields = ['market__name', 'id', 'from_order__id']
    date_hierarchy = 'created_at'
    inlines = [MarketOrderLogInline]

    @admin.display(
        description='Price',
        ordering='price',
    )
    def format_price(self, obj):

        return ("%0.8f" % obj.price).rstrip('0').rstrip('.')


    @admin.display(
        description='amount',
        ordering='amount',
    )
    def format_amount(self, obj):

        return ("%0.8f" % obj.amount).rstrip('0').rstrip('.')


    @admin.display(
        description='spent',
        ordering='spent',
    )
    def format_spent(self, obj):

        return ("%0.8f" % obj.spent).rstrip('0').rstrip('.')


    @admin.display(
        description='commission',
        ordering='commission',
    )
    def format_commission(self, obj):
        if not obj.commission:
            return '--'

        return ("%0.8f" % obj.commission).rstrip('0').rstrip('.')


    @admin.display(
        description='Пара'
    )
    def charts(self, obj):
        """
        Список менеджеров проекта
        :param obj:
        :return:
        """

        str_format = '<a href="{}" target="_blank">{}</a>'
        return format_html(str_format, reverse('trading:chart-market-bot', args=(obj.market.name, obj.bot.name)), obj.market.name)


    @admin.display(
        description='Ticker data'
    )
    def tickers(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """

        str_format = ''
        if obj.ticker_data:
            for key, val in obj.ticker_data.items():
                try:
                    str_format += format_html('{}: {}<br>', key, "%0.8f" % Decimal(val).quantize(Decimal('.00000000')))
                except InvalidOperation:
                    str_format += format_html('{}: {}<br>', key, val)

        return format_html(str_format)


    @admin.display(
        description='Get Order Result'
    )
    def order_info(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """

        str_format = ''

        if obj.get_order_result:
            kkk = obj.get_order_result.items()
            for key, val in obj.get_order_result.items():
                if val:
                    try:
                        str_format += format_html('{}: {}<br>', key, "%0.8f" % Decimal(val).quantize(Decimal('.00000000')))
                    except (InvalidOperation, TypeError):
                        str_format += format_html('{}: {}<br>', key, val)
                else:
                    str_format += format_html('{}: None<br>', key,)

        return format_html(str_format)


    @admin.display(
        description='Max Price'
    )
    def max_price(self, obj):
        """
        max_price
        :param obj:
        :return:
        """

        if obj.type == obj.Type.BUY and obj.status == obj.Status.FILLED:
            market_rank = obj.bot.get_market_rank(obj.market)

            if market_rank:
                if market_rank.max_price > 0:
                    per = 100 * obj.price / market_rank.max_price - 100
                    try:
                        max_price = market_rank.max_price.quantize(Decimal('.00000000'))
                    except InvalidOperation:
                        max_price = market_rank.max_price
                    try:
                        per = per.quantize(Decimal('.00'))
                    except InvalidOperation:
                        pass
                    return format_html('{} - {}%', "%0.8f" % max_price, "%0.8f" % per)
        return '--'


    @admin.display(
        description='Wait Price'
    )
    def wait_price(self, obj):
        """
        max_price
        :param obj:
        :return:
        """
        str_format = ''

        if obj.type == obj.Type.BUY:
            wp = add_stock_fee(obj.price + obj.price * obj.bot.trailing_cost_up / 100)
            try:
                wp = wp.quantize(Decimal('.00000000'))
            except InvalidOperation:
                pass
            str_format += format_html('{}', "%0.8f" % wp)

        market_rank = obj.bot.get_market_rank(obj.market)

        if market_rank and market_rank.ticker_data:
            str_format += '<br>---------<br>'
            for key, val in market_rank.ticker_data.items():
                try:
                    s = "%0.8f" % Decimal(val).quantize(Decimal('.00000000'))
                except InvalidOperation:
                    s = "{}".format(val)

                str_format += format_html('{}: {}<br>', key, s)

        if market_rank and market_rank.trailing_price:
            str_format += '<br>---------<br>'
            str_format += '<br>trailing_price: {}'.format("%0.8f" % market_rank.trailing_price)

        return format_html(str_format)


    @admin.display(
        description='Current Data'
    )
    def current_data(self, obj):
        """
        max_price
        :param obj:
        :return:
        """

        market_rank = obj.bot.get_market_rank(obj.market)

        str_format = ''
        if market_rank.ticker_data:
            for key, val in market_rank.ticker_data.items():
                try:
                    str_format += format_html('{}: {}<br>', key, "%0.8f" % Decimal(val).quantize(Decimal('.00000000')))
                except InvalidOperation:
                    str_format += format_html('{}: {}<br>', key, "%0.8f" % val)

        return format_html(str_format)


    @admin.display(
        description='Profit'
    )
    def profit(self, obj):
        """
        :param obj:
        :return:
        """

        str_format = ''

        if obj.type == obj.Type.SELL and obj.from_order and obj.status == obj.Status.FILLED:
            print('---------------- ptofit -------------------')
            print(obj)
            spent_buy, spent_sell = obj.get_spent()
            diff = obj.get_profit()
            per = obj.get_profit_percent()

            if diff > 0:
                c = 'green'
            elif diff < 0:
                c = 'red'
            else:
                c = 'gray'

            str_format = format_html('b: {}<br>s: {}<br><span style="color:{}">{} - {}%</span>',
                                     "%0.8f" % spent_buy,
                                     "%0.8f" % spent_sell, c,
                                     "%0.8f" % diff,
                                     "%0.2f" % per)

        return str_format



@admin.register(MarketBotRank)
class MarketBotRankAdmin(admin.ModelAdmin):
    list_display = ('market', 'bot', 'rank', 'max_price', 'is_block_trade', 'block_trade_at')
    fields = ['market', 'bot', 'rank', 'max_price', 'is_block_trade', 'block_trade_at']
    list_filter = ['is_block_trade', 'bot']
    search_fields = ['market__name', ]
    readonly_fields = ['created_at', 'updated_at', 'market', 'rank',  'max_price', 'block_trade_at']


class MarketBotRankInline(admin.TabularInline):
    fields = ['market', 'rank', 'max_price', 'is_block_trade', 'block_trade_at']
    readonly_fields = ['market', 'rank',  'max_price', 'block_trade_at']
    model = MarketBotRank
    extra = 0


@admin.register(MarketBot)
class MarketBotAdmin(admin.ModelAdmin):
    change_form_template = 'admin/bot_form_change.html'
    save_as = True
    list_display = ['name', 'exchange', 'is_test', 'bot_last_run', 'max_spend', 'markup', 'order_life_time',
                    'test_bot', 'stat_bot']

    readonly_fields = ['block_panic_sell_at']
    filter_horizontal = ['tick_intervals', 'markets']
    fieldsets = (
        (None, {
            'fields': (
                'name', 'exchange', 'is_test', 'is_ha',
                ('average_safety_start_order_amount', 'max_spend', 'markup', 'order_life_time'),
                ('tick_intervals',),
                ('markets',),
                ('is_green', 'is_dodge', 'is_hummer', 'is_sword', 'is_sword_or_hummer', 'is_simple', 'is_fat'),
                ('is_min_value', 'min_value',),
                ('is_compare_value',),
                ('is_ratio_open_close', 'ratio_open_close'),
            )
        }),

        ('UT BOT', {
            'fields': (('ut_sensitivity', 'ut_atr_period'), )
        }),
        ('Panic Sell', {
            'fields': (('is_block_panic_sell', 'block_panic_sell_at'), )
        }),
        ('Стратегия усреднения', {
            'fields': ('is_average_safety',
                       ('average_safety_orders_amount',
                        'average_safety_orders_max_count',
                        'average_safety_orders_active_count', 'average_safety_price_change',
                        'average_safety_ratio', 'average_safety_step'),
                       )
        }),

        ('Trailing cost', {
            'fields': ('is_trailing_cost', 'trailing_stop_lost',  'trailing_cost_up', 'trailing_cost_fall',)
        }),
        ('Stop Loss', {
            'fields': ('stop_loss', 'stop_loss_block_trade', )
        }),
        ('Пары по рангу', {
            'fields': ('is_market_rank', 'max_rank_pairs', 'rank_base_currency',)
        }),
        ('MACD', {
            'fields': ('is_macd', 'is_macd_cross_bottom_to_top',
                       ('macd_fastperiod', 'macd_slowperiod', 'macd_signalperiod'), ),
        }),
        ('RSI', {
            'fields': ('is_rsi', ('rsi_timeperiod', 'rsi_more', 'rsi_less',)),
        }),
        ('ADX', {
            'fields': ('is_adx', ('adx_timeperiod', 'adx_more', 'adx_less',)),
        }),
        ('Stochastic', {
            'fields': ('is_stochastic_cross', 'is_stochastic_fast_up', 'is_stochastic',
                       ('stochastic_fastk_period', 'stochastic_slowk_period', 'stochastic_slowd_period'),
                       ('stochastic_less', 'stochastic_more')),
        }),
        ('EMA', {
            'fields': ('is_ema', ('ema_fastperiod', 'ema_slowperiod')),
        }),
        ('SMA', {
            'fields': ('is_sma', 'sma_timeperiod', 'is_sma_cross_bottom_to_top',
                       ('sma_fastperiod', 'sma_slowperiod')),
        }),
    )

    @admin.display(
        description='Тестирование'
    )
    def test_bot(self, obj):
        """
        Тестирование бота
        :param obj:
        :return:
        """

        str_format = '<a href="{}" target="_blank">test</a>'
        return format_html(str_format, reverse('trading:test-bot', args=(obj.name, )))

    @admin.display(
        description='Статистика'
    )
    def stat_bot(self, obj):
        """
        Статистиска бота
        :param obj:
        :return:
        """

        str_format = '<a href="{}" target="_blank"><i class="fa fa-table"></i></a>'
        return format_html(str_format, reverse('trading:stats-bot', args=(obj.name, )))

@admin.register(BotTestOrder)
class BotTestOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'status', 'created_at', 'charts', 'price', 'bot', 'tickers')
    list_filter = ['type', 'status', 'bot']
    search_fields = ['market__name', ]
    date_hierarchy = 'created_at'

    @admin.display(
        description='Пара'
    )
    def charts(self, obj):
        """
        Список менеджеров проекта
        :param obj:
        :return:
        """

        str_format = '<a href="{}" target="_blank">{}</a>'
        return format_html(str_format, reverse('trading:test-bot-market', args=(obj.bot.name, obj.market.name)),
                           obj.market.name)


    @admin.display(
        description='Ticker data'
    )
    def tickers(self, obj):
        """
        Ticker data
        :param obj:
        :return:
        """

        str_format = ''
        if obj.ticker_data:
            for key, val in obj.ticker_data.items():
                str_format += format_html('{}: {}<br>', key, val)

        return str_format



@admin.register(HistoryBalance)
class HistoryBalanceAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'btc', 'bnb', 'usdt', 'order')
    readonly_fields = ['created_at', 'btc', 'bnb', 'usdt', 'order']


