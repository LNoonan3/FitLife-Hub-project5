from django import forms
from .models import Review

COUNTRY_CHOICES = [
    ('', 'Select Country'),
    ('IE', 'Ireland'),
    ('GB', 'United Kingdom'),
    ('US', 'United States'),
    ('CA', 'Canada'),
    ('FR', 'France'),
    ('DE', 'Germany'),
    ('ES', 'Spain'),
    ('IT', 'Italy'),
    ('NL', 'Netherlands'),
    ('BE', 'Belgium'),
    ('AU', 'Australia'),
    ('NZ', 'New Zealand'),
    # ...add more countries as needed...
]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    address = forms.CharField(max_length=255, label="Address")
    city = forms.CharField(max_length=100, label="City")
    postcode = forms.CharField(max_length=20, label="Postcode")
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label="Country")
    email = forms.EmailField(max_length=100, label="Email")
    phone = forms.CharField(max_length=20, label="Phone")
