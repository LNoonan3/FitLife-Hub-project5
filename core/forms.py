# core/forms.py
from django import forms
from .models import ProgressUpdate, NewsletterSubscriber


class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = ['title', 'content']


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
