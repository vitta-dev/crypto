from django.core.management import BaseCommand

from trading.models import MarketMyOrder, BotTestOrder, Currency, Market


class Command(BaseCommand):

    def handle(self, *args, **options):
        MarketMyOrder.objects.all().delete()
        # BotTestOrder.objects.all().delete()

        # Currency.objects.filter(created_at__gte='2018-08-04').delete()
        # Market.objects.filter(created_at__gte='2018-08-04').delete()

        # markets = Market.objects.filter(code='-')
        #
        # for market in markets:
        #     market.code = market.get_market_name('binance')
        #     market.save()


