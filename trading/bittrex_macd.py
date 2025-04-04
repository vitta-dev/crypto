import time
import json
import requests
import urllib, http.client
import hmac, hashlib
import sqlite3

# Если нет нужных пакетов - читаем тут: https://bablofil.ru/python-indicators/
import numpy
import talib

from datetime import datetime

# API_KEY = ''
# # обратите внимание, что добавлена 'b' перед строкой
# API_SECRET = b''


API_KEY = '5b8611d4a0094bbb8e971afb47900df1'
API_SECRET = b'059c048e8ce240c8ae607136857fc54d'

# Список пар, на которые торгуем
MARKETS = [
    'USDT-BTC', 'USDT-BCC', 'USDT-ETC', 'USDT-OMG',
    'USDT-XRP', 'USDT-LTC', 'USDT-ZEC', 'USDT-XMR', 'USDT-DASH'
]

CAN_SPEND = 2  # Сколько USDT готовы вложить в бай
MARKUP = 0.001  # 0.001 = 0.1% - Какой навар со сделки хотим получать

STOCK_FEE = 0.0025  # Какую комиссию берет биржа

ORDER_LIFE_TIME = 0.5  # Через сколько минут отменять неисполненный ордер на покупку 0.5 = 30 сек.

USE_MACD = True  # True - оценивать тренд по MACD, False - покупать и продавать невзирая ни на что

BEAR_PERC = 70  # % что считаем поворотом при медведе (подробности - https://bablofil.ru/macd-python-stock-bot/
BULL_PERC = 98  # % что считаем поворотом при быке

# BEAR_PERC = 70  # % что считаем поворотом при медведе
# BULL_PERC = 100  # Так он будет продавать по минималке, как только курс пойдет вверх

API_URL = 'bittrex.com'
API_VERSION = 'v1.1'

USE_LOG = False

numpy.seterr(all='ignore')

conn = sqlite3.connect('local.db')
cursor = conn.cursor()

curr_market = None


# Свой класс исключений
class ScriptError(Exception):
    pass


# все обращения к API проходят через эту функцию
def call_api(**kwargs):
    http_method = kwargs.get('http_method') if kwargs.get('http_method', '') else 'POST'
    method = kwargs.get('method')

    nonce = str(int(round(time.time())))
    payload = {
        'nonce': nonce
    }

    if kwargs:
        payload.update(kwargs)

    uri = "https://" + API_URL + "/api/" + API_VERSION + method + '?apikey=' + API_KEY + '&nonce=' + nonce
    uri += urllib.parse.urlencode(payload)

    payload = urllib.parse.urlencode(payload)

    apisign = hmac.new(API_SECRET,
                       uri.encode(),
                       hashlib.sha512).hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": API_KEY,
               "apisign": apisign}

    conn = http.client.HTTPSConnection(API_URL, timeout=60)
    conn.request(http_method, uri, payload, headers)
    response = conn.getresponse().read()

    conn.close()

    try:
        obj = json.loads(response.decode('utf-8'))

        if 'error' in obj and obj['error']:
            raise ScriptError(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise ScriptError('Ошибка анализа возвращаемых данных, получена строка', response)


# Получаем с биржи данные, необходимые для построения индикаторов
def get_ticks(market):
    chart_data = {}
    # Получаем готовые данные свечей
    res = requests.get(
        "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName=" + market + "&tickInterval=thirtyMin")

    for item in json.loads(res.text)['result']:
        dt_obj = datetime.strptime(item['T'], '%Y-%m-%dT%H:%M:%S')
        ts = int(time.mktime(dt_obj.timetuple()))
        if not ts in chart_data:
            chart_data[ts] = {'open': float(item['O']), 'close': float(item['C']), 'high': float(item['H']),
                              'low': float(item['L'])}

    # Добираем недостающее
    res = requests.get("https://bittrex.com/api/v1.1/public/getmarkethistory?market=" + market)
    for trade in reversed(json.loads(res.text)['result']):
        try:
            dt_obj = datetime.strptime(trade['TimeStamp'], '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            dt_obj = datetime.strptime(trade['TimeStamp'], '%Y-%m-%dT%H:%M:%S')
        ts = int((time.mktime(dt_obj.timetuple()) / 1800)) * 1800  # округляем до 5 минут
        if ts not in chart_data:
            chart_data[ts] = {'open': 0, 'close': 0, 'high': 0, 'low': 0}

        chart_data[ts]['close'] = float(trade['Price'])

        if not chart_data[ts]['open']:
            chart_data[ts]['open'] = float(trade['Price'])

        if not chart_data[ts]['high'] or chart_data[ts]['high'] < float(trade['Price']):
            chart_data[ts]['high'] = float(trade['Price'])

        if not chart_data[ts]['low'] or chart_data[ts]['low'] > float(trade['Price']):
            chart_data[ts]['low'] = float(trade['Price'])

    return chart_data


# С помощью MACD делаем вывод о целесообразности торговли в данный момент (https://bablofil.ru/macd-python-stock-bot/)
def get_macd_advice(chart_data):
    macd, macdsignal, macdhist = talib.MACD(numpy.asarray([chart_data[item]['close'] for item in sorted(chart_data)]),
                                            fastperiod=12, slowperiod=26, signalperiod=9)
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

        if offset in idx and not numpy.isnan(elem):
            # тренд изменился
            max_v = curr_v = 0  # обнуляем пик спреда между линиями

    return ({'trand': trand, 'growing': growing})


# Выводит всякую информацию на экран, самое важное скидывает в Файл log.txt
def log(*args):
    if USE_LOG:
        l = open("./log.txt", 'a', encoding='utf-8')
        print(datetime.now(), *args, file=l)
        l.close()
    print(datetime.now(), *args)


# Ф-ция для создания ордера на покупку 
def create_buy(market):
    global USE_LOG
    USE_LOG = True
    log(market, 'Создаем ордер на покупку')
    log(market, 'Получаем текущие курсы')
    # Получаем публичные данные тикера
    ticker_data = call_api(method="/public/getticker", market=market)
    # Берем цену, по которой кто-то продает - стоимость комиссии заложим в цену продажи
    current_rate = float(ticker_data['result']['Ask'])
    can_buy = CAN_SPEND / current_rate
    pair = market.split('-')
    log(market, """
        Текущая цена - %0.8f
        На сумму %0.8f %s можно купить %0.8f %s
        Создаю ордер на покупку
        """ % (current_rate, CAN_SPEND, pair[0], can_buy, pair[1])
        )

    order_res = call_api(method="/market/buylimit", market=market, quantity=can_buy, rate=current_rate)
    if order_res['success']:
        cursor.execute(
            """
              INSERT INTO orders(
                  order_id,
                  order_type,
                  order_pair,
                  order_created,
                  order_price,
                  order_amount,
                  order_spent
              ) VALUES (
                :order_id,
                'buy',
                :order_pair,
                datetime(),
                :order_price,
                :order_amount,
                :order_spent
              )
            """, {
                'order_id': order_res['result']['uuid'],
                'order_pair': market,
                'order_price': current_rate,
                'order_amount': can_buy,
                'order_spent': CAN_SPEND

            })
        conn.commit()
        log("Создан ордер на покупку %s" % order_res['result']['uuid'])
    else:
        log(market, """
            Не удалось создать ордер: %s
        """ % order_res['message'])
    USE_LOG = False


# Ф-ция для создания ордера на продажу
def create_sell(from_order, market):
    global USE_LOG
    USE_LOG = True

    pair = market.split('-')
    buy_order_q = """
        SELECT order_spent, order_amount FROM orders WHERE order_id='%s'
    """ % from_order
    cursor.execute(buy_order_q)
    order_spent, order_amount = cursor.fetchone()
    new_rate = (order_spent + order_spent * MARKUP) / order_amount

    new_rate_fee = new_rate + (new_rate * STOCK_FEE) / (1 - STOCK_FEE)

    ticker_data = call_api(method="/public/getticker", market=market)
    # Берем цену, по которой кто-то покупает
    current_rate = float(ticker_data['result']['Bid'])

    choosen_rate = current_rate if current_rate > new_rate_fee else new_rate_fee

    log(market, """
        Итого на этот ордер было потрачено %0.8f %s, получено %0.8f %s
        Что бы выйти в плюс, необходимо продать купленную валюту по курсу %0.8f
        Тогда, после вычета комиссии %0.4f останется сумма %0.8f %s
        Итоговая прибыль составит %0.8f %s
        Текущий курс продажи %0.8f
        Создаю ордер на продажу по курсу %0.8f
    """
        % (
            order_spent, pair[0], order_amount, pair[1],
            new_rate_fee,
            STOCK_FEE, (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE), pair[0],
            (new_rate_fee * order_amount - new_rate_fee * order_amount * STOCK_FEE) - order_spent, pair[0],
            current_rate,
            choosen_rate,
        )
        )
    order_res = call_api(method="/market/selllimit", market=market, quantity=order_amount, rate=choosen_rate)
    if order_res['success']:
        cursor.execute(
            """
              INSERT INTO orders(
                  order_id,
                  order_type,
                  order_pair,
                  order_created,
                  order_price,
                  order_amount,
                  from_order_id
              ) VALUES (
                :order_id,
                'sell',
                :order_pair,
                datetime(),
                :order_price,
                :order_amount,
                :from_order_id
              )
            """, {
                'order_id': order_res['result']['uuid'],
                'order_pair': market,
                'order_price': choosen_rate,
                'order_amount': order_amount,
                'from_order_id': from_order

            })
        conn.commit()
        log(market, "Создан ордер на продажу %s" % order_res['result']['uuid'])
    USE_LOG = False


# Если не существует таблиц sqlite3, их нужно создать (первый запуск)
orders_q = """
  create table if not exists
    orders (
      order_id TEXT,
      order_type TEXT,
      order_pair TEXT,
      order_created DATETIME,
      order_filled DATETIME,
      order_cancelled DATETIME,
      from_order_id TEXT,
      order_price REAL,
      order_amount REAL,
      order_spent REAL
    );
"""
cursor.execute(orders_q)

# Бесконечный цикл процесса - основная логика
while True:
    try:

        for market in MARKETS:  # Проходим по каждой паре из списка в начале\
            log(market, "Получаем все неисполненные ордера по БД")
            orders_q = """
                       SELECT
                         o.order_id, 
                         o.order_type, 
                         o.order_price, 
                         o.order_amount,
                         o.order_filled,
                         o.order_created
                       FROM
                         orders o
                       WHERE
                            o.order_pair='%s' 
                            AND (    
                                    (o.order_type = 'buy' and o.order_filled IS NULL)
                                    OR 
                                    (o.order_type = 'buy' AND order_filled IS NOT NULL AND NOT EXISTS (
                                        SELECT 1 FROM orders o2 WHERE o2.from_order_id = o.order_id
                                        )
                                    )
                                    OR (
                                        o.order_type = 'sell' and o.order_filled IS NULL
                                    )
                                ) 
                            AND o.order_cancelled IS NULL
                   """ % market

            # Проходим по всем сохраненным ордерам в локальной базе
            orders_info = {}
            for row in cursor.execute(orders_q):
                orders_info[str(row[0])] = {'order_id': row[0], 'order_type': row[1], 'order_price': row[2],
                                            'order_amount': row[3], 'order_filled': row[4], 'order_created': row[5]
                                            }

            if orders_info:
                # Проверяем, были ли выполнены ранее созданные ордера, и помечаем в БД. 
                log(market, "Получены неисполненные ордера из БД", orders_info)
                for order in orders_info:
                    if not orders_info[order]['order_filled']:
                        log(market, "Проверяем состояние ордера %s" % order)
                        order_info = call_api(method="/account/getorder", uuid=orders_info[order]['order_id'])['result']

                        if order_info['Closed'] and not order_info['CancelInitiated']:
                            log(market, 'Ордер %s уже выполнен!' % order)
                            cursor.execute(
                                """
                                  UPDATE orders
                                  SET
                                    order_filled=datetime(),
                                    order_price=:order_price,
                                    order_amount=:order_amount,
                                    order_spent=order_spent + :fee
                                  WHERE
                                    order_id = :order_id
            
                                """, {
                                    'order_id': order,
                                    'order_price': order_info['Price'],
                                    'order_amount': order_info['Quantity'],
                                    'fee': float(order_info["CommissionPaid"])
                                }
                            )
                            conn.commit()
                            log(market, "Ордер %s помечен выполненным в БД" % order)
                            orders_info[order]['order_filled'] = datetime.now()
                        elif order_info['Closed'] and order_info['CancelInitiated']:
                            log(market, 'Ордер %s отменен!' % order)
                            cursor.execute(
                                """
                                  UPDATE orders
                                  SET
                                    order_cancelled=datetime(),
                                    order_price=:order_price,
                                    order_amount=:order_amount,
                                    order_spent=order_spent + :fee
                                  WHERE
                                    order_id = :order_id
            
                                """, {
                                    'order_id': order,
                                    'order_price': order_info['Price'],
                                    'order_amount': order_info['Quantity'],
                                    'fee': float(order_info["CommissionPaid"])
                                }
                            )
                            conn.commit()
                            log(market, "Ордер %s помечен отмененным в БД" % order)
                            orders_info[order]['order_cancelled'] = datetime.now()

                        else:
                            log(market, "Ордер %s еще не выполнен" % order)
                            if order_info['QuantityRemaining'] != order_info['Quantity']:
                                orders_info[order]['partially_filled'] = True

                for order in orders_info:
                    if orders_info[order]['order_type'] == 'buy':
                        if orders_info[order]['order_filled']:  # если ордер на покупку был выполнен

                            if USE_MACD:
                                macd_advice = get_macd_advice(
                                    chart_data=get_ticks(market))  # проверяем, можно ли создать sell
                                if macd_advice['trand'] == 'BEAR' or (
                                        macd_advice['trand'] == 'BULL' and macd_advice['growing']):
                                    log(market,
                                        'Для ордера %s не создаем ордер на продажу, т.к. ситуация на рынке неподходящая' % order)
                                else:
                                    log(market, "Для выполненного ордера на покупку выставляем ордер на продажу")
                                    create_sell(from_order=orders_info[order]['order_id'], market=market)
                            else:  # создаем sell если тенденция рынка позволяет
                                log(market, "Для выполненного ордера на покупку выставляем ордер на продажу")
                                create_sell(from_order=orders_info[order]['order_id'], market=market)
                        else:  # Если buy не был исполнен, и прошло достаточно времени для отмены ордера, отменяем
                            if not orders_info[order]['partially_filled'] and not orders_info[order]['order_cancelled']:
                                time_passed = time.time() - int(orders_info[order]['order_created'])
                                if time_passed > ORDER_LIFE_TIME * 60:
                                    log('Пора отменять ордер %s' % order)
                                    cancel_res = call_api(method="/market/cancel", uuid=order)
                                    if cancel_res['success']:
                                        cursor.execute(
                                            """
                                              UPDATE orders
                                              SET
                                                order_cancelled=datetime()
                                              WHERE
                                                order_id = :order_id
    
                                            """, {
                                                'order_id': order
                                            }
                                        )
                                        conn.commit()
                                        log(market, "Ордер %s помечен отмененным в БД" % order)
                    else:  # ордер на продажу
                        pass
            else:
                log(market, "Неисполненных ордеров в БД нет, пора ли создать новый?")
                # Проверяем MACD, если рынок в нужном состоянии, выставляем ордер на покупку
                if USE_MACD:
                    macd_advice = get_macd_advice(chart_data=get_ticks(market))
                    if macd_advice['trand'] == 'BEAR' and macd_advice['growing']:
                        log(market, "Создаем ордер на покупку")
                        create_buy(market=market)
                    else:
                        log(market, "Условия рынка не подходят для торговли", macd_advice)
                else:
                    log(market, "Создаем ордер на покупку")
                    create_buy(market=market)

        time.sleep(1)
    except Exception as e:
        print(e)
