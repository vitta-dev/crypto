import time

from django.core.management import BaseCommand
from django.utils import timezone

from trading.backedns.bittrex.client import ApiBittrex
from trading.bots.strategy_average import BotAverage
from trading.models import MarketMyOrder, MarketBot

bot_name = 'averaged_price'
bot = MarketBot.objects.get(name=bot_name)
order = MarketMyOrder.objects.get(id=15145)
tb = BotAverage(bot, order.market)
tb.create_fix_sell(order)
