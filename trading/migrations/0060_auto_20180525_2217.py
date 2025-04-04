# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-25 19:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0059_auto_20180525_1950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketorderlog',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='trading.MarketMyOrder', verbose_name='MarketBot'),
        ),
        migrations.AlterField(
            model_name='marketorderlog',
            name='type',
            field=models.CharField(choices=[('CREATE_ORDER', 'Ордер создан'), ('FILLED_ORDER', 'Ордер выполнен'), ('MAX_PRICE_FIXED', 'MaxPrice зафиксирована'), ('MAX_PRICE_UPDATED', 'MaxPrice обновлена'), ('STOP_LOSS', 'Сработал Stop Loss'), ('TRAILING_FALL', 'Сработал Trailing Fall'), ('STOP_LOSS', 'Установлен Stop Loss')], default='CREATE_ORDER', max_length=25),
        ),
    ]
