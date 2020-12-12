import json
import logging
import smtplib

import time

import datetime
from poloniex import Poloniex
from creds import POLONIEX_API_KEY, POLONIEX_SECRET_KEY, GMAIL_USER, GMAIL_PASSWORD

PAIRS = [
    'USDT_ETC',
    'USDT_ETH',
    'USDT_XRP',
    'USDT_LTC',
    'USDT_XMR',
    'USDT_STR',
    'USDT_ZEC',
    'USDT_DASH',
    'USDT_REP',
    'USDT_NXT'
]

BUY_ENSURE_COEF = 1.5
CANDLE_PERIOD = 86400
CANDLES_NUM = 4
HIGHER_COEF = 1.68
LOWER_COEF = 3
VOL_COEF = 1.8
MAX_VOL_COEF = 8.5
NUM_OF_PAIRS = 9
MIN_PAIRS = 2
TRADE_AMOUNT = 12000
DEPTH_OF_SELLING_GLASS = 50
STOP_LOSS = 0.75
COEF_ALL_CANDLE_MIN = 1.5
COEF_ALL_CANDLE_MID = 3.2
COEF_ALL_CANDLE_MAX = 5.8
COEF_HIGH_LOW_MIN = 0.5
COEF_HIGH_LOW_MAX = 2


class Gmail(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.server = 'smtp.gmail.com'
        self.port = 587
        session = smtplib.SMTP(self.server, self.port)
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.email, self.password)
        self.session = session

    def send_message(self, subject, body):
        """ This must be removed """
        headers = [
            "From: " + self.email,
            "Subject: " + subject,
            "To: " + self.email,
            "MIME-Version: 1.0",
            "Content-Type: text/html"]
        headers = "\r\n".join(headers)
        self.session.sendmail(
            self.email,
            self.email,
            headers + "\r\n\r\n" + body)


def create_poloniex_connection():
    polo = Poloniex()
    polo.key = POLONIEX_API_KEY
    polo.secret = POLONIEX_SECRET_KEY
    return polo


def is_dodge(candle):
    if (candle['high'] - candle['low']) / (
                abs(candle['close'] - candle['open']) + 0.0001) > COEF_ALL_CANDLE_MAX and COEF_HIGH_LOW_MAX < (
                candle['high'] - max([candle['close'], candle['open']])) / (
                    min([candle['close'], candle['open']]) - candle['low'] + 0.0001) < COEF_ALL_CANDLE_MIN:
        return True
    else:
        return False


def is_fat(candle):
    if COEF_ALL_CANDLE_MID > (candle['high'] - candle['low']) / (
                abs(candle['close'] - candle['open']) + 0.0001) > COEF_ALL_CANDLE_MIN and COEF_HIGH_LOW_MIN < (
                candle['high'] - max([candle['close'], candle['open']])) / (
                    min([candle['close'], candle['open']]) - candle['low'] + 0.0001) < COEF_HIGH_LOW_MAX:
        return True
    else:
        return False


def check_hard_condition(candle):
    candle_close = candle['close']
    candle_open = candle['open']
    candle_high = candle['high']
    candle_low = candle['low']

    if candle_close > candle_open:
        close_open = candle_close - candle_open
        high_candle = candle_high - candle_close
        candle_low = candle_open - candle_low if \
            candle_open != candle_low else 0.0001
    elif candle_close < candle_open:
        close_open = candle_open - candle_close
        high_candle = candle_high - candle_open
        candle_low = candle_close - candle_low if \
            candle_close != candle_low else 0.0001
    else:
        close_open = 0.0001
        candle_low = candle_close - candle_low if \
            candle_close != candle_low else 0.0001
        high_candle = candle_high - candle_open
    if high_candle / close_open > HIGHER_COEF \
            and high_candle / candle_low > LOWER_COEF:
        return False
    else:
        return True


def main():
    polo = create_poloniex_connection()
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        filename='{}log/logger{}.log'.format(PROJECT_PATH,
                                                             time.strftime('%Y_%m_%d', datetime.datetime.now(
                                                             ).timetuple())))
    with open(PROJECT_PATH + 'bot_daily_btc_pairs.json') as data_file:
        pairs_bought = json.load(data_file)
    with open(PROJECT_PATH + 'bot_daily_btc_date.json') as data_file:
        last_bought_date = json.load(data_file)
    if pairs_bought != '':
        if pairs_bought != 'no pairs':
            balances = polo.returnBalances()
            null_balances_pairs = 0
            for pair in pairs_bought:
                altcoin_amount = float(balances[pair['name'].split('_')[-1]])
                current_buy_glass = polo.returnOrderBook(pair['name'])['bids']
                sum_previous = 0
                sell_price = 0
                for order in current_buy_glass:
                    sum_previous += float(order[1])
                    if float(sum_previous) >= BUY_ENSURE_COEF * altcoin_amount:
                        while True:
                            sell_price = float(order[0])
                            if sell_price != 0:
                                break
                            else:
                                logging.info('Sell price of {} = 0'.format(pair['name']))
                        break
                if altcoin_amount > 0 and \
                        (time.time() - last_bought_date >= CANDLE_PERIOD or sell_price < STOP_LOSS * pair['price']):
                    polo.sell(pair['name'], sell_price, altcoin_amount)
                    logging.info(
                        'Selling {} {}. Price: {}'.format(altcoin_amount, pair['name'].split('_')[-1], sell_price))

                    gm = Gmail(GMAIL_USER, GMAIL_PASSWORD)
                    gm.send_message('SELL_DAILY', 'Selling {} {}. Price: {}. Time: {}'.format(
                        altcoin_amount, pair['name'].split('_')[-1], sell_price, datetime.datetime.now()))
                if float(polo.returnBalances()[pair['name'].split('_')[-1]]) > 0:
                    null_balances_pairs += 1

            if (time.time() - float(last_bought_date)) >= CANDLE_PERIOD and null_balances_pairs == 0:
                with open(PROJECT_PATH + 'bot_daily_btc_pairs.json', 'w') as f:
                    json.dump('', f)
        else:
            if (time.time() - float(last_bought_date)) >= CANDLE_PERIOD:
                with open(PROJECT_PATH + 'bot_daily_btc_pairs.json', 'w') as f:
                    json.dump('', f)
    with open(PROJECT_PATH + 'bot_daily_btc_pairs.json') as data_file:
        pairs_bought = json.load(data_file)
    if pairs_bought == '':
        pairs_info = []
        for pair in PAIRS:
            candles_data = polo.returnChartData(
                pair, period=CANDLE_PERIOD, start=int(time.time()) - CANDLE_PERIOD * CANDLES_NUM)[:-1]
            data = [
                {'high': float(candle['high']), 'low': float(candle['low']), 'volume': float(candle['volume']),
                 'close': float(candle['close']), 'open': float(candle['open'])}
                for candle in candles_data
            ]
            if (data[1]['close'] > data[1]['open'] or data[2]['close'] > data[2]['open']) and ((
                        check_hard_condition(
                            data[2]) and MAX_VOL_COEF > data[2]['volume'] / data[1]['volume'] > VOL_COEF) or (
                        (check_hard_condition(
                            data[1]) and MAX_VOL_COEF > data[1]['volume'] / data[0]['volume'] > VOL_COEF) and (
                                is_dodge(data[2]) or is_fat(data[2])))):
                pairs_info.append({
                    'name': pair,
                    'coef': data[1]['volume'] / data[0]['volume']
                })
        logging.info('Number of pairs: {}'.format(len(pairs_info)))
        pairs_info = sorted(pairs_info, key=lambda k: k['coef'], reverse=True)[:NUM_OF_PAIRS] if len(
            pairs_info) >= MIN_PAIRS else []
        balances = polo.returnBalances()
        current_usdt = float(balances['USDT'])
        if len(pairs_info) > 0:
            buy_amount = TRADE_AMOUNT / len(pairs_info) if current_usdt > TRADE_AMOUNT else current_usdt / len(
                pairs_info)
            for pair_info in pairs_info:
                current_sell_glass = [
                    [float(order[0]), float(order[1]), float(order[0]) * float(order[1])]
                    for order in polo.returnOrderBook(pair_info['name'], depth=DEPTH_OF_SELLING_GLASS)['asks']
                ]
                sum_previous = 0
                order_price = 0
                for order in current_sell_glass:
                    sum_previous += order[2]
                    if sum_previous >= BUY_ENSURE_COEF * buy_amount:
                        order_price = order[0]
                        break
                if order_price:
                    polo.buy(pair_info['name'], order_price, buy_amount / order_price)
                    logging.info('Buying {} for {} USDT'.format(pair_info['name'].split('_')[-1], buy_amount))
                    pair_info['price'] = order_price

                    gm = Gmail(GMAIL_USER, GMAIL_PASSWORD)
                    gm.send_message(
                        'BUY_DAILY', 'Buying {}{} for {} USDT with rate {} at {}'.format(
                            buy_amount / order_price, pair_info['name'].split(
                                '_')[-1], buy_amount, order_price, datetime.datetime.now()))
            with open(PROJECT_PATH + 'bot_daily_btc_pairs.json', 'w') as f:
                json.dump([{'name': p['name'], 'price': p['price']} for p in pairs_info], f)
        else:
            with open(PROJECT_PATH + 'bot_daily_btc_pairs.json', 'w') as f:
                json.dump('no pairs', f)
        with open(PROJECT_PATH + 'bot_daily_btc_date.json', 'w') as f:
            json.dump(time.time(), f)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception('message')
