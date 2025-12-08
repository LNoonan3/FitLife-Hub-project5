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
    from datetime import date

    # Get the most recent ACTIVE subscription first, then fall back to most recent
    active_subscription = (
        Subscription.objects
        .filter(user=request.user, status='active')
        .order_by('-start_date')
        .first()
    )

    # If no active subscription, get the most recent one (could be canceled)
    subscription = active_subscription or (
        Subscription.objects
        .filter(user=request.user)
        .order_by('-start_date')
        .first()
    )

    # Get recent progress updates
    from core.models import ProgressUpdate
    recent_updates = ProgressUpdate.objects.filter(
        user=request.user
    ).order_by('-created_at')[:3]

    days_until_next_payment = None
    if subscription and subscription.status == 'active' and subscription.next_payment_date:
        next_payment = subscription.next_payment_date
        days_until_next_payment = (next_payment - date.today()).days

    return render(request, 'users/profile.html', {
        'subscription': subscription,
        'recent_updates': recent_updates,
        'days_until_next_payment': days_until_next_payment,
        'today': date.today(),
    })


@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Get the most recent subscription
    subscription = (
        Subscription.objects
        .filter(user=request.user)
        .order_by('-start_date')
        .first()
    )

    days_until_next_payment = None
    if subscription and subscription.next_payment_date and subscription.status == 'active':
        next_payment = subscription.next_payment_date
        days_until_next_payment = (next_payment - date.today()).days

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        'users/profile_edit.html',
        {
            'form': form,
            'subscription': subscription,
            'days_until_next_payment': days_until_next_payment,
            'today': date.today(),
        }
    )
