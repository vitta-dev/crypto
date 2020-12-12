from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

import statistic.views

urlpatterns = [
    url('^main/$', statistic.views.index, name='main'),
    url('^main/bittrex/$', statistic.views.index,  {'exchange_name': 'bittrex'}, name='main-bittrex'),
    url('^main/(?P<exchange_name>[\w-]+)/(?P<market_name>[\w-]+)/$', statistic.views.orders, name='orders-list'),
    url('^period/$', statistic.views.stat_by_period, name='period'),
    url('^orders/$', statistic.views.list_orders, name='orders'),
]
