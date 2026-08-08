import os
from django.db import models
from django.utils import timezone
from django.conf import settings

class BannerImage(models.Model):
    """
        轮播图管理模型。
        图片上传至 MEDIA_ROOT/banners/ 文件夹。
    """
    image = models.ImageField(
        upload_to='banners/',
        blank=True,
        null=False,
        verbose_name="轮播图片",
        help_text="支持 jpg, png, gif, webp 等常见格式"
    )
    alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='替代文本',
        help_text='图片无法显示时的文字说明'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='上传时间'
    )
    discription = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="图片说明",
        help_text="请描述这幅图片内容或作"
    )



# Create your models here.
