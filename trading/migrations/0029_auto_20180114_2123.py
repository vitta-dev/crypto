# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-14 18:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0028_auto_20180114_2110'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='marketbot',
            name='sma_period',
        ),
        migrations.AddField(
            model_name='marketbot',
            name='sma_timeperiod',
            field=models.SmallIntegerField(default=50, verbose_name='SMA timeperiod'),
        ),
    ]
