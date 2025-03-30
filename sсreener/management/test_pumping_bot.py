import requests
from binance.client import Client
from binance.cm_futures import CMFutures

import time

# from trading.backedns.binance.config import API_KEY, SECRET_KEY, COMMISSION

from ..config import *

# Укажите токен вашего Telegram-бота и chat_id
telegram_token = TELEGRAM_BOT_TOKEN
chat_id = TELEGRAM_CHAT_ID
chat_id2 = TELEGRAM_CHAT_ID
chat_list = [chat_id2, chat_id]

# Инициализация клиента Binance
client = Client(api_key, api_secret)
cm_futures_client = CMFutures(api_key_fu, api_secret_fu)


def send_telegram_message(message) -> None:
    """Функция для отправки сообщения в Telegram"""
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=payload)


def get_liquidations(symbol, limit=100):
    print('get_liquidations')
    liquidations = client_fu.futures_liquidation_orders(symbol=symbol, limit=limit)
    print('liquidations', liquidations)
    if liquidations:
        message = f"Ликвидация {symbol} {liquidations}"
        send_telegram_message(message)
    return liquidations

# def get_liquidations(symbol):
#     """Получение ликвидаций"""
#     print('get_liquidations')
#     liquidations = client.futures_liquidation(symbol=symbol)
#     print('liquidations', liquidations)
#     return liquidations


def monitor_liquidations(symbol, interval=60, growth_threshold=10):
    """Функция для анализа роста ликвидаций"""
    previous_count = 0

    while True:
        liquidation_data = get_liquidations(symbol)
        current_count = len(liquidation_data)

        if previous_count > 0:
            growth_percentage = ((current_count - previous_count) / previous_count) * 100
            if growth_percentage >= growth_threshold:
                print(f"Рост ликвидаций! Текущий уровень: {current_count}, "
                      f"Предыдущий уровень: {previous_count}, "
                      f"Процент роста: {growth_percentage:.2f}%")

        previous_count = current_count
        time.sleep(interval)


def get_historical_prices(symbol, interval='1m', limit=20) -> list:
    """Функция для получения исторических цен"""
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    prices = [float(kline[4]) for kline in klines]  # Цена закрытия
    return prices


def monitor_price_movements(symbol) -> None:
    """Функция для мониторинга пампов (лонг и шорт) за 20 минут"""
    print('monitor_price_movements')
    prices = get_historical_prices(symbol)
    print('prices', prices)

    if len(prices) >= 2:
        initial_price = prices[0]
        current_price = prices[-1]

        pump_percentage = ((current_price - initial_price) / initial_price) * 100
        drop_percentage = ((initial_price - current_price) / initial_price) * 100

        if pump_percentage > 0:  # Проверка пампа в лонг
            message = (f"🚀 {symbol} Памп в лонг обнаружен!\n"
                       f"Текущая цена: {current_price}\n"
                       f"Исходная цена: {initial_price}\n"
                       f"Процент пампа: {pump_percentage:.2f}%")
            send_telegram_message(message)

        if drop_percentage > 0:  # Проверка пампа в шорт
            message = (f"📉 {symbol} Памп в шорт обнаружен!\n"
                       f"Текущая цена: {current_price}\n"
                       f"Исходная цена: {initial_price}\n"
                       f"Процент падения: {drop_percentage:.2f}%")
            send_telegram_message(message)

    else:
        print("Недостаточно данных для анализа.")


def get_open_interest(symbol):
    data = cm_futures_client.open_interest(symbol)
    print(symbol, data)

# Пример использования
symbol1 = 'BTCUSDT'
symbol1 = 'BTC'
symbol2 = 'SOLUSDT'
symbol2 = 'LTCUSDT'
symbol2 = 'LTC'
i = 0
# while True and i < 3:
while True:
    # monitor_price_movements(symbol1)
    # monitor_price_movements(symbol2)
    # get_liquidations(symbol1)
    # get_liquidations(symbol2)
    get_open_interest(symbol1)
    get_open_interest(symbol2)
    i += 1
    time.sleep(1)  # Периодическое выполнение анализа каждую минуту
