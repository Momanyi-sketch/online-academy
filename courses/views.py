from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Course, Lesson
from students.models import Enrollment


def home(request):
    courses = Course.objects.filter(is_published=True)

    return render(request, 'courses/home.html', {
        'courses': courses
    })


def course_detail(request, slug):
    course = get_object_or_404(
        Course,
        slug=slug,
        is_published=True
    )

    lessons = course.lessons.filter(is_published=True)

    is_enrolled = False

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            student=request.user,
            course=course,
            is_active=True
        ).exists()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled
    })


@login_required
def lesson_detail(request, slug, lesson_id):

    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__slug=slug,
        course__is_published=True,
        is_published=True
    )

    has_access = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course,
        is_active=True
    ).exists()

    if not has_access:
        return render(
            request,
            'courses/access_denied.html',
            {
                'course': lesson.course,
                'lesson': lesson
            },
            status=403
        )

    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson,
        'course': lesson.course
    })