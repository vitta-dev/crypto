#https://coinbot.club/proofs
#https://github.com/coinbitbot
# coding=utf-8
import os
import time
 
import datetime
from itertools import product
 
from poloniex import Poloniex
 
PROJECT_PATH = os.getcwd()
 
START_BTC = 1
START_ALT = 0
 
CANDLE_PERIOD = 14400
# PAIRS = ['BTC_ETH',
#          'BTC_XRP',
#          'BTC_XEM',
#          'BTC_LTC',
#          'BTC_STR',
#          'BTC_BCN',
#          'BTC_DGB',
#          'BTC_ETC',
#          'BTC_SC',
#          'BTC_DOGE',
#          'BTC_BTS',
#          'BTC_GNT',
#          'BTC_EMC2',
#          'BTC_XMR',
#          'BTC_DASH',
#          'BTC_ARDR',
#          'BTC_STEEM',
#          'BTC_NXT',
#          'BTC_ZEC',
#          'BTC_STRAT',
#          'BTC_DCR',
#          'BTC_NMC',
#          'BTC_MAID',
#          'BTC_BURST',
#          'BTC_GAME',
#          'BTC_FCT',
#          'BTC_LSK',
#          'BTC_FLO',
#          'BTC_CLAM',
#          'BTC_SYS',
#          'BTC_GNO',
#          'BTC_REP',
#          'BTC_RIC',
#          'BTC_XCP',
#          'BTC_PPC',
#          'BTC_AMP',
#          'BTC_SJCX',
#          'BTC_LBC',
#          'BTC_EXP',
#          'BTC_VTC',
#          'BTC_GRC',
#          'BTC_NAV',
#          'BTC_FLDC',
#          'BTC_POT',
#          'BTC_RADS',
#          'BTC_BELA',
#          'BTC_NAUT',
#          'BTC_BTCD',
#          'BTC_XPM',
#          'BTC_NOTE',
#          'BTC_NXC',
#          'BTC_PINK',
#          'BTC_OMNI',
#          'BTC_VIA',
#          'BTC_XBC',
#          'BTC_NEOS',
#          'BTC_PASC',
#          'BTC_BTM',
#          'BTC_SBD',
#          'BTC_VRC',
#          'BTC_BLK',
#          'BTC_BCY',
#          'BTC_XVC',
#          'BTC_HUC'
#          ]
 
PAIRS = ['BTC_ETH',
         'BTC_XRP',
         'BTC_LTC',
         'BTC_STR',
         'BTC_DOGE',
         'BTC_BTS',
         'BTC_XMR',
         'BTC_DASH',
         'BTC_MAID',
         'BTC_FCT',
         'BTC_CLAM',
         ]
 
FEE = 0.0025
DAYS = 30
CANDLES_NUM = DAYS * 6
CANDLES_NUM_FOR_12_HOURS = DAYS * 2
PERIOD_2H = 7200
# NUMS_OF_PAIRS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
NUMS_OF_PAIRS = [9]
MIN_PAIRS = [1, 2]
VOL_COEFS = [1.6, 1.8, 2]
MAX_VOL_COEFS = [5.5]
STOP_LOSS = [0.75]
TAKE_PROFITS = [1.7]
HIGHER_COEFS = [1.45, 1.55, 1.65]
LOWER_COEFS = [3.5, 3.7, 3.9]
COEF_ALL_CANDLE_MIN = [1.8, 2, 2.2]
COEF_ALL_CANDLE_MAX = [5.3, 5.5, 5.7]
COEF_ALL_CANDLE_MID = [3, 3.2, 3.4]
COEF_HIGH_LOW_MIN = [0.3, 0.5, 0.7]
COEF_HIGH_LOW_MAX = [1.8, 2, 2.2]
MIN_TRADE_VOLUME = [400, 600, 800]
SWORD_MULTIPLIER = [1.8, 2, 2.2]
HUMMER_MULTIPLIER = [1.8, 2, 2.2]
 
 
def buy(current_btc, close_price):
    return current_btc * (1 - FEE) / close_price
 
 
def sell(current_alt, close_price):
    return current_alt * (1 - FEE) * close_price
 
 
def get_all_data(pair, candle_period):
    start_time = int(time.time()) - candle_period * (CANDLES_NUM + 1)
    polo = Poloniex()
    poloniex_data = polo.returnChartData(pair, candle_period, str(start_time))
    candles_data = [
        {'high': float(candle['high']), 'low': float(candle['low']), 'volume': float(candle['volume']),
         'close': float(candle['close']), 'open': float(candle['open']), 'date': int(candle['date'])}
        for candle in poloniex_data
    ]
    for i in range(len(candles_data)):
        if candles_data[0]['date'] % 43200 != 0:
            candles_data = candles_data[1:]
            # print(len(candles_data))
        else:
            break
    if len(candles_data) % 3 == 1:
        candles_data = candles_data[:-1]
    elif len(candles_data) % 3 == 2:
        candles_data = candles_data[:-2]
    candles_12h_data = []
    candle_3na4 = []
    for candle in candles_data:
        candle_3na4.append(candle)
        if len(candle_3na4) == 3:
            candle_12h = {'high': (
                max([float(candle_3na4[0]['high']), float(candle_3na4[1]['high']), float(candle_3na4[2]['high'])])),
                'low': (min([float(candle_3na4[0]['low']), float(candle_3na4[1]['low']),
                             float(candle_3na4[2]['low'])])),
                'volume': (sum([float(candle_3na4[0]['volume']), float(candle_3na4[1]['volume']),
                                float(candle_3na4[2]['volume'])])),
                'close': float(candle_3na4[2]['close']), 'open': float(candle_3na4[0]['open']),
                'date': int(candle_3na4[0]['date'])}
            candle_3na4 = []
            candles_12h_data.append(candle_12h)
    # print(len(candles_12h_data))
 
    return candles_12h_data
 
 
def get_all_data_2h(pair, candle_period, candles_num):
    start_time = int(time.time()) - candle_period * candles_num
    polo = Poloniex()
    poloniex_data = polo.returnChartData(pair, candle_period, str(start_time))
    candles_data = [
        {'high': float(candle['high']), 'low': float(candle['low']), 'volume': float(candle['volume']),
         'close': float(candle['close']), 'open': float(candle['open']), 'date': int(candle['date'])}
        for candle in poloniex_data
    ]
    return candles_data
 
 
def is_raise_vol(candle1, candle2):
    return True if candle2['volume'] > candle1['volume'] else False
 
 
def is_green(candle):
    return True if candle['close'] >= candle['open'] else False
 
 
def is_dodge(candle, coef_all_candle_max, coef_high_low_min, coef_high_low_max):
    if (candle['high'] - candle['low']) / (abs(candle['close'] - candle['open']) + 0.0001) > coef_all_candle_max and \
                            coef_high_low_min < (candle['high'] - max([candle['close'], candle['open']])) / (
                                    min([candle['close'], candle['open']]) - candle['low'] + 0.0001
                    ) < coef_high_low_max:
        return True
    else:
        return False
 
 
def is_hummer(candle, hummer_multiplier):
    higth_part = candle['high'] - max([candle['open'], candle['close']])
    middle = candle['open'] - candle['close']
    low_part = min([candle['open'], candle['close']]) - candle['low']
 
    return True if (higth_part + (abs(middle) * hummer_multiplier)) < low_part else False
 
 
def is_sword(candle, sword_multiplier):
    higth_part = candle['high'] - max([candle['open'], candle['close']])
    middle = candle['open'] - candle['close']
    low_part = min([candle['open'], candle['close']]) - candle['low']
 
    return True if (abs(middle) + (low_part * sword_multiplier)) < higth_part else False
 
 
def is_simple(candle, c_all_cand_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult):
    return True if not is_dodge(candle, c_all_cand_max, c_h_l_min, c_h_l_max) and not is_hummer(
        candle, hummer_mult) and not is_sword(candle, sword_mult) else False
 
 
def is_fat(candle, coef_all_candle_mid, coef_all_candle_min, coef_high_low_min, coef_high_low_max):
    if coef_all_candle_mid > (candle['high'] - candle['low']) / (abs(candle['close'] - candle['open']) + 0.0001
                                                                 ) > coef_all_candle_min and \
                            coef_high_low_min < (candle['high'] - max([candle['close'], candle['open']])) / (
                                    min([candle['close'], candle['open']]) - candle['low'] + 0.0001
                    ) < coef_high_low_max:
        return True
    else:
        return False
 
 
def check_hard_condition(candle, higher_coef, lower_coef):
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
    if high_candle / close_open > higher_coef \
            and high_candle / candle_low > lower_coef:
        return False
    else:
        return True
 
 
def analyze(all_data, num_of_pairs, vol_coef, max_vol_coef, higher_coef, lower_coef, stop_loss, min_pairs, take_profit,
            min_trade_volume, c_all_c_min, c_all_c_max, c_all_c_mid, c_h_l_min, c_h_l_max, sword_mult, hummer_mult):
    res_sum = 0
    profits_sum = 0
    fails_sum = 0
    stops_sum = 0
    perc_sum = 0
    for i in range(3, CANDLES_NUM_FOR_12_HOURS):
        pairs_info = []
        date = 0
        for p in PAIRS:
            data = []
            data_2h = []
            for d in all_data:
                if d['pair'] == p:
                    data = d['data']
                    data_2h = d['data_2h']
            if date == 0:
                date = data[i]['date']
            if len(data) == CANDLES_NUM_FOR_12_HOURS:
                if data[i - 1]['volume'] > min_trade_volume and data[i - 2]['volume'] > min_trade_volume and (
                                data[i - 2]['close'] > data[i - 2]['open'] or data[i - 1]['close'] > data[i - 1]['open']
                ) and ((check_hard_condition(data[i - 1], higher_coef, lower_coef) and max_vol_coef > data[i - 1][
                    'volume'] / (data[i - 2]['volume'] + 0.0001) > vol_coef) or (
                                check_hard_condition(data[i - 2], higher_coef, lower_coef) and max_vol_coef >
                                    data[i - 2]['volume'] / (data[i - 3]['volume'] + 0.0001) > vol_coef and (
                                    is_dodge(data[i - 1], c_all_c_max, c_h_l_min, c_h_l_max) or is_fat(
                                    data[i - 1], c_all_c_mid, c_all_c_min, c_h_l_min, c_h_l_max)))):
                    pairs_info.append({
                        'name': p,
                        'koef': data[i - 1]['volume'] / data[i - 2]['volume'],
                        'open': data[i]['open'],
                        'close': data[i]['close'],
                        'low': data[i]['low'],
                        'high': data[i]['high'],
                        'date': data[i]['date'],
                        'data_2h': data_2h
                    })
        pairs_info = sorted(pairs_info, key=lambda k: k['koef'], reverse=True)[:num_of_pairs] if len(
            pairs_info) >= min_pairs else []
        profits = 0
        fails = 0
        stops = 0
        res_balance = 0
        for pair_info in pairs_info:
            candle_1 = next(pair for pair in pair_info['data_2h'] if pair['date'] == pair_info['date'])
            candle_2 = next(pair for pair in pair_info['data_2h'] if pair[
                'date'] - PERIOD_2H == pair_info['date'])
            candle_3 = next(pair for pair in pair_info['data_2h'] if pair[
                'date'] - 2 * PERIOD_2H == pair_info['date'])
            candle_4 = next(pair for pair in pair_info['data_2h'] if pair[
                'date'] - 3 * PERIOD_2H == pair_info['date'])
            if is_green(candle_1) and is_hummer(candle_1, hummer_mult):
                sell_price = (stop_loss * pair_info['open']) if (candle_1['low'] < stop_loss * pair_info['open']
                                                                 ) else candle_1['close']
                sell_price = take_profit * pair_info['open'] if candle_1['high'] > take_profit * pair_info['open'
                ] else sell_price
                if sell_price == take_profit * pair_info['open']:
                    print('{} at {} TAKE PROFIT'.format(pair_info['name'],
                                                        datetime.datetime.fromtimestamp(candle_2['date'])))
                elif sell_price == stop_loss * pair_info['open']:
                    print('{} at {} STOP LOSS'.format(pair_info['name'],
                                                      datetime.datetime.fromtimestamp(candle_2['date'])))
                else:
                    print('{} at {}'.format(pair_info['name'],
                                            datetime.datetime.fromtimestamp(candle_2['date'])))
            elif (is_green(candle_1) and is_green(candle_2) and (
                        (is_simple(candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(
                            candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and not is_raise_vol(
                            candle_1, candle_2)) or (is_simple(
                        candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_dodge(
                        candle_2, c_all_c_max, c_h_l_min, c_h_l_max) or (is_sword(candle_1, sword_mult) and is_hummer(
                                candle_2, hummer_mult))))) or (not is_green(candle_1) and is_green(candle_2) and (
                        (is_simple(candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_hummer(
                            candle_2, hummer_mult) and not is_raise_vol(candle_1, candle_2)) or (is_hummer(
                        candle_1, hummer_mult) and is_simple(
                        candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and not is_raise_vol(
                        candle_1, candle_2)))) or (not is_green(candle_1) and not is_green(candle_2) and is_sword(
                candle_1, sword_mult) and is_simple(
                candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult)) or (
                                    is_green(candle_1) and not is_green(candle_2) and is_hummer(
                                candle_1, hummer_mult) and is_simple(
                            candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and not is_raise_vol(
                        candle_1, candle_2)):
                sell_price = (stop_loss * pair_info['open']) if (
                    min([candle_1['low'], candle_2['low']]) < stop_loss * pair_info['open']
                ) else candle_2['close']
                sell_price = take_profit * pair_info['open'] if max(candle_1['high'], candle_2['high']
                                                                    ) > take_profit * pair_info['open'] else sell_price
                if sell_price == take_profit * pair_info['open']:
                    print('{} at {} TAKE PROFIT'.format(pair_info['name'],
                                                        datetime.datetime.fromtimestamp(candle_3['date'])))
                elif sell_price == stop_loss * pair_info['open']:
                    print('{} at {} STOP LOSS'.format(pair_info['name'],
                                                      datetime.datetime.fromtimestamp(candle_3['date'])))
                else:
                    print('{} at {}'.format(pair_info['name'],
                                            datetime.datetime.fromtimestamp(candle_3['date'])))
            elif (is_green(candle_1) and not is_green(candle_2) and not is_green(
                    candle_3) and is_simple(candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and (
                        (is_hummer(candle_1, hummer_mult) and is_simple(
                            candle_3, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult)) or (
                        is_sword(candle_1, sword_mult) and is_sword(candle_3, sword_mult)))) or (
                                        is_green(candle_1) and not is_green(candle_2) and is_green(
                                    candle_3) and is_simple(
                                candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(
                            candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_sword(
                candle_3, sword_mult)) or (is_green(candle_1) and is_green(candle_2) and is_green(
                candle_3) and is_simple(
                candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_hummer(
                candle_2, hummer_mult) and is_simple(
                candle_3, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult)):
                sell_price = (stop_loss * pair_info['open']) if (
                    min([candle_1['low'], candle_2['low'], candle_3['low']]
                        ) < stop_loss * pair_info['open']) else candle_3['close']
                sell_price = take_profit * pair_info['open'] if max(candle_1['high'], candle_2['high'],
                                                                    candle_3['high']) > take_profit * pair_info[
                    'open'] else sell_price
                if sell_price == take_profit * pair_info['open']:
                    print('{} at {} TAKE PROFIT'.format(pair_info['name'],
                                                        datetime.datetime.fromtimestamp(
                                                            candle_3['date'] + PERIOD_2H)))
                elif sell_price == stop_loss * pair_info['open']:
                    print('{} at {} STOP LOSS'.format(pair_info['name'],
                                                      datetime.datetime.fromtimestamp(
                                                          candle_3['date'] + PERIOD_2H)))
                else:
                    print('{} at {}'.format(pair_info['name'],
                                            datetime.datetime.fromtimestamp(candle_3['date'] + PERIOD_2H)))
            elif (is_green(candle_1) and is_green(candle_2) and is_green(candle_3) and is_green(candle_4) and is_simple(
                    candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_hummer(candle_3, hummer_mult) and is_sword(candle_4, sword_mult)) or (
                                                is_green(candle_1) and is_green(candle_2) and is_green(
                                            candle_3) and not is_green(
                                        candle_4) and is_simple(candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(
                            candle_3, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_sword(candle_4, sword_mult)) or (
                                                is_green(candle_1) and is_green(candle_2) and not is_green(
                                            candle_3) and not is_green(
                                        candle_4) and is_simple(candle_1, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(candle_2, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(
                            candle_3, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult) and is_simple(candle_4, c_all_c_max, c_h_l_min, c_h_l_max, hummer_mult, sword_mult)):
                sell_price = (stop_loss * pair_info['open']) if (
                    min([candle_1['low'], candle_2['low'], candle_3['low'], candle_4['low']]
                        ) < stop_loss * pair_info['open']) else candle_4['close']
                sell_price = take_profit * pair_info['open'] if max(
                    candle_1['high'], candle_2['high'], candle_3['high'], candle_4['high']) > take_profit * pair_info[
                    'open'] else sell_price
                if sell_price == take_profit * pair_info['open']:
                    print('{} at {} TAKE PROFIT'.format(pair_info['name'],
                                                        datetime.datetime.fromtimestamp(
                                                            candle_4['date'] + PERIOD_2H)))
                elif sell_price == stop_loss * pair_info['open']:
                    print('{} at {} STOP LOSS'.format(pair_info['name'],
                                                      datetime.datetime.fromtimestamp(
                                                          candle_4['date'] + PERIOD_2H)))
                else:
                    print('{} at {}'.format(pair_info['name'],
                                            datetime.datetime.fromtimestamp(candle_4['date'] + PERIOD_2H)))
            else:
                sell_price = (stop_loss * pair_info['open']) if (pair_info['low'] < stop_loss * pair_info['open']
                                                                 ) else pair_info['close']
                sell_price = take_profit * pair_info['open'] if pair_info['high'] > take_profit * pair_info[
                    'open'] else sell_price
                if sell_price == take_profit * pair_info['open']:
                    print('{} at 12h candle TAKE PROFIT'.format(pair_info['name']))
                elif sell_price == stop_loss * pair_info['open']:
                    print('{} at 12h candle STOP LOSS'.format(pair_info['name']))
                else:
                    print('{} at 12h candle'.format(pair_info['name']))
 
            if sell_price == stop_loss * pair_info['open']:
                stops += 1
            res = sell(buy(START_BTC, pair_info['open']), sell_price)
            if res >= START_BTC:
                profits += 1
            else:
                fails += 1
            res_balance += res
        percentage = 100 * res_balance / (START_BTC * len(pairs_info)) - 100 if len(pairs_info) >= min_pairs else 0
        perc_sum += percentage
        res_sum += res_balance
        profits_sum += profits
        fails_sum += fails
        stops_sum += stops
        print('Day: {}, perc: {}, profits: {}, fails: {}, stops: {}, pairs: {}'.format(
            datetime.datetime.fromtimestamp(date), percentage, profits, fails, stops, [p['name'] for p in pairs_info]))
    return [res_sum, profits_sum, fails_sum, stops_sum, perc_sum / ((CANDLES_NUM_FOR_12_HOURS - 3) / 2)]
 
 
def main():
    with open(PROJECT_PATH + '/12candles_fourth1.csv', 'a') as f:
        f.write(
            'num_of_pairs,vol_coef,max_vol_coef,higher_coef,lower_coef,stop_loss,min_pairs,'
            'take_profit,min_trade_volume,coef_all_candle_min,coef_all_candle_max, coef_all_candle_mid,'
            'coef_high_low_min,coef_high_low_max,sword_multiplier,hummer_multiplier,res_sum,profits,fails,stops,'
            'profit_per\n')
    all_data = []
    print('Collecting data...')
    for pair in PAIRS:
        print(pair)
        all_data.append({
            'pair': pair,
            'data': get_all_data(pair, CANDLE_PERIOD),
            'data_2h': get_all_data_2h(pair, PERIOD_2H, CANDLES_NUM_FOR_12_HOURS * 6)
        })
    for num_of_pairs, vol_coef, max_vol_coef, higher_coef, lower_coef, stop_loss, min_pairs, \
        take_profit, min_trade_volume, coef_all_candle_min, coef_all_candle_max, coef_all_candle_mid, \
        coef_high_low_min, coef_high_low_max, sword_multiplier, hummer_multiplier in product(
        NUMS_OF_PAIRS, VOL_COEFS, MAX_VOL_COEFS, HIGHER_COEFS, LOWER_COEFS, STOP_LOSS, MIN_PAIRS, TAKE_PROFITS,
        MIN_TRADE_VOLUME, COEF_ALL_CANDLE_MIN, COEF_ALL_CANDLE_MAX, COEF_ALL_CANDLE_MID, COEF_HIGH_LOW_MIN,
        COEF_HIGH_LOW_MAX, SWORD_MULTIPLIER, HUMMER_MULTIPLIER):
        res = analyze(all_data,
                      num_of_pairs,
                      vol_coef,
                      max_vol_coef,
                      higher_coef,
                      lower_coef,
                      stop_loss,
                      min_pairs,
                      take_profit,
                      min_trade_volume,
                      coef_all_candle_min,
                      coef_all_candle_max,
                      coef_all_candle_mid,
                      coef_high_low_min,
                      coef_high_low_max,
                      sword_multiplier,
                      hummer_multiplier)
        with open(PROJECT_PATH + '/12candles_fourth1.csv', 'a') as f:
            f.write(str(num_of_pairs) + ',' +
                    str(vol_coef) + ',' +
                    str(max_vol_coef) + ',' +
                    str(higher_coef) + ',' +
                    str(lower_coef) + ',' +
                    str(stop_loss) + ',' +
                    str(min_pairs) + ',' +
                    str(take_profit) + ',' +
                    str(min_trade_volume) + ',' +
                    str(coef_all_candle_min) + ',' +
                    str(coef_all_candle_max) + ',' +
                    str(coef_all_candle_mid) + ',' +
                    str(coef_high_low_min) + ',' +
                    str(coef_high_low_max) + ',' +
                    str(sword_multiplier) + ',' +
                    str(hummer_multiplier) + ',' +
                    str(res[0]) + ',' +
                    str(res[1]) + ',' +
                    str(res[2]) + ',' +
                    str(res[3]) + ',' +
                    str(res[4]) + '%' + '\n')
 
 
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # print(e)
        raise
