import datetime
from decimal import *
from typing import Tuple

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Exchange(models.Model):
    class Meta:
        verbose_name = u'биржа'
        verbose_name_plural = u'биржы'
        db_table = 'trading_exchange'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField('название', max_length=100)
    code = models.CharField('код', max_length=100, help_text='Для использовния в коде')
    site = models.CharField('сайт', max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return '{}'.format(self.name)


class Currency(models.Model):
    class Meta:
        db_table = 'trading_currency'
        verbose_name = u'валюта'
        verbose_name_plural = u'валюты'
        ordering = ['name']

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    name = models.CharField('название', max_length=100, unique=True)
    name_long = models.CharField('длинное название', max_length=100)
    coin_type = models.CharField('тип монеты', max_length=100)
    min_confirmation = models.IntegerField('MinConfirmation', default=0)
    tx_fee = models.DecimalField('TxFee', max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=False)
    base_address = models.CharField('BaseAddress', max_length=250, null=True, blank=True)
    notice = models.CharField('Notice', max_length=800, null=True, blank=True)

    # коэффициенты
    coef_level = models.FloatField('выравнивающий', default=0.001,
                                   help_text='Влияет на: is_dodge (default=0,001) [ USDT - 0,001 | BTC - 0,00000001 ] ')

    coef_all_candle_min = models.FloatField('COEF_ALL_CANDLE_MIN', default=2,
                                            help_text='Влияет на: is_fat (default=2)')
    coef_all_candle_mid = models.FloatField('COEF_ALL_CANDLE_MID', default=3.2,
                                            help_text='Влияет на: is_fat (default=3.2)')
    coef_all_candle_max = models.FloatField('COEF_ALL_CANDLE_MAX', default=5.5,
                                            help_text='Влияет на: is_dodge (default=5.5)')
    coef_high_low_min = models.FloatField('COEF_HIGH_LOW_MIN', default=0.5,
                                          help_text='Влияет на: is_fat, is_dodge (default=0.5)')
    coef_high_low_max = models.FloatField('COEF_HIGH_LOW_MAX', default=2,
                                          help_text='Влияет на: is_fat, is_dodge (default=2)')
    sword_multilier = models.FloatField('SWORD_MULTIPLIER', default=2,
                                        help_text='Влияет на: is_sword (default=2)')
    hummer_multiplier = models.FloatField('HUMMER_MULTIPLIER', default=2,
                                          help_text='Влияет на: is_hummer (default=2)')

    is_base = models.BooleanField(default=False)

    def __str__(self):
        return '{}'.format(self.name)


class Market(models.Model):
    class Meta:
        verbose_name = u'пара'
        verbose_name_plural = u'пары'
        db_table = 'trading_market'
        unique_together = ['base_currency', 'market_currency']
        ordering = ['base_currency', 'market_currency']

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    market_currency = models.ForeignKey(Currency, verbose_name='MarketCurrency',
                                        related_name="market_currencies")
    base_currency = models.ForeignKey(Currency, verbose_name='BaseCurrency',
                                      related_name="base_currencies")

    name = models.CharField('название', max_length=100)
    code = models.CharField('код', max_length=100, default='-')
    min_trade_size = models.DecimalField('MinTradeSize', max_digits=24, decimal_places=8, default=0)
    is_active = models.BooleanField(default=False)
    is_active_binance = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)

    def __str__(self):
        m = []
        if self.is_active_binance:
            m.append('binance')
        if self.is_active:
            m.append('bittrex')
        return '{} {}'.format(self.name, m)

    def get_market_name(self, exchange):
        if exchange == 'binance':
            return self.code
            # return '{}{}'.format(self.market_currency, self.base_currency)
        return self.name


class MarketSettings(models.Model):
    class Meta:
        db_table = 'trading_market_settings'
        verbose_name = 'Настройки пары на бирже'
        verbose_name_plural = 'Настройки пары на бирже'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    exchange = models.ForeignKey(Exchange, default=1)
    market = models.ForeignKey(Market, default=1, related_name='settings')

    is_active = models.BooleanField(default=False)

    settings = JSONField(blank=True, null=True)


class MarketSummary(models.Model):
    class Meta:
        verbose_name = u'Summary 24H'
        verbose_name_plural = u'Summary 24H'
        db_table = 'trading_market_summary'

    created_at = models.DateTimeField('ADDED', default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField(default=timezone.now)

    market = models.ForeignKey(Market, verbose_name='Market')
    name = models.CharField('DisplayMarketName', max_length=100, blank=True, null=True)

    high = models.DecimalField('24HR HIGH', max_digits=24, decimal_places=8, default=0)  # 0.01350000,
    low = models.DecimalField('24HR LOW', max_digits=24, decimal_places=8, default=0)  # 0.01200000,
    volume = models.DecimalField('Volume', max_digits=24, decimal_places=8, default=0)  # 3833.97619253,
    last = models.DecimalField('Last Price', max_digits=24, decimal_places=8, default=0)  # 0.01349998,
    base_volume = models.DecimalField('BaseVolume', max_digits=24, decimal_places=8, default=0)  # 47.03987026,
    bid = models.DecimalField('Bid', max_digits=24, decimal_places=8, default=0)  # 0.01271001,
    ask = models.DecimalField('Ask', max_digits=24, decimal_places=8, default=0)  # 0.01291100,
    open_by_orders = models.DecimalField('OpenBuyOrders', max_digits=24, decimal_places=8, default=0)  # 45,
    open_sell_orders = models.DecimalField('OpenSellOrders', max_digits=24, decimal_places=8, default=0)  # 45,
    prev_day = models.DecimalField('PrevDay', max_digits=24, decimal_places=8, default=0)  # 0.01229501
    rank = models.DecimalField('rank', max_digits=24, decimal_places=8, default=0)


class MarketRank(models.Model):
    class Meta:
        verbose_name = u'Market Rank'
        verbose_name_plural = u'Markets Rank'
        db_table = 'trading_market_rank'

    created_at = models.DateTimeField('ADDED', default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField(default=timezone.now)

    market = models.ForeignKey(Market, verbose_name='Market')
    name = models.CharField('DisplayMarketName', max_length=100, blank=True, null=True)

    rank = models.DecimalField('rank', max_digits=24, decimal_places=8, default=0)


class MarketOrderBook(models.Model):
    class Meta:
        db_table = 'trading_market_order_book'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    market = models.ForeignKey(Market, verbose_name='Market')

    quantity = models.DecimalField('Quantity', max_digits=24, decimal_places=8, default=0)
    rate = models.DecimalField('rate', max_digits=24, decimal_places=8, default=0)

    BUY = 'BUY'
    SELL = 'SELL'

    TYPE_CHOICES = (
        (BUY, 'Покупка'),
        (SELL, 'Продажа'),

    )
    type = models.CharField(max_length=5, choices=TYPE_CHOICES, default=BUY)


class MarketTrade(models.Model):
    class Meta:
        db_table = 'trading_market_trade'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField('TimeStamp')

    market = models.ForeignKey(Market, verbose_name='Market')

    price = models.DecimalField('Price', max_digits=24, decimal_places=8, default=0)
    quantity = models.DecimalField('Quantity', max_digits=24, decimal_places=8, default=0)
    total = models.DecimalField('Total', max_digits=24, decimal_places=8, default=0)

    BUY = 'BUY'
    SELL = 'SELL'

    TYPE_CHOICES = (
        (BUY, 'Покупка'),
        (SELL, 'Продажа'),

    )
    type = models.CharField(max_length=5, choices=TYPE_CHOICES, default=BUY)


"""
    text = models.TextField()
    is_auto = models.BooleanField(default=False)
    theme = models.ForeignKey(NotifyTheme)
    count_mess = models.IntegerField(default=0)
"""


class OpenOrders(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.exclude(Q(status__in=[MarketMyOrder.Status.CLOSED, MarketMyOrder.Status.CANCELED]) | Q(is_close=True))
        qs = qs.filter(
            Q(cancelled_at__isnull=True),
            Q(
                Q(type=MarketMyOrder.Type.SELL, status__in=[MarketMyOrder.Status.OPEN,
                                                            MarketMyOrder.Status.PART_FILLED])
                |
                Q(type=MarketMyOrder.Type.BUY,
                  kind=MarketMyOrder.Kind.SAFETY,
                  status__in=[MarketMyOrder.Status.OPEN, MarketMyOrder.Status.PART_FILLED]
                  )
                |
                Q(type=MarketMyOrder.Type.BUY,
                  kind=MarketMyOrder.Kind.MAIN,
                  status__in=[MarketMyOrder.Status.OPEN,
                              MarketMyOrder.Status.PART_FILLED,
                              MarketMyOrder.Status.FILLED
                              ]
                  ),
                )
        )

        return qs


class CloseOrders(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(status__in=[MarketMyOrder.Status.FILLED, MarketMyOrder.Status.CLOSED])
        # qs = qs.exclude(Q(status__in=[MarketMyOrder.Status.CLOSED, MarketMyOrder.Status.CANCELED]) | Q(is_close=True))
        # qs = qs.filter(
        #     Q(cancelled_at__isnull=True),
        #     Q(
        #         Q(type=MarketMyOrder.Type.SELL, status__in=[MarketMyOrder.Status.OPEN,
        #                                                     MarketMyOrder.Status.PART_FILLED])
        #         |
        #         Q(type=MarketMyOrder.Type.BUY, status__in=[MarketMyOrder.Status.OPEN,
        #                                                    MarketMyOrder.Status.PART_FILLED,
        #                                                    MarketMyOrder.Status.FILLED
        #                                                    ])
        #     )
        # )

        return qs


class MarketTickInterval(models.Model):
    class Meta:
        verbose_name = u'интервал'
        verbose_name_plural = u'интервалы'
        db_table = 'trading_tick_interval'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    name = models.CharField('название', max_length=100, unique=True)
    value = models.CharField('значение', max_length=100, unique=True)
    value_binance = models.CharField('значение binance', max_length=100, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.value)


class MarketBot(models.Model):
    class Meta:
        db_table = 'trading_market_bot'
        verbose_name = 'Бот'
        verbose_name_plural = 'Боты'

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    exchange = models.ForeignKey(Exchange, verbose_name='Биржа', default=1)

    name = models.CharField('название', max_length=100, unique=True)
    is_test = models.BooleanField(default=True)
    is_ha = models.BooleanField('Проверять по Heikin Ashi', default=False)

    max_spend = models.DecimalField('Максимальная сумма покупки', max_digits=24, decimal_places=8, default=0)
    markup = models.DecimalField('% прибыли', max_digits=5, decimal_places=2, default=1,
                                 help_text='процент прибаляемый к сумме покупки при продаже от 1 до 100')
    order_life_time = models.IntegerField('время жизни ордера', default=60,
                                          help_text='Количество секунд через которе будет удален '
                                                    'неисполненный ордер на покупку')

    is_trailing_cost = models.BooleanField('Trailing cost', default=False,
                                           help_text='')
    trailing_stop_lost = models.DecimalField('Trailing stop loss', max_digits=5, decimal_places=2, default=1,
                                             help_text='процент падения, после которого продаем, вне зависимости от '
                                                       'минимального процента роста')

    trailing_cost_up = models.DecimalField('Минимальный % роста', max_digits=5, decimal_places=2, default=1,
                                           help_text='процент роста после кторого фиксируем максимальную цену')
    trailing_cost_fall = models.DecimalField('% падения', max_digits=5, decimal_places=2, default=1,
                                             help_text='процент падения для фиксации прибыли')
    # currency = models.ForeignKey(Currency, verbose_name='Валюта')

    tick_intervals = models.ManyToManyField(MarketTickInterval, verbose_name='Интервалы')

    is_ema = models.BooleanField('Проверять по EMA', default=False)
    ema_fastperiod = models.SmallIntegerField('EMA fastperiod', default=7)
    ema_slowperiod = models.SmallIntegerField('EMA slowperiod', default=26)

    is_macd = models.BooleanField('Проверять по MACD направление', default=True,
                                  help_text='')
    is_macd_cross_bottom_to_top = models.BooleanField('Проверять по MACD пересечение', default=False,
                                                      help_text='Пересекает быстрая медленную снизу вверх')
    macd_fastperiod = models.SmallIntegerField('MACD fastperiod', default=8)
    macd_slowperiod = models.SmallIntegerField('MACD slowperiod', default=17)
    macd_signalperiod = models.SmallIntegerField('MACD signalperiod', default=9)

    is_rsi = models.BooleanField('Проверять по RSI', default=True,
                                 help_text='Проверяет значение больше, меньше или внутри коридора значений')
    rsi_timeperiod = models.SmallIntegerField('timeperiod', default=7)
    rsi_less = models.SmallIntegerField('RSI меньше', null=True, blank=True)
    rsi_more = models.SmallIntegerField('RSI больше', null=True, blank=True)

    is_green = models.BooleanField('Проверять по green candle', default=False)
    is_dodge = models.BooleanField('Проверять по dodge candle', default=False)
    # is_dodge_prev = models.BooleanField('Проверять по предыдущей dodge candle', default=False)
    is_hummer = models.BooleanField('Проверять по hummer candle', default=False)
    is_sword = models.BooleanField('Проверять по sword candle', default=False)
    is_simple = models.BooleanField('Проверять по simple candle', default=False)
    is_fat = models.BooleanField('Проверять по fat candle', default=False)

    is_min_value = models.BooleanField('Проверять минимальный объем торгов', default=False)
    min_value = models.SmallIntegerField('Минимальный объем торгов', default=150)

    is_compare_value = models.BooleanField('Сравнивать объем торгов', default=False)

    is_ratio_open_close = models.BooleanField('Сравнивать соотношение цены открытия и закрытия', default=False)
    ratio_open_close = models.DecimalField('Коэффициент соотношения', max_digits=5, decimal_places=2, default=1.03)

    is_sma = models.BooleanField('Проверять по SMA', default=False)
    sma_timeperiod = models.SmallIntegerField('SMA timeperiod', default=50)

    is_sma_cross_bottom_to_top = models.BooleanField('Проверять по SMA пересечение', default=False,
                                                     help_text='Пересекает быстрая медленную снизу вверх')
    sma_fastperiod = models.SmallIntegerField('SMA fastperiod', default=5)
    sma_slowperiod = models.SmallIntegerField('SMA slowperiod', default=20)

    is_adx = models.BooleanField('Проверять по ADX', default=False)
    adx_timeperiod = models.SmallIntegerField('timeperiod', default=14)
    adx_less = models.SmallIntegerField('ADX меньше', null=True, blank=True)
    adx_more = models.SmallIntegerField('ADX больше', null=True, blank=True)

    is_stochastic = models.BooleanField('Проверять по Stochastic (больше/меньше)', default=False)
    stochastic_less = models.SmallIntegerField('Stochastic меньше', null=True, blank=True)
    stochastic_more = models.SmallIntegerField('Stochastic больше', null=True, blank=True)

    is_stochastic_cross = models.BooleanField('Проверять по Stochastic пересечение', default=False)
    is_stochastic_fast_up = models.BooleanField('Проверять по Stochastic fast up', default=False)
    stochastic_fastk_period = models.SmallIntegerField('Stochastic fastk_period', default=5)
    stochastic_slowk_period = models.SmallIntegerField('Stochastic slowk_period', default=3)
    stochastic_slowd_period = models.SmallIntegerField('Stochastic slowd_period', default=3)

    bot_last_run = models.DateTimeField('Время поседнего запуска бота', null=True, blank=True)

    # # коэффициенты
    # coef_all_candle_min = models.SmallIntegerField('COEF_ALL_CANDLE_MIN', default=2,
    #                                                help_text='Влияет на: is_fat (default=2)')
    # coef_all_candle_mid = models.SmallIntegerField('COEF_ALL_CANDLE_MID', default=3.2,
    #                                               help_text='Влияет на: is_fat (default=3.2)')
    # coef_all_candle_max = models.SmallIntegerField('COEF_ALL_CANDLE_MAX', default=5.5,
    #                                                help_text='Влияет на: is_dodge (default=5.5)')
    # coef_high_low_min = models.SmallIntegerField('COEF_HIGH_LOW_MIN', default=0.5,
    #                                              help_text='Влияет на: is_fat, is_dodge (default=0.5)')
    # coef_high_low_max = models.SmallIntegerField('COEF_HIGH_LOW_MAX', default=2,
    #                                              help_text='Влияет на: is_fat, is_dodge (default=2)')
    # sword_multilier = models.SmallIntegerField('SWORD_MULTIPLIER', default=2,
    #                                            help_text='Влияет на: is_sword (default=2)')
    # hummer_multiplier = models.SmallIntegerField('HUMMER_MULTIPLIER', default=2,
    #                                              help_text='Влияет на: is_hummer (default=2)')

    # is_stop_loss = models.BooleanField('Проверять Stop Loss', default=True)
    stop_loss = models.DecimalField('% максимальных потерь', max_digits=5, decimal_places=2, default=5,
                                    help_text='процент при падении рынка по достижению которого '
                                              'выставляется ордер на продажу')
    stop_loss_block_trade = models.SmallIntegerField('Количество минут на которое блокируется торговля после stop loss',
                                                     default=60)
    is_market_rank = models.BooleanField('Подбирать пары по рангу', default=False)
    max_rank_pairs = models.IntegerField('Максимальное кол-во пар', default=10)
    rank_base_currency = models.ForeignKey(Currency, verbose_name='Базовая валюта', blank=True, null=True,
                                           limit_choices_to={'is_base': True}, )

    markets = models.ManyToManyField(Market, verbose_name='Пары', blank=True)

    is_average_safety = models.BooleanField('Статегия усреднения', default=False)
    average_safety_start_order_amount = models.DecimalField('Объем стартового ордера', max_digits=24, decimal_places=8,
                                                            default=Decimal(0.0000001))

    average_safety_orders_amount = models.DecimalField('Объем страховочных ордеров', max_digits=24, decimal_places=8,
                                                       default=Decimal(0.0000001))
    average_safety_orders_max_count = models.SmallIntegerField('Максимальное количество страховых ордеров', default=5)
    average_safety_orders_active_count = models.SmallIntegerField('Количество активных страховых ордеров', default=2)
    average_safety_price_change = models.DecimalField('Отклонение цены для выставления страховочного ордера '
                                                      '(% от стоимости начального ордера)',
                                                      max_digits=24, decimal_places=8, default=1)

    average_safety_ratio = models.DecimalField('Множитель объема страховочных ордеров',
                                               max_digits=5, decimal_places=2, default=1)

    average_safety_step = models.DecimalField('Множитель шага страховочных ордеров',
                                              max_digits=5, decimal_places=2, default=1)

    def __str__(self):
        return '{}'.format(self.name)

    def get_api(self):
        if self.exchange.code == 'binance':
            from trading.backedns.binance.client import ApiBinance
            api = ApiBinance()
        else:
            from trading.backedns.bittrex.client import ApiBittrex
            api = ApiBittrex()

        return api

    def get_tick_intervals(self) -> list:
        if self.exchange.code == 'binance':
            tick_intervals = [t.value_binance for t in self.tick_intervals.all()]
        else:
            tick_intervals = [t.value for t in self.tick_intervals.all()]

        return tick_intervals

    def get_market_rank(self, market):
        try:
            market_rank = MarketBotRank.objects.get(bot=self, market=market)
            return market_rank
        except MarketBotRank.DoesNotExist:
            market_rank = MarketBotRank.objects.create(bot=self, market=market)

        return market_rank

    def update_current_price(self, ticker_data, market, market_rank=None):
        if not market_rank:
            market_rank = self.get_market_rank(market)

        if market_rank:
            market_rank.ticker_data = ticker_data
            market_rank.save()

    def check_market_stop_loss(self):
        check_date = timezone.now() - datetime.timedelta(minutes=self.stop_loss_block_trade)

        MarketBotRank.objects.filter(bot=self, is_block_trade=True, block_trade_at__lte=check_date)\
            .update(is_block_trade=False, block_trade_at=None)

    def get_markets(self, api):

        from trading.lib import convert_ticker_to_decimal, convert_ticker_to_float
        satoshi_100 = 0.000001

        markets = []

        if self.is_market_rank:

            MarketBotRank.objects.filter(bot=self).update(rank=0)

            results = api.get_market_summaries()

            if results:
                for r in results:
                    market = api.get_market(r.get(api.convert_tickers.get('MarketName')))
                    # r = convert_ticker_to_decimal(r)
                    r = convert_ticker_to_float(r)

                    if r[api.convert_tickers['Last']] and r[api.convert_tickers['Last']] > satoshi_100:
                        if r[api.convert_tickers['Ask']] and r[api.convert_tickers['Bid']] and r[api.convert_tickers['Volume']]:
                            rank = (r[api.convert_tickers['Ask']] - r[api.convert_tickers['Bid']]) / r[api.convert_tickers['Bid']] * r[api.convert_tickers['Volume']]
                        else:
                            rank = 0
                        data = {
                            'market': market,
                            'bot': self,
                        }
                        mbr, created = MarketBotRank.objects.get_or_create(**data)
                        mbr.rank = rank
                        mbr.save()
                market_data = {
                    'bot': self,
                    'is_block_trade': False,
                }
                if self.rank_base_currency:
                    market_data['market__base_currency'] = self.rank_base_currency
                bot_markets = MarketBotRank.objects.values_list('market_id', flat=True) \
                                  .filter(**market_data).order_by('-rank')[:self.max_rank_pairs+5]
                markets = Market.objects.filter(id__in=list(bot_markets))

        elif self.markets.all():
            markets = self.markets.all()
        else:
            markets = Market.objects.filter(is_bot=True)

        if self.exchange.code == 'binance':
            markets = markets.filter(is_active_binance=True)
        else:
            markets = markets.filter(is_active=True)

        return markets

    def get_settings(self):
        return {
            'is_test': self.is_test,
            'stop_loss': float(self.stop_loss),
            'stop_loss_block_trade': float(self.stop_loss_block_trade),
            'trailing_cost_up': float(self.trailing_cost_up),
            'trailing_cost_fall': float(self.trailing_cost_fall),
        }


class MarketBotRank(models.Model):
    class Meta:
        verbose_name = u'Market Rank'
        verbose_name_plural = u'Markets Rank'
        db_table = 'trading_market_bot_rank'
        ordering = ['-rank']

    created_at = models.DateTimeField('ADDED', default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField(default=timezone.now)

    market = models.ForeignKey(Market, verbose_name='Market', related_name='bot_rank')
    bot = models.ForeignKey(MarketBot, verbose_name='MarketBot', related_name='bot_rank')

    rank = models.DecimalField('rank', max_digits=24, decimal_places=8, default=0)

    max_price = models.DecimalField('max price', max_digits=24, decimal_places=8, default=0)
    trailing_price = models.DecimalField('trailing price', max_digits=24, decimal_places=8, default=0)
    ticker_data = JSONField(blank=True, null=True)

    is_block_trade = models.BooleanField(default=False)
    block_trade_at = models.DateTimeField('Время начала блокировки торговли', null=True, blank=True)

    def block_trade(self):
        self.is_block_trade = True
        self.block_trade_at = timezone.now()
        self.save()

    def clear_max_price(self):
        self.max_price = 0
        self.trailing_price = 0
        self.ticker_data = None
        self.save()


class MarketMyOrder(models.Model):
    objects = models.Manager()  # The default manager.
    open_objects = OpenOrders()  # The Dahl-specific manager.
    close_objects = CloseOrders()

    class Meta:
        db_table = 'trading_market_order_my'
        verbose_name = 'Ордер'
        verbose_name_plural = 'Ордера'

    # uuid = models.UUIDField(blank=True, null=True)
    uuid = models.CharField(max_length=100, blank=True, null=True)
    ext_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    filled_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    market = models.ForeignKey(Market, verbose_name='Market')
    bot = models.ForeignKey(MarketBot, verbose_name='Бот', null=True, blank=True)

    price = models.DecimalField('Price', max_digits=24, decimal_places=8, default=0, help_text='Цена покупки/продажи')
    amount = models.DecimalField('Amount', max_digits=24, decimal_places=8, default=0, help_text='Кол-во')
    spent = models.DecimalField('Spent', max_digits=24, decimal_places=8, default=0, help_text='Потрачено')
    test_spent = models.DecimalField('Spent Test', max_digits=24, decimal_places=8, default=0, help_text='Потрачено test')
    fee = models.DecimalField('Fee', max_digits=24, decimal_places=8, default=0, help_text='')
    commission = models.DecimalField('Commission', max_digits=24, decimal_places=8, default=0, help_text='Комиссия')

    # from_order = models.OneToOneField('self', blank=True, null=True)
    from_order = models.ForeignKey('self', blank=True, null=True)
    is_close = models.BooleanField(default=False)

    get_order_result = JSONField(blank=True, null=True)     # json.dumps(data)

    ticker_data = JSONField(blank=True, null=True)          # json.dumps(data)

    is_stop_loss = models.BooleanField(default=False)
    is_trailing_stop_loss = models.BooleanField(default=False)
    is_test = models.BooleanField(default=False)

    class Kind:
        MAIN = 'MAIN'
        SAFETY = 'SAFETY'
        FIX = 'FIX'

    KIND_CHOICES = (
        (Kind.MAIN, 'Основной'),
        (Kind.SAFETY, 'Страховочный'),
        (Kind.FIX, 'Фиксирующий'),
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=Kind.MAIN)

    class Type:
        BUY = 'BUY'
        SELL = 'SELL'

    TYPE_CHOICES = (
        (Type.BUY, 'Покупка'),
        (Type.SELL, 'Продажа'),

    )
    type = models.CharField(max_length=5, choices=TYPE_CHOICES, default=Type.BUY)

    class Status:
        OPEN = 'OPEN'
        CANCELED = 'CANCELED'
        FILLED = 'FILLED'
        PART_FILLED = 'PART_FILLED'
        CLOSED = 'CLOSED'

    STATUS_CHOICES = (
        (Status.OPEN, 'Открытый'),
        (Status.CANCELED, 'Отменен'),
        (Status.FILLED, 'Исполнен'),
        (Status.PART_FILLED, 'Частично исполнен'),
        (Status.CLOSED, 'Закрыт'),
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=Status.OPEN)

    class CancelStatus:
        TIME = 'TIME'
        STOP_LOSS = 'STOP_LOSS'
        TRAILING_STOP_LOSS = 'TRAILING_STOP_LOSS'
        SAFETY = 'SAFETY'

    STATUS_CANCEL_CHOICES = (
        (CancelStatus.TIME, 'По времени'),
        (CancelStatus.STOP_LOSS, 'Stop Loss'),
        (CancelStatus.TRAILING_STOP_LOSS, 'Trailing Stop Loss'),
        (CancelStatus.SAFETY, 'Куплен страховочный'),
    )
    status_cancel = models.CharField(max_length=25, choices=STATUS_CANCEL_CHOICES, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.id)

    def get_color_marker(self):
        if self.status in [self.Status.FILLED, self.Status.PART_FILLED, self.Status.CLOSED, ]:
            if self.type == self.Type.SELL:
                return "#00CC00"
            else:
                return "#CC0000"
        elif self.status == self.Status.OPEN:
            return '#337ab7'
        else:
            return '#CCCCCC'

    def cancel_order(self, cancel_type=CancelStatus.TIME):
        self.cancelled_at = timezone.now()
        self.status = MarketMyOrder.Status.CANCELED
        if self.type == self.Type.SELL:
            self.is_stop_loss = True
            self.status_cancel = cancel_type

            # закрываем основной ордер
            # self.from_order.close_order()

        self.save()

    def close_order(self):

        self.is_close = True
        self.save()

        if not self.from_order:
            # если основной ордер, закрываем страховочные ордера
            MarketMyOrder.objects.filter(from_order=self, status=MarketMyOrder.Status.FILLED)\
                .update(is_close=True)

    def create_log(self, log_type, ticker_data=None, max_price=0):

        MarketOrderLog.objects.create(
            order=self,
            type=log_type,
            ticker_data=ticker_data,
            bot_data=self.bot.get_settings(),
            max_price=max_price,
        )

    def update_info(self, order_info, res_ticker_data=None):
        if self.bot.is_test:
            if res_ticker_data:
                # self.price = Decimal(res_ticker_data['Bid'])
                # self.spent = self.price * self.amount
                # if self.type == self.Type.BUY:
                #     self.commission = self.price * self.amount / 100 * Decimal(0.25)
                #     self.spent = self.price * self.amount + self.commission
                # else:
                #     self.commission = self.price * self.amount / 100 * Decimal(0.25)
                #     self.spent = self.price * self.amount

                if order_info:
                    self.get_order_result = order_info
                self.save()

        elif order_info:
            if 'PricePerUnit' in order_info and order_info['PricePerUnit']:
                self.price = Decimal(order_info['PricePerUnit'])
            if 'Quantity' in order_info and order_info['Quantity']:
                self.amount = Decimal(order_info['Quantity'])
            if 'Price' in order_info and order_info['Price']:
                self.spent = Decimal(order_info['Price'])
            if 'CommissionPaid' in order_info and order_info['CommissionPaid']:
                self.commission = Decimal(order_info['CommissionPaid'])
            self.get_order_result = order_info
            self.save()

    def get_min_trailing_cost_up(self):
        return self.price + self.price / 100 * self.bot.trailing_cost_up

    def get_amount_for_sell_new(self) -> Tuple[Decimal, Decimal]:
        """Расчитываем количество монет для продажи"""
        orders_buy_count = 1

        # получаем данные по основному ордеру
        if self.from_order:
            from_order = self.from_order
        else:
            from_order = self

        total_amount = from_order.amount
        sum_prices = from_order.price
        # total_spent = from_order.amount * from_order.price
        if from_order.commission:
            total_spent = from_order.spent + from_order.commission
        else:
            total_spent = from_order.price * from_order.amount + (
                    from_order.price * from_order.amount / 100 * Decimal(0.25)
            )

        # TODO: сделать учет не полностью выкупленных ордеров
        # получаем исполненные страховочные ордера
        safety_orders = MarketMyOrder.objects.filter(
            from_order=from_order,
            kind=MarketMyOrder.Kind.SAFETY,
            type=MarketMyOrder.Type.BUY,
            status=MarketMyOrder.Status.FILLED
        )

        for so in safety_orders:
            orders_buy_count += 1
            total_amount += so.amount
            sum_prices += so.price
            if so.commission:
                total_spent += so.spent + so.commission
            else:
                total_spent += so.price * so.amount + so.price * so.amount / 100 * Decimal(0.25)

        average_price = total_spent / total_amount

        return total_amount, average_price

    def get_amount_for_sell(self) -> Tuple[Decimal, int, Decimal]:
        """Расчитываем количество монет для продажи"""
        orders_buy_count = 1

        # получаем данные по основному ордеру
        if self.from_order:
            amount = self.from_order.amount
            from_order = self.from_order
            sum_prices = self.from_order.price
        else:
            amount = self.amount
            from_order = self
            sum_prices = self.price
        # TODO: сделать учет не полностью выкупленных ордеров
        safety_orders = MarketMyOrder.objects.filter(
            from_order=from_order,
            kind=MarketMyOrder.Kind.SAFETY,
            type=MarketMyOrder.Type.BUY,
            status=MarketMyOrder.Status.FILLED
        )

        for so in safety_orders:
            orders_buy_count += 1
            amount += so.amount
            sum_prices += so.price

        return amount, orders_buy_count, sum_prices

    def get_profit(self):
        """
            :param obj:
            :return:
            """

        spent_buy, spent_sell = self.get_spent()
        diff = Decimal(spent_sell - spent_buy).quantize(Decimal('.00000000'))
        # diff = spent_sell - spent_buy

        return diff

    def get_spent(self):
        if self.from_order:
            print('if self.from_order:', self, self.from_order)
            spent_buy = self.get_average_spend(self.from_order)
        else:
            print('else:')
            spent_buy = self.get_average_spend()

        if self.type == self.Type.BUY:
            main_order = self.from_order or self
            orders = MarketMyOrder.objects.filter(from_order=main_order,
                                                  type=MarketMyOrder.Type.SELL,
                                                  status=MarketMyOrder.Status.FILLED)

            spent_sell = 0
            for o in orders:
                if o.commission:
                    spent_sell = o.spent - o.commission
                else:
                    spent_sell = o.price * o.amount + o.price * o.amount / 100 * Decimal(0.25)
        else:
            if self.commission:
                spent_sell = self.spent - self.commission
                # spent_buy = self.from_order.spent + self.from_order.commission
            else:
                spent_sell = self.price * self.amount + self.price * self.amount / 100 * Decimal(0.25)
                # spent_buy = self.from_order.price * self.amount + self.from_order.price * self.from_order.amount / 100 * Decimal(0.5)
        print('spent_buy, spent_sell', spent_buy, spent_sell)
        return spent_buy, spent_sell

    def get_average_spend(self, order=None):
        # получаем потраченную сумму
        print('get_average_spend', order)
        if not order:
            order = self
        if order.commission:
            spent = order.spent + order.commission
        else:
            spent = order.price * order.amount + order.price * order.amount / 100 * Decimal(0.25)
        print('spent', spent)
        safety_orders = MarketMyOrder.objects.filter(from_order=order,
                                                     kind=MarketMyOrder.Kind.SAFETY,
                                                     type=MarketMyOrder.Type.BUY,
                                                     status=MarketMyOrder.Status.FILLED)
        print('safety_orders', safety_orders)
        for so in safety_orders:
            if self.commission:
                spent += so.spent + so.commission
            else:
                spent += so.price * so.amount + so.price * so.amount / 100 * Decimal(0.25)
        print('spent*', spent)
        return spent

    def get_average_price(self):
        # получаем усредненую цену

        amount = self.amount
        spent = self.spent

        safety_orders_filled = MarketMyOrder.objects.filter(from_order=self,
                                                            kind=MarketMyOrder.Kind.SAFETY,
                                                            type=MarketMyOrder.Type.BUY,
                                                            status=MarketMyOrder.Status.FILLED)

        for so in safety_orders_filled:
            amount += so.amount
            spent += so.spent

        if amount != 0:
            return spent/amount

        return 0

    def get_profit_percent(self):

            """
            100*х/у-100 - на столько процентов х больше у
            100-100*у/х - на столько процентов у меньше х
            """
            spent_buy, spent_sell = self.get_spent()
            if spent_buy != 0:
                diff_percent = 100 * spent_sell / spent_buy - 100
            else:
                diff_percent = '--'

            return diff_percent

    def get_min_profit(self):
        from trading.utils import add_stock_fee
        min_profit = add_stock_fee(self.amount * self.price)
        return min_profit

    def get_sell_orders(self):
        if self.type == self.Type.BUY and self.kind == self.Kind.MAIN:
            orders = MarketMyOrder.objects.filter(
                from_order=self, type=MarketMyOrder.Type.SELL
            ).exclude(status=MarketMyOrder.Status.CANCELED)
            return orders
        return {}

    def get_sell_price(self):
        if self.type == self.Type.BUY and self.kind == self.Kind.MAIN:
            orders = MarketMyOrder.objects.filter(
                from_order=self, type=MarketMyOrder.Type.SELL
            ).exclude(status=MarketMyOrder.Status.CANCELED).order_by('id')

            order = orders.last()
            print('**** order', order)
            return order

        return None

    def get_wait_price(self):
        if self.type == self.Type.BUY:
            from trading.utils import add_stock_fee
            price = self.get_average_price()
            wp = add_stock_fee(price + price * self.bot.trailing_cost_up / 100)
            try:
                wp = wp.quantize(Decimal('.00000000'))
            except InvalidOperation:
                pass
            return wp

    def get_current_price(self):
        market_rank = self.bot.get_market_rank(self.market)

        if market_rank and market_rank.ticker_data:
            print('************** market_rank', market_rank.ticker_data)
            from trading.utils import get_price_for_sell
            return get_price_for_sell(market_rank.ticker_data)

    def get_safety_orders_info(self) -> dict:
        """Возвращает информацию по страховочным ордерам"""
        safety = {
            'filled': {'count': 0, 'amount': 0},
            'opened': {'count': 0, 'amount': 0},
        }
        if self.type == self.Type.BUY and self.kind == self.Kind.MAIN:
            orders = MarketMyOrder.objects.filter(from_order=self, type=MarketMyOrder.Type.BUY)\
                .exclude(status=MarketMyOrder.Status.CANCELED)
            for so in orders:
                if so.status == MarketMyOrder.Status.OPEN:
                    safety['opened']['count'] += 1
                    safety['opened']['amount'] += so.spent

                elif so.status == MarketMyOrder.Status.FILLED:
                    safety['filled']['count'] += 1
                    safety['filled']['amount'] += so.spent
        return safety

    def get_uuid(self):
        if self.bot.exchange.code == 'binance':
            return self.ext_id

        return self.uuid


class MarketOrderLog(models.Model):
    class Meta:
        verbose_name = u'Order Log'
        verbose_name_plural = u'Orders Log'
        db_table = 'trading_market_order_log'

    class Type:
        CREATE_ORDER = 'CREATE_ORDER'
        FILLED_ORDER = 'FILLED_ORDER'
        MAX_PRICE_FIXED = 'MAX_PRICE_FIXED'
        MAX_PRICE_UPDATED = 'MAX_PRICE_UPDATED'
        TRAILING_MAX_PRICE_FIXED = 'MAX_PRICE_FIXED'
        TRAILING_MAX_PRICE_UPDATED = 'MAX_PRICE_UPDATED'
        TRAILING_FALL = 'TRAILING_FALL'
        TRAILING_STOP_LOSS = 'TRAILING_STOP_LOSS'
        STOP_LOSS = 'STOP_LOSS'

    TYPE_CHOICES = (
        (Type.CREATE_ORDER, 'Ордер создан'),
        (Type.FILLED_ORDER, 'Ордер выполнен'),
        (Type.MAX_PRICE_FIXED, 'MaxPrice зафиксирована'),
        (Type.MAX_PRICE_UPDATED, 'MaxPrice обновлена'),
        (Type.STOP_LOSS, 'Сработал Stop Loss'),
        (Type.TRAILING_FALL, 'Сработал Trailing Fall'),
        (Type.TRAILING_STOP_LOSS, 'Сработал Trailing Stop Loss'),
        (Type.TRAILING_MAX_PRICE_FIXED, 'Trailing Price зафиксирована'),
        (Type.TRAILING_MAX_PRICE_UPDATED, 'Trailing Price обновлена'),
        (Type.STOP_LOSS, 'Установлен Stop Loss'),

    )

    created_at = models.DateTimeField('ADDED', default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    order = models.ForeignKey(MarketMyOrder, verbose_name='MarketBot', related_name='logs')

    max_price = models.DecimalField('max price', max_digits=24, decimal_places=8, default=0)
    ticker_data = JSONField(blank=True, null=True)
    bot_data = JSONField(blank=True, null=True)

    type = models.CharField(max_length=25, choices=TYPE_CHOICES, default=Type.CREATE_ORDER)


class BotTestOrder(models.Model):
    objects = models.Manager()  # The default manager.
    open_objects = OpenOrders()  # The Dahl-specific manager.

    class Meta:
        db_table = 'trading_bot_test_order'
        verbose_name = 'Тестовый ордер'
        verbose_name_plural = 'Тестовые ордера'

    created_at = models.DateTimeField(default=timezone.now)
    period = models.DateTimeField(blank=True, null=True)

    market = models.ForeignKey(Market, verbose_name='Market')
    bot = models.ForeignKey(MarketBot, verbose_name='Бот', null=True, blank=True)

    price = models.DecimalField('Price', max_digits=24, decimal_places=8, default=0, help_text='Цена покупки/продажи')

    get_order_result = models.TextField(blank=True, null=True)  # json.dumps(data)
    ticker_data = JSONField(blank=True, null=True)  # json.dumps(data)

    class Type:
        BUY = 'BUY'
        SELL = 'SELL'

    TYPE_CHOICES = (
        (Type.BUY, 'Покупка'),
        (Type.SELL, 'Продажа'),

    )
    type = models.CharField(max_length=5, choices=TYPE_CHOICES, default=Type.BUY)

    class Status:
        OPEN = 'OPEN'
        CANCELED = 'CANCELED'
        FILLED = 'FILLED'
        PART_FILLED = 'PART_FILLED'
        CLOSED = 'CLOSED'

    STATUS_CHOICES = (
        (Status.OPEN, 'Открытый'),
        (Status.CANCELED, 'Отменен'),
        (Status.FILLED, 'Исполнен'),
        (Status.PART_FILLED, 'Частично исполнен'),
        (Status.CLOSED, 'Закрыт'),
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=Status.OPEN)

    def __str__(self):
        return '{}'.format(self.id)

    def get_color_marker(self):
        if self.status in [self.Status.FILLED, self.Status.PART_FILLED, self.Status.CLOSED, ]:
            if self.type == self.Type.SELL:
                return "#00CC00"
            else:
                return "#CC0000"
        elif self.status == self.Status.OPEN:
            return '#337ab7'
        else:
            return '#CCCCCC'


class BotStat(models.Model):

    class Meta:
        db_table = 'trading_bot_stat'
        verbose_name = 'Сатистика'
        verbose_name_plural = 'Статистика'

    date = models.DateField()

    market = models.ForeignKey(Market, verbose_name='Market')
    bot = models.ForeignKey(MarketBot, verbose_name='Бот', null=True, blank=True)

    buy = models.IntegerField('Ордеров на покупку', default=0)
    buy_sum = models.DecimalField('Продано на сумму', max_digits=24, decimal_places=8, default=0, )

    sell = models.IntegerField('Ордеров на продажу', default=0)
    sell_sum = models.DecimalField('Куплено на сумму', max_digits=24, decimal_places=8, default=0, )

    def __str__(self):
        return '{}'.format(self.date)


class CheckMarketFilter(models.Model):

    class Meta:
        db_table = 'check_market_filter'
        verbose_name = 'Проверка фильтров'
        verbose_name_plural = 'Проверка фильтров'

    created_at = models.DateTimeField(default=timezone.now)

    symbol = models.CharField('название', max_length=100)
    maxPrice = models.CharField(max_length=100)
    minPrice = models.CharField(max_length=100)
    tickSize = models.CharField(max_length=100)
    p_avgPriceMins = models.CharField(max_length=100)
    multiplierUp = models.CharField(max_length=100)
    multiplierDown = models.CharField(max_length=100)
    maxQty = models.CharField(max_length=100)
    minQty = models.CharField(max_length=100)
    stepSize = models.CharField(max_length=100)
    minNotional = models.CharField(max_length=100)
    n_avgPriceMins = models.CharField(max_length=100)
    applyToMarket = models.CharField(max_length=100)
    limit = models.CharField(max_length=100)
    maxNumAlgoOrders = models.CharField(max_length=100)

    def __str__(self):
        return '{}'.format(self.symbol)


class ExchangeCurrency(models.Model):
    class Meta:
        verbose_name = u'валюта на бирже'
        verbose_name_plural = u'валюты на бирже'
        db_table = 'trading_exchange_currency'
        unique_together = ['currency', 'exchange']

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    currency = models.ForeignKey(Currency, verbose_name='Валюта', related_name="exchange_currencies")
    exchange = models.ForeignKey(Exchange, verbose_name='Биржа', related_name="currencies")

    start_amount = models.DecimalField('Начальный баланс', max_digits=24, decimal_places=8, default=0)
    free = models.DecimalField('Текущий баланс', max_digits=24, decimal_places=8, default=0)
    locked = models.DecimalField('Текущий баланс', max_digits=24, decimal_places=8, default=0)

    def __str__(self):
        return '{} {}'.format(self.currency.name, self.exchange.name)


class ExchangeCurrencyStatistic(models.Model):

    class Meta:
        verbose_name = u'статистика валюты на бирже'
        verbose_name_plural = u'статистика валют на бирже'
        db_table = 'trading_exchange_currency_statistic'

    class Operation:
        BUY = 'BUY'
        SELL = 'SELL'
        CHECK = 'CHECK'

    OPERATION_CHOICES = (
        (Operation.BUY, 'Покупка'),
        (Operation.SELL, 'Продажа'),
        (Operation.CHECK, 'Проверка'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # exchange_currency = models.ForeignKey(ExchangeCurrency, verbose_name='Валюта')
    currency = models.ForeignKey(Currency, verbose_name='Валюта', null=True)
    order = models.ForeignKey(MarketMyOrder, verbose_name='Order', null=True, blank=True)

    free = models.DecimalField('Доступно', max_digits=24, decimal_places=8, default=0)
    locked = models.DecimalField('Заблокировано', max_digits=24, decimal_places=8, default=0)
    total = models.DecimalField('Всего', max_digits=24, decimal_places=8, default=0)
    price = models.DecimalField('курс USDT', max_digits=24, decimal_places=8, default=0)
    usdt = models.DecimalField('Всего USDT', max_digits=24, decimal_places=8, default=0)

    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES, default=Operation.CHECK)

    def __str__(self):
        return '{}'.format(self.currency.name)

    def set_total(self, api):
        self.total = self.free + self.locked
        price_info = api.get_price(self.currency.name, self.total)
        self.price = Decimal(price_info['price'])
        self.usdt = Decimal(price_info['USDT'])
        self.save()
