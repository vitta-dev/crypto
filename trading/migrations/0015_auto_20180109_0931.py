# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-09 06:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0014_marketbot'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='marketbot',
            options={'verbose_name': 'Бот', 'verbose_name_plural': 'Боты'},
        ),
        migrations.RemoveField(
            model_name='marketbot',
            name='currency',
        ),
        migrations.AlterField(
            model_name='marketbot',
            name='is_test',
            field=models.BooleanField(default=True),
        ),
    ]
