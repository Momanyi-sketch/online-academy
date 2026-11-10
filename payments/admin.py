from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'course',
        'amount',
        'phone_number',
        'status',
        'created_at'
    )

    list_filter = (
        'status',
        'created_at'
    )

    search_fields = (
        'student__username',
        'course__title',
        'mpesa_receipt_number'
    )

    readonly_fields = (
        'created_at',
        'updated_at'
    )