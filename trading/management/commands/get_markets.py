from django.core.management import BaseCommand

from trading.backedns.bittrex.client import ApiBittrex
from trading.models import Currency, Market


class Command(BaseCommand):

    def handle(self, *args, **options):

        api = ApiBittrex()

        results = api.get_markets()

        update_false = Market.objects.all().update(is_active=False)
        print('update_false', update_false)

        for c in results:
            base_currency, created = Currency.objects.get_or_create(name=c['BaseCurrency'])
            market_currency, created = Currency.objects.get_or_create(name=c['MarketCurrency'])
            data = {
                'market_currency':  market_currency,
                'base_currency': base_currency,
            }

            market_pair, created = Market.objects.get_or_create(**data)
            market_pair.name = c['MarketName']
            market_pair.min_trade_size = c['MinTradeSize']
            market_pair.is_active = c['IsActive']

            market_pair.save()

