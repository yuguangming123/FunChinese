from django.urls import path
from . import views

app_name = 'vocabularyAPP'

urlpatterns = [
    path('vocabulary/',views.vocabulary,name='vocabulary'),
]