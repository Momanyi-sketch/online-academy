
from django.db import models
from django.utils.text import slugify


class Course(models.Model):

    title = models.CharField(max_length=200)

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        blank=True,
        null=True
    )

    is_published = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    lesson_number = models.PositiveIntegerField(default=1)

    video_file = models.FileField(
        upload_to='lessons/videos/',
        blank=True,
        null=True
    )

    video_url = models.URLField(
        blank=True,
        null=True
    )

    notes_file = models.FileField(
        upload_to='lessons/notes/',
        blank=True,
        null=True
    )

    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lesson_number']
        unique_together = ['course', 'lesson_number']

    def __str__(self):
        return f'{self.course.title} - {self.title}'