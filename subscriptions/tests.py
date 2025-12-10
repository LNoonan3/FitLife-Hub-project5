from operator import sub
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
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
        self.yearly_plan = Plan.objects.create(
            name='Yearly',
            description='Yearly plan',
            price=99.99,
            interval='yearly',
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

    def test_subscription_str_method(self):
        # Test the __str__ method of Subscription
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test123',
            start_date='2025-01-01',
            status='active'
        )
        expected = f"{self.user.username} → {self.plan.name}"
        self.assertEqual(str(sub), expected)

    def test_subscription_status_choices(self):
        # Test different subscription status values
        statuses = ['active', 'canceled', 'past_due']
        for status in statuses:
            sub = Subscription.objects.create(
                user=self.user,
                plan=self.plan,
                stripe_sub_id=f'sub_test_{status}',
                start_date='2025-01-01',
                status=status
            )
            self.assertEqual(sub.status, status)

    def test_subscription_with_end_date(self):
        # Test subscription with an end date (canceled)
        end_date = date(2025, 2, 1)
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test_canceled',
            start_date='2025-01-01',
            end_date=end_date,
            status='canceled'
        )
        self.assertEqual(sub.end_date, end_date)

    def test_subscription_next_payment_date(self):
        # Test next_payment_date field
        next_payment = date(2025, 2, 1)
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test_payment',
            start_date='2025-01-01',
            next_payment_date=next_payment,
            status='active'
        )
        self.assertEqual(sub.next_payment_date, next_payment)

    def test_plan_str_method(self):
        # Test the __str__ method of Plan
        self.assertEqual(str(self.plan), 'Monthly')
        self.assertEqual(str(self.yearly_plan), 'Yearly')

    def test_plan_price_display(self):
        # Test plan price formatting
        self.assertEqual(self.plan.price, 9.99)
        self.assertEqual(self.yearly_plan.price, 99.99)

    def test_plan_interval_choices(self):
        # Test plan interval values
        monthly = Plan.objects.create(
            name='Test Monthly',
            description='Test',
            price=10.00,
            interval='monthly',
            is_active=True
        )
        yearly = Plan.objects.create(
            name='Test Yearly',
            description='Test',
            price=100.00,
            interval='yearly',
            is_active=True
        )
        self.assertEqual(monthly.interval, 'monthly')
        self.assertEqual(yearly.interval, 'yearly')

    def test_plan_is_active_field(self):
        # Test plan active/inactive status
        active_plan = Plan.objects.create(
            name='Active Plan',
            description='Test',
            price=10.00,
            interval='monthly',
            is_active=True
        )
        inactive_plan = Plan.objects.create(
            name='Inactive Plan',
            description='Test',
            price=10.00,
            interval='monthly',
            is_active=False
        )
        self.assertTrue(active_plan.is_active)
        self.assertFalse(inactive_plan.is_active)

    def test_user_multiple_subscriptions(self):
        # Test user with multiple subscriptions
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test_1',
            start_date='2025-01-01',
            status='active'
        )
        Subscription.objects.create(
            user=self.user,
            plan=self.yearly_plan,
            stripe_sub_id='sub_test_2',
            start_date='2025-01-01',
            status='canceled'
        )
        user_subs = Subscription.objects.filter(user=self.user)
        self.assertEqual(user_subs.count(), 2)

    def test_plan_multiple_subscriptions(self):
        # Test plan with multiple user subscriptions
        user2 = User.objects.create_user(
            username='user2',
            password='pass'
        )
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_user1',
            start_date='2025-01-01',
            status='active'
        )
        Subscription.objects.create(
            user=user2,
            plan=self.plan,
            stripe_sub_id='sub_user2',
            start_date='2025-01-01',
            status='active'
        )
        plan_subs = self.plan.subscription_set.all()
        self.assertEqual(plan_subs.count(), 2)

    def test_subscription_timestamps(self):
        # Test created_at and updated_at timestamps
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test_ts',
            start_date='2025-01-01',
            status='active'
        )
        self.assertIsNotNone(sub.created_at)
        self.assertIsNotNone(sub.updated_at)

    def test_subscription_unique_stripe_id(self):
        # Test that stripe_sub_id is unique
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_unique_id',
            start_date='2025-01-01',
            status='active'
        )
        with self.assertRaises(Exception):
            Subscription.objects.create(
                user=self.user,
                plan=self.yearly_plan,
                stripe_sub_id='sub_unique_id',
                start_date='2025-01-01',
                status='active'
            )


class SubscriptionViewTests(TestCase):
    """
    View tests for subscriptions app:
    list plans, show user's subscription, subscribe, cancel, and status pages.
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
            is_active=True,
            stripe_price_id='price_monthly_test'
        )
        self.yearly_plan = Plan.objects.create(
            name='Yearly',
            description='Yearly plan',
            price=99.99,
            interval='yearly',
            is_active=True,
            stripe_price_id='price_yearly_test'
        )
        # authenticate client for views that require login
        self.client.login(username='subuser', password='pass')

    def test_plan_list_view(self):
        # Plan list should be accessible and include the created plan name
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)
        self.assertContains(response, self.yearly_plan.name)

    def test_plan_list_view_template(self):
        # Verify correct template is used
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'subscriptions/plan_list.html')

    def test_plan_list_view_context(self):
        # Verify context contains plans
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertIn('plans', response.context)
        self.assertEqual(len(response.context['plans']), 2)

    def test_plan_list_only_active_plans(self):
        # Only active plans should be displayed
        Plan.objects.create(
            name='Inactive',
            description='Inactive plan',
            price=5.00,
            interval='monthly',
            is_active=False
        )
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertNotContains(response, 'Inactive')
        self.assertEqual(len(response.context['plans']), 2)

    def test_my_subscription_view_no_subscription(self):
        # When user has no subscription the page should inform them accordingly
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/my_subscription.html')

    def test_my_subscription_view_requires_login(self):
        # My subscription view should require login
        self.client.logout()
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_my_subscription_view_with_subscription(self):
        # With an active subscription present the user's subscription page
        # should display plan details and active status.
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test123',
            start_date='2025-01-01',
            next_payment_date=date.today() + timedelta(days=30),
            status='active'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)
        self.assertContains(response, "Active")

    def test_my_subscription_view_with_canceled_subscription(self):
        # Canceled subscription should display with canceled status
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_canceled',
            start_date='2025-01-01',
            end_date=date.today(),
            status='canceled'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)

    def test_my_subscription_view_context(self):
        # Verify context contains subscription data
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_context',
            start_date='2025-01-01',
            next_payment_date=date.today() + timedelta(days=30),
            status='active'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertIn('subscription', response.context)
        self.assertEqual(response.context['subscription'], sub)

    def test_subscribe_plan_view_requires_login(self):
        # Subscribe view should require login
        self.client.logout()
        url = reverse('subscriptions:subscribe_plan', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

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
        # Should redirect to my_subscription, not 200
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )

    def test_subscribe_plan_view_inactive_plan(self):
        # Cannot subscribe to an inactive plan
        inactive = Plan.objects.create(
            name='Inactive',
            description='Test',
            price=5.00,
            interval='monthly',
            is_active=False
        )
        url = reverse('subscriptions:subscribe_plan', args=[inactive.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_subscribe_plan_view_invalid_plan(self):
        # Trying to subscribe to a non-existent plan should return 404
        url = reverse('subscriptions:subscribe_plan', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_subscribe_plan_view_plan_without_stripe_id(self):
        # Plan without stripe_price_id should show error
        plan_no_stripe = Plan.objects.create(
            name='No Stripe',
            description='Test',
            price=5.00,
            interval='monthly',
            is_active=True,
            stripe_price_id=None
        )
        url = reverse('subscriptions:subscribe_plan', args=[plan_no_stripe.id])
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:plan_list')
        )

    def test_subscribe_plan_view_plan_switching_warning(self):
        # Switching plans should show warning about old subscription
        # and redirect to Stripe checkout
        Subscription.objects.create(
            user=self.user,
            plan=self.yearly_plan,
            stripe_sub_id='sub_old',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:subscribe_plan', args=[self.plan.id])
        with patch('stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = MagicMock(url='http://stripe.example.com')
            response = self.client.post(url)
            # Should redirect to Stripe checkout (302 redirect via redirect() function)
            self.assertEqual(response.status_code, 302)
            # Verify it's redirecting to Stripe URL
            self.assertIn('stripe.example.com', response.url)

    def test_cancel_subscription_view_requires_login(self):
        # Cancel subscription view should require login
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_test456',
            start_date='2025-01-01',
            status='active'
        )
        self.client.logout()
        url = reverse('subscriptions:cancel_subscription', args=[sub.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_cancel_subscription_view_only_own_subscription(self):
        # User can only cancel their own subscriptions
        other_user = User.objects.create_user(
            username='otheruser',
            password='pass'
        )
        sub = Subscription.objects.create(
            user=other_user,
            plan=self.plan,
            stripe_sub_id='sub_other',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:cancel_subscription', args=[sub.id])
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
        with patch('stripe.Subscription.delete') as mock_delete:
            mock_delete.return_value = None
            response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'canceled')
        self.assertIsNotNone(sub.end_date)

    def test_cancel_subscription_view_already_canceled(self):
        # Attempting to cancel an already canceled subscription
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_already_canceled',
            start_date='2025-01-01',
            end_date=date.today(),
            status='canceled'
        )
        url = reverse('subscriptions:cancel_subscription', args=[sub.id])
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )

    def test_cancel_subscription_stripe_error(self):
        # Handle Stripe API errors gracefully
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_stripe_error',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:cancel_subscription', args=[sub.id])
        with patch('stripe.Subscription.delete') as mock_delete:
            import stripe
            mock_delete.side_effect = stripe.error.StripeError('API Error')
            response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('subscriptions:my_subscription')
        )

    def test_subscription_success_view(self):
        # Success page shown after subscription flow completes
        url = reverse('subscriptions:subscription_success')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/subscription_success.html')
        self.assertContains(response, "successful")

    def test_subscription_cancel_view(self):
        # confirmation page for cancelled subscription should render
        url = reverse('subscriptions:subscription_cancel')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/subscription_cancel.html')

    def test_subscription_cancel_view_shows_cancellation_info(self):
        # Cancel page should inform user about cancellation
        url = reverse('subscriptions:subscription_cancel')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_plan_list_shows_user_active_plans(self):
        # Plan list should indicate which plans user has active
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_active',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertIn('user_active_plan_ids', response.context)
        self.assertIn(self.plan.id, response.context['user_active_plan_ids'])

    def test_plan_list_shows_user_canceled_plans(self):
        # Plan list should indicate which plans user has canceled
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_canceled',
            start_date='2025-01-01',
            end_date=date.today(),
            status='canceled'
        )
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertIn('user_canceled_plan_ids', response.context)

    def test_plan_list_anonymous_user(self):
        # Anonymous users can view plan list
        self.client.logout()
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)

    def test_plan_list_shows_current_plan(self):
        # Plan list shows current plan for authenticated users
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_current',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertIn('current_plan', response.context)
        self.assertEqual(response.context['current_plan'], self.plan)

    def test_my_subscription_view_shows_subscription_history(self):
        # My subscription page should show subscription history
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_current',
            start_date='2025-01-01',
            status='active'
        )
        Subscription.objects.create(
            user=self.user,
            plan=self.yearly_plan,
            stripe_sub_id='sub_old',
            start_date='2024-01-01',
            end_date='2024-12-31',
            status='canceled'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertIn('all_subscriptions', response.context)

    def test_my_subscription_view_calculates_days_until_payment(self):
        # My subscription should calculate days until next payment
        next_payment = date.today() + timedelta(days=15)
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_payment',
            start_date='2025-01-01',
            next_payment_date=next_payment,
            status='active'
        )
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertIn('days_until_next_payment', response.context)
        self.assertEqual(response.context['days_until_next_payment'], 15)

    def test_cancel_subscription_view_stripe_invalid_request(self):
        # Handle InvalidRequestError when subscription doesn't exist on Stripe
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_invalid',
            start_date='2025-01-01',
            status='active'
        )
        url = reverse('subscriptions:cancel_subscription', args=[subscription.id])
        with patch('stripe.Subscription.delete') as mock_delete:
            import stripe
            # InvalidRequestError requires message and param arguments
            mock_delete.side_effect = stripe.error.InvalidRequestError(
                message='No such subscription',
                param='id'
            )
            self.client.post(url)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'canceled')

    def test_plan_multiple_intervals(self):
        # Test both monthly and yearly plans exist
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        plans = response.context['plans']
        intervals = [p.interval for p in plans]
        self.assertIn('monthly', intervals)
        self.assertIn('yearly', intervals)

    def test_subscription_foreign_key_relationships(self):
        # Test that subscription maintains foreign key relationships
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_sub_id='sub_fk',
            start_date='2025-01-01',
            status='active'
        )
        self.assertEqual(sub.user.username, 'subuser')
        self.assertEqual(sub.plan.name, 'Monthly')
        self.assertEqual(sub.plan.price, 9.99)
