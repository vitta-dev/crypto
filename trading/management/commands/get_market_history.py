from django.core.management import BaseCommand

from trading.backedns.bittrex.client import ApiBittrex
from trading.models import Currency, Market, MarketTrade


class Command(BaseCommand):

    def handle(self, *args, **options):

        api = ApiBittrex()

        results = api.get_market_summaries()

        for summary in results:
            r = summary['Summary']
            print(r)
            market, created = Market.objects.get_or_create(name=r['MarketName'])
            data = {
                'market':  market,
                
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
            }
            print(data)
            MarketTrade.objects.create(**data)


data = {
        
        'High': 0.00000919,
        'Low': 0.00000820,
        'Volume': 74339.61396015,
        'Last': 0.00000820,
        'BaseVolume': 0.64966963,
        'TimeStamp': '2014-07-09T07:19:30.15',
        'Bid': 0.00000820,
        'Ask': 0.00000831,
        'OpenBuyOrders': 15,
        'OpenSellOrders': 15,
        'PrevDay': 0.00000821,
        'Created': '2014-03-20T06:00:00',
        'DisplayMarketName': None
}