from django.urls import path
from . import views

app_name = 'practiceApp'

urlpatterns = [
    path('<int:lesson_id>/sorting/', views.sorting_practice, name='practice_sorting'),
    path('<int:lesson_id>/writing/', views.writing_practice, name='practice_writing'),
    path('<int:lesson_id>/', views.practice, name='practice'),
    path('api/start_session/', views.start_session, name='start_session'),
    path('api/submit_answer/', views.submit_answer, name='submit_answer'),
    path('api/complete_session/', views.complete_session, name='complete_session'),
    path('api/tts/', views.tts, name='tts'),
    path('api/evaluate_speech/', views.evaluate_speech, name='evaluate_speech'),
]
