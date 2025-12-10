from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ProgressUpdate, NewsletterSubscriber

# Get the active user model (custom or default)
User = get_user_model()


class CoreModelTests(TestCase):
    """Model-level tests for core app:
    ProgressUpdate and NewsletterSubscriber."""

    def setUp(self):
        # Create a user to associate with progress updates in model tests
        self.user = User.objects.create_user(
            username='coreuser',
            password='pass'
        )

    def test_create_progress_update(self):
        # Ensure a ProgressUpdate can be created and retains correct fields
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="First Progress",
            content="Made great progress today!"
        )
        self.assertEqual(update.title, "First Progress")
        self.assertEqual(update.content, "Made great progress today!")
        self.assertEqual(update.user, self.user)

    def test_progress_update_str_method(self):
        # Test the __str__ method of ProgressUpdate
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="Test Title",
            content="Test content"
        )
        self.assertEqual(str(update), f"{self.user.username}: Test Title")

    def test_progress_update_created_at_timestamp(self):
        # Test that created_at timestamp is set automatically
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="Timestamp Test",
            content="Testing timestamps"
        )
        self.assertIsNotNone(update.created_at)

    def test_progress_update_updated_at_timestamp(self):
        # Test that updated_at timestamp is set and can be updated
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="Update Test",
            content="Testing update timestamp"
        )
        original_updated_at = update.updated_at
        update.content = "Updated content"
        update.save()
        self.assertGreaterEqual(update.updated_at, original_updated_at)

    def test_create_newsletter_subscriber(self):
        # Ensure a NewsletterSubscriber can be created with an email
        subscriber = NewsletterSubscriber.objects.create(
            email="test@example.com"
        )
        self.assertEqual(subscriber.email, "test@example.com")

    def test_newsletter_subscriber_str_method(self):
        # Test the __str__ method of NewsletterSubscriber
        subscriber = NewsletterSubscriber.objects.create(
            email="subscriber@example.com"
        )
        self.assertEqual(str(subscriber), "subscriber@example.com")

    def test_newsletter_subscriber_unique_email(self):
        # Test that email field is unique
        NewsletterSubscriber.objects.create(email="unique@example.com")
        with self.assertRaises(Exception):
            NewsletterSubscriber.objects.create(email="unique@example.com")

    def test_newsletter_subscriber_subscribed_at_timestamp(self):
        # Test that subscribed_at is set automatically
        subscriber = NewsletterSubscriber.objects.create(
            email="timestamp@example.com"
        )
        self.assertIsNotNone(subscriber.subscribed_at)

    def test_multiple_progress_updates_same_user(self):
        # Test that a user can have multiple progress updates
        ProgressUpdate.objects.create(
            user=self.user,
            title="First",
            content="First update"
        )
        ProgressUpdate.objects.create(
            user=self.user,
            title="Second",
            content="Second update"
        )
        self.assertEqual(
            ProgressUpdate.objects.filter(user=self.user).count(), 2
        )

    def test_progress_update_ordering_by_user(self):
        # Test that multiple updates can be retrieved and ordered
        update1 = ProgressUpdate.objects.create(
            user=self.user,
            title="First Update",
            content="Content 1"
        )
        update2 = ProgressUpdate.objects.create(
            user=self.user,
            title="Second Update",
            content="Content 2"
        )
        updates = ProgressUpdate.objects.filter(user=self.user).order_by('-created_at')
        self.assertEqual(updates[0].id, update2.id)
        self.assertEqual(updates[1].id, update1.id)

    def test_progress_update_content_can_be_long(self):
        # Test that ProgressUpdate can handle long content
        long_content = "x" * 1000
        update = ProgressUpdate.objects.create(
            user=self.user,
            title="Long Content Test",
            content=long_content
        )
        self.assertEqual(len(update.content), 1000)

    def test_newsletter_subscriber_email_validation(self):
        # Test that email field validates email format (Django EmailField)
        # Valid emails should work
        subscriber = NewsletterSubscriber.objects.create(
            email="valid.email+tag@example.co.uk"
        )
        self.assertEqual(subscriber.email, "valid.email+tag@example.co.uk")


class CoreViewTests(TestCase):
    """View-level tests for core app:
    list/create/delete and newsletter actions."""

    def setUp(self):
        # Create a user and a sample progress update for view tests
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
        # Public progress list should load and contain the created title
        url = reverse('core:progress_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Progress Title")

    def test_progress_list_view_template_used(self):
        # Verify correct template is used
        url = reverse('core:progress_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'core/progress_list.html')

    def test_progress_list_view_context(self):
        # Verify context contains updates
        url = reverse('core:progress_list')
        response = self.client.get(url)
        self.assertIn('updates', response.context)
        self.assertEqual(len(response.context['updates']), 1)

    def test_progress_list_view_ordering(self):
        # Test that updates are ordered by most recent first
        old_update = self.progress
        new_update = ProgressUpdate.objects.create(
            user=self.user,
            title="Newer Progress",
            content="This is newer"
        )
        url = reverse('core:progress_list')
        response = self.client.get(url)
        updates = response.context['updates']
        self.assertEqual(updates[0].id, new_update.id)
        self.assertEqual(updates[1].id, old_update.id)

    def test_progress_create_view_requires_login(self):
        # Unauthenticated users should be redirected when accessing create view
        url = reverse('core:progress_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_progress_create_view_get_authenticated(self):
        # Authenticated users should see the form
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/progress_form.html')

    def test_progress_create_view_get_has_form(self):
        # Verify form is in context
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        response = self.client.get(url)
        self.assertIn('form', response.context)

    def test_progress_create_view_valid_post(self):
        # Logged-in user can post valid progress data
        # and create a ProgressUpdate
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

    def test_progress_create_view_valid_post_redirects_to_list(self):
        # After creating, should redirect to progress list
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        data = {
            'title': 'Redirect Test',
            'content': 'Testing redirect'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('core:progress_list'))

    def test_progress_create_view_invalid_post_missing_title(self):
        # Missing required title should return form with errors (status 200)
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

    def test_progress_create_view_invalid_post_missing_content(self):
        # Missing required content should return form with errors
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        data = {
            'title': 'Has Title',
            'content': ''  # Content required
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('content', form.errors)

    def test_progress_delete_by_owner(self):
        # Owner can delete their own progress update
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProgressUpdate.objects.filter(pk=self.progress.pk).exists()
        )

    def test_progress_delete_by_owner_redirects_to_list(self):
        # After deletion, should redirect to progress list
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('core:progress_list'))

    def test_progress_delete_by_other_user_forbidden(self):
        # Another authenticated user should not be able to delete
        # someone else's progress update
        User.objects.create_user(
            username='otheruser',
            password='pass'
        )
        self.client.login(username='otheruser', password='pass')
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        # Expect 404 if access restricted (object not found for other user)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            ProgressUpdate.objects.filter(pk=self.progress.pk).exists()
        )

    def test_progress_delete_nonexistent_progress(self):
        # Trying to delete a non-existent progress update should return 404
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_delete', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_newsletter_subscribe(self):
        # Submitting a valid email should create a
        # NewsletterSubscriber and redirect
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

    def test_newsletter_subscribe_redirects(self):
        # Newsletter subscribe should redirect back to referrer or home
        response = self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': 'redirect@example.com'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_newsletter_subscribe_invalid_email(self):
        # Invalid email should not create a subscriber and should redirect back
        response = self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': 'not-an-email'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            NewsletterSubscriber.objects.filter(email='not-an-email').exists()
        )

    def test_newsletter_subscribe_empty_email(self):
        # Empty email should not create a subscriber
        response = self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': ''}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)

    def test_newsletter_subscribe_duplicate_email(self):
        # Subscribing with an already subscribed email should fail gracefully
        NewsletterSubscriber.objects.create(email='duplicate@example.com')
        self.client.post(
            reverse('core:newsletter_subscribe'),
            {'email': 'duplicate@example.com'}
        )
        # Should still be one subscriber with that email
        self.assertEqual(
            NewsletterSubscriber.objects.filter(
                email='duplicate@example.com'
            ).count(),
            1
        )

    def test_progress_create_view_invalid_post(self):
        # Missing required title should return form with errors (status 200)
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
        # Deleting without logging in should redirect (not allowed)
        url = reverse('core:progress_delete', args=[self.progress.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_progress_list_empty(self):
        # Progress list should handle empty case gracefully
        ProgressUpdate.objects.all().delete()
        url = reverse('core:progress_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        updates = response.context['updates']
        self.assertEqual(len(updates), 0)

    def test_progress_create_with_special_characters(self):
        # Test that progress updates can contain special characters
        self.client.login(username='coreuser', password='pass')
        url = reverse('core:progress_create')
        data = {
            'title': 'Progress with émojis & symbols! 💪',
            'content': 'Content with "quotes" and \'apostrophes\' & special chars!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProgressUpdate.objects.filter(
                title='Progress with émojis & symbols! 💪'
            ).exists()
        )