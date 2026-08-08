from django.db import models
from userApp.models import UserInfo


class CourseCategory(models.Model):
    """课程分类（如：HSK备考、商务汉语、少儿汉语等）"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级分类'
    )
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Course(models.Model):
    """课程主体"""
    DIFFICULTY_CHOICES = [
        ('beginner', '入门'),
        ('elementary', '初级'),
        ('intermediate', '中级'),
        ('upper_intermediate', '中高级'),
        ('advanced', '高级'),
    ]

    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='课程分类'
    )
    name = models.CharField(max_length=200, verbose_name='课程名称')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='副标题')
    cover_image = models.ImageField(
        upload_to='course/covers/',
        blank=True,
        verbose_name='封面图片'
    )
    description = models.TextField(blank=True, verbose_name='课程描述')
    teacher = models.ForeignKey(
        UserInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught',
        verbose_name='授课教师'
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        verbose_name='难度等级'
    )
    heat = models.IntegerField(default=0, verbose_name='热度/学习人数')
    is_published = models.BooleanField(default=False, verbose_name='是否发布')
    is_free = models.BooleanField(default=True, verbose_name='是否免费')
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='价格'
    )
    original_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='原价'
    )
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    total_chapters = models.IntegerField(default=0, verbose_name='章节总数')
    total_lessons = models.IntegerField(default=0, verbose_name='课时总数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.name


class Chapter(models.Model):
    """课程章节（单元）"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name='所属课程'
    )
    name = models.CharField(max_length=200, verbose_name='章节名称')
    description = models.TextField(blank=True, verbose_name='章节描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程章节'
        verbose_name_plural = verbose_name
        ordering = ['course', 'sort_order', 'id']
        unique_together = ['course', 'sort_order']

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Lesson(models.Model):
    """课时（最小的学习单元）"""
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='所属章节'
    )
    name = models.CharField(max_length=200, verbose_name='课时名称')
    description = models.TextField(blank=True, verbose_name='课时描述')
    duration = models.IntegerField(default=0, help_text='预计学习时长（分钟）', verbose_name='预计时长')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_trial = models.BooleanField(default=False, verbose_name='是否可试学')
    video_url = models.URLField(blank=True, verbose_name='视频URL')
    audio_url = models.URLField(blank=True, verbose_name='音频URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课时'
        verbose_name_plural = verbose_name
        ordering = ['chapter', 'sort_order', 'id']
        unique_together = ['chapter', 'sort_order']

    def __str__(self):
        return f"{self.chapter.course.name} > {self.chapter.name} > {self.name}"


class LearningContent(models.Model):
    """学习内容（支持多种内容类型，使用 JSONField 灵活存储结构化数据）"""
    CONTENT_TYPE_CHOICES = [
        ('text', '课文'),
        ('vocabulary', '生词'),
        ('sentence', '句型'),
        ('grammar', '语法'),
        ('dialogue', '对话'),
        ('exercise', '练习'),
        ('pronunciation', '发音'),
        ('culture', '文化拓展'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name='所属课时'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name='内容类型'
    )
    title = models.CharField(max_length=200, blank=True, verbose_name='内容标题')
    content = models.JSONField(default=dict, verbose_name='内容数据')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '学习内容'
        verbose_name_plural = verbose_name
        ordering = ['lesson', 'sort_order', 'id']

    def __str__(self):
        return f"{self.lesson.name} - {self.get_content_type_display()}"


class Exercise(models.Model):
    """练习题"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises', verbose_name='所属课时')
    sentences = models.TextField(verbose_name='题目内容（JSON格式）')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    image = models.ImageField(upload_to='exercise_images/', blank=True, null=True, verbose_name='句子配图')
    audio_url = models.URLField(blank=True, verbose_name='音频URL')
    word_analysis = models.JSONField(default=list, blank=True, verbose_name='逐词分析')
    grammar_hint = models.TextField(blank=True, verbose_name='语法提示')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '练习题'
        verbose_name_plural = verbose_name
        ordering = ['lesson', 'sort_order']

    def __str__(self):
        return f"{self.lesson.name} - 题"


class UserCourseEnrollment(models.Model):
    """用户课程报名"""
    user = models.ForeignKey(
        UserInfo,
        on_delete=models.CASCADE,
        related_name='course_enrollments',
        verbose_name='用户'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='课程'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name='学习进度（%）'
    )

    class Meta:
        verbose_name = '用户课程报名'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class UserLessonProgress(models.Model):
    """课时学习进度"""
    user = models.ForeignKey(
        UserInfo,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='用户'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name='课时'
    )
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    score = models.IntegerField(null=True, blank=True, verbose_name='得分')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    last_studied_at = models.DateTimeField(auto_now=True, verbose_name='最后学习时间')
    attempt_count = models.IntegerField(default=0, verbose_name='尝试次数')

    class Meta:
        verbose_name = '课时学习进度'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'lesson']
        ordering = ['-last_studied_at']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.name}"
