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
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

import statistic.urls as stat_url

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

urlpatterns = [
    url(r'^e5c9247a98c58dda4e6749fe081fb79a/', admin.site.urls),
    url(r'^e5c9247a98c58dda4e6749fe081fb79a/trade/', include('trading.urls')),
    # url('^e5c9247a98c58dda4e6749fe081fb79a/stat/$', include('statistic.urls'), name='stat'),
    url('^e5c9247a98c58dda4e6749fe081fb79a/stat/', include(stat_url.urlpatterns, namespace='stat')),
    url('^telegram/', include('test_telegram.urls', namespace='telegram')),
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
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

