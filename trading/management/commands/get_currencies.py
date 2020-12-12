from django.core.management import BaseCommand

from cripto.utils import split_to_chunks
from trading.backedns.bittrex.client import ApiBittrex
from trading.models import Currency


class Command(BaseCommand):

    def handle(self, *args, **options):

        api = ApiBittrex()

        results = api.get_currencies()

        for currencies in split_to_chunks(results, 500):
            currencies_data = []
            for c in currencies:
                currency, created = Currency.objects.get_or_create(name=c['Currency'])
                currency.name = c['Currency']
                currency.name_long = c['CurrencyLong']
                currency.coin_type = c['CoinType']
                currency.min_confirmation = c['MinConfirmation']
                currency.tx_fee = c['TxFee']
                currency.is_active = c['IsActive']
                currency.base_address = c['BaseAddress']
                currency.save()

            #     data = {
            #         'name': c['Currency'],
            #         'name_long': c['CurrencyLong'],
            #         'coin_type': c['CoinType'],
            #         'min_confirmation': c['MinConfirmation'],
            #         'tx_fee': c['TxFee'],
            #         'is_active': c['IsActive'],
            #         'base_address': c['BaseAddress']
            #     }
            #     currencies_data.append(Currency(**data))
            #
            # Currency.objects.bulk_create(currencies_data)


