import requests

from ..config import *

# Укажите токен вашего Telegram-бота и chat_id
telegram_token = TELEGRAM_BOT_TOKEN
chat_id = TELEGRAM_CHAT_ID
chat_id2 = TELEGRAM_CHAT_ID
chat_list = [chat_id2, chat_id]


def get_chat_id():
    url = f'https://api.telegram.org/bot{telegram_token}/getUpdates'
    response = requests.get(url)

    if response.status_code == 200:
        updates = response.json()['result']
        if updates:
            # Предполагается, что вы отправляли сообщение боту
            for update in updates:
                chat_id = update['message']['chat']['id']
                chat_name = update['message']['chat']['first_name']
                print(f"Chat ID: {chat_id}, Chat Name: {chat_name}")
        else:
            print("Нет обновлений.")
    else:
        print("Ошибка при получении обновлений.")


# Функция для отправки сообщения в Telegram
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=payload)

# Запуск функции
get_chat_id()

# message = (f'📉 Памп в шорт обнаружен!\n'
#            f'Текущая цена: {1111}\n'
#            f'Исходная цена: {222}\n'
#            f'Процент падения: {32:.2f}%'
#            )
# send_telegram_message(message)