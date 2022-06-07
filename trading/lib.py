import time

from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import *

# Если нет нужных пакетов - читаем тут: https://bablofil.ru/python-indicators/
import numpy
import pytz
import talib
from django.conf import settings
from django.utils import timezone

from trading.backedns.bittrex.config import BEAR_PERC, BULL_PERC, CAN_SPEND, MARKUP, STOCK_FEE


def print_debug(str_print):
    if settings.BOT_PRINT_DEBUG:
        print(str_print)


def split_to_chunks(ll, chunk_size):
    chunk_size_counter = 0
    chunk = []
    for item in ll:
        chunk.append(item)
        chunk_size_counter += 1
        if chunk_size_counter == chunk_size:
            yield chunk
            chunk = []
            chunk_size_counter = 0

    if chunk:
        yield chunk


def convert_number(value):
    try:
        return Decimal(value).quantize(Decimal('.00000000'))
    except InvalidOperation:
        return value


def convert_ticker_to_decimal(res_ticker_data):
    ticker_data = {}
    if res_ticker_data:
        for k in res_ticker_data:
            if res_ticker_data[k]:
                ticker_data[k] = convert_number(res_ticker_data[k])

    return ticker_data


def convert_number_to_float(value):
    try:
        return float(value)
    except ValueError:
        return value


def convert_ticker_to_float(res_ticker_data):
    ticker_data = {}
    if res_ticker_data:
        for k in res_ticker_data:
            if res_ticker_data[k]:
                ticker_data[k] = convert_number_to_float(res_ticker_data[k])

    return ticker_data


def convert_date(date_str, date_format='%Y-%m-%dT%H:%M:%S'):
    if isinstance(date_str, int):
        datetime_obj_utc = datetime.fromtimestamp(date_str/1000)
        return datetime_obj_utc
    if isinstance(date_str, str):
        datetime_obj = datetime.strptime(date_str, date_format)
        datetime_obj_utc = datetime_obj.replace(tzinfo=pytz.timezone('UTC'))
        return datetime_obj_utc


def round_time(dt=None, round_to=None, round_to_hours=None):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """

    # dm = datetime.min.replace(tzinfo=pytz.timezone('UTC'))
    # dt = dt + (dm - dt) % date_delta

    # dt += date_delta
    # dt -= timedelta(minutes=dt.minute % 30,
    #                 seconds=dt.second,
    #                 microseconds=dt.microsecond)

    if round_to:
        discard = timedelta(minutes=dt.minute % round_to,
                            seconds=dt.second,
                            microseconds=dt.microsecond)
        dt -= discard
        if discard >= timedelta(minutes=round_to):
            dt += timedelta(minutes=round_to)

    if round_to_hours:
        discard = timedelta(hours=dt.hour % round_to_hours,
                            minutes=dt.minute,
                            seconds=dt.second,
                            microseconds=dt.microsecond)
        dt -= discard
        if settings.BOT_PRINT_DEBUG:
            print('round_to_hours', round_to_hours)
            print('discard', discard)
        if discard >= timedelta(hours=round_to_hours):
            dt += timedelta(hours=round_to_hours)

    return dt

    # round_to = date_delta.total_seconds()
    # print('not convert - ', dt)
    # print('round_time')
    # print('round_to', round_to)
    # print('date_delta', date_delta)
    #
    # if dt == None : dt = timezone.now()
    # # k = dt.min.replace(tzinfo=pytz.timezone('UTC'))
    # seconds = (dt - dt.min.replace(tzinfo=pytz.timezone('UTC'))).seconds
    # print('seconds', seconds)
    # # // is a floor division, not a comment on following line:
    # rounding = (seconds + round_to/2) // round_to * round_to
    # print('rounding', rounding)
    # print(timedelta(0, rounding-seconds, -dt.microsecond))
    # print(timedelta(0, rounding - seconds - 1, -dt.microsecond))
    # print(dt + timedelta(0, rounding, -dt.microsecond))
    # print(dt + timedelta(0, rounding-seconds, -dt.microsecond))
    # print('end')
    # return dt + timedelta(0, rounding-seconds, -dt.microsecond)


def convert_ticker(chart_data, round_to=None, round_to_hours=None):
    """
    Конвертируем свечи в больший период
    :param round_to:
    :param chart_data:
    :return:
    """

    new_chart_data = OrderedDict()

    for dt_obj in chart_data:
        # округляем до date_delta
        # if settings.BOT_PRINT_DEBUG:
        #     print('---')
        #     print('not convert ', dt_obj)
        new_dt_obj = round_time(dt_obj, round_to, round_to_hours)
        # if settings.BOT_PRINT_DEBUG:
        #     print('converted - ', new_dt_obj)
        #     print(chart_data[dt_obj])
        if new_dt_obj not in new_chart_data:
            new_chart_data[new_dt_obj] = {
                'open': chart_data[dt_obj]['open'],
                'close': chart_data[dt_obj]['close'],
                'high': chart_data[dt_obj]['high'],
                'low': chart_data[dt_obj]['low'],
                'value': chart_data[dt_obj]['value'],
            }
        else:
            new_chart_data[new_dt_obj]['close'] = chart_data[dt_obj]['close']
            new_chart_data[new_dt_obj]['value'] += chart_data[dt_obj]['value']

            if chart_data[dt_obj]['low'] < new_chart_data[new_dt_obj]['low']:
                new_chart_data[new_dt_obj]['low'] = chart_data[dt_obj]['low']

            if chart_data[dt_obj]['high'] > new_chart_data[new_dt_obj]['high']:
                new_chart_data[new_dt_obj]['high'] = chart_data[dt_obj]['high']
        # if settings.BOT_PRINT_DEBUG:
        #     print(new_chart_data[new_dt_obj])

    return new_chart_data


def get_price_for_buy(ticker_data):
    # return ticker_data['Bid'] - satoshi_1
    rate = Decimal(ticker_data['Bid'])
    try:
        rate = rate.quantize(Decimal('.00000000'))
    except (InvalidOperation, AttributeError):
        pass
    return rate


def get_price_for_sell(ticker_data) -> Decimal:
    """Возвращает текущий курс на основе данных с биржи"""
    # return ticker_data['Ask'] - satoshi_1

    rate = Decimal(ticker_data['Ask'])
    try:
        rate = rate.quantize(Decimal('.00000000'))
    except (InvalidOperation, AttributeError):
        pass
    return rate


def add_stock_fee(rate):
    # new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)
    new_rate = rate + (rate * STOCK_FEE * 2)
    return new_rate


def get_macd_advice(chart_data):
    # С помощью MACD делаем вывод о целесообразности торговли в данный момент
    # (https://bablofil.ru/macd-python-stock-bot/)

    print('get_macd_advice')
    macd, macdsignal, macdhist = talib.MACD(numpy.asarray([chart_data[item]['close'] for item in sorted(chart_data)]),
                                            fastperiod=12, slowperiod=26, signalperiod=9)
    # print('macd', macd)
    # print('macdsignal', macdsignal)
    # print('macdhist', macdhist)
    idx = numpy.argwhere(numpy.diff(numpy.sign(macd - macdsignal)) != 0).reshape(-1) + 0

    trand = 'BULL' if macd[-1] > macdsignal[-1] else 'BEAR'

    max_v = 0

    activity_time = False
    growing = False

    for offset, elem in enumerate(macdhist):

        growing = False

        curr_v = macd[offset] - macdsignal[offset]
        if abs(curr_v) > abs(max_v):
            max_v = curr_v
        perc = curr_v / max_v

        if ((macd[offset] > macdsignal[offset] and perc * 100 > BULL_PERC)  # восходящий тренд
                or (macd[offset] < macdsignal[offset] and perc * 100 < (100 - BEAR_PERC))):
            activity_time = True
            growing = True
        #     print('# восходящий тренд')
        # else:
        #     print('# else')

        if offset in idx and not numpy.isnan(elem):
            # тренд изменился
            # обнуляем пик спреда между линиями
            max_v = 0
            curr_v = 0

    return {'trand': trand, 'growing': growing}
