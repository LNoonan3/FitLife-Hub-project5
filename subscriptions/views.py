import stripe
from datetime import date, timedelta
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.contrib.auth.models import User
from .models import Subscription, Plan


stripe.api_key = settings.STRIPE_SECRET_KEY


def plan_list(request):
    """Display available subscription plans."""
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'subscriptions/plan_list.html', {'plans': plans})


@login_required
def subscribe_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)
    if not plan.stripe_price_id:
        messages.error(request, "This plan is not configured for Stripe subscriptions.")
        return redirect('subscriptions:plan_list')
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri(
            reverse('subscriptions:subscription_success')
        ),
        cancel_url=request.build_absolute_uri(
            reverse('subscriptions:subscription_cancel')
        ),
        metadata={'plan_id': plan.id}
    )
    return redirect(session.url, code=303)


@login_required
def cancel_subscription(request, sub_id):
    subscription = Subscription.objects.get(pk=sub_id, user=request.user)
    if subscription.status == 'active':
        subscription.status = 'canceled'
        subscription.end_date = date.today()
        subscription.save()
        messages.success(request, "Your subscription has been canceled.")
    else:
        messages.info(request, "Subscription is already canceled.")
    return redirect('subscriptions:my_subscription')


@login_required
def my_subscription(request):
    subscription = Subscription.objects.filter(user=request.user).order_by('-start_date').first()
    return render(request, 'subscriptions/my_subscription.html', {'subscription': subscription})


def subscription_success(request):
    """Show a success message after subscribing."""
    return render(request, 'subscriptions/subscription_success.html')


def subscription_cancel(request):
    """Show a cancellation message if user cancels checkout."""
    return render(request, 'subscriptions/subscription_cancel.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        stripe_sub_id = session.get('subscription')
        plan_id = session['metadata'].get('plan_id')

        try:
            user = User.objects.get(email=customer_email)
            plan = Plan.objects.get(id=plan_id)
        except (User.DoesNotExist, Plan.DoesNotExist):
            return HttpResponse(status=400)

        stripe_subscription = stripe.Subscription.retrieve(stripe_sub_id)
        next_payment_unix = stripe_subscription['current_period_end']
        next_payment_date = timezone.datetime.fromtimestamp(next_payment_unix).date()

        Subscription.objects.update_or_create(
            stripe_sub_id=stripe_sub_id,
            defaults={
                'user': user,
                'plan': plan,
                'status': 'active',
                'start_date': timezone.now().date(),
                'next_payment_date': next_payment_date,
            }
        )

    return HttpResponse(status=200)
