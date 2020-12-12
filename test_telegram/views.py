# coding=utf-8
import json
import telebot

from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import TestWebhook


@csrf_exempt
def test_webhook_data(request):

    # data = request.POST.dict()
    # new_test_data = TestWebhook(text=json.dumps(data), method='POST')
    # new_test_data.save()

    # new_test_data = TestWebhook(text=json.loads(request.body), method='BODY')

    mess = telebot.types.Update.de_json(request.body.decode())

    chat_id = mess.message.chat.id

    new_test_data = TestWebhook(text=request.body, method='BODY')
    new_test_data = TestWebhook(text=mess.message.text, method='BODY')
    new_test_data.save()


    # keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    # keyboard.add(*[telebot.types.KeyboardButton(name) for name in ['Шерлок Холмс', 'Доктор Ватсон']])
    # bot.send_message(m.chat.id, 'Кого выбираешь?',
    #                  reply_markup=keyboard)

    TELEGRAM_NAME_BOT = 'tlight_test1_bot'
    TELEGRAM_API_KEY = '355309427:AAFv7fgiOqLtAXSqPTqVgeGrzx6ZjnODH6Y'

    chat_id = '283926507'

    # bot = telebot.TeleBot(TELEGRAM_API_KEY)
    # bot.send_message(chat_id, 'Привет')
    #
    # if mess.message.text == 'Stat today':
    #     bot.send_message(chat_id, 'Today 50 clicks')
    #
    # if mess.message.text == 'Статистика сегодня':
    #     bot.send_message(chat_id, 'Сегодня 50 кликов')
    #
    # if mess.message.text == 'Статистика вчера':
    #     bot.send_message(chat_id, 'Вчера 70 лидов')
    #
    # if mess.message.text == 'Баланс':
    #     bot.send_message(chat_id, 'Баланс 50 руб')

    return JsonResponse({'ok': True})


def view_webhook_data(request):

    if 'delete_all' in request.GET:
        TestWebhook.objects.all().delete()

    data = TestWebhook.objects.all()

    context = {
        'webhooks': data
    }

    return render(request, "data.html", context)


def emulate_telegram_bot(request):
    data = {'result': [{'update_id': 892498982,
                        'message': {
                            'entities': [
                                {'offset': 0, 'length': 6, 'type': 'bot_command'}],
                            'from': {'username': 'vittadev', 'first_name': 'Елена', 'is_bot': False,
                                     'last_name': 'Белова', 'id': 283926507, 'language_code': 'ru-RU'},
                            'message_id': 2, 'date': 1509428621,
                            'chat': {'username': 'vittadev', 'last_name': 'Белова', 'first_name':
                                'Елена', 'id': 283926507, 'type': 'private'},
                            'text': '/start'}
                        },
                       {'update_id': 892498983,
                        'message': {'date': 1509428645, 'text': 'check',
                                    'from': {'username': 'vittadev', 'first_name': 'Елена', 'is_bot': False,
                                             'last_name': 'Белова', 'id': 283926507, 'language_code': 'ru-RU'},
                                    'message_id': 3,
                                    'chat': {'username': 'vittadev', 'last_name': 'Белова', 'first_name': 'Елена',
                                             'id': 283926507, 'type': 'private'}
                                    }
                        }
                       ],
            'ok': True}
    return JsonResponse(data)

"""
############# local ###############

cd /home/vitta/www/karateka39.tpl/env
source ./bin/activate

redis-cli

cd /home/vitta/www/karateka39.tpl/karateka
hg addremove
hg add
hg commit -m "v.2016-01-13 yandex meta"
hg commit -m "telegram test"
hg push https://Vitta@bitbucket.org/Vitta/karateka

hg pull https://Vitta@bitbucket.org/Vitta/karateka
hg update

cd /home/vitta/www/karateka39.tpl/karateka/
./manage.py runserver 8007

http://127.0.0.1:8007/

./manage.py makemigrations siteblocks

./manage.py migrate

./manage.py dumpdata siteblocks.settings

file:///home/vitta/www/karateka39.tpl/docs/dis/packet-project/HTML/LAYOUT-1/STANDARD/index.html
"""