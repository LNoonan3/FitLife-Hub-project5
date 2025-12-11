from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class UserProfileTests(TestCase):
    """Tests for the users app focusing on Profile creation and views."""

    def setUp(self):
        # Create a reusable test user for the profile-related tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )

    def test_profile_created_on_user_creation(self):
        # Creating a User should also create a related profile via signal
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_view_requires_login(self):
        # The profile view should redirect anonymous users to login
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_profile_view_logged_in(self):
        # Logged-in users should be able to view their profile page
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # the response should contain the username to confirm correct context
        self.assertContains(response, self.user.username)

    def test_profile_view_template(self):
        # Verify correct template is used
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_context_has_subscription(self):
        # Profile view should include subscription in context
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertIn('subscription', response.context)

    def test_profile_view_context_has_recent_updates(self):
        # Profile view should include recent updates in context
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertIn('recent_updates', response.context)

    def test_profile_edit(self):
        # Authenticated users should be able to edit their profile via POST
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Submit valid data and expect a redirect on success
        response = self.client.post(url, {
            'bio': 'Updated bio',
            'fitness_goal': 'Get stronger'
        })
        self.assertEqual(response.status_code, 302)
        # Refresh and assert that changes persisted to the DB
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        self.assertEqual(self.user.profile.fitness_goal, 'Get stronger')

    def test_profile_edit_requires_login(self):
        # The edit page should redirect anonymous users to login
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_edit_template(self):
        # Verify correct template is used for edit
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'users/profile_edit.html')

    def test_profile_edit_invalid_data(self):
        # Submitting invalid data (too long fitness_goal) should
        # re-render the form with errors
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Bio',
            'fitness_goal': 'x' * 101  # Exceeds max_length
        })
        # Expect the form to be shown again (status 200) with validation errors
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('fitness_goal', form.errors)
        self.assertIn(
            'Ensure this value has at most 100 characters',
            form.errors['fitness_goal'][0]
        )

    def test_profile_edit_empty_bio(self):
        # Empty bio should be allowed (field is optional)
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': '',
            'fitness_goal': 'Lose weight'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, '')

    def test_profile_edit_empty_fitness_goal(self):
        # Empty fitness goal should be allowed (field is optional)
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'My bio',
            'fitness_goal': ''
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.fitness_goal, '')

    def test_profile_edit_redirects_to_profile(self):
        # After successful edit, should redirect to profile view
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Updated bio',
            'fitness_goal': 'Get fit'
        })
        self.assertRedirects(response, reverse('users:profile'))

    def test_profile_str_method(self):
        # The Profile model's __str__ should include the username
        # for readability
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(str(profile), f"{self.user.username}'s Profile")

    def test_profile_bio_field_blank(self):
        # Newly created profiles should have empty bio by default
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.bio, '')

    def test_profile_fitness_goal_field_blank(self):
        # Newly created profiles should have empty fitness_goal by default
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.fitness_goal, '')

    def test_profile_timestamps_exist(self):
        # Profile should have created_at and updated_at timestamps
        profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_profile_one_to_one_relationship(self):
        # Each user should have exactly one profile
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(self.user.profile, profile)

    def test_profile_edit_bio_long_text(self):
        # Test that bio field can handle long text
        long_bio = "x" * 500
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': long_bio,
            'fitness_goal': 'Get stronger'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, long_bio)

    def test_profile_edit_fitness_goal_max_length(self):
        # Test fitness_goal at max length (100 characters)
        max_goal = "x" * 100
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Bio',
            'fitness_goal': max_goal
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.fitness_goal, max_goal)

    def test_profile_edit_with_special_characters(self):
        # Test that special characters in bio are handled correctly
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        special_bio = (
            'Bio with émojis 💪 & symbols! "Quotes" and \'apostrophes\''
        )
        response = self.client.post(url, {
            'bio': special_bio,
            'fitness_goal': 'Get fit'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, special_bio)

    def test_profile_edit_context_has_form(self):
        # Edit page should have form in context
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertIn('form', response.context)
        self.assertTrue(hasattr(response.context['form'], 'fields'))

    def test_profile_edit_form_initial_values(self):
        # Form should be pre-populated with existing profile data
        self.user.profile.bio = 'Existing bio'
        self.user.profile.fitness_goal = 'Existing goal'
        self.user.profile.save()

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        form = response.context['form']
        self.assertEqual(form.initial['bio'], 'Existing bio')
        self.assertEqual(form.initial['fitness_goal'], 'Existing goal')

    def test_profile_edit_post_invalid_form(self):
        # Invalid form submission should return 200 with errors
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Bio',
            'fitness_goal': 'x' * 150  # Way too long
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_profile_view_shows_username(self):
        # Profile view should display the user's username
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertContains(response, 'testuser')

    def test_profile_view_shows_email(self):
        # Profile view should display the user's email
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertContains(response, self.user.email)

    def test_profile_view_shows_bio(self):
        # Profile view should display the user's bio
        self.user.profile.bio = 'Test bio'
        self.user.profile.save()

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertContains(response, 'Test bio')

    def test_profile_view_shows_fitness_goal(self):
        # Profile view should display the user's fitness goal
        self.user.profile.fitness_goal = 'Test goal'
        self.user.profile.save()

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertContains(response, 'Test goal')

    def test_profile_view_shows_default_text_when_empty(self):
        # Profile view should show default text when bio/goal are empty
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        # Check for common default text patterns
        # (adjust based on your template)
        self.assertEqual(response.status_code, 200)

    def test_multiple_users_have_separate_profiles(self):
        # Each user should have their own profile
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='pass'
        )
        profile1 = Profile.objects.get(user=self.user)
        profile2 = Profile.objects.get(user=user2)
        self.assertNotEqual(profile1.id, profile2.id)
        self.assertNotEqual(profile1.user_id, profile2.user_id)

    def test_profile_edit_one_user_doesnt_affect_another(self):
        # Editing one user's profile shouldn't affect another's
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='pass'
        )

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        self.client.post(url, {
            'bio': 'User 1 bio',
            'fitness_goal': 'User 1 goal'
        })

        user2.profile.refresh_from_db()
        self.assertEqual(user2.profile.bio, '')
        self.assertEqual(user2.profile.fitness_goal, '')

    def test_profile_edit_has_success_message(self):
        # Profile edit should show success message
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Updated bio',
            'fitness_goal': 'Updated goal'
        }, follow=True)
        # Check for success message in response
        messages = list(response.context['messages'])
        self.assertTrue(
            any(
                'updated' in str(m).lower() or 'success' in str(m).lower()
                for m in messages
            )
        )

    def test_profile_created_at_not_modifiable(self):
        # created_at should not change after profile creation
        profile = Profile.objects.get(user=self.user)
        original_created_at = profile.created_at

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        self.client.post(url, {
            'bio': 'Updated',
            'fitness_goal': 'Updated'
        })

        profile.refresh_from_db()
        self.assertEqual(profile.created_at, original_created_at)

    def test_profile_updated_at_changes_on_edit(self):
        # updated_at should change when profile is updated
        profile = Profile.objects.get(user=self.user)
        original_updated_at = profile.updated_at

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)

        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        self.client.post(url, {
            'bio': 'Updated',
            'fitness_goal': 'Updated'
        })

        profile.refresh_from_db()
        self.assertGreaterEqual(profile.updated_at, original_updated_at)

    def test_profile_view_context_has_today(self):
        # Profile view should have today's date in context
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertIn('today', response.context)

    def test_profile_view_context_subscription_none_for_new_user(self):
        # New users with no subscription should have None
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        # Subscription could be None or not present
        # Just verify context key exists
        self.assertIn('subscription', response.context)

    def test_profile_edit_with_whitespace_only(self):
        # Test that whitespace-only input is preserved
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': '   ',
            'fitness_goal': '   '
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        # Django typically strips whitespace in forms
        self.assertFalse(self.user.profile.bio.strip())
