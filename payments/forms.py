from django import forms
import re


class CheckoutForm(forms.Form):

    phone_number = forms.CharField(
        label="M-Pesa Phone Number",
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 0712345678',
        })
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()

        pattern = r'^(\+254|254|0)(7|1)\d{8}$'

        if not re.match(pattern, phone):
            raise forms.ValidationError(
                "Enter a valid Kenyan phone number."
            )

        if phone.startswith('+254'):
            phone = phone[1:]
        elif phone.startswith('0'):
            phone = '254' + phone[1:]

        return phone