# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-01-07 08:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0086_auto_20190106_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketmyorder',
            name='status_cancel',
            field=models.CharField(blank=True, choices=[('TIME', 'По времени'), ('STOP_LOSS', 'Stop Loss'), ('TRAILING_STOP_LOSS', 'Trailing Stop Loss'), ('SAFETY', 'Куплен страховочный')], max_length=25, null=True),
        ),
    ]
