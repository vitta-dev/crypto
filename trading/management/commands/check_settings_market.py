import time
import datetime
from django.core.management import BaseCommand

from trading.backedns.binance.client import ApiBinance
from trading.models import CheckMarketFilter


class Command(BaseCommand):

    def handle(self, *args, **options):

        api = ApiBinance()

        while True:
            results = api.get_markets()

            for c in results:
                update_data = {}

                market_settings = CheckMarketFilter.objects.filter(symbol=c['symbol']).order_by('created_at').last()
                update_flag = False if market_settings else True

                if c.get('filters'):
                    update_data['symbol'] = c.get('symbol')
                    for f in c.get('filters'):
                        if f['filterType'] == 'PERCENT_PRICE':
                            update_data['p_avgPriceMins'] = f.get('avgPriceMins', 0)
                            if market_settings and market_settings.p_avgPriceMins != str(f.get('avgPriceMins', 0)):
                                update_flag = True
                        if f['filterType'] == 'MIN_NOTIONAL':
                            update_data['n_avgPriceMins'] = f.get('avgPriceMins', 0)
                            if market_settings and market_settings.n_avgPriceMins != str(f.get('avgPriceMins', 0)):
                                update_flag = True

                        for key, val in f.items():
                            if key not in ('filterType', 'avgPriceMins', 'minTrailingAboveDelta',
                                           'maxTrailingAboveDelta', 'minTrailingBelowDelta', 'maxTrailingBelowDelta',
                                           'bidMultiplierUp', 'bidMultiplierDown', 'askMultiplierUp',
                                           'askMultiplierDown',  'applyMinToMarket', 'maxNotional', 'applyMaxToMarket',
                                           'maxNumOrders'):
                                update_data[key] = val
                                if market_settings and getattr(market_settings, key) != str(val):
                                    update_flag = True

                if update_flag:
                    print(update_data)
                    CheckMarketFilter.objects.create(**update_data)

            print('break', datetime.datetime.now())
            time.sleep(600)
