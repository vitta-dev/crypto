# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-09 08:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0019_markettickinterval'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketbot',
            name='tick_intervals',
            field=models.ManyToManyField(to='trading.MarketTickInterval', verbose_name='Интервалы'),
        ),
    ]
