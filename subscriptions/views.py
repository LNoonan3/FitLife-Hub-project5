import stripe
# from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Subscription, Plan


stripe.api_key = settings.STRIPE_SECRET_KEY


def plan_list(request):
    plans = Plan.objects.filter(is_active=True)
    user_active_plan_ids = []
    user_canceled_plan_ids = []
    current_plan = None

    if request.user.is_authenticated:
        # Get active subscriptions
        active_subs = Subscription.objects.filter(
            user=request.user,
            status='active'
        )
        user_active_plan_ids = list(
            active_subs.values_list('plan_id', flat=True)
        )

        # Get the current active subscription
        current_subscription = active_subs.first()
        if current_subscription:
            current_plan = current_subscription.plan

        # Get canceled subscriptions
        # (for showing "Renew" instead of "Subscribe")
        user_canceled_plan_ids = list(
            Subscription.objects.filter(
                user=request.user,
                status='canceled'
            ).values_list(
                'plan_id',
                flat=True
            )
        )

    # Check for success messages
    if request.GET.get('subscribed') == '1':
        if request.GET.get('switched') == '1':
            messages.success(
                request,
                (
                    "Your plan has been successfully switched! "
                    "Your old subscription has been canceled."
                )
            )
        else:
            messages.success(
                request,
                "Thank you! Your subscription was successful."
            )

    return render(
        request,
        'subscriptions/plan_list.html',
        {
            'plans': plans,
            'user_active_plan_ids': user_active_plan_ids,
            'user_canceled_plan_ids': user_canceled_plan_ids,
            'current_plan': current_plan,
        }
    )


@login_required
def subscribe_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)

    # Check for existing active subscription to THIS specific plan
    existing_active = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='active'
    ).first()

    if existing_active:
        messages.error(
            request,
            "You already have an active subscription to this plan."
        )
        return redirect('subscriptions:my_subscription')

    # Check if user has ANY other active subscription
    other_active_subscription = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).exclude(plan=plan).first()

    if other_active_subscription:
        messages.warning(
            request,
            (

                f"You currently have an active "
                f"{other_active_subscription.plan.name} subscription. "
                "When you complete checkout, your current plan will be canceled "
                "and replaced with the new plan."

            )
        )

    if not plan.stripe_price_id:
        messages.error(
            request,
            "This plan is not configured for Stripe subscriptions."
        )
        return redirect('subscriptions:plan_list')

    # Create Stripe Checkout Session with metadata
    metadata = {
        'plan_id': plan.id,
        'user_id': request.user.id,
    }

    # Add existing subscription info to metadata if switching plans
    if other_active_subscription:
        metadata['old_subscription_id'] = other_active_subscription.id
        metadata['old_stripe_sub_id'] = other_active_subscription.stripe_sub_id
        metadata['switching_plans'] = 'true'

    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri(
            reverse('subscriptions:plan_list') + '?subscribed=1&switched=1'
        ),
        cancel_url=request.build_absolute_uri(
            reverse('subscriptions:subscription_cancel')
        ),
        metadata=metadata
    )
    return redirect(session.url, code=303)


@login_required
def cancel_subscription(request, sub_id):
    subscription = get_object_or_404(
        Subscription,
        pk=sub_id,
        user=request.user
    )

    if subscription.status == 'active':
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Cancel the subscription on Stripe
            stripe.Subscription.delete(subscription.stripe_sub_id)

            # Update the local database record immediately
            subscription.status = 'canceled'
            subscription.end_date = timezone.now().date()
            subscription.save()

            messages.success(
                request,
                "Your subscription has been successfully canceled. "
                "You will retain access until the end of your billing period."
            )
        except stripe.error.InvalidRequestError:
            # Handle case where subscription doesn't exist on Stripe
            messages.warning(
                request,
                "Subscription not found on Stripe. Canceling locally."
            )
            subscription.status = 'canceled'
            subscription.end_date = timezone.now().date()
            subscription.save()
        except stripe.error.StripeError as e:
            messages.error(
                request,
                f"Could not cancel subscription on Stripe: {str(e)}. "
                "Please contact support."
            )
            return redirect('subscriptions:my_subscription')
        except Exception:
            messages.error(
                request,
                "An unexpected error occurred. Please contact support."
            )
            return redirect('subscriptions:my_subscription')
    else:
        messages.info(
            request,
            "This subscription is already canceled."
        )

    return redirect('subscriptions:my_subscription')


@login_required
def my_subscription(request):
    from datetime import date

    # Get the most recent ACTIVE subscription first
    active_subscription = (
        Subscription.objects
        .filter(user=request.user, status='active')
        .order_by('-start_date')
        .first()
    )

    # If no active subscription, get the most recent canceled one
    subscription = active_subscription or (
        Subscription.objects
        .filter(user=request.user)
        .order_by('-start_date')
        .first()
    )

    # Get all user's subscriptions for history (excluding current)
    if subscription:
        all_subscriptions = (
            Subscription.objects
            .filter(user=request.user)
            .exclude(id=subscription.id)
            .order_by('-start_date')
        )
    else:
        all_subscriptions = Subscription.objects.none()

    days_until_next_payment = None
    if (
        subscription
        and subscription.next_payment_date
        and subscription.status == 'active'
    ):
        next_payment = subscription.next_payment_date
        days_until_next_payment = (next_payment - date.today()).days

    return render(
        request,
        'subscriptions/my_subscription.html',
        {
            'subscription': subscription,
            'all_subscriptions': all_subscriptions,
            'days_until_next_payment': days_until_next_payment,
            'today': date.today(),
        }
    )


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
    except ValueError as e:
        print("Invalid payload:", e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print("Invalid signature:", e)
        return HttpResponse(status=400)
    except Exception as e:
        print("Webhook error:", e)
        return HttpResponse(status=400)

    print(f"Stripe event received: {event['type']}")

    # Handle successful checkout
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        stripe_sub_id = session.get('subscription')
        plan_id = session.get('metadata', {}).get('plan_id')
        user_id = session.get('metadata', {}).get('user_id')
        old_subscription_id = (
            session.get('metadata', {}).get('old_subscription_id')
        )
        old_stripe_sub_id = (
            session.get('metadata', {}).get('old_stripe_sub_id')
        )
        metadata = session.get('metadata', {})
        switching_plans_value = metadata.get('switching_plans')
        switching_plans = switching_plans_value == 'true'

        try:
            # Get user and plan
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(email=customer_email)
            plan = Plan.objects.get(id=plan_id)
        except User.DoesNotExist:
            print(f"User not found: {customer_email or user_id}")
            return HttpResponse(status=400)
        except Plan.DoesNotExist:
            print(f"Plan not found: {plan_id}")
            return HttpResponse(status=400)

        start_date = timezone.now().date()

        # Calculate next payment date
        if plan.interval == 'monthly':
            next_payment_date = start_date + relativedelta(months=1)
        elif plan.interval == 'yearly':
            next_payment_date = start_date + relativedelta(years=1)
        else:
            next_payment_date = None

        # STEP 1: Handle plan switching - cancel old subscription FIRST
        if switching_plans:
            if old_subscription_id:
                try:
                    old_sub = Subscription.objects.get(
                        id=old_subscription_id,
                        user=user
                    )
                    # Only cancel if still active
                    if old_sub.status == 'active':
                        # Cancel on Stripe first
                        if old_stripe_sub_id or old_sub.stripe_sub_id:
                            try:
                                stripe.Subscription.delete(
                                    old_stripe_sub_id or old_sub.stripe_sub_id
                                )
                                print(
                                    f"✓ Canceled old Stripe subscription: "
                                    f"{old_stripe_sub_id or old_sub.stripe_sub_id}"
                                )
                            except stripe.error.InvalidRequestError:
                                print(
                                    "Old subscription already canceled on Stripe: "
                                    f"{old_stripe_sub_id or old_sub.stripe_sub_id}"
                                )
                            except stripe.error.StripeError as e:
                                print(f"Error canceling old Stripe subscription: {e}")

                        # Update old subscription in database
                        old_sub.status = 'canceled'
                        old_sub.end_date = timezone.now().date()
                        old_sub.save()
                        print(
                            f"✓ Canceled old subscription #{old_sub.id} "
                            f"({old_sub.plan.name}) for user {user.email}"
                        )
                except Subscription.DoesNotExist:
                    print(f"Old subscription {old_subscription_id} not found")
            else:
                # Fallback: Find and cancel any active subscription
                # for this user
                active_subs = Subscription.objects.filter(
                    user=user,
                    status='active'
                ).exclude(plan=plan)

                for old_sub in active_subs:
                    try:
                        stripe.Subscription.delete(old_sub.stripe_sub_id)
                        print(
                            f"✓ Canceled Stripe subscription: "
                            f"{old_sub.stripe_sub_id}"
                        )
                    except Exception:
                        pass

                    old_sub.status = 'canceled'
                    old_sub.end_date = timezone.now().date()
                    old_sub.save()
                    print(
                        f"✓ Canceled subscription #{old_sub.id} "
                        f"({old_sub.plan.name})"
                    )

        # STEP 2: Check if renewing a canceled subscription to the SAME plan
        old_canceled_subscription = Subscription.objects.filter(
            user=user,
            plan=plan,
            status='canceled'
        ).order_by('-end_date').first()

        if old_canceled_subscription and not switching_plans:
            # Renewing the same canceled plan - update existing record
            old_canceled_subscription.stripe_sub_id = stripe_sub_id
            old_canceled_subscription.status = 'active'
            old_canceled_subscription.start_date = start_date
            old_canceled_subscription.next_payment_date = next_payment_date
            old_canceled_subscription.end_date = None
            old_canceled_subscription.save()
            print(
                f"✓ Subscription RENEWED: User {user.email} → {plan.name} "
                f"(ID: {old_canceled_subscription.id})"
            )
        else:
            # STEP 3: Create new subscription for different plan
            new_sub = Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_sub_id=stripe_sub_id,
                status='active',
                start_date=start_date,
                next_payment_date=next_payment_date,
                end_date=None,
            )
            print(
                f"✓ NEW subscription created: User {user.email} → {plan.name} "
                f"(ID: {new_sub.id})"
            )

    # Handle subscription cancellation
    elif event['type'] == 'customer.subscription.deleted':
        stripe_sub_id = event['data']['object']['id']
        try:
            sub = Subscription.objects.get(stripe_sub_id=stripe_sub_id)
            sub.status = 'canceled'
            sub.end_date = timezone.now().date()
            sub.save()
            print(
                f"✓ Subscription canceled via webhook: {stripe_sub_id} "
                f"for user {sub.user.email}"
            )
        except Subscription.DoesNotExist:
            print(
                f"Subscription not found for cancel webhook: "
                f"{stripe_sub_id}"
            )

    # Handle subscription updates (status changes, etc.)
    elif event['type'] == 'customer.subscription.updated':
        subscription_data = event['data']['object']
        stripe_sub_id = subscription_data['id']
        stripe_status = subscription_data['status']

        try:
            sub = Subscription.objects.get(stripe_sub_id=stripe_sub_id)

            # Map Stripe status to our status
            if stripe_status == 'active':
                sub.status = 'active'
                sub.end_date = None
            elif stripe_status in ['canceled', 'incomplete_expired']:
                sub.status = 'canceled'
                if not sub.end_date:
                    sub.end_date = timezone.now().date()
            elif stripe_status == 'past_due':
                sub.status = 'past_due'

            sub.save()
            print(
                f"✓ Subscription updated via webhook: {stripe_sub_id} - "
                f"Status: {stripe_status}"
            )
        except Subscription.DoesNotExist:
            print(
                f"Subscription not found for update webhook: "
                f"{stripe_sub_id}"
            )

    return HttpResponse(status=200)
