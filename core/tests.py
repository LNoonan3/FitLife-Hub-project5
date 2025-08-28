from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ProgressUpdate, NewsletterSubscriber

User = get_user_model()


class CoreModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='coreuser',
            password='pass'
        )

    def test_create_progress_update(self):
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="First Progress",
            content="Made great progress today!"
        )
        self.assertEqual(update.title, "First Progress")
        self.assertEqual(update.user, self.user)

    def test_create_newsletter_subscriber(self):
        subscriber = NewsletterSubscriber.objects.create(
            email="test@example.com"
        )
        self.assertEqual(subscriber.email, "test@example.com")


class CoreViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='coreuser',
            password='pass'
        )
        self.progress = ProgressUpdate.objects.create(
            user=self.user,
            title="Progress Title",
            content="Progress content."
        )

    def test_progress_list_view(self):
        url = reverse('core:progress_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Progress Title")

    def test_progress_create_view_requires_login(self):
        url = reverse('core:progress_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_newsletter_subscribe(self):
        response = self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': 'newsub@example.com'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            NewsletterSubscriber.objects.filter(
                email='newsub@example.com'
            ).exists()
        )

    def test_progress_create_view_valid_post(self):
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        data = {
            'title': 'New Progress',
            'content': 'Feeling great!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProgressUpdate.objects.filter(
                title='New Progress',
                user=self.user
            ).exists()
        )

    def test_progress_create_view_invalid_post(self):
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        data = {
            'title': '',  # Title required
            'content': 'Missing title'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('title', form.errors)
        self.assertIn('This field is required.', form.errors['title'][0])

    def test_progress_delete_requires_login(self):
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_progress_delete_by_owner(self):
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProgressUpdate.objects.filter(pk=self.progress.pk).exists()
        )

    def test_progress_delete_by_other_user_forbidden(self):
        User.objects.create_user(
            username='otheruser',
            password='pass'
        )
        self.client.login(username='otheruser', password='pass')
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            ProgressUpdate.objects.filter(pk=self.progress.pk).exists()
        )

    def test_newsletter_subscribe_invalid_email(self):
        response = self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': 'not-an-email'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            NewsletterSubscriber.objects.filter(email='not-an-email').exists()
        )
