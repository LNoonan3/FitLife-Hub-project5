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
    plans = Plan.objects.filter(is_active=True)
    user_active_plan_ids = []
    if request.user.is_authenticated:
        user_active_plan_ids = list(
            Subscription.objects.filter(user=request.user, status='active').values_list('plan_id', flat=True)
        )
    if request.GET.get('subscribed') == '1':
        messages.success(request, "Thank you! Your subscription was successful.")
    return render(
        request,
        'subscriptions/plan_list.html',
        {
            'plans': plans,
            'user_active_plan_ids': user_active_plan_ids,
        }
    )


@login_required
def subscribe_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)
    existing = Subscription.objects.filter(user=request.user, plan=plan, status='active').first()
    if existing:
        messages.error(request, "You already have an active subscription to this plan.")
        return redirect('subscriptions:my_subscription')

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
            reverse('subscriptions:plan_list') + '?subscribed=1'
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
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Subscription.delete(subscription.stripe_sub_id)
        except Exception:
            messages.error(request, "Could not cancel on Stripe. Please contact support.")
            return redirect('subscriptions:my_subscription')
        messages.success(request, "Your subscription has been canceled. You will retain access until the end of your billing period.")
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
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("Webhook signature verification failed:", e)
        return HttpResponse(status=400)

    print("Stripe event received:", event['type'])

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        stripe_sub_id = session.get('subscription')
        plan_id = session.get('metadata', {}).get('plan_id')

        print("Session data:", session)
        print("customer_email:", customer_email, "stripe_sub_id:", stripe_sub_id, "plan_id:", plan_id)

        try:
            user = User.objects.get(email=customer_email)
        except User.DoesNotExist:
            print("User not found for email:", customer_email)
            return HttpResponse(status=400)
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            print("Plan not found for id:", plan_id)
            return HttpResponse(status=400)
        try:
            stripe_subscription = stripe.Subscription.retrieve(stripe_sub_id)
            items = stripe_subscription['items']['data']
            if items and 'current_period_end' in items[0]:
                next_payment_unix = items[0]['current_period_end']
                next_payment_date = timezone.datetime.fromtimestamp(next_payment_unix).date()
            else:
                print("No current_period_end found in subscription items!")
                next_payment_date = None
        except Exception as e:
            print("Stripe subscription retrieve failed:", e)
            return HttpResponse(status=400)

        Subscription.objects.update_or_create(
            stripe_sub_id=stripe_sub_id,
            defaults={
                'user': user,
                'plan': plan,
                'status': 'active',
                'start_date': timezone.now().date(),
                'next_payment_date': next_payment_date,
                'end_date': None,
            }
        )
        print("Subscription activated for user:", user.email)

    if event['type'] == 'customer.subscription.deleted':
        stripe_sub_id = event['data']['object']['id']
        try:
            sub = Subscription.objects.get(stripe_sub_id=stripe_sub_id)
            sub.status = 'canceled'
            sub.end_date = timezone.now().date()
            sub.save()
            print("Subscription canceled:", stripe_sub_id)
        except Subscription.DoesNotExist:
            print("Subscription not found for cancel:", stripe_sub_id)

    return HttpResponse(status=200)
