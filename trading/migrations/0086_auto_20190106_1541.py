# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-01-06 12:41
from __future__ import unicode_literals

from django.db import migrations, models


def set_type_news(apps, schema_editor):
    """
    :param apps:
    :param schema_editor:
    :return:
    """

    update_info = {
        'oneMin': '1m',
        'fiveMin': '5m',
        'hour': '1h',
        'thirtyMin': '30m',
        'fifteenMin': '15m',
        'Day': '1d',
    }
    interval_model = apps.get_model("trading", "MarketTickInterval")
    for interval in interval_model.objects.all():
        interval.value_binance = update_info[interval.value]
        interval.save()


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0085_auto_20190104_1642'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='checkmarketfilter',
            options={'verbose_name': 'Проверка фильтров', 'verbose_name_plural': 'Проверка фильтров'},
        ),
        migrations.AddField(
            model_name='markettickinterval',
            name='value_binance',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='значение binance'),
        ),
        migrations.RunPython(set_type_news),
    ]
