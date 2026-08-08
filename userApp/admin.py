from django.contrib import admin
from .models import UserInfo

# Register your models here.

admin.site.site_header = "趣学汉语后台管理"   # 登录后页面顶部显示的标题[reference:3]
admin.site.site_title = "趣学汉语后台管理"   # 浏览器标签页的标题[reference:4]

class UserInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'nickname', 'first_name', 'last_name', 'telephone', 'email', 'headimg', 'is_staff', 'is_superuser', 'is_active', 'last_login', 'date_joined']


admin.site.register(UserInfo, UserInfoAdmin)