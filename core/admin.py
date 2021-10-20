# -*- coding: utf-8 -*-
from decimal import *
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


from core.models import SystemMonitor, BotLog


class SystemMonitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'started_at', 'finished_at')


class BotLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'error')


# admin.site.register(SystemMonitor, SystemMonitorAdmin)
# admin.site.register(BotLog, BotLogAdmin)
