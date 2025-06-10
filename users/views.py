from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProfileForm
from .models import Profile
from subscriptions.models import Subscription
from datetime import date


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:profile_edit')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile(request):
    subscription = Subscription.objects.filter(user=request.user).order_by('-start_date').first()
    days_until_next_payment = None
    if subscription and subscription.next_payment_date:
        days_until_next_payment = (subscription.next_payment_date - date.today()).days
    return render(request, 'users/profile.html', {
        'subscription': subscription,
        'days_until_next_payment': days_until_next_payment,
    })


@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    subscription = Subscription.objects.filter(user=request.user, status='active').order_by('-start_date').first()
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'users/profile_edit.html', {'form': form, 'subscription': subscription})
