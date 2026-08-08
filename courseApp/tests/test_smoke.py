"""冒烟测试：验证 pytest 测试设施与核心模型可用。"""

import pytest

from courseApp.models import (
    Chapter,
    Course,
    CourseCategory,
    Exercise,
    LearningContent,
    Lesson,
    UserCourseEnrollment,
    UserLessonProgress,
)
from practiceApp.models import PracticeRecord, PracticeSession

CORE_MODELS = [
    CourseCategory,
    Course,
    Chapter,
    Lesson,
    LearningContent,
    Exercise,
    UserCourseEnrollment,
    UserLessonProgress,
]


def test_all_core_models_importable():
    """courseApp 8 个核心模型均可导入。"""
    assert all(model is not None for model in CORE_MODELS)


def test_practice_models_importable():
    """practiceApp 2 个模型均可导入。"""
    assert PracticeSession is not None
    assert PracticeRecord is not None


@pytest.mark.django_db
def test_lesson_chain_and_session_roundtrip():
    """Course → Chapter → Lesson → PracticeSession 可创建并读取（验证 SQLite 测试库可用）。"""
    course = Course.objects.create(name='冒烟课程')
    chapter = Chapter.objects.create(course=course, name='冒烟章节')
    lesson = Lesson.objects.create(chapter=chapter, name='冒烟课时')

    session = PracticeSession.objects.create(
        lesson=lesson,
        mode='typing',
        status='in_progress',
        total_questions=1,
    )

    fetched = PracticeSession.objects.get(pk=session.pk)
    assert fetched.lesson == lesson
    assert fetched.mode == 'typing'
    assert fetched.total_questions == 1
