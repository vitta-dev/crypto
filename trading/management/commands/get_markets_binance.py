from django.core.management import BaseCommand

from trading.backedns.binance.client import ApiBinance
from trading.models import Currency, Market


class Command(BaseCommand):

    def handle(self, *args, **options):

        api = ApiBinance()

        results = api.get_markets()

        update_false = Market.objects.all().update(is_active_binance=False)
        print('update_false', update_false)

        for c in results:
            if c['baseAsset'] == 'XVC' or c['baseAsset'] == 'XVC':
                print(c['symbol'])

            base_currency, created = Currency.objects.get_or_create(name=c['quoteAsset'])
            market_currency, created = Currency.objects.get_or_create(name=c['baseAsset'])
            data = {
                'market_currency':  market_currency,
                'base_currency': base_currency,
            }

            market_pair, created = Market.objects.get_or_create(**data)
            market_pair.name = '{}-{}'.format(c['quoteAsset'], c['baseAsset'])
            market_pair.code = c['symbol']

            if c['status'] == 'TRADING':
                market_pair.is_active_binance = True

            if c.get('filters'):
                for f in c.get('filters'):
                    if f['filterType'] == 'LOT_SIZE':
                        market_pair.min_trade_size = f.get('minQty', 0)

            market_pair.save()

            market_settings = api.market_settings(market_pair)
            # print(created, market_pair)
            m_set = {
                "status": "TRADING",
                "symbol": "ETHBTC",
                "filters": [
                    {"maxPrice": "0.00000000",
                     "minPrice": "0.00000000",
                     "tickSize": "0.00000100",
                     "filterType": "PRICE_FILTER"},
                    {"filterType": "PERCENT_PRICE",
                     "avgPriceMins": 5,
                     "multiplierUp": "10",
                     "multiplierDown": "0.1"},
                    {"maxQty": "100000.00000000",
                     "minQty": "0.00100000",
                     "stepSize": "0.00100000",
                     "filterType": "LOT_SIZE"},
                    {"filterType": "MIN_NOTIONAL",
                     "minNotional": "0.00100000",
                     "avgPriceMins": 5,
                     "applyToMarket": True},
                    {"limit": 10,
                     "filterType": "ICEBERG_PARTS"},
                    {"filterType": "MAX_NUM_ALGO_ORDERS",
                     "maxNumAlgoOrders": 5}
                ],
                "baseAsset": "ETH",
                "orderTypes": ["LIMIT", "LIMIT_MAKER", "MARKET", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"],
                "quoteAsset": "BTC",
                "icebergAllowed": True,
                "quotePrecision": 8,
                "baseAssetPrecision": 8
            }
