class TechnicalAnalysis(object):

    BUY_ENSURE_COEF = 1.5
    CANDLE_4H_PERIOD = 14400
    CANDLE_2H_PERIOD = 7200
    PERIOD_MOD = 3
    CANDLES_NUM = 4 * PERIOD_MOD
    HIGHER_COEF = 1.55
    LOWER_COEF = 3.7
    VOL_COEF = 1.9
    MAX_VOL_COEF = 5.5
    NUM_OF_PAIRS = 9
    MIN_PAIRS = 1
    TRADE_AMOUNT = 0.1
    DEPTH_OF_SELLING_GLASS = 200
    STOP_LOSS = 0.75
    TAKE_PROFIT = 1.7
    COEF_LEVEL = 0.001
    COEF_ALL_CANDLE_MIN = 2
    COEF_ALL_CANDLE_MID = 3.2
    COEF_ALL_CANDLE_MAX = 5.5
    COEF_HIGH_LOW_MIN = 0.5
    COEF_HIGH_LOW_MAX = 2
    MIN_VOLUME_TO_TRADE = 500
    SWORD_MULTIPLIER = 2
    HUMMER_MULTIPLIER = 2

    def __init__(self, market=None):

        if market:
            self.COEF_LEVEL = market.base_currency.coef_level
            self.COEF_ALL_CANDLE_MIN = market.base_currency.coef_all_candle_min
            self.COEF_ALL_CANDLE_MID = market.base_currency.coef_all_candle_mid
            self.COEF_ALL_CANDLE_MAX = market.base_currency.coef_all_candle_max
            self.COEF_HIGH_LOW_MIN = market.base_currency.coef_high_low_min
            self.COEF_HIGH_LOW_MAX = market.base_currency.coef_high_low_max
            self.SWORD_MULTIPLIER = market.base_currency.sword_multilier
            self.HUMMER_MULTIPLIER = market.base_currency.hummer_multiplier

    @staticmethod
    def is_green(candle):
        return True if candle['close'] >= candle['open'] else False

    @staticmethod
    def is_red(candle):
        return True if candle['open'] >= candle['close'] else False

    @staticmethod
    def is_min_value(candle, min_value):
        print('------------- ========= ', candle['value'])
        return True if candle['value'] > min_value else False

    @staticmethod
    def is_compare_value(candle, candle_previous):
        # print('candle', candle)
        # print('candle_previous', candle_previous)
        return True if candle['value'] > candle_previous['value'] else False

    @staticmethod
    def is_ratio_open_close(candle, candle_previous, ratio_open_close):
        first_condition = False
        second_condition = False

        if max(candle_previous['open'], candle_previous['close']) / \
                min(candle_previous['open'], candle_previous['close']) > ratio_open_close:
            first_condition = True
            print("ratio prev condition {}".format(first_condition))

        if max(candle['open'], candle['close']) / \
                min(candle['open'], candle['close']) > ratio_open_close:
            second_condition = True
            print("ratio current condition {}".format((second_condition)))

        return True if first_condition and second_condition else False

    @staticmethod
    def is_sma(candle):
        return True if candle['sma'] > candle['open'] else False

    @staticmethod
    def is_cross(fast_previous, slow_previous, fast, slow):
        # print('=========================== CHECK IS CROSS!!!! =========================')
        # print(fast_previous, slow_previous, fast, slow)
        # print(fast_previous, slow_previous, fast, slow)
        if fast_previous and slow_previous and fast and slow:
            # print((slow_previous - fast_previous) * (slow - fast))
            if ((slow_previous - fast_previous) * (slow - fast)) < 0:
                y = (fast + fast_previous + slow + slow_previous) / 4
                # print('y', Decimal(y).quantize(Decimal('.00000000')))
                if y:
                    # print('=========================== CROSS!!!! =========================')
                    # time.sleep(3)
                    return True
        return False

    @staticmethod
    def heikin_ashi(candle, candle_previous, ha_previous=None):
        """
        xClose = (Open+High+Low+Close)/4
        o Average price of the current bar

        xOpen = [xOpen(Previous Bar) + xClose(Previous Bar)]/2
        o Midpoint of the previous bar

        xHigh = Max(High, xOpen, xClose)
        o Highest value in the set

        xLow = Min(Low, xOpen, xClose)
        o Lowest value in the set

        Read more: Heikin-Ashi: A Better Candlestick
        https://www.investopedia.com/articles/technical/04/092204.asp#ixzz55OHVMTuJ

        :param ha_previous:
        :param candle_previous:
        :param candle:
        :return:
        """
        ha_close = (candle['open'] + candle['high'] + candle['low'] + candle['close']) / 4
        if ha_previous:
            ha_open = (ha_previous['open'] + ha_previous['close']) / 2
        elif candle_previous:
            ha_open = (candle_previous['open'] + candle_previous['close']) / 2
        else:
            ha_open = (candle['open'] + candle['close']) / 2

        ha = {
            'close': ha_close,
            'open': ha_open,
            'high': max(candle['high'], ha_close, ha_open),
            'low': min(candle['low'], ha_close, ha_open),
            'value': candle['value'],
        }
        return ha

    def is_dodge(self, candle):

        # coef = 0.001        # USDT
        # coef = 0.00000001   # BTC

        # if candle['open'] in (0.000032301400791334855, 698.184840901419):
        #     print('DODGE =============================', candle['low'])
        #     print((candle['high'] - candle['low']) / (
        #             abs(candle['close'] - candle['open']) + self.COEF_LEVEL))
        #     print(self.COEF_ALL_CANDLE_MAX, self.COEF_HIGH_LOW_MIN)
        #     print(((candle['high'] - max([candle['close'], candle['open']])) / (
        #             min([candle['close'], candle['open']]) - candle['low'] + self.COEF_LEVEL)))
        #     print(self.COEF_HIGH_LOW_MAX)
        #     print((candle['high'] - candle['low']) / (
        #             abs(candle['close'] - candle['open']) + self.COEF_LEVEL), '>', self.COEF_ALL_CANDLE_MAX , 'and' , self.COEF_HIGH_LOW_MIN ,'<', (
        #             candle['high'] - max([candle['close'], candle['open']])) / (
        #             min([candle['close'], candle['open']]) - candle['low'] + self.COEF_LEVEL),'<', self.COEF_HIGH_LOW_MAX)
        if (candle['high'] - candle['low']) / (
                abs(candle['close'] - candle['open']) + self.COEF_LEVEL) > self.COEF_ALL_CANDLE_MAX and self.COEF_HIGH_LOW_MIN < (
                candle['high'] - max([candle['close'], candle['open']])) / (
                min([candle['close'], candle['open']]) - candle['low'] + self.COEF_LEVEL) < self.COEF_HIGH_LOW_MAX:
            # print('++++++++++++++++++++++++++++++++ DODGE')
            return True
        else:
            return False

    def is_hummer(self, candle):
        higth_part = candle['high'] - max([candle['open'], candle['close']])
        middle = candle['open'] - candle['close']
        low_part = min([candle['open'], candle['close']]) - candle['low']

        return True if (higth_part + (abs(middle) * self.HUMMER_MULTIPLIER)) < low_part else False

    def is_sword(self, candle):
        higth_part = candle['high'] - max([candle['open'], candle['close']])
        middle = candle['open'] - candle['close']
        low_part = min([candle['open'], candle['close']]) - candle['low']

        return True if (abs(middle) + (low_part * self.SWORD_MULTIPLIER)) < higth_part else False

    def is_simple(self, candle):
        return True if not self.is_dodge(candle) and not self.is_hummer(candle) and not self.is_sword(candle) else False

    def is_fat(self, candle):
        if self.COEF_ALL_CANDLE_MID > (candle['high'] - candle['low']) / (
                abs(candle['close'] - candle['open']) + 0.0001) > self.COEF_ALL_CANDLE_MIN and self.COEF_HIGH_LOW_MIN < (
                candle['high'] - max([candle['close'], candle['open']])) / (
                min([candle['close'], candle['open']]) - candle['low'] + 0.0001) < self.COEF_HIGH_LOW_MAX:
            return True
        else:
            return False

    @staticmethod
    def is_raise_vol(candle1, candle2):
        return True if candle2['volume'] > candle1['volume'] else False
