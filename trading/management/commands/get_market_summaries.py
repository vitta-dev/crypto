from django.core.management import BaseCommand

from trading.backedns.bittrex.client import ApiBittrex
from trading.models import Currency, Market, MarketSummary


class Command(BaseCommand):

    def handle(self, *args, **options):

        # MarketSummary.objects.all().delete()
        api = ApiBittrex()

        satoshi_1 = 0.00000001
        satoshi_100 = 0.000001

        results = api.get_market_summaries()

        for r in results:
            # r = summary['Summary']
            # print(r)
            market, created = Market.objects.get_or_create(name=r['MarketName'])
            if r['Last'] > satoshi_100:
                if r['Ask'] and r['Bid'] and r['Volume']:
                    rank = (r['Ask'] - r['Bid']) / r['Bid'] * r['Volume']
                else:
                    rank = 0
                data = {
                    'high': r['High'] or 0,
                    'low': r['Low'] or 0,
                    'volume': r['Volume'] or 0,
                    'last': r['Last'] or 0,
                    'base_volume': r['BaseVolume'] or 0,
                    'timestamp': r['TimeStamp'] or 0,
                    'bid': r['Bid'] or 0,
                    'ask': r['Ask'] or 0,
                    'open_by_orders': r['OpenBuyOrders'] or 0,
                    'open_sell_orders': r['OpenSellOrders'] or 0,
                    'prev_day': r['PrevDay'] or 0,
                    'created_at': r['Created'],
                    'rank': rank,
                }
                # print(data)
                market_summary, created = MarketSummary.objects.get_or_create(market=market)
                market_summary.high = r['High'] or 0
                market_summary.low = r['Low'] or 0
                market_summary.volume = r['Volume'] or 0
                market_summary.last = r['Last'] or 0
                market_summary.base_volume = r['BaseVolume'] or 0
                market_summary.timestamp = r['TimeStamp'] or 0
                market_summary.bid = r['Bid'] or 0
                market_summary.ask = r['Ask'] or 0
                market_summary.open_by_orders = r['OpenBuyOrders'] or 0
                market_summary.open_sell_orders = r['OpenSellOrders'] or 0
                market_summary.prev_day = r['PrevDay'] or 0
                market_summary.created_at = r['Created']
                market_summary.rank = rank or 0
                market_summary.save()

# data = {'Id': 66895027, 'Quantity': 1.18157975, 'OrderType': 'BUY', 'Price': 0.00203612,
#          'TimeStamp': '2017-12-02T11:16:44.463', 'FillType': 'FILL', 'Total': 0.00240583},
