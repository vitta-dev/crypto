from django.urls import path

import trading.views

urlpatterns = [

    path('stats/', trading.views.stats, name='stats'),
    path('stats/<slug:bot_name>/', trading.views.stats, name='stats-bot'),

    path('charts/', trading.views.charts, name='charts'),
    path('chart/<slug:market_name>/', trading.views.charts, name='chart-market'),
    path('chart/<slug:market_name>/<slug:bot_name>/', trading.views.charts, name='chart-market-bot'),

    path('test-bot/<slug:bot_name>/', trading.views.check_bot_strategy, name='test-bot'),
    path('test-bot/<slug:bot_name>/<slug:market_name>/', trading.views.check_bot_strategy, name='test-bot-market'),

]
