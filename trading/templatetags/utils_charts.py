import time
from datetime import datetime
from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def to_point(value):
    return str(value).replace(",", ".")


@register.simple_tag
def diff_percent(from_price, to_price, is_round=False):
    if from_price and to_price:
        diff_percent = 100 * from_price / to_price - 100
        if is_round:
            diff_percent = int(diff_percent)
        return diff_percent


@register.simple_tag
def progress_price(buy_price, sell_price, current_price):
    """Высчитывает где сейчас находится цена по отношению покупки и продажи"""

    buy_price = Decimal(buy_price or 0)
    sell_price = Decimal(sell_price or 0)
    current_price = Decimal(current_price or 0)
    is_increase = True
    if buy_price > current_price:
        is_increase = False
        temp = buy_price
        buy_price = current_price
        current_price = temp
    if buy_price >= 0 and sell_price > 0 and current_price > 0:
        middle_price = current_price - buy_price
        wait_price = sell_price - buy_price
        diff_percent = int(100 * middle_price / wait_price )
        return {'value': diff_percent, 'is_increase': is_increase}
    return {'value': 0, 'is_increase': is_increase}


@register.filter
def print_timestamp(timestamp):
    """Конвертируем миллисекунды во время"""
    dt = datetime.fromtimestamp(int(timestamp)/1000.0)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
