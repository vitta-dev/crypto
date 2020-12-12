import datetime

from django import forms
from django.utils import timezone

import re
import logging
import time
from decimal import Decimal

from collections import Iterable
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q

from trading.models import MarketBot, MarketMyOrder

DEFAULT_ITEMS_PER_PAGE = 25


def paginate(items, page_number, items_per_page=DEFAULT_ITEMS_PER_PAGE):

    page_number = page_number or 1

    if items_per_page is None:
        items_per_page = DEFAULT_ITEMS_PER_PAGE

    items_per_page = int(items_per_page or 0)
    pager = Paginator(items, items_per_page)

    try:
        page = pager.page(page_number)
    except PageNotAnInteger:
        page = pager.page(1)
    except EmptyPage:
        page = pager.page(pager.num_pages)

    return page


def get_default_created_at_from():
    return timezone.localtime(timezone.now()).date() - datetime.timedelta(days=30)


class OrderFilter(forms.Form):

    date_from = forms.DateField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    bot = forms.ModelChoiceField(MarketBot.objects, required=False, )

    search = forms.CharField(required=False)

    @staticmethod
    def get_query():

        orders = MarketMyOrder.objects.filter(type=MarketMyOrder.Type.BUY, kind=MarketMyOrder.Kind.MAIN)
        # orders = orders.exclude(status=MarketMyOrder.Status.CANCELED)
        orders = orders.prefetch_related('bot', 'market').order_by('-id')

        return orders

    def apply_filter(self):
        items = self.get_query()
        assert self.is_valid(), str(dict(self.errors))
        data = self.cleaned_data

        if data['search']:
            items = items.filter(market__name__icontains=data['search'])

        if data['date_from']:
            items = items.filter(created_at__gte=data['date_from'])

        if data['date_to']:
            items = items.filter(created_at__lt=data['date_to'] + datetime.timedelta(days=1))

        # if data['status']:
        #     items = items.filter(status__in=data['status'])

        if data['bot']:
            items = items.filter(bot=data['bot'])

        return items

    def get_items_per_page(self):
        # data = self.cleaned_data
        # if data['items_per_page']:
        #     return data['items_per_page']
        # else:
        return 20

    def __init__(self, user, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Copy so we do not mess initial dict and don't get exception on Immutable GET
        data = self.data.copy()
        self.data = data

        # # Set default values here:
        # data['useragent_type'] = data.get('useragent_type', '').strip('. ')
        # data['items_per_page'] = data.get('items_per_page', 100)

        date = data.get('date')
        if date:
            data['date_from'] = date
            data['date_to'] = date
        # else:
        #     data.setdefault('date_from', get_default_created_at_from())

        print(data)
