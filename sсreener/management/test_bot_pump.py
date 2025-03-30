import websocket
import json
# import pandas as pd
import requests
from datetime import timedelta, datetime
from collections import deque
import time

from ..config import *

# Укажите токен вашего Telegram-бота и chat_id
telegram_token = TELEGRAM_BOT_TOKEN
chat_id = TELEGRAM_CHAT_ID
chat_id2 = TELEGRAM_CHAT_ID
chat_list = [chat_id2, chat_id]


def send_telegram_message(message) -> None:
    """Функция для отправки сообщения в Telegram"""
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    for c_id in chat_list:
        payload = {
            'chat_id': c_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, data=payload)

# Параметры проверки
n_minutes = 5  # Проверка за последние n минут
increase_percentage_volume = 10  # Увеличение объема в процентах
increase_percentage_price = 5  # Увеличение цены в процентах
increase_threshold_liquidations = 5  # Увеличение ликвидаций

# Очереди для хранения объемов, цен и ликвидаций
volume_history = deque()
price_history = deque()
liquidation_history = deque()


class BinanceWebSocket:

    def __init__(
            self,
            token: str,
            chat_id: str,
            minimum_total_dollars: int = 0,
            time_frame_minutes: int = 5,
            minimum_percentage_increase: int = 10
    ) -> None:

        self.socket = 'wss://fstream.binance.com/stream?streams=!miniTicker@arr'
        self.interval = "1m"

        self.minimum_total_dollars = minimum_total_dollars
        self.minimum_percentage_increase = minimum_percentage_increase
        self.set_ticker = None
        self.data_list = []
        # self.previous_volumes_df = pd.DataFrame(columns=['Symbol', 'Last Update', 'Total($)', 'Cumulative Total($)'])
        self.time_frame_minutes = time_frame_minutes
        self.time_frame = timedelta(minutes=time_frame_minutes)
        self.telegram_bot_token = token
        self.telegram_chat_id = chat_id

        # Интервал хранения истории в секундах (20 минут)
        self.WINDOW_SECONDS = 60 * 20

        self.history_send_message_price = {}
        self.history_send_message_volume = {}
        self.stop_send_massage = 60 * 2

        self.alert_count_price = {}
        self.alert_count_volume = {}

        # История по символам: ключ – символ, значение – deque с элементами (timestamp, price, volume)
        self.history = {}

        self.pump_price_percent = 10
        self.pump_volume_percent = 10

        self.ws = websocket.WebSocketApp(self.socket, on_message=self.on_message, on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open

    def send_telegram_message(self, message: str) -> None:
        url = f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage'
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message
        }
        requests.post(url, data=payload)

    def on_message(self, ws, message):
        global volume_history, price_history, liquidation_history
        data = json.loads(message)
        # print('data', data)

        if data.get('stream') == '!miniTicker@arr':
            self.check_pump(data.get('data'))

    def check_pump(self, data):
        current_time = time.time()
        current_moscow_time = datetime.now() + timedelta(hours=3)  # Москва UTC+3

        # Сброс счетчиков в полночь
        if current_moscow_time.hour == 0 and current_moscow_time.minute == 0:
            self.alert_count_price = {symbol: 0 for symbol in self.history.keys()}
            self.alert_count_volume = {symbol: 0 for symbol in self.history.keys()}

        for ticker in data:
            symbol = ticker.get("s")
            try:
                current_price = float(ticker.get("c"))
                current_volume = float(ticker.get("v"))
            except (TypeError, ValueError):
                continue

            if symbol not in self.history:
                self.history[symbol] = deque()
            if symbol not in self.history_send_message_price:
                self.history_send_message_price[symbol] = deque()
            if symbol not in self.history_send_message_volume:
                self.history_send_message_volume[symbol] = deque()
            if symbol not in self.alert_count_price:
                self.alert_count_price[symbol] = 0  # Инициализируем счетчик
            if symbol not in self.alert_count_volume:
                self.alert_count_volume[symbol] = 0  # Инициализируем счетчик

            self.history[symbol].append((current_time, current_price, current_volume))

            # Удаляем старые записи
            while self.history[symbol] and (current_time - self.history[symbol][0][0] > self.WINDOW_SECONDS):
                self.history[symbol].popleft()

            while (self.history_send_message_price[symbol] and
                   (current_time - self.history_send_message_price[symbol][0][0] > self.stop_send_massage)):
                self.history_send_message_price[symbol].popleft()

            while (self.history_send_message_volume[symbol] and
                   (current_time - self.history_send_message_volume[symbol][0][0] > self.stop_send_massage)):
                self.history_send_message_volume[symbol].popleft()

            if self.history[symbol]:
                min_price = min(record[1] for record in self.history[symbol])
                min_volume = min(record[2] for record in self.history[symbol])

                price_trigger = current_price >= min_price + min_price / 100 * self.pump_price_percent
                volume_trigger = current_volume >= min_volume + min_volume / 100 * self.pump_volume_percent

                if price_trigger:
                    if not self.history_send_message_price[symbol]:
                        self.alert_count_price[symbol] += 1  # Увеличиваем счетчик
                        pump_percentage = ((current_price - min_price) / min_price) * 100
                        message = (f"🚀 {symbol} Памп в лонг обнаружен! [{self.alert_count_price[symbol]}]\n"
                                   f"Процент пампа: {pump_percentage:.2f}%\n\n"
                                   f"Текущая цена: {current_price}\n"
                                   f"Исходная цена: {min_price}\n"
                                   f'<a href="https://www.coinglass.com/tv/ru/Binance_{symbol}">CoinGlass</a>\n\n'
                                   f"#{symbol}")
                        send_telegram_message(message)
                        print(message)
                        self.history_send_message_price[symbol].append((current_time, current_price))

                if volume_trigger and self.history_send_message_price[symbol]:
                    if not self.history_send_message_volume[symbol]:
                        self.alert_count_volume[symbol] += 1
                        pump_percentage = ((current_volume - min_volume) / min_volume) * 100
                        message = (f'✴️ {symbol} Рост объема обнаружен! [{self.alert_count_volume[symbol]}]\n'
                                   f'Процент роста: {pump_percentage:.2f}%\n\n'
                                   f'Текущий объем: {current_volume}\n'
                                   f'Исходный объем: {min_volume}\n'
                                   f'<a href="https://www.coinglass.com/tv/ru/Binance_{symbol}">CoinGlass</a>\n\n'
                                   f'#{symbol}')
                        send_telegram_message(message)
                        print(message)
                        self.history_send_message_volume[symbol].append((current_time, current_volume))

        # TODO добавитьт отслеживаение открытого интереса по тем парам где есть рост

    def on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        print('Error:', error)

    def on_close(self, ws: websocket.WebSocketApp) -> None:
        print('Connection closed')

    def on_open(self, ws: websocket.WebSocketApp) -> None:

        current_timestamp_ms = int(time.time() * 1000)
        print("Timestamp (ms) с использованием time.time():", current_timestamp_ms)
        print('Connection opened')

    def run(self) -> None:
        self.ws.run_forever()


binance_ws = BinanceWebSocket(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
binance_ws.run()
