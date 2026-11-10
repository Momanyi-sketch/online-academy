from django.contrib import admin
from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'price',
        'is_published',
        'created_at'
    )

    list_filter = ('is_published', 'created_at')

    search_fields = ('title', 'description')

    prepopulated_fields = {'slug': ('title',)}

    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'course',
        'lesson_number',
        'is_published'
    )

    list_filter = ('course', 'is_published')

    search_fields = ('title', 'description')