# Generated by Django 3.2.7 on 2024-06-11 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0095_remove_marketbot_strategy'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketbot',
            name='is_sword_or_hummer',
            field=models.BooleanField(default=False, verbose_name='Проверять по sword или hummer candle'),
        ),
    ]
