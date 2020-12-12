from django.conf.urls import url

from .views import test_webhook_data, view_webhook_data


urlpatterns = [
    url('^bot$', test_webhook_data),
    url('^view$', view_webhook_data),
]
