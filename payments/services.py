
import base64
from datetime import datetime

import requests
from django.conf import settings


def get_mpesa_base_url():
    if settings.MPESA_ENVIRONMENT == 'production':
        return 'https://api.safaricom.co.ke'

    return 'https://sandbox.safaricom.co.ke'


def get_access_token():
    url = (
        f'{get_mpesa_base_url()}'
        '/oauth/v1/generate?grant_type=client_credentials'
    )

    response = requests.get(
        url,
        auth=(
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET
        ),
        timeout=30
    )

    response.raise_for_status()

    return response.json()['access_token']


def generate_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    raw_password = (
        settings.MPESA_SHORTCODE
        + settings.MPESA_PASSKEY
        + timestamp
    )

    password = base64.b64encode(
        raw_password.encode()
    ).decode()

    return password, timestamp


def initiate_stk_push(payment):
    token = get_access_token()

    password, timestamp = generate_password()

    shortcode = settings.MPESA_SHORTCODE

    amount = int(payment.amount)

    if amount <= 0 or payment.amount != amount:
        raise ValueError(
            'Payment amount must be a positive whole number.'
        )

    url = (
        f'{get_mpesa_base_url()}'
        '/mpesa/stkpush/v1/processrequest'
    )

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': settings.MPESA_TRANSACTION_TYPE,
        'Amount': amount,
        'PartyA': payment.phone_number,
        'PartyB': shortcode,
        'PhoneNumber': payment.phone_number,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': 'ACADEMY',
        'TransactionDesc': 'Course Payment'
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def query_stk_status(checkout_request_id):
    token = get_access_token()

    password, timestamp = generate_password()

    url = (
        f'{get_mpesa_base_url()}'
        '/mpesa/stkpushquery/v1/query'
    )

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
