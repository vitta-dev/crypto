"""cripto URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.urls import path

# import statistic.urls as stat_url

# urlpatterns = [
#     url('^e5c9247a98c58dda4e6749fe081fb79a/', include([
#         url('^admin/$', admin.site.urls),
#         url('^statistic/$', include('statistic.urls'), name='statistic'),
#         url('^trading/$', include('trading.urls'), name='traiding'),
#     ],
#     )),
#
#     url('^telegram/', include('test_telegram.urls', namespace='telegram')),
# ]

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('sentry-debug/', trigger_error),
    # path('e5c9247a98c58dda4e6749fe081fb79a/', admin.site.urls),
    # path('e5c9247a98c58dda4e6749fe081fb79a/statistic/', include(('statistic.urls', 'statistic'), namespace='statistic')),
    path('e5c9247a98c58dda4e6749fe081fb79a/tr/', include(('trading.urls', 'trading'), namespace='trading')),
    path('e5c9247a98c58dda4e6749fe081fb79a/st/', include(('statistic.urls', 'statistic'), namespace='statistic')),
    # url('^e5c9247a98c58dda4e6749fe081fb79a/stat/', include(('statistic.urls', 'statistic'), namespace='stat')),
    # url('^e5c9247a98c58dda4e6749fe081fb79a/stat/', include(('statistic.urls', 'statistic'), namespace='stat')),
    # url(r'^e5c9247a98c58dda4e6749fe081fb79a/stat/', include(('statistic.urls', 'statistic'), namespace='statistic')),
    # path('telegram/', include(('test_telegram.urls', 'telegram'), namespace='telegram')),
    path('jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    path('jet/', include('jet.urls', 'jet')),
    path('e5c9247a98c58dda4e6749fe081fb79a/', admin.site.urls),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # urlpatterns += [
    #     (r'^media/(?P<path>.*)$', 'django.views.static.serve',
    #      {'document_root': settings.MEDIA_ROOT}),
    #     (r'^static/(?P<path>.*)$', 'django.views.static.serve',
    #      {'document_root': settings.STATIC_ROOT}),
    #
    #     # url(r'^__debug__/', include(debug_toolbar.urls)),
    # ]

    import debug_toolbar
    urlpatterns += (
        path('__debug__/', include(debug_toolbar.urls)),
    )

