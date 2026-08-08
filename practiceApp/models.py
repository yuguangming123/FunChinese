from django.db import models
from userApp.models import UserInfo
from courseApp.models import Lesson


class PracticeSession(models.Model):
    """练习会话"""
    MODE_CHOICES = [
        ('typing', '打字练习'),
        ('speaking', '口语练习'),
        ('translate', '英译中模式'),
        ('listening', '听力模式'),
    ]
    STATUS_CHOICES = [
        ('in_progress', '进行中'),
        ('completed', '已完成'),
    ]

    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True, blank=True, related_name='practice_sessions', verbose_name='用户')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='practice_sessions', verbose_name='关联课时')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, verbose_name='练习模式')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name='会话状态')
    total_questions = models.IntegerField(default=0, verbose_name='总题数')
    correct_count = models.IntegerField(default=0, verbose_name='正确数')
    wrong_count = models.IntegerField(default=0, verbose_name='错误数')
    score = models.IntegerField(default=0, verbose_name='得分')
    exercise_snapshot = models.JSONField(default=list, blank=True, verbose_name='题目快照')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '练习会话'
        verbose_name_plural = verbose_name
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.username if self.user else "匿名"} - {self.lesson.name} - {self.get_mode_display()}'


class PracticeRecord(models.Model):
    """单题练习记录"""
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='records', verbose_name='所属会话')
    question_index = models.IntegerField(default=0, verbose_name='题号')
    question_data = models.JSONField(default=dict, verbose_name='题目数据')
    user_answer = models.TextField(blank=True, verbose_name='用户答案')
    correct_answer = models.TextField(blank=True, verbose_name='正确答案')
    is_correct = models.BooleanField(null=True, verbose_name='是否正确')
    score = models.IntegerField(default=0, verbose_name='本题得分')
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name='答题时间')

    class Meta:
        verbose_name = '练习记录'
        verbose_name_plural = verbose_name
        ordering = ['session', 'question_index']

    def __str__(self):
        return f'{self.session} - 第{self.question_index + 1}题'
