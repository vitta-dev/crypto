from django import forms
from django.db.models import Q
from django.http import QueryDict


class MACDFilter(forms.Form):

    # SORT_BY_CHOICES = [
    #     ('created_at', 'Дата добавления'),
    #     ('name', 'Имени'),
    #     ('odk_days_7_epm', 'EPM за 7 дней (Одноклассники)'),
    #     ('vk_days_7_epm', 'EPM за 7 дней (ВКонтакте)'),
    # ]
    #
    # search = forms.CharField(required=False)

    # category = forms.ModelMultipleChoiceField(OfferCategory.objects, required=False)
    # gender = forms.ChoiceField(Gender.choices(None), widget=forms.CheckboxSelectMultiple(), required=False)
    # sources = forms.ModelMultipleChoiceField(OfferTrafficSource.objects, required=False)

    fastperiod = forms.IntegerField(label='fastperiod', required=True, initial=12)  # 12, 8 и 17 и для покупки
    slowperiod = forms.IntegerField(label='slowperiod', required=True, initial=26)  # 26
    signalperiod = forms.IntegerField(label='signalperiod', required=True, initial=9)  # 9

    # def __init__(self, user, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.user = user
    #     data = QueryDict(mutable=True)
    #     data.update(self.data)
    #     data.setdefault('sort_by', 'created_at')
    #     self.data = data

    # def apply_filter(self, items):
    #
    #     data = self.cleaned_data
    #
    #     if data['search']:
    #         # data['search'] = data['search'].replace('ё', 'е')
    #         # data['search'] = data['search'].replace('Ё', 'Е')
    #         search_token = data['search'].strip()
    #         q = Q(name__icontains=search_token)
    #         try:
    #             int(search_token)
    #             q |= Q(id=search_token)
    #         except ValueError:
    #             pass
    #
    #         items = items.filter(q)
    #
    #     if data['category']:
    #         items = items.filter(category__in=data['category'])
    #
    #     if data['gender']:
    #         items = items.filter(gender__in=('', data['gender']))
    #
    #     if data['countries']:
    #         advertiser_offers = dict(AdvertiserOffer.objects\
    #             .filter(is_active=True, country__in=data['countries']).values_list('id', 'offer'))
    #
    #         if self.user:
    #             advertiserofferaffiliate_qs = AdvertiserOfferAffiliate.objects\
    #                 .filter(advertiser_offer__country__in=data['countries'])
    #             for row in advertiserofferaffiliate_qs.values_list('is_active', 'advertiser_offer', 'advertiser_offer__offer'):
    #                 print(row)
    #                 is_active, advertiser_offer_id, offer_id = row
    #                 if is_active:
    #                     advertiser_offers[advertiser_offer_id] = offer_id
    #                 else:
    #                     advertiser_offers.pop(advertiser_offer_id, None)
    #
    #         offer_ids = tuple(advertiser_offers.values())
    #
    #         items = items.filter(id__in=set(offer_ids))
    #
    #     return items
    #
    # def sort(self, it):
    #
    #     sort_by = self.cleaned_data['sort_by']
    #     if not sort_by:
    #         return it
    #
    #     if sort_by == 'name':
    #         it = sorted(it, key=lambda offer: offer.name)
    #
    #     if sort_by == 'created_at':
    #         it = sorted(it, key=self._sort_by_date, reverse=True)
    #
    #     if sort_by == 'odk_days_7_epm':
    #         net = SocNetwork(SocNetwork.ODK)
    #         it = sorted(it, key=lambda offer: offer.posting_stats[net].get('all_days_7_epm', 0), reverse=True)
    #
    #     if sort_by == 'vk_days_7_epm':
    #         net = SocNetwork(SocNetwork.VK)
    #         it = sorted(it, key=lambda offer: offer.posting_stats[net].get('all_days_7_epm', 0), reverse=True)
    #
    #     return it
    #
    # @staticmethod
    # def _sort_by_date(offer):
    #     return offer.published_at or offer.created_at
