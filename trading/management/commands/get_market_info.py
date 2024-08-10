from django.core.management import BaseCommand

from trading.backedns.binance.client import ApiBinance
from trading.backedns.bittrex.client import ApiBittrex
from trading.models import Currency, Market


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('market', nargs='?')

    def handle(self, *args, **options):

        market_name = options['market']

        api = ApiBinance()

        results = api.get_market_info(market_name)
        print(results)
        return

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

