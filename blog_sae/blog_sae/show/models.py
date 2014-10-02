#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from datetime import datetime

class MyShow(models.Model):
    """
    游戏展示
    """
    title = models.CharField(max_length=255, verbose_name=u"标题")
    content = models.TextField(verbose_name=u"内容")
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u"创建时间")
    last_modified = models.DateTimeField(default=datetime.now(), verbose_name=u"最近修改时间")

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u"游戏展示"
        verbose_name_plural = verbose_name