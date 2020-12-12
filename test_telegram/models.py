from django.db import models
from django.utils import timezone


class TestWebhook(models.Model):

    class Meta:
        db_table = 'test_webhook'

    created_at = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    method = models.CharField(max_length=50, default='GET')
