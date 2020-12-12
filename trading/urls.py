from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

import trading.views

urlpatterns = [
    url('^stats/$', trading.views.stats, name='stats'),
    url('^stats/(?P<bot_name>[\w-]+)/$', trading.views.stats, name='stats-bot'),

    url('^charts/$', trading.views.charts, name='charts'),
    url('^chart/(?P<market_name>[\w-]+)/$', trading.views.charts, name='chart-market'),
    url('^chart/(?P<market_name>[\w-]+)/(?P<bot_name>[\w-]+)$', trading.views.charts, name='chart-market-bot'),

    url('^test-bot/(?P<bot_name>[\w-]+)/$', trading.views.check_bot_strategy, name='test-bot'),
    url('^test-bot/(?P<bot_name>[\w-]+)/(?P<market_name>[\w-]+)/$', trading.views.check_bot_strategy,
        name='test-bot-market'),

]
