
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Plan, Subscription

User = get_user_model()


class SubscriptionModelTests(TestCase):
    """
    Model tests for subscriptions app:
    verify Plan and Subscription model behavior and relations.
    """
    def setUp(self):
        # Create a test user and an active plan used by model tests
        self.user = User.objects.create_user(
            username='subuser',
            password='pass'
        )
        self.plan = Plan.objects.create(
            name='Monthly',
            description='Monthly plan',
            price=9.99,
            interval='monthly',
            is_active=True
        )

    def test_create_subscription(self):
        # Creating a Subscription should link the user and plan correctly
        # and set the provided status.
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test123',
            start_date='2025-01-01',
            status='active'
        )
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.plan, self.plan)
        self.assertEqual(sub.status, 'active')


class SubscriptionViewTests(TestCase):
    """
    View tests for subscriptions app:
    list plans, show user's subscription, subscribe, cancel, and status pagges.
    """
    def setUp(self):
        # Create a logged-in test user and a sample plan for view tests
        self.user = User.objects.create_user(
            username='subuser',
            password='pass'
        )
        self.plan = Plan.objects.create(
            name='Monthly',
            description='Monthly plan',
            price=9.99,
            interval='monthly',
            is_active=True
        )
        # authenticate client for views that require login
        self.client.login(username='subuser', password='pass')

    def test_plan_list_view(self):
        # Plan list should be accessible and include the created plan name
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)

    def test_my_subscription_view_no_subscription(self):
        # When user has no subscription the page should inform them accordingly
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You do not have an active subscription")

    def test_my_subscription_view_with_subscription(self):
        # With an active subscription present the user's subscription page
        # should display plan details and active status.
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test123',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)
        self.assertContains(response, "Active")

    def test_subscribe_plan_view_prevents_duplicate_subscription(self):
        # Attempting to subscribe to a plan when the user already has an
        # active subscription should redirect back to the subscription page
        # and include an informative message.
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test123',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:subscribe_plan', args=[self.plan.id])
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any(
                "already have an active subscription" in str(m)
                for m in messages
            )
        )

    def test_subscribe_plan_view_invalid_plan(self):
        # Trying to subscribe to a non-existent plan should return 404
        url = reverse('subscriptions:subscribe_plan', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_cancel_subscription_view(self):
        # Cancel endpoint should call external API (mocked here),
        # redirect back to my-subscription and update DB accordingly.
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test456',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:cancel_subscription', args=[sub.id])
        from unittest.mock import patch
        # Patch stripe.Subscription.delete so tests don't call the real API
        with patch('stripe.Subscription.delete') as mock_delete:
            mock_delete.return_value = None
            response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )
        # Ensure subscription state persisted in DB (refresh and check)
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'active')

    def test_subscription_success_view(self):
        # Success page shown after subscription flow completes
        url = reverse('subscriptions:subscription_success')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Subscription")

    def test_subscription_cancel_view(self):
        # confirmation page for cancelled subscription should render
        url = reverse('subscriptions:subscription_cancel')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cancelled")
