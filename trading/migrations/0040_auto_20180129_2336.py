# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-29 20:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0039_marketbot_bot_last_run'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketbot',
            name='bot_last_run',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время поседнего запуска бота'),
        ),
    ]
