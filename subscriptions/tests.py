
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Plan, Subscription

User = get_user_model()


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='subuser', password='pass')
        self.plan = Plan.objects.create(
            name='Monthly',
            description='Monthly plan',
            price=9.99,
            interval='monthly',
            is_active=True
        )

    def test_create_subscription(self):
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
    def setUp(self):
        self.user = User.objects.create_user(username='subuser', password='pass')
        self.plan = Plan.objects.create(
            name='Monthly',
            description='Monthly plan',
            price=9.99,
            interval='monthly',
            is_active=True
        )
        self.client.login(username='subuser', password='pass')

    def test_plan_list_view(self):
        url = reverse('subscriptions:plan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)

    def test_my_subscription_view_no_subscription(self):
        url = reverse('subscriptions:my_subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You do not have an active subscription")

    def test_my_subscription_view_with_subscription(self):
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
