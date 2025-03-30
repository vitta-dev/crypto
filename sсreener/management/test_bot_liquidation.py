import websocket
import json
import pandas as pd
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
    payload = {
        'chat_id': chat_id,
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

        self.socket = 'wss://fstream.binance.com/ws/!forceOrder@arr'
        self.interval = "1m"

        self.minimum_total_dollars = minimum_total_dollars
        self.minimum_percentage_increase = minimum_percentage_increase
        self.set_ticker = None
        self.data_list = []
        self.previous_volumes_df = pd.DataFrame(columns=['Symbol', 'Last Update', 'Total($)', 'Cumulative Total($)'])
        self.time_frame_minutes = time_frame_minutes
        self.time_frame = timedelta(minutes=time_frame_minutes)
        self.telegram_bot_token = token
        self.telegram_chat_id = chat_id

        # Интервал хранения истории в секундах (20 минут)
        self.WINDOW_SECONDS = 60 * 20

        self.history_send_message_price = {}
        self.history_send_message_volume = {}
        self.stop_send_massage = 60 * 2

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
        print('data', data)

        self.check_liquidations(data)

        # if data.get('stream') == '!miniTicker@arr':
        #     self.check_pump(data.get('data'))
        #
        #     print("всего данных", len(data.get('data')))
        #     # print(self.history)
        #     # print("")

    def check_liquidations(self, data):
        """проверка ликвидаций"""
        order_data = data['o']
        trade_time = pd.to_datetime(order_data['T'], unit='ms', utc=True).tz_convert('Europe/Kaliningrad')

        # Удаление данных старше одного часа
        one_hour_ago = pd.Timestamp.now(tz='Europe/Kaliningrad') - pd.Timedelta(hours=1)
        self.previous_volumes_df = self.previous_volumes_df[self.previous_volumes_df['Last Update'] > one_hour_ago]

        new_row = {
            'Symbol': order_data['s'],
            'Side': order_data['S'],
            'Price': float(order_data['p']),
            'Quantity': float(order_data['q']),
            'Total($)': round(float(order_data['p']) * float(order_data['q']), 2),
            'Trade Time': trade_time.strftime('%Y-%m-%d %H:%M:%S')
        }

        key = new_row['Symbol']
        total_liquidations = new_row['Total($)']

        if key in self.previous_volumes_df['Symbol'].values:
            previous_row = self.previous_volumes_df[self.previous_volumes_df['Symbol'] == key].iloc[0]
            previous_time = previous_row['Last Update']
            previous_total = previous_row['Total($)']
            cumulative_total = previous_row['Cumulative Total($)'] + total_liquidations

            if (trade_time - previous_time).total_seconds() / 60 >= self.time_frame_minutes:
                percentage_increase = (total_liquidations - previous_total) / previous_total * 100
                if percentage_increase >= self.minimum_percentage_increase:
                    msg = (f"📉 {key} увеличение ликвидаций на {percentage_increase:.2f}% "
                           f"за {self.time_frame_minutes} минут")
                    print(msg)
                    # self.send_telegram_message(msg)

            self.previous_volumes_df.loc[
                self.previous_volumes_df['Symbol'] == key, ['Last Update', 'Total($)', 'Cumulative Total($)']] = (
                trade_time, total_liquidations, cumulative_total)
        else:
            cumulative_total = total_liquidations  # Первое появление пары
            new_volume_row = pd.DataFrame([[key, trade_time, total_liquidations, cumulative_total]],
                                          columns=['Symbol', 'Last Update', 'Total($)', 'Cumulative Total($)'])
            self.previous_volumes_df = pd.concat([self.previous_volumes_df, new_volume_row], ignore_index=True)

        if ((self.set_ticker is None or new_row['Symbol'] in self.set_ticker)
                and new_row['Total($)'] >= self.minimum_total_dollars):
            self.data_list.append(new_row)
            df = pd.DataFrame(self.data_list)
            print(df)
            print("")
            print(self.previous_volumes_df)
            print("")
        else:
            print("Error: Please check the filter.")

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
