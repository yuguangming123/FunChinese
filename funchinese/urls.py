"""
URL configuration for funchinese project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

import courseApp
from courseApp.admin_views import auto_analyze_view, auto_image_view, cleanup_images_view, extract_keywords_view, save_image_url_view, upload_image_view, upload_dict_view, list_dicts_view
from homeApp.views import home
from django.conf.urls import include

urlpatterns = [
    # 自定义 admin API 端点（必须在 admin.site.urls 之前）
    path('admin/courseApp/exercise/auto_analyze/', auto_analyze_view, name='auto_analyze'),
    path('admin/courseApp/exercise/upload_dict/', upload_dict_view, name='upload_dict'),
    path('admin/courseApp/exercise/auto_image/', auto_image_view, name='auto_image'),
    path('admin/courseApp/exercise/extract_keywords/', extract_keywords_view, name='extract_keywords'),
    path('admin/courseApp/exercise/list_dicts/', list_dicts_view, name='list_dicts'),
    path('admin/courseApp/exercise/cleanup_images/', cleanup_images_view, name='cleanup_images'),
    path('admin/courseApp/exercise/save_image_url/', save_image_url_view, name='save_image_url'),
    path('admin/courseApp/exercise/upload_image/', upload_image_view, name='upload_image'),
    path('admin/', admin.site.urls),
    path('',home,name='home'),                     # 添加首页路由
    path('courseApp/',include('courseApp.urls')),  # 添加课程广场的一级路由
    path('textbookApp/',include('textbookApp.urls')), # 添加教材同步一级路由
    path('vocabularyAPP/',include('vocabularyAPP.urls')), # 添加词汇一级路由
    path('practiceApp/', include('practiceApp.urls')),     # 添加练习路由
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
