from django.contrib import admin
from .models import PracticeSession, PracticeRecord


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'lesson', 'mode', 'status', 'total_questions', 'correct_count', 'score', 'started_at']
    list_filter = ['mode', 'status']


@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question_index', 'is_correct', 'score', 'answered_at']
    list_filter = ['is_correct']
