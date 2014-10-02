#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^list/', views.BlogList.as_view(), name="blog_list"),
    url(r'^(?P<pk>\d+)/show/', views.BlogDetail.as_view(), name="blog_detail"),

    #根据类别列出博客
    url(r'^(?P<category_name>.*)/category/list/', views.BlogCategoryList, name="blog_by_category_list"),
    #根据时间
    url(r'^(?P<month>.*)/month/list/', views.BlogMonthList, name="blog_by_month_list"),

    #根据博客title模糊查询
    url(r'^(?P<blog_title>.*)/title/list/', views.BlogLikeTitleList, name="blog_like_title_list"),
)
