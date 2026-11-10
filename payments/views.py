import json
import logging
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction

from .services import initiate_stk_push, query_stk_status
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import requests

from courses.models import Course
from students.models import Enrollment

from .models import Payment
from .forms import CheckoutForm
from .services import initiate_stk_push


@login_required
def checkout(request, slug):

    course = get_object_or_404(
        Course,
        slug=slug,
        is_published=True
    )

    # Prevent duplicate enrolment.
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists()

    if enrollment:
        return redirect('student_dashboard')

    if request.method == 'POST':

        form = CheckoutForm(request.POST)

        if form.is_valid():

            # Create a pending payment record.
            payment = Payment.objects.create(
                student=request.user,
                course=course,
                amount=course.price,
                phone_number=form.cleaned_data['phone_number'],
                status='PENDING'
            )

            try:
                # Send the STK Push request.
                response = initiate_stk_push(payment)

                # Safaricom accepted the STK Push request.
                if response.get('ResponseCode') == '0':

                    payment.merchant_request_id = response.get(
                        'MerchantRequestID'
                    )

                    payment.checkout_request_id = response.get(
                        'CheckoutRequestID'
                    )

                    payment.save(update_fields=[
                        'merchant_request_id',
                        'checkout_request_id',
                        'updated_at'
                    ])

                    messages.success(
                        request,
                        'STK Push sent. Check your phone and follow '
                        'the M-Pesa sandbox instructions.'
                    )

                else:
                    # Safaricom rejected the request.
                    payment.status = 'FAILED'
                    payment.save(update_fields=[
                        'status',
                        'updated_at'
                    ])

                    messages.error(
                        request,
                        response.get(
                            'ResponseDescription',
                            'Safaricom rejected the payment request.'
                        )
                    )

            except (requests.RequestException, ValueError, KeyError) as error:

                # A network timeout can be ambiguous: Safaricom
                # may have received the request despite no response.
                # Keep the payment pending for reconciliation.
                messages.warning(
                    request,
                    'We could not confirm the STK Push response. '
                    'Your payment remains pending. Please check '
                    'its status before trying again.'
                )

                print('M-Pesa request error:', error)

            return redirect(
                'payment_status',
                payment_id=payment.id
            )

    else:
        form = CheckoutForm()

    return render(request, 'payments/checkout.html', {
        'course': course,
        'form': form
    })


@login_required
def payment_status(request, payment_id):

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        student=request.user
    )

    return render(request, 'payments/payment_status.html', {
        'payment': payment
    })


logger = logging.getLogger(__name__)



@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    Process Safaricom STK Push callbacks.
    Validate the callback details before activating enrolment.
    """

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'ResultCode': 1, 'ResultDesc': 'Invalid JSON'},
            status=400
        )

    callback = data.get('Body', {}).get('stkCallback')

    if not callback:
        return JsonResponse(
            {'ResultCode': 1, 'ResultDesc': 'Invalid callback'},
            status=400
        )

    checkout_id = callback.get('CheckoutRequestID')
    merchant_id = callback.get('MerchantRequestID')
    callback_result = callback.get('ResultCode')

    if (
        not checkout_id
        or not merchant_id
        or callback_result is None
    ):
        return JsonResponse(
            {'ResultCode': 1, 'ResultDesc': 'Missing callback details'},
            status=400
        )

    payment = Payment.objects.filter(
        checkout_request_id=checkout_id,
        merchant_request_id=merchant_id
    ).first()

    if not payment:
        logger.warning(
            'No payment found for checkout request %s',
            checkout_id
        )
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Callback received'
        })

    # Safaricom reports a failed or cancelled transaction.
    if str(callback_result) != '0':
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().get(
                pk=payment.pk
            )

            if locked_payment.status == 'PENDING':
                locked_payment.status = 'FAILED'
                locked_payment.save(update_fields=[
                    'status',
                    'updated_at'
                ])

        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Payment failure recorded'
        })

    # Extract successful transaction metadata.
    metadata = callback.get('CallbackMetadata', {}).get('Item', [])

    details = {
        item.get('Name'): item.get('Value')
        for item in metadata
        if 'Name' in item
    }

    receipt = details.get('MpesaReceiptNumber')
    amount = details.get('Amount')
    phone = details.get('PhoneNumber')

    try:
        received_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        received_amount = None

    if (
        not receipt
        or received_amount != payment.amount
        or str(phone) != payment.phone_number
    ):
        logger.warning(
            'Payment metadata mismatch for payment %s',
            payment.id
        )
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Payment verification pending'
        })

    # Update payment and activate enrolment atomically.
    with transaction.atomic():
        locked_payment = Payment.objects.select_for_update().get(
            pk=payment.pk
        )

        if locked_payment.status == 'SUCCESS':
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Payment already processed'
            })

        if locked_payment.status != 'PENDING':
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Payment is not pending'
            })

        locked_payment.status = 'SUCCESS'
        locked_payment.mpesa_receipt_number = str(receipt)

        locked_payment.save(update_fields=[
            'status',
            'mpesa_receipt_number',
            'updated_at'
        ])

        Enrollment.objects.update_or_create(
            student=locked_payment.student,
            course=locked_payment.course,
            defaults={'is_active': True}
        )

    logger.info('Payment %s successfully processed', payment.id)

    return JsonResponse({
        'ResultCode': 0,
        'ResultDesc': 'Payment successfully processed'
    })
