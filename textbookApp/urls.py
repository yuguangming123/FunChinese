from django.urls import path
from . import views

app_name = 'textbookApp'

urlpatterns = [
    path('textbook/',views.textbook,name='textbook'),
]