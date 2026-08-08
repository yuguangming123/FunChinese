from django.urls import path
from . import views

app_name = 'courseApp'

urlpatterns = [
    path('course/', views.course, name='course'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
]