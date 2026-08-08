from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Course, CourseCategory, Chapter


def course(request):
    categories = CourseCategory.objects.filter(is_active=True)
    courses = Course.objects.filter(is_published=True).select_related('teacher', 'category')
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    return render(request, 'course.html', {
        'categories': categories,
        'courses': courses,
        'current_category': int(category_id) if category_id else 0,
        'active_menu': 'course-menu',
        'collapse_menu': 'collapse-std',
    })


def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related('teacher', 'category').prefetch_related(
            Prefetch('chapters', queryset=Chapter.objects.prefetch_related('lessons'))
        ),
        id=course_id, is_published=True
    )
    return render(request, 'course_detail.html', {
        'course': course,
        'chapters': course.chapters.all(),
        'total_lessons': sum(ch.lessons.count() for ch in course.chapters.all()),
        'active_menu': 'course-menu',
        'collapse_menu': 'collapse-std',
    })