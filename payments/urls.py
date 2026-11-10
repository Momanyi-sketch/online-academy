from django.urls import path
from . import views

urlpatterns = [
    path(
        'checkout/<slug:slug>/',
        views.checkout,
        name='checkout'
    ),

    path(
        'status/<int:payment_id>/',
        views.payment_status,
        name='payment_status'
    ),

    path(
        'callback/',
        views.mpesa_callback,
        name='mpesa_callback'
    ),
]