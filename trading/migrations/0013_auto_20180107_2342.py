# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-07 20:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0012_auto_20180107_2247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketmyorder',
            name='status',
            field=models.CharField(choices=[('OPEN', 'Открытый'), ('CANCELED', 'Отменен'), ('FILLED', 'Исполнен'), ('PART_FILLED', 'Частично исполнен'), ('CLOSED', 'Закрыт')], default='OPEN', max_length=25),
        ),
    ]
