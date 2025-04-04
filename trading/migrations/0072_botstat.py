# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-05 17:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0071_marketmyorder_status_cancel'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('buy', models.IntegerField(default=0, verbose_name='Ордеров на покупку')),
                ('buy_sum', models.DecimalField(decimal_places=8, default=0, max_digits=24, verbose_name='Продано на сумму')),
                ('sell', models.IntegerField(default=0, verbose_name='Ордеров на продажу')),
                ('sell_sum', models.DecimalField(decimal_places=8, default=0, max_digits=24, verbose_name='Куплено на сумму')),
                ('bot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='trading.MarketBot', verbose_name='Бот')),
                ('market', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trading.Market', verbose_name='Market')),
            ],
            options={
                'verbose_name_plural': 'Статистика',
                'db_table': 'trading_bot_stat',
                'verbose_name': 'Сатистика',
            },
        ),
    ]
