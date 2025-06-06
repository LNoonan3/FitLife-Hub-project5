import stripe
from datetime import date
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Plan, Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


def plan_list(request):
    """Display available subscription plans."""
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'subscriptions/plan_list.html', {'plans': plans})


@login_required
def subscribe_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': plan.name},
                'unit_amount': int(plan.price * 100)
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            redirect('subscriptions:subscription_success').url
        ),
        cancel_url=request.build_absolute_uri(
            redirect('subscriptions:subscription_cancel').url
        ),
        metadata={'plan_id': plan.id}
    )
    return redirect(session.url, code=303)


def subscription_success(request):
    """Show a success message after subscribing."""
    return render(request, 'subscriptions/subscription_success.html')


def subscription_cancel(request):
    """Show a cancellation message if user cancels checkout."""
    return render(request, 'subscriptions/subscription_cancel.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type']=='checkout.session.completed':
        sess = event['data']['object']
        plan_id = sess['metadata']['plan_id']
        from django.contrib.auth.models import User
        user = User.objects.filter(email=sess['customer_details']['email']).first()
        plan = Plan.objects.get(pk=plan_id)
        Subscription.objects.create(
            user=user, plan=plan,
            stripe_sub_id=sess.get('subscription',''),
            start_date=date.today(),
            status='active'
        )
    return HttpResponse(status=200)
