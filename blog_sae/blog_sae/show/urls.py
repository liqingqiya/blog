#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^something/', views.show_page, name="something_show"),
)
