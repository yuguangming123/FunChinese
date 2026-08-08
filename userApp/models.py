from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class UserInfo(AbstractUser):
    telephone = models.CharField(max_length=15)
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    headimg = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name