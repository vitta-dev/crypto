from django.urls import path

from .views import test_webhook_data, view_webhook_data


urlpatterns = [
    path('bot', test_webhook_data),
    path('view', view_webhook_data),
]
