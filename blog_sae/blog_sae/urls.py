#-*- coding:utf-8 -*-
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf.urls.static import static
import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^summernote/', include('django_summernote.urls')),
    url(r"^blog/", include("blog_sae.blog.urls", namespace="blog")),
    url(r"^show/", include("blog_sae.show.urls", namespace="show")),

    url(r"^$", "blog_sae.show.views.homepage", name="homepage")
)

if settings.DEBUG:
    #测试环境的静态文件重定向
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.CSS_URL, document_root=settings.CSS_ROOT)
    urlpatterns += static(settings.JS_URL, document_root=settings.JS_ROOT)
    urlpatterns += static(settings.IMG_URL, document_root=settings.IMG_ROOT)
    urlpatterns += static(settings.FONTS_URL, document_root=settings.FONTS_ROOT)