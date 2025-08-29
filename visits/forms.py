# visits/forms.py
from decimal import Decimal, ROUND_HALF_UP
from django import forms
from django.core.exceptions import ValidationError
from .models import NewVisit, Customer, CustomerContact


class NewVisitForm(forms.ModelForm):
    # ✅ Add read-only fields for template
    contact_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'id_contact_number'
        })
    )
    designation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'id_designation'
        })
    )

    class Meta:
        model = NewVisit
        exclude = ['added_by', 'created_at', 'updated_at']
        widgets = {
            'productionline': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.Select(attrs={'class': 'form-select', 'id': 'id_company_name'}),
            'contact_person': forms.Select(attrs={'class': 'form-select', 'id': 'id_contact_person'}),
            'meeting_purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_outcome': forms.TextInput(attrs={'class': 'form-control'}),
            'item_discussed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_order_quoted': forms.Select(attrs={'class': 'form-select'}, choices=[(True, 'Yes'), (False, 'No')]),
            'order_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason_no_order': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always show companies
        self.fields['company_name'].queryset = Customer.objects.all().order_by('company_name')

        # Default: no contacts
        self.fields['contact_person'].queryset = CustomerContact.objects.none()
        self.fields['contact_person'].empty_label = "Select company first"

        # If company already chosen (re-render or editing)
        company_id = None
        if self.data.get('company_name'):
            try:
                company_id = int(self.data.get('company_name'))
            except (ValueError, TypeError):
                company_id = None
        elif self.instance.pk and getattr(self.instance, 'company_name_id', None):
            company_id = self.instance.company_name_id

        if company_id:
            self.fields['contact_person'].queryset = CustomerContact.objects.filter(
                customer_id=company_id
            ).order_by('contact_name')
            self.fields['contact_person'].empty_label = "Select contact"

    def clean(self):
        cleaned = super().clean()

        # ✅ Geo required
        lat = cleaned.get('latitude')
        lon = cleaned.get('longitude')
        if not lat or not lon:
            raise ValidationError("Location not detected yet. Please allow location access and wait for the map.")

        try:
            cleaned['latitude'] = str(Decimal(str(lat)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
            cleaned['longitude'] = str(Decimal(str(lon)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
        except Exception:
            raise ValidationError("Invalid coordinates received. Please refresh and try again.")

        # ✅ Quotation logic
        is_quoted = cleaned.get('is_order_quoted')
        order_amount = cleaned.get('order_amount')
        reason = cleaned.get('reason_no_order')

        if isinstance(is_quoted, str):
            is_quoted = True if is_quoted == "True" else False if is_quoted == "False" else None
            cleaned['is_order_quoted'] = is_quoted

        if is_quoted is True and not order_amount:
            self.add_error('order_amount', "Order amount is required when order is quoted.")
        elif is_quoted is False and not reason:
            self.add_error('reason_no_order', "Reason is required when order is not quoted.")

        return cleaned




# visits/forms.py
from decimal import Decimal, ROUND_HALF_UP
from django import forms
from django.core.exceptions import ValidationError
from .models import FollowUp, Customer, CustomerContact


class FollowUpForm(forms.ModelForm):
    # ✅ Read-only fields for template
    contact_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'id_contact_number'
        })
    )
    designation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'id': 'id_designation'
        })
    )

    class Meta:
        model = FollowUp
        exclude = ['added_by', 'created_at', 'updated_at']
        widgets = {
            'productionline': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.Select(attrs={'class': 'form-select', 'id': 'id_company_name'}),
            'contact_person': forms.Select(attrs={'class': 'form-select', 'id': 'id_contact_person'}),
            'meeting_purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_outcome': forms.TextInput(attrs={'class': 'form-control'}),
            'item_discussed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            # Order quoted
            'is_order_quoted': forms.Select(attrs={'class': 'form-select'}, choices=[(True, 'Yes'), (False, 'No')]),
            'order_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason_no_order': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # ✅ Payment collected
            'is_payment_collected': forms.Select(attrs={'class': 'form-select'}, choices=[(True, 'Yes'), (False, 'No')]),
            'payment_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason_no_payment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Location
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always show companies
        self.fields['company_name'].queryset = Customer.objects.all().order_by('company_name')

        # Default: no contacts
        self.fields['contact_person'].queryset = CustomerContact.objects.none()
        self.fields['contact_person'].empty_label = "Select company first"

        # If company already chosen
        company_id = None
        if self.data.get('company_name'):
            try:
                company_id = int(self.data.get('company_name'))
            except (ValueError, TypeError):
                company_id = None
        elif self.instance.pk and getattr(self.instance, 'company_name_id', None):
            company_id = self.instance.company_name_id

        if company_id:
            self.fields['contact_person'].queryset = CustomerContact.objects.filter(
                customer_id=company_id
            ).order_by('contact_name')
            self.fields['contact_person'].empty_label = "Select contact"

    def clean(self):
        cleaned = super().clean()

        # ✅ Geo required
        lat = cleaned.get('latitude')
        lon = cleaned.get('longitude')
        if not lat or not lon:
            raise ValidationError("Location not detected yet. Please allow location access and wait for the map.")

        try:
            cleaned['latitude'] = str(Decimal(str(lat)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
            cleaned['longitude'] = str(Decimal(str(lon)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
        except Exception:
            raise ValidationError("Invalid coordinates received. Please refresh and try again.")

        # ✅ Order quoted logic
        is_quoted = cleaned.get('is_order_quoted')
        order_amount = cleaned.get('order_amount')
        reason = cleaned.get('reason_no_order')

        if isinstance(is_quoted, str):
            is_quoted = True if is_quoted == "True" else False if is_quoted == "False" else None
            cleaned['is_order_quoted'] = is_quoted

        if is_quoted is True and not order_amount:
            self.add_error('order_amount', "Order amount is required when order is quoted.")
        elif is_quoted is False and not reason:
            self.add_error('reason_no_order', "Reason is required when order is not quoted.")

        # ✅ Payment collected logic (new)
        is_payment = cleaned.get('is_payment_collected')
        payment_amount = cleaned.get('payment_amount')
        reason_payment = cleaned.get('reason_no_payment')

        if isinstance(is_payment, str):
            is_payment = True if is_payment == "True" else False if is_payment == "False" else None
            cleaned['is_payment_collected'] = is_payment

        if is_payment is True and not payment_amount:
            self.add_error('payment_amount', "Payment amount is required when payment is collected.")
        elif is_payment is False and not reason_payment:
            self.add_error('reason_no_payment', "Reason is required when payment is not collected.")

        return cleaned
