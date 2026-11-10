from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path(
        'course/<slug:slug>/',
        views.course_detail,
        name='course_detail'
    ),

    path(
        'course/<slug:slug>/lesson/<int:lesson_id>/',
        views.lesson_detail,
        name='lesson_detail'
    ),
]