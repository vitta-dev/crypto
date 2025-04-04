from django.urls import path

import statistic.views

urlpatterns = [

    path('main/', statistic.views.index, name='main'),
    path('main/bittrex/', statistic.views.index, {'exchange_name': 'bittrex'}, name='main-bittrex'),
    path('main/<slug:exchange_name>/<slug:market_name>/', statistic.views.orders, name='orders-list'),
    path('period/', statistic.views.stat_by_period, name='period'),
    path('orders/', statistic.views.list_orders, name='orders'),
    path('order/<int:order_id>', statistic.views.order_detail, name='order-detail'),
    path('order/<int:order_id>/panic_sell/', statistic.views.order_panic_sell, name='order-panic-sell'),

]
