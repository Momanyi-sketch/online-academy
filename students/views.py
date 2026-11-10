from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST

from .forms import StudentRegistrationForm
from .models import Enrollment


def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'students/register.html', {
        'form': form
    })


def student_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('student_dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'students/login.html', {
        'form': form
    })


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')

    return render(request, 'students/dashboard.html', {
        'enrollments': enrollments
    })


@login_required
@require_POST
def student_logout(request):
    logout(request)
    return redirect('home')